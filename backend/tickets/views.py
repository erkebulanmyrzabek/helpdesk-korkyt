from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from django.contrib.auth import authenticate
from django.conf import settings
from .models import Ticket, User, Corpus, Feedback, SystemSetting
from .serializers import TicketSerializer, UserSerializer, CorpusSerializer, FeedbackSerializer, SystemSettingSerializer
from django.db.models import Count, Q, Avg
from django.utils import timezone
import datetime
import pytz
import openpyxl
import io
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from django.http import HttpResponse
from openpyxl.styles import Font, Alignment
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

class IsTeacher(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'teacher'

class IsHelpdesk(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'helpdesk'

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def custom_obtain_auth_token(request):
    """
    Custom token authentication view that works with custom User model
    """
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({'error': 'Username and password required'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(username=username, password=password)
    
    if not user:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
    
    token, created = Token.objects.get_or_create(user=user)
    return Response({'token': token.key, 'role': user.role})

class CorpusViewSet(viewsets.ModelViewSet):
    queryset = Corpus.objects.all()
    serializer_class = CorpusSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsAdmin()]
        return [permissions.IsAuthenticated()]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Check if any tickets use this building name
        ticket_count = Ticket.objects.filter(building=instance.name).exists()
        if ticket_count:
            return Response(
                {"error": f"Нельзя удалить здание '{instance.name}', так как за ним закреплены заявки. Сначала удалите или переместите заявки."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all().order_by('-is_overdue', '-created_at')
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Base ordering: Overdue first, then newest
        base_qs = Ticket.objects.all().order_by('-is_overdue', '-created_at')
        
        if user.role == 'teacher':
            return base_qs.filter(author=user)
        elif user.role == 'helpdesk':
            return base_qs
        elif user.role == 'admin':
            return base_qs
        return Ticket.objects.none()

    def perform_create(self, serializer):
        # Time Restriction from Database
        sys_settings = SystemSetting.get_settings()
        if not sys_settings.allow_outside_working_hours:
            now_utc = timezone.now()
            almaty_tz = pytz.timezone('Asia/Almaty')
            now_local = now_utc.astimezone(almaty_tz).time()
            
            if not (sys_settings.work_start_time <= now_local <= sys_settings.work_end_time):
                 raise ValidationError({
                     "detail": f"Заявки принимаются только с {sys_settings.work_start_time.strftime('%H:%M')} до {sys_settings.work_end_time.strftime('%H:%M')}."
                 })

        ticket = serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsHelpdesk])
    def take(self, request, pk=None):
        ticket = self.get_object()
        
        if ticket.status != 'NEW':
            return Response({'error': 'Заявка уже не новая'}, status=status.HTTP_400_BAD_REQUEST)
        
        ticket.status = 'IN_PROGRESS'
        ticket.assigned_to = request.user
        ticket.taken_at = timezone.now()
        ticket.started_at = timezone.now()
        
        ticket.save()
        return Response(TicketSerializer(ticket, context={'request': request}).data)



    @action(detail=True, methods=['post'], permission_classes=[IsHelpdesk], url_path='need-parts')
    def need_parts(self, request, pk=None):
        ticket = self.get_object()
        
        # Check permissions: must be assigned to this user
        if ticket.assigned_to != request.user:
             return Response({'error': 'Вы не исполнитель этой заявки'}, status=status.HTTP_403_FORBIDDEN)
        
        # Check status transition
        if ticket.status != 'IN_PROGRESS':
            return Response({'error': 'Заявка должна быть в работе'}, status=status.HTTP_400_BAD_REQUEST)

        comment = request.data.get('comment')
        if not comment:
            return Response({'error': 'Комментарий обязателен'}, status=status.HTTP_400_BAD_REQUEST)

        # Set parts wait reason
        ticket.parts_wait_reason = comment
        
        ticket.status = 'WAITING_FOR_PARTS'
        ticket.save()
        
        return Response(TicketSerializer(ticket, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHelpdesk])
    def complete(self, request, pk=None):
        ticket = self.get_object()
        if ticket.assigned_to != request.user:
             return Response({'error': 'Вы не исполнитель этой заявки'}, status=status.HTTP_403_FORBIDDEN)
        
        # Check for media_after (Optional)
        if 'media_after' in request.FILES:
            ticket.media_after = request.FILES['media_after']
            
        report_comment = request.data.get('report_comment')
        # Comment is optional now. If present, set it as report_comment.
        # Logic: Show ONLY the comment entered here.
        if report_comment is not None:
            ticket.report_comment = report_comment
        
        ticket.status = 'CLOSED'
        ticket.completed_at = timezone.now()
        ticket.save()

        return Response(TicketSerializer(ticket, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsTeacher])
    def cancel(self, request, pk=None):
        ticket = self.get_object()
        
        if ticket.author != request.user:
            return Response({'error': 'Вы не автор этой заявки'}, status=status.HTTP_403_FORBIDDEN)
        
        if ticket.status == 'CLOSED':
            return Response({'error': 'Нельзя отменить завершенную заявку'}, status=status.HTTP_400_BAD_REQUEST)
        
        if ticket.status == 'CANCELED':
            return Response({'error': 'Заявка уже отменена'}, status=status.HTTP_400_BAD_REQUEST)
        
        ticket.status = 'CANCELED'
        ticket.save()
        
        return Response(TicketSerializer(ticket, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsTeacher])
    def leave_feedback(self, request, pk=None):
        ticket = self.get_object()
        if ticket.author != request.user:
            return Response({'error': 'Вы не автор этой заявки'}, status=status.HTTP_403_FORBIDDEN)
        
        if ticket.status != 'CLOSED':
            return Response({'error': 'Можно оставить отзыв только для закрытой заявки'}, status=status.HTTP_400_BAD_REQUEST)
        
        if hasattr(ticket, 'feedback'):
             return Response({'error': 'Отзыв уже оставлен'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Handle Feedback
        rating = request.data.get('rating')
        comment = request.data.get('comment')
        
        if not rating:
            return Response({'error': 'Оценка обязательна'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            rating = float(rating)
            if 1 <= rating <= 5:
                Feedback.objects.create(
                    ticket=ticket,
                    user=ticket.assigned_to, # Feedback is FOR the helper
                    rating=rating,
                    comment=comment
                )
                
                # Recalculate Helper Rating
                helper = ticket.assigned_to
                if helper:
                    avg_rating = Feedback.objects.filter(user=helper).aggregate(Avg('rating'))['rating__avg']
                    helper.rating = avg_rating or 0.0
                    helper.save()
                    
                return Response({'status': 'Feedback created'})
            else:
                 return Response({'error': 'Оценка должна быть от 1 до 5'}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({'error': 'Некорректный формат оценки'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[IsAdmin])
    def stats(self, request):
        total = Ticket.objects.count()
        by_status = Ticket.objects.values('status').annotate(count=Count('status'))
        
        # Stats by Helpdesk
        helpdesk_stats = User.objects.filter(role='helpdesk').annotate(
            total_tickets=Count('assigned_tickets', filter=Q(assigned_tickets__status='CLOSED')),
            avg_rating=Avg('assigned_tickets__feedback__rating')
        ).values('id', 'username', 'first_name', 'last_name', 'total_tickets', 'avg_rating', 'rating')
        
        # New Metrics
        total_helpers = User.objects.filter(role='helpdesk').count()
        overdue_count = Ticket.objects.filter(is_overdue=True).exclude(status='CLOSED').count()

        return Response({
            'total': total,
            'by_status': by_status,
            'helpdesk_stats': list(helpdesk_stats),
            'total_helpers': total_helpers,
            'overdue_count': overdue_count
        })

    def _get_report_queryset(self, request):
        queryset = Ticket.objects.all().order_by('-created_at')
        
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        statuses = request.query_params.getlist('statuses[]') or request.query_params.getlist('statuses')
        building = request.query_params.get('building')
        helper_id = request.query_params.get('helper_id')

        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        if statuses:
            queryset = queryset.filter(status__in=statuses)
        if building:
            queryset = queryset.filter(building=building)
        if helper_id:
            queryset = queryset.filter(assigned_to_id=helper_id)
            
        return queryset

    @action(detail=False, methods=['get'], permission_classes=[IsAdmin])
    def report(self, request):
        queryset = self._get_report_queryset(request)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAdmin])
    def export_report(self, request):
        queryset = self._get_report_queryset(request)
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Tickets Report"
        
        # Headers
        headers = [
            'ID', 'Дата создания', 'Статус', 'Автор (ФИО/Email)', 
            'Здание', 'Кабинет', 'Описание', 'Исполнитель', 
            'Дата закрытия'
        ]
        ws.append(headers)
        
        # Style headers
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')

        status_map = dict(Ticket.STATUS_CHOICES)
        
        for ticket in queryset:
            created_at = ticket.created_at.astimezone(pytz.timezone('Asia/Almaty')).strftime('%d.%m.%Y %H:%M') if ticket.created_at else ''
            completed_at = ticket.completed_at.astimezone(pytz.timezone('Asia/Almaty')).strftime('%d.%m.%Y %H:%M') if ticket.completed_at else ''
            
            author_info = f"{ticket.author.get_full_name()} ({ticket.author.email})" if ticket.author.get_full_name() else ticket.author.username
            if not author_info and ticket.author.email:
                author_info = ticket.author.email
            
            row = [
                ticket.id,
                created_at,
                status_map.get(ticket.status, ticket.status),
                author_info,
                ticket.building,
                ticket.room,
                ticket.description,
                ticket.assigned_to.get_full_name() or ticket.assigned_to.username if ticket.assigned_to else '-',
                completed_at or '-',
            ]
            ws.append(row)

        # Auto-adjust column width
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
            adjusted_width = (max_length + 2)
            ws.column_dimensions[column_letter].width = min(adjusted_width, 50)

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = f"tickets_report_{datetime.date.today()}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        wb.save(response)
        return response

    @action(detail=False, methods=['get'], permission_classes=[IsAdmin])
    def export_pdf_stats(self, request):
        queryset = self._get_report_queryset(request).filter(status='CLOSED', assigned_to__isnull=False)
        
        # Aggregate statistics
        stats = queryset.values('assigned_to__first_name', 'assigned_to__last_name', 'assigned_to__username').annotate(count=Count('id')).order_by('-count')
        
        if not stats:
            return Response({'error': 'Нет данных для формирования отчета за этот период'}, status=status.HTTP_400_BAD_REQUEST)
        
        total_closed = sum(s['count'] for s in stats)
        
        labels = []
        sizes = []
        for s in stats:
            name = f"{s['assigned_to__first_name']} {s['assigned_to__last_name']}".strip() or s['assigned_to__username']
            labels.append(name)
            sizes.append(s['count'])

        # Prepare period string for report
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        period_str = "За весь период"
        if date_from and date_to:
            period_str = f"Период: {date_from} — {date_to}"
        elif date_from:
            period_str = f"С {date_from}"
        elif date_to:
            period_str = f"По {date_to}"

        # Generate Chart
        plt.figure(figsize=(10, 6))
        plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'sans-serif']
        
        # Use a more compact layout for the pie chart
        wedges, texts, autotexts = plt.pie(
            sizes, 
            autopct='%1.1f%%', 
            startangle=140, 
            shadow=False,
            pctdistance=0.85
        )
        # Place legend below the chart to keep it centered
        plt.legend(wedges, labels, title="Исполнители", loc="upper center", bbox_to_anchor=(0.5, -0.05), ncol=2)
        plt.title(f"Распределение закрытых заявок (Всего: {total_closed})", pad=20)
        plt.axis('equal')
        
        chart_buffer = io.BytesIO()
        plt.savefig(chart_buffer, format='png', bbox_inches='tight', dpi=150)
        plt.close()
        chart_buffer.seek(0)
        
        # Create PDF
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # Register font for Cyrillic support in PDF
        font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
        font_bold_path = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
        font_name = "Helvetica"
        font_bold_name = "Helvetica-Bold"
        
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('Arial', font_path))
                font_name = "Arial"
                font_bold_name = "Arial" # Fallback
            except:
                pass
        
        if os.path.exists(font_bold_path):
            try:
                pdfmetrics.registerFont(TTFont('Arial-Bold', font_bold_path))
                font_bold_name = "Arial-Bold"
            except:
                pass
        
        # Header
        p.setFont(font_bold_name, 16)
        p.drawCentredString(width/2, height - 2*cm, "Отчет по эффективности хелпдескеров")
        
        p.setFont(font_name, 11)
        p.drawCentredString(width/2, height - 2.8*cm, period_str)
        
        # Draw Chart (Centered)
        from reportlab.lib.utils import ImageReader
        chart_img = ImageReader(chart_buffer)
        chart_w = 16*cm
        chart_h = 10*cm
        p.drawImage(chart_img, (width-chart_w)/2, height - 13.5*cm, width=chart_w, height=chart_h, preserveAspectRatio=True, mask='auto')
        
        # Table of Stats
        y = height - 14.5*cm
        p.setFont(font_bold_name, 12)
        p.drawString(2*cm, y, "Статистика закрытых заявок:")
        y -= 0.8*cm
        
        p.setFont(font_name, 10)
        p.drawString(2*cm, y, "Имя исполнителя")
        p.drawString(10*cm, y, "Кол-во заявок")
        p.drawString(13*cm, y, "Процент (%)")
        y -= 0.2*cm
        p.line(2*cm, y, width - 2*cm, y)
        y -= 0.5*cm
        
        for name, count in zip(labels, sizes):
            if y < 3*cm: # Pagination check
                # Add date footer to page before switching
                p.setFont(font_name, 8)
                p.drawRightString(width - 2*cm, 1*cm, f"Дата формирования: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}")
                p.showPage()
                y = height - 2*cm
                p.setFont(font_name, 10)
            
            percentage = (count / total_closed) * 100
            p.drawString(2*cm, y, name)
            p.drawString(10*cm, y, str(count))
            p.drawString(13*cm, y, f"{percentage:.1f}%")
            y -= 0.6*cm
            
        # Footer Date on last page
        p.setFont(font_name, 8)
        p.drawRightString(width - 2*cm, 1*cm, f"Дата формирования: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}")
        
        p.showPage()
        p.save()
        buffer.seek(0)
        
        response = HttpResponse(buffer, content_type='application/pdf')
        filename = f"stats_report_{datetime.date.today()}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated(), IsAdmin()]
        if self.action in ['list', 'destroy']:
             return [permissions.IsAuthenticated(), IsAdmin()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SystemSettingViewSet(viewsets.ModelViewSet):
    queryset = SystemSetting.objects.all()
    serializer_class = SystemSettingSerializer
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'create', 'destroy']:
            return [permissions.IsAuthenticated(), IsAdmin()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=['get'])
    def current(self, request):
        settings = SystemSetting.get_settings()
        serializer = self.get_serializer(settings)
        return Response(serializer.data)

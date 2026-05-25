from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from django.contrib.auth import authenticate
from django.conf import settings
from .models import Ticket, User, Corpus, Feedback, SystemSetting, RegistrationRequest, TicketAssistOffer
from .serializers import (
    TicketSerializer, UserSerializer, CorpusSerializer, 
    FeedbackSerializer, SystemSettingSerializer, RegistrationRequestSerializer,
    TicketAssistOfferSerializer
)
from django.db.models import Count, Q, Avg, F
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

class IsAdminOrHelpdesk(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['admin', 'helpdesk']

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
        
        if user.role == 'teacher':
            return Ticket.objects.filter(author=user) \
                .filter(Q(hidden_at_by_author__isnull=True) | Q(updated_at__gt=F('hidden_at_by_author'))) \
                .order_by('-updated_at')
        elif user.role in ['admin', 'helpdesk']:
            return self._get_report_queryset(self.request)
            
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

        author = self.request.user
        author_name = author.full_name or author.get_full_name() or author.username
        ticket = serializer.save(author=author, author_name_display=author_name)

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

        if ticket.status != 'IN_PROGRESS':
            return Response({'error': 'Заявку можно завершить только со статусом "В работе"'}, status=status.HTTP_400_BAD_REQUEST)
        
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

    @action(detail=True, methods=['post'], permission_classes=[IsTeacher], url_path='parts-ready')
    def parts_ready(self, request, pk=None):
        ticket = self.get_object()

        if ticket.author != request.user:
            return Response({'error': 'Вы не автор этой заявки'}, status=status.HTTP_403_FORBIDDEN)

        if ticket.status != 'WAITING_FOR_PARTS':
            return Response({'error': 'Заявка не находится в статусе ожидания запчастей'}, status=status.HTTP_400_BAD_REQUEST)

        ticket.status = 'IN_PROGRESS'
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

    @action(detail=True, methods=['post'], permission_classes=[IsHelpdesk], url_path='assist-offers')
    def send_assist_offer(self, request, pk=None):
        ticket = self.get_object()
        
        # 1. Only the main performer can send offers
        if ticket.assigned_to != request.user:
            return Response({'error': 'Только основной исполнитель может приглашать помощников'}, status=status.HTTP_403_FORBIDDEN)
            
        # 2. Check ticket status
        if ticket.status not in ['IN_PROGRESS', 'WAITING_FOR_PARTS']:
            return Response({'error': 'Пригласить помощника можно только для заявок в работе'}, status=status.HTTP_400_BAD_REQUEST)
            
        to_helpdesk_id = request.data.get('to_helpdesk_id')
        if not to_helpdesk_id:
            return Response({'error': 'Не указан ID помощника'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            to_helpdesk = User.objects.get(id=to_helpdesk_id, role='helpdesk')
        except User.DoesNotExist:
            return Response({'error': 'Помощник не найден или не является хелпдеском'}, status=status.HTTP_404_NOT_FOUND)
            
        # 3. Cannot send to self
        if to_helpdesk == request.user:
            return Response({'error': 'Нельзя отправить предложение самому себе'}, status=status.HTTP_400_BAD_REQUEST)
            
        # 4. Cannot send to current assistants
        if ticket.assistants.filter(id=to_helpdesk.id).exists():
            return Response({'error': 'Этот пользователь уже является помощником по данной заявке'}, status=status.HTTP_400_BAD_REQUEST)
            
        # 5. Check if we already have an assistant or a pending offer
        if ticket.assistants.count() >= 1:
             return Response({'error': 'К заявке уже прикреплен помощник. Максимум 2 исполнителя.'}, status=status.HTTP_400_BAD_REQUEST)
             
        if TicketAssistOffer.objects.filter(ticket=ticket, status='PENDING').exists():
            return Response({'error': 'У этой заявки уже есть активное предложение о помощи'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Create offer
        offer = TicketAssistOffer.objects.create(
            ticket=ticket,
            from_helpdesk=request.user,
            to_helpdesk=to_helpdesk,
            status='PENDING'
        )
        
        return Response(TicketAssistOfferSerializer(offer).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsTeacher])
    def hide(self, request, pk=None):
        ticket = self.get_object()
        
        if ticket.author != request.user:
            return Response({'error': 'Вы не автор этой заявки'}, status=status.HTTP_403_FORBIDDEN)
            
        # Use update to avoid triggering auto_now on updated_at
        Ticket.objects.filter(pk=ticket.pk).update(hidden_at_by_author=timezone.now())
        
        return Response({'status': 'hidden'})

    @action(detail=False, methods=['get'], permission_classes=[IsAdmin])
    def stats(self, request):
        total = Ticket.objects.count()
        by_status = Ticket.objects.values('status').annotate(count=Count('status'))
        
        # Stats by Helpdesk (Main + Assisted)
        helpdesks = User.objects.filter(role='helpdesk')
        helpdesk_stats_list = []
        
        for hd in helpdesks:
            # Count where they are the main performer
            main_count = Ticket.objects.filter(assigned_to=hd, status='CLOSED').count()
            # Count where they are the assistant
            asst_count = Ticket.objects.filter(assistants=hd, status='CLOSED').count()
            
            # Average rating (only from tickets where they were main performer usually, 
            # or from Feedback model which has user FK)
            avg_rating = Feedback.objects.filter(user=hd).aggregate(Avg('rating'))['rating__avg']
            
            helpdesk_stats_list.append({
                'id': hd.id,
                'username': hd.username,
                'first_name': hd.first_name,
                'last_name': hd.last_name,
                'total_tickets': main_count + asst_count,
                'avg_rating': avg_rating,
                'rating': hd.rating
            })
        
        # New Metrics
        total_helpers = helpdesks.count()
        overdue_count = Ticket.objects.filter(is_overdue=True).exclude(status='CLOSED').count()

        return Response({
            'total': total,
            'by_status': by_status,
            'helpdesk_stats': helpdesk_stats_list,
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
            queryset = queryset.filter(Q(assigned_to_id=helper_id) | Q(assistants__id=helper_id)).distinct()
            
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
            'Здание', 'Кабинет', 'Описание', 'Исполнитель', 'Помощники',
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
            
            # Assistants string
            assistants = ", ".join([a.full_name or a.username for a in ticket.assistants.all()])

            row = [
                ticket.id,
                created_at,
                status_map.get(ticket.status, ticket.status),
                author_info,
                ticket.building,
                ticket.room,
                ticket.description,
                ticket.assigned_to.get_full_name() or ticket.assigned_to.username if ticket.assigned_to else '-',
                assistants or '-',
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
        queryset = self._get_report_queryset(request).filter(status='CLOSED')
        
        # Manual aggregation for multiple helpdesks
        helpdesk_counts = {} # user_id -> {'name': str, 'count': int}
        
        for ticket in queryset:
            # Main performer
            if ticket.assigned_to:
                uid = ticket.assigned_to.id
                if uid not in helpdesk_counts:
                    name = f"{ticket.assigned_to.first_name} {ticket.assigned_to.last_name}".strip() or ticket.assigned_to.username
                    helpdesk_counts[uid] = {'name': name, 'count': 0}
                helpdesk_counts[uid]['count'] += 1
            
            # Assistants
            for asst in ticket.assistants.all():
                uid = asst.id
                if uid not in helpdesk_counts:
                    name = f"{asst.first_name} {asst.last_name}".strip() or asst.username
                    helpdesk_counts[uid] = {'name': name, 'count': 0}
                helpdesk_counts[uid]['count'] += 1
        
        if not helpdesk_counts:
            return Response({'error': 'Нет данных для формирования отчета за этот период'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Sort by count desc
        sorted_hd = sorted(helpdesk_counts.values(), key=lambda x: x['count'], reverse=True)
        
        total_closed = sum(s['count'] for s in sorted_hd)
        
        labels = [s['name'] for s in sorted_hd]
        sizes = [s['count'] for s in sorted_hd]

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
        if self.action == 'list':
             return [permissions.IsAuthenticated(), IsAdminOrHelpdesk()]
        if self.action == 'destroy':
             return [permissions.IsAuthenticated(), IsAdmin()]
        if self.action == 'details':
             return [permissions.IsAuthenticated(), IsAdminOrHelpdesk()]
        return [permissions.IsAuthenticated()]

    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        user = self.get_object()
        serializer = self.get_serializer(user)
        return Response(serializer.data)

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

class RegistrationRequestViewSet(viewsets.ModelViewSet):
    queryset = RegistrationRequest.objects.all()
    serializer_class = RegistrationRequestSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsAdmin()]

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def approve(self, request, pk=None):
        reg_request = self.get_object()
        if reg_request.status != 'PENDING':
            return Response({'error': 'Этот запрос уже обработан'}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(username=reg_request.username).exists():
            return Response({'error': 'Пользователь с таким логином уже существует'}, status=status.HTTP_400_BAD_REQUEST)

        # Create user
        # Split full_name into first/last name if possible for standard Django fields
        name_parts = reg_request.full_name.split()
        first_name = name_parts[0] if len(name_parts) > 0 else ""
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        user = User.objects.create(
            username=reg_request.username,
            first_name=first_name,
            last_name=last_name,
            full_name=reg_request.full_name,
            institute=reg_request.institute,
            position=reg_request.position,
            role='teacher',
            plain_password=reg_request.plain_password
        )
        user.password = reg_request.password # It's already hashed
        user.save()
        
        reg_request.status = 'APPROVED'
        reg_request.save()
        
        return Response({'status': 'approved', 'user_id': user.id})

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def reject(self, request, pk=None):
        reg_request = self.get_object()
        if reg_request.status != 'PENDING':
            return Response({'error': 'Этот запрос уже обработан'}, status=status.HTTP_400_BAD_REQUEST)
        
        reg_request.status = 'REJECTED'
        reg_request.save()
        return Response({'status': 'rejected'})

class TicketAssistOfferViewSet(viewsets.ModelViewSet):
    queryset = TicketAssistOffer.objects.all()
    serializer_class = TicketAssistOfferSerializer
    permission_classes = [permissions.IsAuthenticated, IsHelpdesk]

    def get_queryset(self):
        user = self.request.user
        queryset = TicketAssistOffer.objects.filter(to_helpdesk=user)
        
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
            
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        # We handle creation via TicketViewSet action for better URL structure
        pass

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        offer = self.get_object()
        
        if offer.to_helpdesk != request.user:
            return Response({'error': 'Это не ваше предложение'}, status=status.HTTP_403_FORBIDDEN)
            
        if offer.status != 'PENDING':
            return Response({'error': 'Предложение уже обработано'}, status=status.HTTP_400_BAD_REQUEST)
            
        ticket = offer.ticket
        if ticket.status in ['CLOSED', 'CANCELED']:
            return Response({'error': 'Заявка уже закрыта или отменена'}, status=status.HTTP_400_BAD_REQUEST)

        # Update offer
        offer.status = 'ACCEPTED'
        offer.responded_at = timezone.now()
        offer.save()

        # Add assistant to ticket
        ticket.assistants.add(request.user)
        ticket.save()

        return Response({'status': 'accepted'})

    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        offer = self.get_object()
        
        if offer.to_helpdesk != request.user:
            return Response({'error': 'Это не ваше предложение'}, status=status.HTTP_403_FORBIDDEN)
            
        if offer.status != 'PENDING':
            return Response({'error': 'Предложение уже обработано'}, status=status.HTTP_400_BAD_REQUEST)

        offer.status = 'DECLINED'
        offer.responded_at = timezone.now()
        offer.save()

        return Response({'status': 'declined'})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        offer = self.get_object()
        
        if offer.from_helpdesk != request.user:
            return Response({'error': 'Вы не автор этого предложения'}, status=status.HTTP_403_FORBIDDEN)
            
        if offer.status != 'PENDING':
            return Response({'error': 'Предложение уже обработано'}, status=status.HTTP_400_BAD_REQUEST)

        offer.status = 'CANCELED'
        offer.responded_at = timezone.now()
        offer.save()

        return Response({'status': 'canceled'})

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from tickets.services.email_service import EmailService
from django.conf import settings
from .models import Ticket, User, Corpus, Feedback, SystemSetting, EmailTemplate, EmailLog
from .serializers import (
    TicketSerializer, UserSerializer, CorpusSerializer, 
    FeedbackSerializer, SystemSettingSerializer,
    EmailTemplateSerializer, EmailLogSerializer
)
from django.db.models import Count, Q, Avg
from django.utils import timezone
import logging
import datetime
import pytz

logger = logging.getLogger('email_forwarding')

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
        
        # Send email logic via Service
        context = {
            'ticket_id': ticket.id,
            'title': ticket.title,
            'description': ticket.description,
            'building': ticket.building,
            'room': ticket.room,
            'user_name': ticket.author.username,
            'dashboard_link': 'http://localhost:5173/helpdesk'
        }
        
        helpdesk_users = User.objects.filter(role='helpdesk')
        recipient_list = [u.email for u in helpdesk_users if u.email]
        
        if recipient_list:
            EmailService.send_notification('new_ticket', context, recipient_list)

    @action(detail=True, methods=['post'], permission_classes=[IsHelpdesk])
    def take(self, request, pk=None):
        ticket = self.get_object()
        
        if ticket.status != 'NEW':
            return Response({'error': 'Заявка уже не новая'}, status=status.HTTP_400_BAD_REQUEST)
        
        ticket.status = 'IN_PROGRESS'
        ticket.assigned_to = request.user
        ticket.taken_at = timezone.now()
        ticket.started_at = timezone.now()
        
        # Set Deadline: Current Day End Time from Settings
        sys_settings = SystemSetting.get_settings()
        now = timezone.now()
        almaty_tz = pytz.timezone('Asia/Almaty')
        now_local = now.astimezone(almaty_tz)
        
        deadline_local = now_local.replace(
            hour=sys_settings.work_end_time.hour,
            minute=sys_settings.work_end_time.minute,
            second=0, microsecond=0
        )
        
        ticket.deadline = deadline_local
        ticket.save()
        return Response(TicketSerializer(ticket, context={'request': request}).data)



    @action(detail=True, methods=['post'], permission_classes=[IsHelpdesk])
    def add_comment(self, request, pk=None):
        ticket = self.get_object()
        


        comment = request.data.get('comment')
        
        if not comment:
            return Response({'error': 'Комментарий обязателен'}, status=status.HTTP_400_BAD_REQUEST)
        
        ticket.report_comment = f"{ticket.report_comment or ''}\n[{timezone.now()}] {request.user.username}: {comment}"
        
        # Extend deadline by 7 days
        ticket.deadline = timezone.now() + datetime.timedelta(days=7)
        ticket.is_overdue = False # Reset overdue if extended
        ticket.save()

        # Send Email Notification via Service
        if ticket.author.email:
            helper_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
            context = {
                'ticket_id': ticket.id,
                'title': ticket.title,
                'comment': comment,
                'helper_name': helper_name,
                'dashboard_link': 'http://localhost:5173/helpdesk'
            }
            EmailService.send_notification('comment_added', context, [ticket.author.email])
        
        return Response(TicketSerializer(ticket, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHelpdesk])
    def complete(self, request, pk=None):
        ticket = self.get_object()
        if ticket.assigned_to != request.user:
             return Response({'error': 'Вы не исполнитель этой заявки'}, status=status.HTTP_403_FORBIDDEN)
        
        # Check for media_after (Optional)
        if 'media_after' in request.FILES:
            ticket.media_after = request.FILES['media_after']

        ticket.status = 'WAITING_APPROVE'
        ticket.completed_at = timezone.now() # Technically finished work, waiting approve
        ticket.save()

        # Send Email Notification via Service
        if ticket.author.email:
            resolution = ticket.report_comment or 'Комментарий отсутствует'
            helper_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
            context = {
                'ticket_id': ticket.id,
                'title': ticket.title,
                'resolution': resolution,
                'helper_name': helper_name,
                'dashboard_link': 'http://localhost:5173/helpdesk'
            }
            EmailService.send_notification('ticket_completed', context, [ticket.author.email])

        return Response(TicketSerializer(ticket, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsTeacher])
    @action(detail=True, methods=['post'], permission_classes=[IsTeacher])
    def approve(self, request, pk=None):
        ticket = self.get_object()
        if ticket.author != request.user:
            return Response({'error': 'Вы не автор этой заявки'}, status=status.HTTP_403_FORBIDDEN)
        
        if ticket.status != 'WAITING_APPROVE':
            return Response({'error': 'Заявка не ожидает подтверждения'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Handle Feedback
        rating = request.data.get('rating')
        comment = request.data.get('feedback')
        
        if rating:
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
                    avg_rating = Feedback.objects.filter(user=helper).aggregate(Avg('rating'))['rating__avg']
                    helper.rating = avg_rating
                    helper.save()
            except ValueError:
                pass # Ignore invalid rating

        ticket.status = 'CLOSED'
        ticket.save()
        return Response(TicketSerializer(ticket, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def mark_unfixable(self, request, pk=None):
        ticket = self.get_object()
        if ticket.status == 'CLOSED':
            raise ValidationError("Нельзя пометить закрытую заявку как неисправимую.")
        
        ticket.status = 'UNFIXABLE'
        ticket.save()
        return Response(TicketSerializer(ticket, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def extend_deadline(self, request, pk=None):
        ticket = self.get_object()
        days = int(request.data.get('days', 3))
        if ticket.deadline:
            ticket.deadline += datetime.timedelta(days=days)
        else:
            ticket.deadline = timezone.now() + datetime.timedelta(days=days)
        
        ticket.is_overdue = False
        ticket.save()
        return Response(TicketSerializer(ticket, context={'request': request}).data)

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

    @action(detail=False, methods=['post'], permission_classes=[IsAdmin])
    def send_test_email(self, request):
        to_email = request.data.get('to_email')
        if not to_email:
            return Response({'error': 'Email получателя обязателен'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Test context
        context = {
            'ticket_id': 'TEST-123',
            'title': 'Тестовая заявка',
            'description': 'Это тестовое уведомление для проверки настроек SMTP.',
            'building': 'Главный корпус',
            'room': '101',
            'user_name': request.user.username,
            'dashboard_link': 'http://localhost:5173',
            'helper_name': 'Система',
            'comment': 'Тестовый комментарий',
            'resolution': 'Проблема успешно решена (тест)'
        }
        
        # We try to send a 'new_ticket' template as a test
        # Note: In a real scenario, we might want to use EmailService.process_send directly
        # but here we use the task entry point to verify the whole chain if task is async
        # Let's use process_send directly to give immediate feedback in the UI for the TEST button
        success = EmailService.process_send('new_ticket', context, [to_email])
        
        if success:
            return Response({'message': f'Тестовое письмо успешно отправлено на {to_email}'})
        else:
            return Response({'error': 'Ошибка при отправке письма. Проверьте логи писем и настройки SMTP.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EmailTemplateViewSet(viewsets.ModelViewSet):
    queryset = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

class EmailLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EmailLog.objects.all()
    serializer_class = EmailLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get_queryset(self):
        queryset = super().get_queryset()
        to_email = self.request.query_params.get('to_email')
        if to_email:
            queryset = queryset.filter(to_email__icontains=to_email)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

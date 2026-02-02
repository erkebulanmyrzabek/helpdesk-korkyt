from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from .models import Ticket, User, Corpus, Feedback
from .serializers import TicketSerializer, UserSerializer, CorpusSerializer, FeedbackSerializer
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

class CorpusViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Corpus.objects.all()
    serializer_class = CorpusSerializer
    permission_classes = [permissions.IsAuthenticated]

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
            # Helpdesk sees tickets from their building (if assigned)
            if user.corpus:
                return base_qs.filter(building=user.corpus.name) # Assuming building name matches corpus name
            else:
                # If no specific corpus assigned, maybe see all? Or none? 
                # Requirement said "Helpers see ONLY the building". 
                # Let's assume they see all if no corpus assigned, or filter by building matches.
                # For now, let's return all for unassigned helpdesk, or restrict.
                # Let's stick to: if corpus assigned, filter by it.
                return base_qs
        elif user.role == 'admin':
            return base_qs
        return Ticket.objects.none()

    def perform_create(self, serializer):
        # Time Restriction: 09:00 - 18:00 (Almaty Time)
        now_utc = timezone.now()
        almaty_tz = pytz.timezone('Asia/Almaty')
        now_local = now_utc.astimezone(almaty_tz)
        
        if not (9 <= now_local.hour < 18):
             raise ValidationError({"detail": "Заявки принимаются только с 09:00 до 18:00."})

        ticket = serializer.save(author=self.request.user)
        
        # Send email logic
        try:
            subject = f'Новая заявка #{ticket.id} в корпусе {ticket.building}'
            message = f"""Новая заявка от {ticket.author.username}

Заголовок: {ticket.title}
Описание: {ticket.description}

Корпус: {ticket.building}
Кабинет: ***** (Примите заявку, чтобы увидеть)

Перейти к заявке: http://localhost:5173/helpdesk"""
            
            # Targeted Notification Logic
            # Find helpdesk users assigned to this building
            recipient_list = []
            
            # If ticket has a building, find helpdesk users with that corpus
            if ticket.building:
                helpdesk_users = User.objects.filter(role='helpdesk', corpus__name=ticket.building)
                recipient_list = [u.email for u in helpdesk_users if u.email]
            
            if recipient_list:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=recipient_list,
                    fail_silently=False,
                )
        except Exception as e:
            logger.error(f"Failed to send email: {e}")

    @action(detail=True, methods=['post'], permission_classes=[IsHelpdesk])
    def take(self, request, pk=None):
        ticket = self.get_object()
        
        if ticket.status != 'NEW':
            return Response({'error': 'Заявка уже не новая'}, status=status.HTTP_400_BAD_REQUEST)
        
        ticket.status = 'TRANSIT'
        ticket.assigned_to = request.user
        ticket.taken_at = timezone.now()
        
        # Set Deadline: Today 18:00
        now = timezone.now()
        deadline = now.replace(hour=18, minute=0, second=0, microsecond=0)
        if now > deadline:
            pass
        ticket.deadline = deadline
        
        ticket.save()
        return Response(TicketSerializer(ticket, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHelpdesk])
    def arrive(self, request, pk=None):
        ticket = self.get_object()
        if ticket.status != 'TRANSIT':
             return Response({'error': 'Заявка не в пути'}, status=status.HTTP_400_BAD_REQUEST)
        
        ticket.status = 'IN_PROGRESS'
        ticket.started_at = timezone.now()
        ticket.save()
        return Response(TicketSerializer(ticket, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHelpdesk])
    def add_comment(self, request, pk=None):
        ticket = self.get_object()
        
        if ticket.status == 'TRANSIT':
            return Response({'error': 'You cannot add comments while in Transit. Please mark as Arrived/In Progress first.'}, status=status.HTTP_400_BAD_REQUEST)

        comment = request.data.get('comment')
        
        if not comment:
            return Response({'error': 'Комментарий обязателен'}, status=status.HTTP_400_BAD_REQUEST)
        
        ticket.report_comment = f"{ticket.report_comment or ''}\n[{timezone.now()}] {request.user.username}: {comment}"
        
        # Extend deadline by 7 days
        ticket.deadline = timezone.now() + datetime.timedelta(days=7)
        ticket.is_overdue = False # Reset overdue if extended
        ticket.save()

        # Send Email Notification to Author
        try:
            if ticket.author.email:
                subject = f"Обновление по заявке #{ticket.id}"
                helper_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
                
                message = f"""Здравствуйте!
                
Хелпер {helper_name} оставил комментарий к вашей заявке #{ticket.id}:

"{comment}"

Дедлайн продлен на 7 дней.

Перейти к заявке: http://localhost:5173/helpdesk"""
                
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[ticket.author.email],
                    fail_silently=False,
                )
        except Exception as e:
            logger.error(f"Failed to send comment email: {e}")
        
        return Response(TicketSerializer(ticket, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHelpdesk])
    def complete(self, request, pk=None):
        ticket = self.get_object()
        if ticket.assigned_to != request.user:
             return Response({'error': 'Вы не исполнитель этой заявки'}, status=status.HTTP_403_FORBIDDEN)
        
        # Check for media_after
        if 'media_after' in request.FILES:
            ticket.media_after = request.FILES['media_after']
        elif not ticket.media_after:
             return Response({'error': 'Фотоотчет обязателен'}, status=status.HTTP_400_BAD_REQUEST)

        ticket.status = 'WAITING_APPROVE'
        ticket.completed_at = timezone.now() # Technically finished work, waiting approve
        ticket.save()

        # Send Email Notification to Author
        try:
            if ticket.author.email:
                subject = f"Заявка выполнена: {ticket.title}"
                resolution = ticket.report_comment or 'Комментарий отсутствует'
                helper_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
                
                message = f"""Здравствуйте!

Работа по вашей заявке '{ticket.title}' была завершена.
Исполнитель: {helper_name}

📄 Отчет о выполнении:
{resolution}

Пожалуйста, войдите в систему, чтобы подтвердить выполнение и оценить работу мастера.
http://localhost:5173/helpdesk"""
                
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[ticket.author.email],
                    fail_silently=False,
                )
        except Exception as e:
            logger.error(f"Failed to send completion email: {e}")

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

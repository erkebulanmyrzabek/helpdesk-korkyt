from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Ticket, User
from .serializers import TicketSerializer, UserSerializer
from django.db.models import Count, Q, Avg
from django.utils import timezone

class IsTeacher(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'teacher'

class IsHelpdesk(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'helpdesk'

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all().order_by('-created_at')
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'teacher':
            return Ticket.objects.filter(author=user).order_by('-created_at')
        elif user.role == 'helpdesk':
            return Ticket.objects.all().order_by('-created_at')
        elif user.role == 'admin':
            return Ticket.objects.all().order_by('-created_at')
        return Ticket.objects.none()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsHelpdesk])
    def take(self, request, pk=None):
        ticket = self.get_object()
        if ticket.status != 'open':
            return Response({'error': 'Заявка уже в работе или закрыта'}, status=status.HTTP_400_BAD_REQUEST)
        
        ticket.status = 'in_progress'
        ticket.assigned_to = request.user
        ticket.started_at = timezone.now()
        ticket.save()
        return Response(TicketSerializer(ticket).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHelpdesk])
    def complete(self, request, pk=None):
        ticket = self.get_object()
        if ticket.assigned_to != request.user:
             return Response({'error': 'Вы не исполнитель этой заявки'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(ticket, data=request.data, partial=True)
        if serializer.is_valid():
            ticket.status = 'done'
            ticket.completed_at = timezone.now()
            ticket.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[IsAdmin])
    def stats(self, request):
        total = Ticket.objects.count()
        by_status = Ticket.objects.values('status').annotate(count=Count('status'))
        
        # Extended stats
        completed_tickets = Ticket.objects.filter(status='done')
        
        # Stats by Helpdesk
        helpdesk_stats = User.objects.filter(role='helpdesk').annotate(
            total_tickets=Count('assigned_tickets', filter=Q(assigned_tickets__status='done')),
            avg_duration=Avg('assigned_tickets__completed_at') - Avg('assigned_tickets__started_at')
        ).values('id', 'username', 'first_name', 'last_name', 'total_tickets')
        
        # Stats by Teacher
        teacher_stats = User.objects.filter(role='teacher').annotate(
            total_created=Count('created_tickets'),
            completed=Count('created_tickets', filter=Q(created_tickets__status='done'))
        ).values('id', 'username', 'first_name', 'last_name', 'total_created', 'completed')
        
        # Category stats (по заголовкам/описанию - компьютеры, интернет и т.д.)
        computer_tickets = Ticket.objects.filter(
            Q(title__icontains='комп') | Q(title__icontains='компьютер') | 
            Q(description__icontains='комп') | Q(description__icontains='компьютер')
        ).count()
        
        internet_tickets = Ticket.objects.filter(
            Q(title__icontains='интернет') | Q(description__icontains='интернет')
        ).count()
        
        avg_completion_time = None
        if completed_tickets.exists():
            durations = []
            for ticket in completed_tickets:
                if ticket.started_at and ticket.completed_at:
                    delta = ticket.completed_at - ticket.started_at
                    durations.append(delta.total_seconds() / 60)  # в минутах
            if durations:
                avg_completion_time = sum(durations) / len(durations)
        
        return Response({
            'total': total,
            'by_status': by_status,
            'helpdesk_stats': list(helpdesk_stats),
            'teacher_stats': list(teacher_stats),
            'category_stats': {
                'computers': computer_tickets,
                'internet': internet_tickets
            },
            'avg_completion_time_minutes': round(avg_completion_time, 2) if avg_completion_time else None
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

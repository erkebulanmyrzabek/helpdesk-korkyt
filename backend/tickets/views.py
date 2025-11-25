from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Ticket, User
from .serializers import TicketSerializer, UserSerializer
from django.db.models import Count

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
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'teacher':
            return Ticket.objects.filter(author=user)
        elif user.role == 'helpdesk':
            return Ticket.objects.all() 
        elif user.role == 'admin':
            return Ticket.objects.all()
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
        ticket.save()
        return Response(TicketSerializer(ticket).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHelpdesk])
    def complete(self, request, pk=None):
        ticket = self.get_object()
        if ticket.assigned_to != request.user:
             return Response({'error': 'Вы не исполнитель этой заявки'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(ticket, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(status='done')
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[IsAdmin])
    def stats(self, request):
        total = Ticket.objects.count()
        by_status = Ticket.objects.values('status').annotate(count=Count('status'))
        return Response({
            'total': total,
            'by_status': by_status
        })

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

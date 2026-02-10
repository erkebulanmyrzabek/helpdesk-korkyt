from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import RegistrationRequest, Feedback
from .views import IsAdmin

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_notifications_summary(request):
    """
    Returns counts of new (unviewed) items for admin dashboard
    """
    new_requests = RegistrationRequest.objects.filter(
        status='PENDING',
        is_viewed_by_admin=False
    ).count()
    
    new_feedbacks = Feedback.objects.filter(
        is_viewed_by_admin=False
    ).count()
    
    return Response({
        'new_requests': new_requests,
        'new_feedbacks': new_feedbacks
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def mark_requests_viewed(request):
    """
    Mark all pending registration requests as viewed by admin
    """
    RegistrationRequest.objects.filter(
        status='PENDING',
        is_viewed_by_admin=False
    ).update(is_viewed_by_admin=True)
    
    return Response({'status': 'marked_viewed'})

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def mark_feedbacks_viewed(request):
    """
    Mark all feedbacks as viewed by admin
    """
    Feedback.objects.filter(
        is_viewed_by_admin=False
    ).update(is_viewed_by_admin=True)
    
    return Response({'status': 'marked_viewed'})

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TicketViewSet, UserViewSet, CorpusViewSet, 
    custom_obtain_auth_token, FeedbackViewSet, 
    SystemSettingViewSet, RegistrationRequestViewSet,
    TicketAssistOfferViewSet
)
from .admin_notifications import (
    admin_notifications_summary,
    mark_requests_viewed,
    mark_feedbacks_viewed
)

router = DefaultRouter()
router.register(r'tickets', TicketViewSet)
router.register(r'users', UserViewSet)
router.register(r'corpuses', CorpusViewSet, basename='corpus')
router.register(r'feedbacks', FeedbackViewSet)
router.register(r'settings', SystemSettingViewSet)
router.register(r'registration-requests', RegistrationRequestViewSet)
router.register(r'assist-offers', TicketAssistOfferViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('api-token-auth/', custom_obtain_auth_token, name='api-token-auth'),
    path('auth/registration-request/', RegistrationRequestViewSet.as_view({'post': 'create'}), name='registration-request'),
    path('admin/notifications/summary/', admin_notifications_summary, name='admin-notifications-summary'),
    path('admin/notifications/mark-requests-viewed/', mark_requests_viewed, name='mark-requests-viewed'),
    path('admin/notifications/mark-feedbacks-viewed/', mark_feedbacks_viewed, name='mark-feedbacks-viewed'),
]

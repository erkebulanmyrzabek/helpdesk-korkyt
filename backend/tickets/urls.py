from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TicketViewSet, UserViewSet, CorpusViewSet, custom_obtain_auth_token, FeedbackViewSet, SystemSettingViewSet

router = DefaultRouter()
router.register(r'tickets', TicketViewSet)
router.register(r'users', UserViewSet)
router.register(r'corpuses', CorpusViewSet, basename='corpus')
router.register(r'feedbacks', FeedbackViewSet)
router.register(r'settings', SystemSettingViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('api-token-auth/', custom_obtain_auth_token, name='api-token-auth'),
]

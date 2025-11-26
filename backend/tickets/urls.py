from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TicketViewSet, UserViewSet, CorpusViewSet
from rest_framework.authtoken.views import obtain_auth_token

router = DefaultRouter()
router.register(r'tickets', TicketViewSet)
router.register(r'users', UserViewSet)
router.register(r'corpuses', CorpusViewSet, basename='corpus')

urlpatterns = [
    path('', include(router.urls)),
    path('api-token-auth/', obtain_auth_token),
]

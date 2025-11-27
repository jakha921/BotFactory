"""
URLs for telegram app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.telegram.views import TelegramUserViewSet

app_name = 'telegram'

router = DefaultRouter()
router.register(r'bots/(?P<bot_id>[^/.]+)/users', TelegramUserViewSet, basename='telegram_user')

urlpatterns = [
    path('', include(router.urls)),
    # Update status endpoint (using detail action)
    path('users/<uuid:pk>/status/', TelegramUserViewSet.as_view({'post': 'update_status'}), name='user-status'),
]


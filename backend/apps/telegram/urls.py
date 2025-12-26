"""
URLs for telegram app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.telegram.views import TelegramUserViewSet, webhook_view
from apps.telegram.webhook_views import TelegramWebhookView

app_name = 'telegram'

router = DefaultRouter()
router.register(r'bots/(?P<bot_id>[^/.]+)/users', TelegramUserViewSet, basename='telegram_user')

urlpatterns = [
    path('', include(router.urls)),
    # Update status endpoint (using detail action)
    path('users/<uuid:pk>/status/', TelegramUserViewSet.as_view({'post': 'update_status'}), name='user-status'),
    # Webhook endpoint - uses bot UUID instead of token for security
    path('webhook/<uuid:bot_id>/', TelegramWebhookView.as_view(), name='telegram-webhook'),
]

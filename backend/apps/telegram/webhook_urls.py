"""
Webhook URLs for telegram app.
Separate URL configuration for webhook endpoint.
"""
from django.urls import path

from apps.telegram.views import webhook_view

app_name = 'telegram_webhook'

urlpatterns = [
    # POST /webhook/<token>/
    path('', webhook_view, name='telegram-webhook'),
]


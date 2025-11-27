"""
URLs for bots app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.bots.views import BotViewSet

app_name = 'bots'

router = DefaultRouter()
router.register(r'', BotViewSet, basename='bot')

urlpatterns = [
    path('', include(router.urls)),
]


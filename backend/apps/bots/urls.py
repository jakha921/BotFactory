"""
URLs for bots app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.bots.views import BotViewSet
from apps.bots.ai_views import ImproveInstructionView, GenerateContentView

app_name = 'bots'

router = DefaultRouter()
router.register(r'', BotViewSet, basename='bot')

urlpatterns = [
    path('', include(router.urls)),
    path('improve-instruction/', ImproveInstructionView.as_view(), name='improve-instruction'),
    path('generate-content/', GenerateContentView.as_view(), name='generate-content'),
]


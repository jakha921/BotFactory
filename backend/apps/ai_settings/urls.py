"""
AI Settings URL configuration.
"""
from django.urls import path
from .views import (
    ImproveInstructionView,
    GenerateContentView,
    AIUsageLimitView,
    AIModelsListView
)

app_name = 'ai_settings'

urlpatterns = [
    path('improve-instruction/', ImproveInstructionView.as_view(), name='improve-instruction'),
    path('generate-content/', GenerateContentView.as_view(), name='generate-content'),
    path('usage-limits/', AIUsageLimitView.as_view(), name='usage-limits'),
    path('models/', AIModelsListView.as_view(), name='models'),
]

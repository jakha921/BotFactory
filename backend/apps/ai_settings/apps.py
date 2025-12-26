"""
AI Settings app configuration.
"""
from django.apps import AppConfig


class AiSettingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ai_settings'
    verbose_name = 'AI Settings'

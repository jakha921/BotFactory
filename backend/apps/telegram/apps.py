"""
Telegram app configuration.
"""
from django.apps import AppConfig


class TelegramConfig(AppConfig):
    """Configuration for telegram app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.telegram'
    verbose_name = 'Telegram'

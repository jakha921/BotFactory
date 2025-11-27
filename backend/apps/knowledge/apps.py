"""
Knowledge app configuration.
"""
from django.apps import AppConfig


class KnowledgeConfig(AppConfig):
    """Configuration for knowledge app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.knowledge'
    verbose_name = 'Knowledge Base'

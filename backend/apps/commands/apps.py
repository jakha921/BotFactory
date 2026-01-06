"""
Commands app configuration.
"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CommandsConfig(AppConfig):
    """Configuration for commands app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.commands'
    verbose_name = _('Commands')

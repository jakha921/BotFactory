"""
Development settings.
"""
from .base import *  # noqa
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

DEBUG = True

# Development-specific settings
# All database settings are now read from .env via base.py
# Allow localhost, 0.0.0.0, and any hosts from ALLOWED_HOSTS env variable
default_hosts = ['localhost', '127.0.0.1', '0.0.0.0']
env_hosts = env.list('ALLOWED_HOSTS', default=[])

# Email backend (console for development)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}


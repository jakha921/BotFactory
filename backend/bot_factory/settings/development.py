"""
Development settings for Bot Factory project.
"""
from .base import *  # noqa
from pathlib import Path

DEBUG = True

# Development-specific settings
# Allow localhost, 0.0.0.0, and any hosts from ALLOWED_HOSTS env variable
default_hosts = ['localhost', '127.0.0.1', '0.0.0.0']
env_hosts = env.list('ALLOWED_HOSTS', default=[])
ALLOWED_HOSTS = list(set(default_hosts + env_hosts))

# For development, dynamically allow ngrok domains via middleware
# The DisallowedHostBypassMiddleware will add ngrok hosts to ALLOWED_HOSTS on-the-fly

# Use SQLite for development if PostgreSQL is not configured
# Override database settings for easier development
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Try to use PostgreSQL if credentials are provided, otherwise use SQLite
db_name = env('DB_NAME', default=None)
db_user = env('DB_USER', default=None)

if db_name and db_user:
    # Use PostgreSQL if configured
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': db_name,
            'USER': db_user,
            'PASSWORD': env('DB_PASSWORD', default='postgres'),
            'HOST': env('DB_HOST', default='localhost'),
            'PORT': env('DB_PORT', default='5432'),
        }
    }
else:
    # Fallback to SQLite for development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

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


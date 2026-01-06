"""
Base settings for Bot Factory project.
"""
import os
from pathlib import Path
from datetime import timedelta
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BASE_DIR.parent  # Root directory of the entire project

# Initialize environment variables
env = environ.Env(
    DEBUG=(bool, False)
)

# Read .env file from project root (not backend/.env)
environ.Env.read_env(os.path.join(PROJECT_ROOT, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='django-insecure-dn#pks(p1h95+&-m9u#9&h_q-klo7ep*m+*04ep-r7hq+(0(tq')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG', default=True)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# Application definition
INSTALLED_APPS = [
    # Django Unfold Admin
    'unfold',  # must be before django.contrib.admin
    'unfold.contrib.filters',
    'unfold.contrib.forms',
    
    # Django core apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',  # JWT token blacklist
    'drf_spectacular',  # OpenAPI 3.0 schema generation
    'corsheaders',
    'django_filters',
    
    # Local apps
    'apps.accounts',
    'apps.bots',
    'apps.knowledge',
    'apps.telegram',  # Must be before chat (chat references TelegramUser)
    'apps.chat',
    'apps.analytics',
    'apps.ai_settings',  # AI settings and usage limits
]

MIDDLEWARE = [
    'core.middleware.DisallowedHostBypassMiddleware',  # Allow ngrok domains in development (MUST be before SecurityMiddleware)
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS middleware (early)
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.middleware.TenantMiddleware',  # Resolve tenant from user or headers
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.APIRequestLoggingMiddleware',  # API request logging
]

ROOT_URLCONF = 'bot_factory.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'bot_factory.wsgi.application'
ASGI_APPLICATION = 'bot_factory.asgi.application'

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='bot_factory_db'),
        'USER': env('DB_USER', default='postgres'),
        'PASSWORD': env('DB_PASSWORD', default='postgres'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Redis Configuration for FSM Storage (aiogram webhook gateway)
# Format: redis://[:password@]host[:port][/db]
# Example: redis://localhost:6379/0
# Example with password: redis://:password@localhost:6379/0
REDIS_URL = env('REDIS_URL', default='redis://localhost:6379/0')

# Cache Configuration (used for rate limiting)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Use Redis cache in production if available
if REDIS_URL and not DEBUG:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
        }
    }

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'core.pagination.StandardResultsSetPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# CORS Settings
# Allow additional origins from environment variable (comma-separated)
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    'http://localhost:3000',  # Frontend dev server
    'http://127.0.0.1:3000',
])

CORS_ALLOW_CREDENTIALS = True

# Import logging configuration
from bot_factory.settings.logging_config import LOGGING

# Django Unfold Settings
UNFOLD = {
    'SITE_TITLE': 'Bot Factory Admin',
    'SITE_HEADER': 'Bot Factory Administration',
    'SITE_URL': '/',
    'SITE_ICON': None,
    'SITE_LOGO': None,
    'SITE_SYMBOL': 'settings',
    'SHOW_HISTORY': True,
    'SHOW_VIEW_ON_SITE': True,
    'ENVIRONMENT': 'bot_factory.settings.environment_callback',
    'DASHBOARD_CALLBACK': None,
    'LOGIN': {
        'image': None,
        'redirect_after': None,
    },
    'STYLES': [],
    'SCRIPTS': [],
}

def environment_callback(request):
    """Callback function for environment indicator in admin."""
    return env('DJANGO_ENV', default='development')

# Google Gemini API
GEMINI_API_KEY = env('GEMINI_API_KEY', default='')

# Webhook Configuration
WEBHOOK_BASE_URL = env('WEBHOOK_BASE_URL', default='http://localhost:8000')

# Rate Limiting
RATELIMIT_ENABLE = env.bool('RATELIMIT_ENABLE', default=True)
RATELIMIT_USE_CACHE = 'default'


# drf-spectacular settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'Bot Factory API',
    'DESCRIPTION': 'REST API for Bot Factory - SaaS platform for creating and managing AI bots with Telegram integration and Google Gemini.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': '/api/v1',
    'COMPONENT_SPLIT_REQUEST': True,
    'AUTHENTICATION_WHITELIST': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'SERVERS': [
        {'url': 'http://localhost:8000', 'description': 'Development server'},
    ],
    'TAGS': [
        {'name': 'Authentication', 'description': 'User authentication and authorization'},
        {'name': 'Bots', 'description': 'Bot management (CRUD operations)'},
        {'name': 'Knowledge Base', 'description': 'Documents and text snippets for bot knowledge'},
        {'name': 'Chat', 'description': 'Chat sessions and message generation'},
        {'name': 'Telegram', 'description': 'Telegram integration and webhooks'},
        {'name': 'Analytics', 'description': 'Statistics and analytics'},
        {'name': 'Subscription', 'description': 'Subscription and usage information'},
    ],
}


# Celery Configuration
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes



"""
ASGI config for bot_factory project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os
import django

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bot_factory.settings.development')

# Initialize Django ASGI application early to ensure everything is set up
# This is important for async views and webhook handlers
django_asgi_app = get_asgi_application()

application = django_asgi_app

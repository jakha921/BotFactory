"""
Bot Factory Django Settings Package
"""
from .base import *  # noqa

# Import environment-specific settings
import os

ENV = os.environ.get('DJANGO_ENV', 'development')

if ENV == 'production':
    from .production import *  # noqa
else:
    from .development import *  # noqa


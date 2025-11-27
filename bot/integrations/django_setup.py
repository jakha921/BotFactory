"""
Django setup for bot usage.
Initializes Django environment for accessing Django ORM and models.
"""
import os
import sys
from pathlib import Path

_django_configured = False


def setup_django():
    """Setup Django for bot usage."""
    global _django_configured
    
    # Only setup once
    if _django_configured:
        return
    
    # Get backend directory
    backend_dir = Path(__file__).resolve().parent.parent.parent / 'backend'
    
    # Add backend to path
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bot_factory.settings.development')
    
    # Initialize Django
    import django
    django.setup()
    
    _django_configured = True


# Auto-setup Django when this module is imported (if not already done)
if not _django_configured:
    setup_django()


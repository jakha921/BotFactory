#!/usr/bin/env python
"""
Script to reset admin password.
Usage: python reset_admin_password.py
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bot_factory.settings.development')
django.setup()

from apps.accounts.models import User

# Default password (you can change this)
DEFAULT_PASSWORD = 'admin123'

# Get or create admin user
admin_email = 'admin@botfactory.com'
try:
    user = User.objects.get(email=admin_email)
    print(f"Found user: {user.email} ({user.name})")
except User.DoesNotExist:
    print(f"Creating new admin user: {admin_email}")
    user = User.objects.create_superuser(
        email=admin_email,
        password=DEFAULT_PASSWORD,
        name='Admin User'
    )
    print(f"Created user: {user.email}")
else:
    # Reset password
    user.set_password(DEFAULT_PASSWORD)
    user.save()
    print(f"Password reset for user: {user.email}")

print("\n" + "="*50)
print("Admin credentials:")
print("="*50)
print(f"Email: {admin_email}")
print(f"Password: {DEFAULT_PASSWORD}")
print("="*50)
print("\nYou can now login at:")
print("  Frontend: http://localhost:3000")
print("  Admin: http://localhost:8000/admin/")
print()


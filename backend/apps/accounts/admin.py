"""
Admin configuration for accounts app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.decorators import display
from unfold.admin import ModelAdmin

from apps.accounts.models import User


@admin.register(User)
class UserAdmin(ModelAdmin, BaseUserAdmin):
    """Admin interface for User model using django-unfold."""
    
    list_display = [
        'email',
        'name',
        'plan',
        'is_active',
        'is_staff',
        'created_at',
    ]
    list_filter = [
        'plan',
        'is_active',
        'is_staff',
        'is_superuser',
        'created_at',
    ]
    search_fields = [
        'email',
        'name',
    ]
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_login']
    
    fieldsets = (
        (None, {
            'fields': ('id', 'email', 'password')
        }),
        ('Personal Info', {
            'fields': ('name', 'avatar', 'telegram_id')
        }),
        ('Subscription', {
            'fields': ('plan',)
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important dates', {
            'fields': ('created_at', 'updated_at', 'last_login')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2', 'plan'),
        }),
    )

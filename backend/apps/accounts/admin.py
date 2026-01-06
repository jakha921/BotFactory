"""
Admin configuration for accounts app.
"""
from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.accounts.models import User, Tenant


@admin.register(Tenant)
class TenantAdmin(ModelAdmin):
    """Admin interface for Tenant model."""
    list_display = ['name', 'slug', 'plan', 'max_bots', 'messages_used', 'created_at']
    list_filter = ['plan', 'created_at']
    search_fields = ['name', 'slug']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'slug')
        }),
        ('Plan', {
            'fields': ('plan', 'plan_expires_at', 'max_bots', 'max_messages_per_month', 'messages_used')
        }),
        ('AI Settings', {
            'fields': ('openai_api_key', 'use_platform_key')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(User)
class UserAdmin(ModelAdmin):
    """Admin interface for User model using django-unfold."""

    list_display = [
        'email',
        'name',
        'tenant',
        'is_active',
        'is_staff',
        'created_at',
    ]
    list_filter = [
        'tenant',
        'tenant__plan',
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
        ('Organization', {
            'fields': ('tenant',)
        }),
        ('Personal Info', {
            'fields': ('name', 'telegram_id', 'avatar')
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
            'fields': ('email', 'name', 'password1', 'password2', 'tenant'),
        }),
    )

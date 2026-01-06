"""
Admin configuration for commands app.
"""
from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.commands.models import Command


@admin.register(Command)
class CommandAdmin(ModelAdmin):
    """Admin interface for Command model."""
    list_display = ['name', 'bot', 'response_type', 'is_active', 'priority', 'created_at']
    list_filter = ['response_type', 'is_active', 'bot', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at']

    fieldsets = (
        ('Basic', {
            'fields': ('bot', 'name', 'description', 'is_active', 'priority')
        }),
        ('Response Type', {
            'fields': ('response_type',)
        }),
        ('Content', {
            'fields': (
                'text_response',
                'ai_prompt_override',
                'form_id',
                'menu_config'
            )
        }),
        ('Metadata', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    )

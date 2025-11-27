"""
Admin configuration for bots app.
"""
from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.bots.models import Bot


@admin.register(Bot)
class BotAdmin(ModelAdmin):
    """Admin interface for Bot model using django-unfold."""
    
    list_display = [
        'name',
        'owner',
        'status',
        'provider',
        'model',
        'created_at',
    ]
    list_filter = [
        'status',
        'provider',
        'created_at',
    ]
    search_fields = [
        'name',
        'description',
        'owner__email',
    ]
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at', 'conversations_count', 'documents_count']
    
    fieldsets = (
        (None, {
            'fields': ('id', 'owner', 'name', 'description', 'status')
        }),
        ('AI Configuration', {
            'fields': ('provider', 'model', 'temperature', 'system_instruction', 'thinking_budget')
        }),
        ('Integrations', {
            'fields': ('telegram_token', 'avatar')
        }),
        ('Statistics', {
            'fields': ('conversations_count', 'documents_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def conversations_count(self, obj):
        """Display conversations count."""
        return obj.conversations_count
    conversations_count.short_description = 'Conversations'
    
    def documents_count(self, obj):
        """Display documents count."""
        return obj.documents_count
    documents_count.short_description = 'Documents'

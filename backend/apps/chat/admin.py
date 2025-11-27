"""
Admin configuration for chat app.
"""
from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.chat.models import ChatSession, ChatMessage


@admin.register(ChatSession)
class ChatSessionAdmin(ModelAdmin):
    """Admin interface for ChatSession model."""
    
    list_display = [
        'id',
        'bot',
        'user',
        'sentiment',
        'is_flagged',
        'updated_at',
    ]
    list_filter = [
        'sentiment',
        'is_flagged',
        'created_at',
    ]
    search_fields = [
        'bot__name',
        'user__first_name',
        'user__username',
    ]
    ordering = ['-updated_at']
    readonly_fields = ['id', 'created_at', 'updated_at', 'message_count']
    
    def message_count(self, obj):
        """Display message count."""
        return obj.message_count
    message_count.short_description = 'Messages'


@admin.register(ChatMessage)
class ChatMessageAdmin(ModelAdmin):
    """Admin interface for ChatMessage model."""
    
    list_display = [
        'id',
        'session',
        'role',
        'content_preview',
        'timestamp',
        'is_flagged',
    ]
    list_filter = [
        'role',
        'is_flagged',
        'timestamp',
    ]
    search_fields = [
        'content',
        'session__bot__name',
    ]
    ordering = ['-timestamp']
    readonly_fields = ['id', 'timestamp']
    
    def content_preview(self, obj):
        """Display content preview."""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

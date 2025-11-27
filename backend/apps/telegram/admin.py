"""
Admin configuration for telegram app.
"""
from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.telegram.models import TelegramUser


@admin.register(TelegramUser)
class TelegramUserAdmin(ModelAdmin):
    """Admin interface for TelegramUser model."""
    
    list_display = [
        'first_name',
        'username',
        'bot',
        'status',
        'message_count',
        'last_active',
    ]
    list_filter = [
        'status',
        'bot',
        'last_active',
    ]
    search_fields = [
        'first_name',
        'last_name',
        'username',
        'telegram_id',
        'bot__name',
    ]
    ordering = ['-last_active']
    readonly_fields = ['id', 'telegram_id', 'first_seen', 'last_active', 'message_count']

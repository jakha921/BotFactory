"""
Admin configuration for analytics app.
"""
from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import BotAnalytics, MessageEvent, UserFeedback, TokenUsage, UserRetention


@admin.register(BotAnalytics)
class BotAnalyticsAdmin(ModelAdmin):
    list_display = ['bot', 'date', 'messages_received', 'messages_sent', 'unique_users', 'tokens_used', 'feedback_ratio']
    list_filter = ['date', 'bot']
    search_fields = ['bot__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'


@admin.register(MessageEvent)
class MessageEventAdmin(ModelAdmin):
    list_display = ['bot', 'event_type', 'telegram_user', 'message_length', 'response_time_ms', 'used_rag', 'timestamp']
    list_filter = ['event_type', 'used_rag', 'timestamp']
    search_fields = ['bot__name', 'telegram_user__username']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'


@admin.register(UserFeedback)
class UserFeedbackAdmin(ModelAdmin):
    list_display = ['bot', 'telegram_user', 'feedback', 'created_at']
    list_filter = ['feedback', 'created_at']
    search_fields = ['bot__name', 'telegram_user__username', 'comment']
    readonly_fields = ['created_at']


@admin.register(TokenUsage)
class TokenUsageAdmin(ModelAdmin):
    list_display = ['bot', 'date', 'input_tokens', 'output_tokens', 'total_tokens', 'estimated_cost_cents']
    list_filter = ['date', 'bot']
    search_fields = ['bot__name']
    readonly_fields = ['total_tokens', 'estimated_cost_cents', 'created_at', 'updated_at']
    date_hierarchy = 'date'


@admin.register(UserRetention)
class UserRetentionAdmin(ModelAdmin):
    list_display = ['bot', 'cohort_date', 'total_users_in_cohort', 'day_1_retention_rate', 'day_7_retention_rate', 'day_30_retention_rate']
    list_filter = ['cohort_date', 'bot']
    search_fields = ['bot__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'cohort_date'

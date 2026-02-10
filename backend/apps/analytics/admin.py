"""
Admin configuration for analytics app.
"""
from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import (
    BotAnalytics, MessageEvent, UserFeedback,
    TokenUsage, UserRetention, WebhookEvent, WebhookMetrics
)


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


@admin.register(WebhookEvent)
class WebhookEventAdmin(ModelAdmin):
    list_display = ['bot', 'event_type', 'status', 'update_id', 'processing_time_ms', 'telegram_signature_valid', 'timestamp']
    list_filter = ['event_type', 'status', 'telegram_signature_valid', 'timestamp']
    search_fields = ['bot__name', 'error_type', 'error_message']
    readonly_fields = ['timestamp', 'total_processing_time_ms']
    date_hierarchy = 'timestamp'

    fieldsets = (
        ('Basic Info', {
            'fields': ('bot', 'event_type', 'status', 'update_id', 'webhook_delivery_time')
        }),
        ('Processing', {
            'fields': ('processing_time_ms', 'celery_task_id', 'response_sent', 'response_time_ms')
        }),
        ('Errors', {
            'fields': ('error_type', 'error_message', 'retry_count'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent', 'telegram_signature_valid')
        }),
        ('Read-only', {
            'fields': ('timestamp', 'total_processing_time_ms')
        }),
    )


@admin.register(WebhookMetrics)
class WebhookMetricsAdmin(ModelAdmin):
    list_display = ['bot', 'date', 'hour', 'requests_received', 'success_rate', 'error_rate', 'avg_processing_time_ms']
    list_filter = ['date', 'bot']
    search_fields = ['bot__name']
    readonly_fields = ['success_rate', 'error_rate', 'created_at', 'updated_at']
    date_hierarchy = 'date'

    fieldsets = (
        ('Basic Info', {
            'fields': ('bot', 'date', 'hour')
        }),
        ('Request Metrics', {
            'fields': ('requests_received', 'requests_processed', 'requests_failed')
        }),
        ('Performance Metrics', {
            'fields': ('avg_processing_time_ms', 'p95_processing_time_ms', 'p99_processing_time_ms')
        }),
        ('Response Metrics', {
            'fields': ('responses_sent', 'avg_response_time_ms')
        }),
        ('Error Breakdown', {
            'fields': ('signature_validation_failures', 'processing_errors', 'timeout_errors')
        }),
        ('Read-only', {
            'fields': ('success_rate', 'error_rate', 'created_at', 'updated_at')
        }),
    )

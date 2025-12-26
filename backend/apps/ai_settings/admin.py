"""
Admin configuration for AI Settings.
"""
from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import AIProvider, AIModel, AIFeature, AIUsageLimit, AIUsageLog


class AIModelInline(TabularInline):
    model = AIModel
    extra = 0
    fields = ['name', 'display_name', 'model_id', 'capability', 'is_active', 'is_default']


@admin.register(AIProvider)
class AIProviderAdmin(ModelAdmin):
    list_display = ['display_name', 'name', 'is_active', 'models_count', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'display_name']
    inlines = [AIModelInline]
    fields = ['name', 'display_name', 'api_key', 'is_active', 'base_url']
    
    def models_count(self, obj):
        return obj.models.count()
    models_count.short_description = 'Models'


@admin.register(AIModel)
class AIModelAdmin(ModelAdmin):
    list_display = ['display_name', 'provider', 'model_id', 'capability', 'is_active', 'is_default']
    list_filter = ['provider', 'capability', 'is_active', 'is_default']
    search_fields = ['name', 'display_name', 'model_id']
    ordering = ['provider', 'sort_order']
    fields = [
        'provider', 'name', 'display_name', 'model_id', 'capability',
        'max_tokens', 'input_cost_per_1k', 'output_cost_per_1k',
        'supports_thinking', 'supports_vision', 'is_active', 'is_default', 'sort_order'
    ]


class AIUsageLimitInline(TabularInline):
    model = AIUsageLimit
    extra = 0
    fields = ['plan', 'max_uses', 'period', 'is_unlimited']


@admin.register(AIFeature)
class AIFeatureAdmin(ModelAdmin):
    list_display = ['name', 'code', 'default_model', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    fields = ['code', 'name', 'description', 'default_model', 'is_active']
    inlines = [AIUsageLimitInline]


@admin.register(AIUsageLimit)
class AIUsageLimitAdmin(ModelAdmin):
    list_display = ['plan', 'feature', 'max_uses', 'period', 'is_unlimited']
    list_filter = ['plan', 'period', 'is_unlimited']
    search_fields = ['plan', 'feature__name']
    fields = ['plan', 'feature', 'max_uses', 'period', 'is_unlimited']


@admin.register(AIUsageLog)
class AIUsageLogAdmin(ModelAdmin):
    list_display = ['user_email', 'feature', 'model_used', 'input_tokens', 'output_tokens', 'success', 'created_at']
    list_filter = ['feature', 'success', 'created_at']
    search_fields = ['user__email', 'user__name']
    readonly_fields = [
        'id', 'user', 'feature', 'model_used', 'bot', 'input_tokens',
        'output_tokens', 'cost_cents', 'success', 'error_message', 'metadata', 'created_at'
    ]
    date_hierarchy = 'created_at'
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def has_add_permission(self, request):
        return False  # Logs are created automatically
    
    def has_change_permission(self, request, obj=None):
        return False  # Logs cannot be edited

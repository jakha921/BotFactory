"""
AI Settings models - providers, models, features, usage limits and logs.
"""
import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from core.utils import encrypt_token, decrypt_token


class AIProvider(models.Model):
    """AI providers (OpenAI, Google, Anthropic)."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)  # openai, gemini, anthropic
    display_name = models.CharField(max_length=100)  # OpenAI, Google Gemini, Anthropic Claude
    api_key = models.CharField(max_length=500, blank=True)  # Encrypted key
    is_active = models.BooleanField(default=True)
    base_url = models.URLField(blank=True)  # For custom endpoints
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'AI Provider'
        verbose_name_plural = 'AI Providers'
        ordering = ['name']
    
    def __str__(self):
        return self.display_name
    
    def save(self, *args, **kwargs):
        """Encrypt API key before saving."""
        if self.api_key and not self.api_key.startswith('gAAAAAB'):  # Not encrypted
            self.api_key = encrypt_token(self.api_key)
        super().save(*args, **kwargs)
    
    @property
    def decrypted_api_key(self) -> str:
        """Return decrypted API key."""
        if not self.api_key:
            return ''
        return decrypt_token(self.api_key)


class AIModel(models.Model):
    """AI models available for use."""
    
    CAPABILITY_CHOICES = [
        ('chat', 'Chat/Conversation'),
        ('reasoning', 'Advanced Reasoning'),
        ('fast', 'Fast Response'),
        ('vision', 'Vision/Images'),
        ('code', 'Code Generation'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(AIProvider, on_delete=models.CASCADE, related_name='models')
    name = models.CharField(max_length=100)  # gpt-4o, gemini-2.5-flash, claude-4-opus
    display_name = models.CharField(max_length=150)  # GPT-4o (Latest), Gemini 2.5 Flash
    model_id = models.CharField(max_length=100)  # Actual API model ID
    capability = models.CharField(max_length=20, choices=CAPABILITY_CHOICES, default='chat')
    max_tokens = models.IntegerField(default=8192)
    input_cost_per_1k = models.DecimalField(max_digits=10, decimal_places=6, default=0)  # $ per 1k tokens
    output_cost_per_1k = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    supports_thinking = models.BooleanField(default=False)
    supports_vision = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)  # Default model for new bots
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'AI Model'
        verbose_name_plural = 'AI Models'
        ordering = ['provider', 'sort_order', 'name']
        unique_together = ['provider', 'model_id']
        indexes = [
            models.Index(fields=['is_active', 'is_default']),
        ]
    
    def __str__(self):
        return f"{self.provider.display_name} - {self.display_name}"


class AIFeature(models.Model):
    """AI features that have usage limits."""
    
    FEATURE_CHOICES = [
        ('improve_instruction', 'Improve with AI'),
        ('generate_content', 'Generate with AI'),
        ('chat_response', 'Chat Response'),
        ('transcription', 'Audio Transcription'),
        ('file_processing', 'File Processing'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True, choices=FEATURE_CHOICES)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    default_model = models.ForeignKey(
        AIModel, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='default_for_features'
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'AI Feature'
        verbose_name_plural = 'AI Features'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class AIUsageLimit(models.Model):
    """Usage limits per subscription plan."""
    
    PERIOD_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan = models.CharField(max_length=20)  # Free, Pro, Enterprise
    feature = models.ForeignKey(AIFeature, on_delete=models.CASCADE, related_name='limits')
    max_uses = models.IntegerField(default=1)  # Number of uses
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES, default='weekly')
    is_unlimited = models.BooleanField(default=False)  # For Enterprise
    
    class Meta:
        verbose_name = 'AI Usage Limit'
        verbose_name_plural = 'AI Usage Limits'
        unique_together = ['plan', 'feature']
        ordering = ['plan', 'feature']
    
    def __str__(self):
        if self.is_unlimited:
            return f"{self.plan} - {self.feature.name}: Unlimited"
        return f"{self.plan} - {self.feature.name}: {self.max_uses}/{self.period}"


class AIUsageLog(models.Model):
    """Log of AI feature usage by users."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_usage_logs')
    feature = models.ForeignKey(AIFeature, on_delete=models.CASCADE, related_name='usage_logs')
    model_used = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True, related_name='usage_logs')
    bot = models.ForeignKey('bots.Bot', on_delete=models.SET_NULL, null=True, blank=True, related_name='ai_usage_logs')
    input_tokens = models.IntegerField(default=0)
    output_tokens = models.IntegerField(default=0)
    cost_cents = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)  # Additional context
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'AI Usage Log'
        verbose_name_plural = 'AI Usage Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'feature', 'created_at']),
            models.Index(fields=['created_at']),
            models.Index(fields=['success']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.feature.name} - {self.created_at}"
    
    @classmethod
    def get_usage_count(cls, user, feature_code: str, period: str = 'weekly') -> int:
        """Get usage count for a feature within a period."""
        now = timezone.now()
        
        if period == 'daily':
            start_date = now - timedelta(days=1)
        elif period == 'weekly':
            start_date = now - timedelta(weeks=1)
        elif period == 'monthly':
            start_date = now - timedelta(days=30)
        else:
            start_date = now - timedelta(weeks=1)
        
        return cls.objects.filter(
            user=user,
            feature__code=feature_code,
            created_at__gte=start_date,
            success=True
        ).count()
    
    @classmethod
    def can_use_feature(cls, user, feature_code: str) -> tuple[bool, str]:
        """Check if user can use a feature based on limits."""
        try:
            feature = AIFeature.objects.get(code=feature_code, is_active=True)
        except AIFeature.DoesNotExist:
            return False, "Feature not available"
        
        try:
            limit = AIUsageLimit.objects.get(plan=user.plan, feature=feature)
        except AIUsageLimit.DoesNotExist:
            return False, "No limit configured for your plan"
        
        if limit.is_unlimited:
            return True, "Unlimited"
        
        current_usage = cls.get_usage_count(user, feature_code, limit.period)
        
        if current_usage >= limit.max_uses:
            return False, f"Limit reached: {current_usage}/{limit.max_uses} per {limit.period}"
        
        remaining = limit.max_uses - current_usage
        return True, f"{remaining} uses remaining this {limit.period}"

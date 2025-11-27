"""
Bots models for Bot Factory.
Bot model represents an AI bot configuration.
"""
import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings
from core.utils import encrypt_token, decrypt_token


class Bot(models.Model):
    """
    Bot model representing an AI bot configuration.
    
    Fields according to frontend/types.ts:
    - id: UUID primary key
    - owner: FK to User
    - name: Bot name (max 100 chars)
    - description: Bot description (optional)
    - status: Bot status (draft/active/paused/error)
    - model: AI model name (gemini-2.5-flash, gpt-4, etc.)
    - provider: AI provider (gemini/openai/anthropic)
    - temperature: Temperature parameter (0-2)
    - system_instruction: System instruction for the bot
    - thinking_budget: Thinking budget in ms (optional, for Gemini thinking models)
    - telegram_token: Telegram bot token (optional, encrypted)
    - avatar: Avatar emoji or URL (optional)
    - created_at: Creation timestamp
    - updated_at: Last update timestamp
    """
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('error', 'Error'),
    ]
    
    PROVIDER_CHOICES = [
        ('gemini', 'Gemini'),
        ('openai', 'OpenAI'),
        ('anthropic', 'Anthropic'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bots'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    model = models.CharField(max_length=100)  # gemini-2.5-flash, gpt-4, etc.
    provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        default='gemini'
    )
    temperature = models.FloatField(default=0.7)
    system_instruction = models.TextField(blank=True)
    thinking_budget = models.IntegerField(null=True, blank=True)  # For Gemini thinking models
    telegram_token = models.CharField(max_length=500, blank=True)  # Encrypted token (stored longer)
    avatar = models.CharField(max_length=200, blank=True)  # Emoji or URL
    
    # UI Configuration for Telegram Bot
    ui_config = models.JSONField(default=dict, blank=True)  # General UI configuration (inline keyboards, forms)
    default_inline_keyboard = models.JSONField(default=list, blank=True)  # Default inline keyboard configuration
    welcome_message = models.TextField(blank=True)  # Welcome message for /start command
    help_message = models.TextField(blank=True)  # Help message for /help command
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Bot'
        verbose_name_plural = 'Bots'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.owner.email})"
    
    def __repr__(self):
        return f"<Bot: {self.name} (id={self.id})>"
    
    @property
    def conversations_count(self):
        """Return the number of conversations for this bot."""
        # Will be implemented when chat app is created
        if hasattr(self, 'chat_sessions'):
            return self.chat_sessions.count()
        return 0
    
    @property
    def documents_count(self):
        """Return the number of documents for this bot."""
        # Will be implemented when knowledge app is created
        if hasattr(self, 'documents'):
            return self.documents.count()
        return 0
    
    def save(self, *args, **kwargs):
        """Override save to encrypt telegram_token before saving."""
        # Encrypt telegram_token if it's provided and not already encrypted
        if self.telegram_token and not self.telegram_token.startswith('gAAAAAB'):  # Fernet prefix
            # Check if it looks like a plain token (contains colon and numbers)
            if ':' in self.telegram_token and len(self.telegram_token.split(':')) == 2:
                self.telegram_token = encrypt_token(self.telegram_token)
        super().save(*args, **kwargs)
    
    @property
    def decrypted_telegram_token(self) -> str:
        """Return decrypted telegram_token."""
        if not self.telegram_token:
            return ''
        return decrypt_token(self.telegram_token)

"""
Chat models for Bot Factory.
ChatSession and ChatMessage models for managing chat conversations.
"""
import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings
# from django.contrib.postgres.fields import JSONField  # Not needed in Django 3.1+


class ChatSession(models.Model):
    """
    ChatSession model for managing chat sessions between users and bots.
    
    Fields according to frontend/types.ts:
    - id: UUID primary key
    - bot: FK to Bot
    - user: FK to TelegramUser (will be created in telegram app)
    - created_at: Session creation timestamp
    - updated_at: Last update timestamp
    - is_flagged: Whether session is flagged
    - sentiment: Sentiment analysis (positive/neutral/negative)
    - last_message: Cached last message text
    """
    
    SENTIMENT_CHOICES = [
        ('positive', 'Positive'),
        ('neutral', 'Neutral'),
        ('negative', 'Negative'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bot = models.ForeignKey(
        'bots.Bot',
        on_delete=models.CASCADE,
        related_name='chat_sessions'
    )
    user = models.ForeignKey(
        'telegram.TelegramUser',
        on_delete=models.CASCADE,
        related_name='chat_sessions',
        null=True,  # Will be set when telegram app is created
        blank=True
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_flagged = models.BooleanField(default=False)
    sentiment = models.CharField(
        max_length=20,
        choices=SENTIMENT_CHOICES,
        default='neutral'
    )
    last_message = models.TextField(blank=True)  # Cached last message
    
    class Meta:
        verbose_name = 'Chat Session'
        verbose_name_plural = 'Chat Sessions'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['bot', 'updated_at']),
            models.Index(fields=['user']),
            models.Index(fields=['is_flagged']),
        ]
    
    def __str__(self):
        return f"Session {self.id} - {self.bot.name}"
    
    def __repr__(self):
        return f"<ChatSession: {self.id} (bot={self.bot.name})>"
    
    @property
    def message_count(self):
        """Return the number of messages in this session."""
        return self.messages.count()


class ChatMessage(models.Model):
    """
    ChatMessage model for storing individual messages in chat sessions.
    
    Fields according to frontend/types.ts:
    - id: UUID primary key
    - session: FK to ChatSession
    - role: Message role (user/model)
    - content: Message content
    - timestamp: Message timestamp
    - is_thinking: Whether this is a thinking message (optional, for Gemini)
    - is_flagged: Whether message is flagged
    - attachments: JSONField for attachments (optional)
    """
    
    ROLE_CHOICES = [
        ('user', 'User'),
        ('model', 'Model'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES
    )
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    is_thinking = models.BooleanField(default=False)  # For Gemini thinking models
    is_flagged = models.BooleanField(default=False)
    attachments = models.JSONField(default=dict, blank=True, null=True)  # For future use
    
    class Meta:
        verbose_name = 'Chat Message'
        verbose_name_plural = 'Chat Messages'
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['session', 'timestamp']),
            models.Index(fields=['role', 'timestamp']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['role']),
            models.Index(fields=['is_flagged']),
        ]
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."
    
    def __repr__(self):
        return f"<ChatMessage: {self.id} (role={self.role})>"
    
    def save(self, *args, **kwargs):
        """Save message and update session's last_message and updated_at."""
        super().save(*args, **kwargs)
        # Update session's last_message and updated_at
        self.session.last_message = self.content[:200]  # Cache first 200 chars
        self.session.updated_at = self.timestamp
        self.session.save(update_fields=['last_message', 'updated_at'])

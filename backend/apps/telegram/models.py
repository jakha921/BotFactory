"""
Telegram models for Bot Factory.
TelegramUser model for managing Telegram users interacting with bots.
"""
import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings


class TelegramUser(models.Model):
    """
    TelegramUser model for managing Telegram users.
    
    Fields according to frontend/types.ts:
    - id: UUID primary key
    - telegram_id: Telegram user ID (BigInteger, unique)
    - bot: FK to Bot
    - username: Telegram username (optional)
    - first_name: User's first name
    - last_name: User's last name (optional)
    - avatar_url: Avatar URL (optional)
    - status: User status (active/blocked)
    - first_seen: First interaction timestamp
    - last_active: Last activity timestamp
    - message_count: Total message count
    - notes: Admin notes (optional)
    """
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('blocked', 'Blocked'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    telegram_id = models.BigIntegerField(unique=True)
    bot = models.ForeignKey(
        'bots.Bot',
        on_delete=models.CASCADE,
        related_name='telegram_users'
    )
    username = models.CharField(max_length=100, blank=True, null=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    avatar_url = models.URLField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    first_seen = models.DateTimeField(default=timezone.now)
    last_active = models.DateTimeField(auto_now=True)
    message_count = models.IntegerField(default=0)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Telegram User'
        verbose_name_plural = 'Telegram Users'
        ordering = ['-last_active']
        indexes = [
            models.Index(fields=['bot', 'status']),
            models.Index(fields=['telegram_id']),
            models.Index(fields=['last_active']),
        ]
        unique_together = [['telegram_id', 'bot']]  # One user per bot
    
    def __str__(self):
        name = f"{self.first_name} {self.last_name or ''}".strip()
        if self.username:
            return f"{name} (@{self.username})"
        return f"{name} (ID: {self.telegram_id})"
    
    def __repr__(self):
        return f"<TelegramUser: {self.telegram_id} (bot={self.bot.name})>"

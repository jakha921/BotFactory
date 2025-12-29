"""
Models for accounts app.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from cryptography.fernet import Fernet
from django.conf import settings


class User(AbstractUser):
    """Custom User model with telegram integration."""
    telegram_id = models.BigIntegerField(null=True, blank=True, unique=False)  # Changed from unique=True
    plan = models.CharField(max_length=50, default='Free')  # Added plan field
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'auth_user'
        swappable = 'AUTH_USER_MODEL'
        verbose_name = 'user'
        verbose_name_plural = 'users'
    
    def __str__(self):
        return self.username or self.email


class UserAPIKey(models.Model):
    """User API Keys for AI providers with encryption."""
    PROVIDER_CHOICES = [
        ('openai', 'OpenAI'),
        ('gemini', 'Google Gemini'),
        ('anthropic', 'Anthropic'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    encrypted_key = models.CharField(max_length=500)
    name = models.CharField(max_length=100)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [['user', 'provider', 'name']]
        verbose_name = 'User API Key'
        verbose_name_plural = 'User API Keys'
    
    def __str__(self):
        return f"{self.user.email} - {self.provider} - {self.name}"
    
    def encrypt_key(self, plain_key: str) -> None:
        """Encrypt using Fernet (symmetric encryption)."""
        fernet_key = settings.ENCRYPTION_KEY.encode()
        f = Fernet(fernet_key)
        self.encrypted_key = f.encrypt(plain_key.encode()).decode()
    
    def decrypt_key(self) -> str:
        """Decrypt the API key."""
        fernet_key = settings.ENCRYPTION_KEY.encode()
        f = Fernet(fernet_key)
        return f.decrypt(self.encrypted_key.encode()).decode()
    
    @property
    def masked_key(self) -> str:
        """Return a masked version of the key for display."""
        try:
            decrypted = self.decrypt_key()
            if len(decrypted) <= 8:
                return '****'
            return f"{decrypted[:3]}...{decrypted[-4:]}"
        except:
            return '****'


class UserNotificationPreferences(models.Model):
    """User notification preferences."""
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='notification_prefs'
    )
    email_alerts = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=False)
    weekly_digest = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Notification Preferences'
        verbose_name_plural = 'Notification Preferences'
    
    def __str__(self):
        return f"Notification Preferences for {self.user.email}"

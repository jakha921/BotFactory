"""
Models for accounts app.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from cryptography.fernet import Fernet
from django.conf import settings


class Tenant(models.Model):
    """Organization/Company - owner of bots."""
    name = models.CharField(max_length=255, verbose_name="Name")
    slug = models.SlugField(unique=True, max_length=100)

    # Plan type
    PLAN_CHOICES = [
        ('FREE', 'Free'),
        ('STARTER', 'Starter'),
        ('PRO', 'Pro'),
        ('ENTERPRISE', 'Enterprise'),
    ]
    plan = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        default='FREE',
        verbose_name="Plan"
    )
    plan_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Plan expires at"
    )

    # Limits
    max_bots = models.IntegerField(
        default=1,
        verbose_name="Max bots",
        help_text="Maximum number of bots allowed"
    )
    max_messages_per_month = models.IntegerField(
        default=1000,
        verbose_name="Max messages per month"
    )
    messages_used = models.IntegerField(
        default=0,
        verbose_name="Messages used"
    )

    # AI settings
    openai_api_key = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name="OpenAI API Key",
        help_text="Encrypted API key for OpenAI"
    )
    use_platform_key = models.BooleanField(
        default=True,
        verbose_name="Use platform key",
        help_text="Use platform's API key instead of custom"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated at")

    class Meta:
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"
        ordering = ['-created_at']
        db_table = 'accounts_tenant'

    def __str__(self):
        return f"{self.name} ({self.plan})"

    @property
    def has_openai_key(self) -> bool:
        """Check if tenant has custom OpenAI key."""
        return bool(self.openai_api_key and not self.use_platform_key)

    def get_openai_key(self) -> str:
        """Get decrypted OpenAI key."""
        if not self.openai_api_key:
            return settings.OPENAI_API_KEY or ""

        try:
            fernet_key = settings.ENCRYPTION_KEY.encode()
            f = Fernet(fernet_key)
            return f.decrypt(self.openai_api_key.encode()).decode()
        except Exception:
            return ""

    def set_openai_key(self, key: str) -> None:
        """Encrypt and set OpenAI key."""
        fernet_key = settings.ENCRYPTION_KEY.encode()
        f = Fernet(fernet_key)
        self.openai_api_key = f.encrypt(key.encode()).decode()

    def can_create_bot(self) -> bool:
        """Check if tenant can create more bots."""
        return self.bots.count() < self.max_bots

    def has_messages_remaining(self) -> bool:
        """Check if tenant has messages remaining this month."""
        return self.messages_used < self.max_messages_per_month


class User(AbstractUser):
    """Custom User model with telegram integration."""
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='users',
        null=True,  # Temporarily null for migration
        blank=True,
        verbose_name="Organization"
    )
    telegram_id = models.BigIntegerField(
        null=True,
        blank=True,
        unique=False,
        verbose_name="Telegram ID"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated at")
    
    class Meta:
        db_table = 'auth_user'
        swappable = 'AUTH_USER_MODEL'
        verbose_name = 'user'
        verbose_name_plural = 'users'

    @property
    def plan(self):
        """Get plan from tenant for backward compatibility."""
        return self.tenant.plan if self.tenant else 'FREE'

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

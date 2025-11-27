"""
Accounts models for Bot Factory.
Custom User model with UUID primary key and subscription plan.
"""
import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom user manager for User model."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user with an email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser with an email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('plan', 'Enterprise')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model with UUID primary key.
    
    Fields:
    - id: UUID primary key
    - email: Unique email address (used for authentication)
    - name: User's full name
    - password: Hashed password
    - plan: Subscription plan (Free/Pro/Enterprise)
    - telegram_id: Optional Telegram user ID
    - avatar: Optional avatar URL or path
    - is_active: Account active status
    - is_staff: Admin access status
    - is_superuser: Superuser status
    - created_at: Account creation timestamp
    - updated_at: Last update timestamp
    """
    
    PLAN_CHOICES = [
        ('Free', 'Free'),
        ('Pro', 'Pro'),
        ('Enterprise', 'Enterprise'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, max_length=255)
    name = models.CharField(max_length=255)
    plan = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        default='Free'
    )
    telegram_id = models.BigIntegerField(null=True, blank=True, unique=True)
    avatar = models.CharField(max_length=500, blank=True)  # URL or file path
    
    # Django auth fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['created_at']),
            models.Index(fields=['plan']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.email})"
    
    def __repr__(self):
        return f"<User: {self.email}>"
    
    def get_full_name(self):
        """Return the user's full name."""
        return self.name
    
    def get_short_name(self):
        """Return the user's short name."""
        return self.name.split()[0] if self.name else self.email
    
    @property
    def is_free_plan(self):
        """Check if user is on Free plan."""
        return self.plan == 'Free'
    
    @property
    def is_pro_plan(self):
        """Check if user is on Pro plan."""
        return self.plan == 'Pro'
    
    @property
    def is_enterprise_plan(self):
        """Check if user is on Enterprise plan."""
        return self.plan == 'Enterprise'

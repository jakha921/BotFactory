"""
Commands app - Bot command management.
"""
from django.db import models
from apps.bots.models import Bot


class ResponseType(models.TextChoices):
    """Command response types."""
    TEXT = 'text', 'Текст'
    AI = 'ai', 'AI ответ'
    FORM = 'form', 'Форма'
    MENU = 'menu', 'Меню'


class Command(models.Model):
    """
    Bot commands (e.g., /start, /help).

    Allows dynamic command configuration through admin panel
    instead of hardcoding them in bot handlers.
    """
    bot = models.ForeignKey(
        Bot,
        on_delete=models.CASCADE,
        related_name='commands',
        verbose_name="Bot"
    )
    name = models.CharField(
        max_length=100,
        help_text="Command name without / (e.g., start, help)"
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Description"
    )

    # Response type
    response_type = models.CharField(
        max_length=20,
        choices=ResponseType.choices,
        default=ResponseType.TEXT,
        verbose_name="Response type"
    )

    # Content based on response type
    text_response = models.TextField(
        blank=True,
        verbose_name="Text response",
        help_text="For TEXT type: the message to send"
    )
    ai_prompt_override = models.TextField(
        blank=True,
        verbose_name="AI prompt override",
        help_text="For AI type: override system prompt"
    )
    form_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Form ID",
        help_text="For FORM type: form identifier"
    )
    menu_config = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Menu config",
        help_text="For MENU type: inline keyboard configuration"
    )

    # Settings
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is active"
    )
    priority = models.IntegerField(
        default=0,
        verbose_name="Priority",
        help_text="For sorting (higher first)"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created at"
    )

    class Meta:
        verbose_name = "Command"
        verbose_name_plural = "Commands"
        ordering = ['-priority', 'name']
        unique_together = [['bot', 'name']]
        db_table = 'commands_command'

    def __str__(self):
        return f"/{self.name} ({self.bot.name})"

    @property
    def full_command(self):
        """Return full command with slash."""
        return f"/{self.name}"

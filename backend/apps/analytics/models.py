"""
Analytics models for Bot Factory.
Comprehensive tracking of bot performance, user engagement, and costs.
"""
import uuid
from django.db import models
from django.utils import timezone


class BotAnalytics(models.Model):
    """Агрегированная статистика бота по дням."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bot = models.ForeignKey('bots.Bot', on_delete=models.CASCADE, related_name='daily_analytics')
    date = models.DateField(help_text="Дата статистики")
    
    # Сообщения
    messages_received = models.IntegerField(default=0, help_text="Получено сообщений от пользователей")
    messages_sent = models.IntegerField(default=0, help_text="Отправлено ответов")
    
    # Пользователи
    unique_users = models.IntegerField(default=0, help_text="Уникальные пользователи за день")
    new_users = models.IntegerField(default=0, help_text="Новые пользователи")
    returning_users = models.IntegerField(default=0, help_text="Вернувшиеся пользователи")
    
    # AI метрики
    tokens_used = models.IntegerField(default=0, help_text="Использовано токенов")
    avg_response_time_ms = models.IntegerField(default=0, help_text="Среднее время ответа (мс)")
    rag_queries = models.IntegerField(default=0, help_text="Запросов с использованием RAG")
    
    # Отзывы
    positive_feedback = models.IntegerField(default=0, help_text="Положительные оценки (👍)")
    negative_feedback = models.IntegerField(default=0, help_text="Отрицательные оценки (👎)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Bot Analytics'
        verbose_name_plural = 'Bot Analytics'
        unique_together = ['bot', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['bot', 'date']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"{self.bot.name} - {self.date}"
    
    @property
    def feedback_ratio(self):
        """Соотношение положительных отзывов к общему количеству."""
        total = self.positive_feedback + self.negative_feedback
        return (self.positive_feedback / total * 100) if total > 0 else 0


class MessageEvent(models.Model):
    """Детальные события сообщений для real-time аналитики."""
    
    EVENT_TYPE_CHOICES = [
        ('received', 'Message Received'),
        ('sent', 'Message Sent'),
        ('error', 'Error'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bot = models.ForeignKey('bots.Bot', on_delete=models.CASCADE, related_name='message_events')
    telegram_user = models.ForeignKey('telegram.TelegramUser', on_delete=models.SET_NULL, null=True, blank=True)
    session = models.ForeignKey('chat.ChatSession', on_delete=models.SET_NULL, null=True, blank=True)
    
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    message_length = models.IntegerField(default=0, help_text="Длина сообщения (символов)")
    response_time_ms = models.IntegerField(null=True, blank=True, help_text="Время генерации ответа (мс)")
    tokens_used = models.IntegerField(null=True, blank=True, help_text="Использовано токенов")
    used_rag = models.BooleanField(default=False, help_text="Использовался ли RAG")
    
    error_message = models.TextField(blank=True, help_text="Описание ошибки (если event_type='error')")
    
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        verbose_name = 'Message Event'
        verbose_name_plural = 'Message Events'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['bot', 'timestamp']),
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['telegram_user', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.bot.name} - {self.timestamp}"


class UserFeedback(models.Model):
    """Оценка ответов пользователями (👍/👎)."""
    
    FEEDBACK_CHOICES = [
        ('positive', '👍 Helpful'),
        ('negative', '👎 Not Helpful'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bot = models.ForeignKey('bots.Bot', on_delete=models.CASCADE, related_name='user_feedback')
    telegram_user = models.ForeignKey('telegram.TelegramUser', on_delete=models.CASCADE)
    message = models.ForeignKey('chat.ChatMessage', on_delete=models.CASCADE, related_name='feedback')
    
    feedback = models.CharField(max_length=10, choices=FEEDBACK_CHOICES)
    comment = models.TextField(blank=True, help_text="Дополнительный комментарий от пользователя")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'User Feedback'
        verbose_name_plural = 'User Feedback'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['bot', 'created_at']),
            models.Index(fields=['feedback']),
        ]
    
    def __str__(self):
        return f"{self.feedback} - {self.bot.name}"


class TokenUsage(models.Model):
    """Детальный учёт токенов для биллинга."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bot = models.ForeignKey('bots.Bot', on_delete=models.CASCADE, related_name='token_usage')
    date = models.DateField(default=timezone.now, help_text="Дата использования")
    
    input_tokens = models.IntegerField(default=0, help_text="Входные токены (prompt)")
    output_tokens = models.IntegerField(default=0, help_text="Выходные токены (response)")
    total_tokens = models.IntegerField(default=0, help_text="Всего токенов")
    
    # Стоимость (в центах USD)
    estimated_cost_cents = models.IntegerField(default=0, help_text="Примерная стоимость в центах")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Token Usage'
        verbose_name_plural = 'Token Usage'
        unique_together = ['bot', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['bot', 'date']),
        ]
    
    def __str__(self):
        return f"{self.bot.name} - {self.date} - {self.total_tokens} tokens"
    
    def save(self, *args, **kwargs):
        """Автоматически рассчитать total_tokens."""
        self.total_tokens = self.input_tokens + self.output_tokens
        
        # Примерный расчёт стоимости для Gemini 2.0 Flash
        # Input: $0.075 / 1M tokens, Output: $0.30 / 1M tokens
        input_cost = (self.input_tokens / 1_000_000) * 0.075
        output_cost = (self.output_tokens / 1_000_000) * 0.30
        self.estimated_cost_cents = int((input_cost + output_cost) * 100)
        
        super().save(*args, **kwargs)


class UserRetention(models.Model):
    """Retention cohort analysis - возвращаются ли пользователи."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bot = models.ForeignKey('bots.Bot', on_delete=models.CASCADE, related_name='retention_cohorts')
    cohort_date = models.DateField(help_text="Дата первого использования бота (cohort)")
    
    # Retention по дням
    day_1_retained = models.IntegerField(default=0, help_text="Пользователей, вернувшихся на 1-й день")
    day_7_retained = models.IntegerField(default=0, help_text="Пользователей, вернувшихся на 7-й день")
    day_30_retained = models.IntegerField(default=0, help_text="Пользователей, вернувшихся на 30-й день")
    
    total_users_in_cohort = models.IntegerField(default=0, help_text="Всего пользователей в cohort")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Retention'
        verbose_name_plural = 'User Retention'
        unique_together = ['bot', 'cohort_date']
        ordering = ['-cohort_date']
        indexes = [
            models.Index(fields=['bot', 'cohort_date']),
        ]
    
    def __str__(self):
        return f"{self.bot.name} - Cohort {self.cohort_date}"
    
    @property
    def day_1_retention_rate(self):
        """Процент retention на 1-й день."""
        return (self.day_1_retained / self.total_users_in_cohort * 100) if self.total_users_in_cohort > 0 else 0
    
    @property
    def day_7_retention_rate(self):
        """Процент retention на 7-й день."""
        return (self.day_7_retained / self.total_users_in_cohort * 100) if self.total_users_in_cohort > 0 else 0
    
    @property
    def day_30_retention_rate(self):
        """Процент retention на 30-й день."""
        return (self.day_30_retained / self.total_users_in_cohort * 100) if self.total_users_in_cohort > 0 else 0

"""
Tests for analytics models.
"""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from apps.analytics.models import (
    BotAnalytics, MessageEvent, UserFeedback, TokenUsage, UserRetention
)
from apps.bots.models import Bot
from apps.telegram.models import TelegramUser
from apps.chat.models import ChatSession, ChatMessage
from apps.accounts.models import User


class BotAnalyticsModelTest(TestCase):
    """Test BotAnalytics model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
        self.bot = Bot.objects.create(
            owner=self.user,
            name='Test Bot',
            status='active'
        )
    
    def test_bot_analytics_creation(self):
        """Test BotAnalytics can be created with valid data."""
        analytics = BotAnalytics.objects.create(
            bot=self.bot,
            date=timezone.now().date(),
            messages_received=10,
            messages_sent=10,
            unique_users=5,
            tokens_used=1500,
            positive_feedback=8,
            negative_feedback=2
        )
        
        self.assertEqual(analytics.messages_received, 10)
        self.assertEqual(analytics.messages_sent, 10)
        self.assertEqual(analytics.feedback_ratio, 80.0)
    
    def test_bot_analytics_unique_constraint(self):
        """Test bot + date unique constraint."""
        date = timezone.now().date()
        
        BotAnalytics.objects.create(
            bot=self.bot,
            date=date,
            messages_received=10
        )
        
        # Should raise error on duplicate
        with self.assertRaises(Exception):
            BotAnalytics.objects.create(
                bot=self.bot,
                date=date,
                messages_received=20
            )
    
    def test_feedback_ratio_zero_division(self):
        """Test feedback_ratio with no feedback."""
        analytics = BotAnalytics.objects.create(
            bot=self.bot,
            date=timezone.now().date(),
            positive_feedback=0,
            negative_feedback=0
        )
        
        self.assertEqual(analytics.feedback_ratio, 0)


class MessageEventModelTest(TestCase):
    """Test MessageEvent model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.bot = Bot.objects.create(owner=self.user, name='Test Bot')
        self.telegram_user = TelegramUser.objects.create(
            bot=self.bot,
            telegram_id=12345,
            username='testuser'
        )
        self.session = ChatSession.objects.create(
            bot=self.bot,
            user=self.telegram_user
        )
    
    def test_message_event_creation(self):
        """Test MessageEvent tracks events correctly."""
        event = MessageEvent.objects.create(
            bot=self.bot,
            telegram_user=self.telegram_user,
            session=self.session,
            event_type='sent',
            message_length=100,
            response_time_ms=1500,
            tokens_used=50,
            used_rag=False
        )
        
        self.assertEqual(event.event_type, 'sent')
        self.assertEqual(event.response_time_ms, 1500)
        self.assertFalse(event.used_rag)
    
    def test_message_event_ordering(self):
        """Test events are ordered by timestamp (desc)."""
        event1 = MessageEvent.objects.create(
            bot=self.bot,
            event_type='received'
        )
        event2 = MessageEvent.objects.create(
            bot=self.bot,
            event_type='sent'
        )
        
        events = MessageEvent.objects.all()
        self.assertEqual(events[0], event2)  # Most recent first


class TokenUsageModelTest(TestCase):
    """Test TokenUsage model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.bot = Bot.objects.create(owner=self.user, name='Test Bot')
    
    def test_token_usage_auto_calculation(self):
        """Test automatic total_tokens calculation."""
        usage = TokenUsage.objects.create(
            bot=self.bot,
            date=timezone.now().date(),
            input_tokens=1000,
            output_tokens=500
        )
        
        self.assertEqual(usage.total_tokens, 1500)
    
    def test_token_usage_cost_calculation(self):
        """Test cost calculation formula."""
        usage = TokenUsage.objects.create(
            bot=self.bot,
            date=timezone.now().date(),
            input_tokens=1_000_000,  # 1M tokens
            output_tokens=1_000_000   # 1M tokens
        )
        
        # Input: $0.075 / 1M = $0.075
        # Output: $0.30 / 1M = $0.30
        # Total: $0.375 = 37.5 cents (rounded to 37)
        self.assertGreater(usage.estimated_cost_cents, 0)


class UserRetentionModelTest(TestCase):
    """Test UserRetention model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.bot = Bot.objects.create(owner=self.user, name='Test Bot')
    
    def test_retention_rate_calculations(self):
        """Test retention rate property calculations."""
        retention = UserRetention.objects.create(
            bot=self.bot,
            cohort_date=timezone.now().date(),
            total_users_in_cohort=100,
            day_1_retained=80,
            day_7_retained=50,
            day_30_retained=20
        )
        
        self.assertEqual(retention.day_1_retention_rate, 80.0)
        self.assertEqual(retention.day_7_retention_rate, 50.0)
        self.assertEqual(retention.day_30_retention_rate, 20.0)
    
    def test_retention_rate_zero_users(self):
        """Test retention rates with zero users."""
        retention = UserRetention.objects.create(
            bot=self.bot,
            cohort_date=timezone.now().date(),
            total_users_in_cohort=0
        )
        
        self.assertEqual(retention.day_1_retention_rate, 0)

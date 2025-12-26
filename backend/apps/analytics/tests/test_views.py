"""
Tests for analytics views (Dashboard APIs).
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from apps.analytics.models import BotAnalytics, MessageEvent, TokenUsage, UserRetention
from apps.bots.models import Bot
from apps.accounts.models import User


class DashboardStatsViewTest(TestCase):
    """Test DashboardStatsView API."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.bot = Bot.objects.create(owner=self.user, name='Test Bot')
        
    def test_dashboard_stats_requires_auth(self):
        """Test that endpoint requires authentication."""
        response = self.client.get('/api/v1/stats/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_dashboard_stats_with_data(self):
        """Test dashboard returns correct stats."""
        # Create analytics data
        BotAnalytics.objects.create(
            bot=self.bot,
            date=timezone.now().date(),
            messages_sent=100,
            unique_users=50,
            tokens_used=5000,
            avg_response_time_ms=1500
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/stats/?period=Last 7 days')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 4)  # 4 KPIs
        self.assertEqual(data[0]['title'], 'Active Users')


class TokenUsageViewTest(TestCase):
    """Test TokenUsageView API."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.bot = Bot.objects.create(owner=self.user, name='Test Bot')
    
    def test_token_usage_summary(self):
        """Test token usage returns correct summary."""
        TokenUsage.objects.create(
            bot=self.bot,
            date=timezone.now().date(),
            input_tokens=1000,
            output_tokens=500
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/stats/tokens/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['summary']['total_tokens'], 1500)
        self.assertIn('estimated_cost', data['summary'])

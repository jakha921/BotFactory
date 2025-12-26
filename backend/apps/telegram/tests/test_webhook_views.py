"""
Tests for Telegram webhook views.
"""
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework import status as http_status
from apps.bots.models import Bot
from apps.accounts.models import User
import json


class TelegramWebhookViewTest(TestCase):
    """Test TelegramWebhookView with security features."""
    
    def setUp(self):
        """Set up test client and bot."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.bot = Bot.objects.create(
            owner=self.user,
            name='Test Bot',
            status='active',
            model='gemini-2.0-flash',
            provider='gemini',
            webhook_secret='test_secret_token_123'
        )
        self.webhook_url = f'/api/v1/webhook/{self.bot.id}/'
    
    def test_webhook_requires_valid_bot(self):
        """Test that webhook returns 404 for invalid bot ID."""
        import uuid
        invalid_id = uuid.uuid4()
        response = self.client.post(
            f'/api/v1/webhook/{invalid_id}/',
            data={'update_id': 123},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, http_status.HTTP_404_NOT_FOUND)
    
    def test_webhook_requires_active_bot(self):
        """Test that webhook returns 404 for inactive bot."""
        self.bot.status = 'paused'
        self.bot.save()
        
        response = self.client.post(
            self.webhook_url,
            data={'update_id': 123},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, http_status.HTTP_404_NOT_FOUND)
    
    def test_webhook_validates_signature(self):
        """Test that webhook validates Telegram signature."""
        update_data = {
            'update_id': 123456789,
            'message': {
                'message_id': 1,
                'from': {'id': 123, 'first_name': 'John'},
                'chat': {'id': 123, 'type': 'private'},
                'text': 'Hello'
            }
        }
        
        # Missing signature
        response = self.client.post(
            self.webhook_url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        # Should still accept (signature optional if not set in header)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        
        # Invalid signature
        response = self.client.post(
            self.webhook_url,
            data=json.dumps(update_data),
            content_type='application/json',
            HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN='wrong_secret'
        )
        self.assertEqual(response.status_code, http_status.HTTP_401_UNAUTHORIZED)
        
        # Valid signature
        response = self.client.post(
            self.webhook_url,
            data=json.dumps(update_data),
            content_type='application/json',
            HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN='test_secret_token_123'
        )
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
    
    def test_webhook_rejects_invalid_json(self):
        """Test that webhook rejects invalid JSON."""
        response = self.client.post(
            self.webhook_url,
            data='invalid json{',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
    
    def test_webhook_accepts_valid_update(self):
        """Test that webhook accepts valid Telegram update."""
        update_data = {
            'update_id': 123456789,
            'message': {
                'message_id': 1,
                'from': {'id': 123, 'first_name': 'John'},
                'chat': {'id': 123, 'type': 'private'},
                'date': 1234567890,
                'text': 'Hello bot!'
            }
        }
        
        response = self.client.post(
            self.webhook_url,
            data=json.dumps(update_data),
            content_type='application/json',
            HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN='test_secret_token_123'
        )
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.content.decode(), 'OK')
    
    @override_settings(RATELIMIT_ENABLE=False)
    def test_webhook_get_endpoint(self):
        """Test GET endpoint for webhook (for testing)."""
        response = self.client.get(self.webhook_url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['bot_id'], str(self.bot.id))

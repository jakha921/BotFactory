"""
Tests for Telegram webhook views.

These tests cover the webhook endpoint with delivery_mode filtering
(Stage 3 of webhook migration plan).
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
            webhook_secret='test_secret_token_123',
            delivery_mode='webhook'  # Must be in webhook mode
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


class DeliveryModeWebhookTest(TestCase):
    """Test delivery_mode filtering in webhook endpoint."""

    def setUp(self):
        """Set up test client and bots with different delivery modes."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        # Create webhook mode bot
        self.webhook_bot = Bot.objects.create(
            owner=self.user,
            name='Webhook Bot',
            status='active',
            model='gemini-2.0-flash',
            provider='gemini',
            webhook_secret='webhook_secret_123',
            delivery_mode='webhook'
        )
        # Create polling mode bot
        self.polling_bot = Bot.objects.create(
            owner=self.user,
            name='Polling Bot',
            status='active',
            model='gemini-2.0-flash',
            provider='gemini',
            webhook_secret='polling_secret_123',
            delivery_mode='polling'
        )

    def test_webhook_rejects_polling_mode_bots(self):
        """Test that webhook returns 400 for polling mode bots."""
        update_data = {
            'update_id': 123456789,
            'message': {
                'message_id': 1,
                'from': {'id': 123, 'first_name': 'John'},
                'chat': {'id': 123, 'type': 'private'},
                'text': 'Hello'
            }
        }

        response = self.client.post(
            f'/api/v1/webhook/{self.polling_bot.id}/',
            data=json.dumps(update_data),
            content_type='application/json',
            HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN='polling_secret_123'
        )
        # Should reject because bot is in polling mode
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn('delivery_mode', data.get('error', '').lower())

    def test_webhook_accepts_webhook_mode_bots(self):
        """Test that webhook accepts requests for webhook mode bots."""
        update_data = {
            'update_id': 123456789,
            'message': {
                'message_id': 1,
                'from': {'id': 123, 'first_name': 'John'},
                'chat': {'id': 123, 'type': 'private'},
                'text': 'Hello'
            }
        }

        response = self.client.post(
            f'/api/v1/webhook/{self.webhook_bot.id}/',
            data=json.dumps(update_data),
            content_type='application/json',
            HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN='webhook_secret_123'
        )
        # Should accept (will process asynchronously)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

    def test_switching_to_webhook_mode_enables_webhook(self):
        """Test that switching bot to webhook mode allows webhook processing."""
        # Start with polling mode
        self.assertEqual(self.polling_bot.delivery_mode, 'polling')

        # Try webhook endpoint (should fail)
        update_data = {
            'update_id': 123456789,
            'message': {
                'message_id': 1,
                'from': {'id': 123, 'first_name': 'John'},
                'chat': {'id': 123, 'type': 'private'},
                'text': 'Hello'
            }
        }

        response = self.client.post(
            f'/api/v1/webhook/{self.polling_bot.id}/',
            data=json.dumps(update_data),
            content_type='application/json',
            HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN='polling_secret_123'
        )
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)

        # Switch to webhook mode
        self.polling_bot.delivery_mode = 'webhook'
        self.polling_bot.save()

        # Try webhook endpoint again (should succeed)
        response = self.client.post(
            f'/api/v1/webhook/{self.polling_bot.id}/',
            data=json.dumps(update_data),
            content_type='application/json',
            HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN='polling_secret_123'
        )
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

    def test_switching_to_polling_mode_disables_webhook(self):
        """Test that switching bot to polling mode rejects webhook processing."""
        # Start with webhook mode
        self.assertEqual(self.webhook_bot.delivery_mode, 'webhook')

        # Switch to polling mode
        self.webhook_bot.delivery_mode = 'polling'
        self.webhook_bot.save()

        # Try webhook endpoint (should fail)
        update_data = {
            'update_id': 123456789,
            'message': {
                'message_id': 1,
                'from': {'id': 123, 'first_name': 'John'},
                'chat': {'id': 123, 'type': 'private'},
                'text': 'Hello'
            }
        }

        response = self.client.post(
            f'/api/v1/webhook/{self.webhook_bot.id}/',
            data=json.dumps(update_data),
            content_type='application/json',
            HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN='webhook_secret_123'
        )
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)

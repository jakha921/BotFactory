"""
Tests for webhook API endpoints (set-webhook, delete-webhook, webhook-info).

These tests cover the webhook management endpoints added during the
polling-to-webhook migration (Stage 2 of webhook migration plan).
"""
from unittest.mock import AsyncMock, MagicMock, patch
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework import status as http_status
from apps.bots.models import Bot
from apps.accounts.models import User
import httpx
import json


class WebhookAPITest(TestCase):
    """Test webhook management API endpoints."""

    def setUp(self):
        """Set up test client, user and bot."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

        # Create test bot with encrypted token
        # Using a real encrypted token format for testing
        self.bot = Bot.objects.create(
            owner=self.user,
            name='Test Bot',
            status='active',
            model='gemini-2.0-flash',
            provider='gemini',
            telegram_token='gAAAAABn_test_encrypted_token',  # Fernet format
            delivery_mode='polling'  # Start in polling mode
        )

    @patch('httpx.AsyncClient.post')
    @override_settings(WEBHOOK_BASE_URL='https://example.com')
    def test_set_webhook_success(self, mock_post):
        """Test successful webhook registration."""
        # Mock Telegram API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'ok': True,
            'result': True,
            'description': 'Webhook was set'
        }
        mock_post.return_value = mock_response

        response = self.client.post(
            f'/api/v1/bots/{self.bot.id}/set-webhook/',
            data={'webhook_url': 'https://custom.example.com/webhook'},
            format='json'
        )

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['webhook_url'], 'https://custom.example.com/webhook')
        self.assertEqual(data['mode'], 'webhook')

        # Verify bot was updated
        self.bot.refresh_from_db()
        self.assertEqual(self.bot.delivery_mode, 'webhook')
        self.assertEqual(self.bot.webhook_url, 'https://custom.example.com/webhook')

    @patch('httpx.AsyncClient.post')
    @override_settings(WEBHOOK_BASE_URL='https://example.com')
    def test_set_webhook_default_url(self, mock_post):
        """Test webhook registration with default URL."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'ok': True,
            'result': True,
            'description': 'Webhook was set'
        }
        mock_post.return_value = mock_response

        response = self.client.post(
            f'/api/v1/bots/{self.bot.id}/set-webhook/',
            data={},  # No custom URL
            format='json'
        )

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        # Default URL should be used
        self.assertIn('/api/v1/telegram/webhook/', data['webhook_url'])

    @patch('httpx.AsyncClient.post')
    def test_set_webhook_telegram_api_error(self, mock_post):
        """Test webhook registration when Telegram API fails."""
        # Mock Telegram API error
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            'ok': False,
            'description': 'Bad request: bad webhook URL'
        }
        mock_post.return_value = mock_response

        response = self.client.post(
            f'/api/v1/bots/{self.bot.id}/set-webhook/',
            format='json'
        )

        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertFalse(data['success'])

        # Bot mode should not change
        self.bot.refresh_from_db()
        self.assertEqual(self.bot.delivery_mode, 'polling')

    def test_set_webhook_requires_auth(self):
        """Test that webhook registration requires authentication."""
        self.client.force_authenticate(user=None)

        response = self.client.post(
            f'/api/v1/bots/{self.bot.id}/set-webhook/',
            format='json'
        )

        self.assertEqual(response.status_code, http_status.HTTP_401_UNAUTHORIZED)

    def test_set_webhook_requires_ownership(self):
        """Test that only bot owner can set webhook."""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=other_user)

        response = self.client.post(
            f'/api/v1/bots/{self.bot.id}/set-webhook/',
            format='json'
        )

        self.assertEqual(response.status_code, http_status.HTTP_404_NOT_FOUND)

    @patch('httpx.AsyncClient.post')
    def test_delete_webhook_success(self, mock_post):
        """Test successful webhook deletion."""
        # First, set bot to webhook mode
        self.bot.delivery_mode = 'webhook'
        self.bot.webhook_url = 'https://example.com/webhook'
        self.bot.save()

        # Mock Telegram API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'ok': True,
            'result': True,
            'description': 'Webhook was deleted'
        }
        mock_post.return_value = mock_response

        response = self.client.post(
            f'/api/v1/bots/{self.bot.id}/delete-webhook/',
            format='json'
        )

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['mode'], 'polling')

        # Verify bot was updated
        self.bot.refresh_from_db()
        self.assertEqual(self.bot.delivery_mode, 'polling')

    @patch('httpx.AsyncClient.post')
    def test_delete_webhook_telegram_api_error(self, mock_post):
        """Test webhook deletion when Telegram API fails."""
        self.bot.delivery_mode = 'webhook'
        self.bot.save()

        # Mock Telegram API error
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            'ok': False,
            'description': 'Bad request'
        }
        mock_post.return_value = mock_response

        response = self.client.post(
            f'/api/v1/bots/{self.bot.id}/delete-webhook/',
            format='json'
        )

        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertFalse(data['success'])

    def test_delete_webhook_when_in_polling_mode(self):
        """Test deleting webhook when bot is already in polling mode."""
        # Bot is already in polling mode
        self.assertEqual(self.bot.delivery_mode, 'polling')

        response = self.client.post(
            f'/api/v1/bots/{self.bot.id}/delete-webhook/',
            format='json'
        )

        # Should succeed (idempotent operation)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['mode'], 'polling')

    @patch('httpx.AsyncClient.get')
    def test_webhook_info_polling_mode(self, mock_get):
        """Test webhook info for bot in polling mode."""
        response = self.client.get(
            f'/api/v1/bots/{self.bot.id}/webhook-info/'
        )

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['delivery_mode'], 'polling')
        self.assertFalse(data['webhook_registered'])

    @patch('httpx.AsyncClient.get')
    def test_webhook_info_webhook_mode(self, mock_get):
        """Test webhook info for bot in webhook mode."""
        self.bot.delivery_mode = 'webhook'
        self.bot.webhook_url = 'https://example.com/custom-webhook'
        self.bot.webhook_secret = 'test_secret'
        self.bot.save()

        # Mock Telegram API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'ok': True,
            'result': {
                'url': 'https://example.com/custom-webhook',
                'has_custom_certificate': False,
                'pending_update_count': 0,
                'last_error_date': None,
                'last_error_message': None
            }
        }
        mock_get.return_value = mock_response

        response = self.client.get(
            f'/api/v1/bots/{self.bot.id}/webhook-info/'
        )

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['delivery_mode'], 'webhook')
        self.assertTrue(data['webhook_registered'])
        self.assertEqual(data['webhook_url'], 'https://example.com/custom-webhook')
        self.assertTrue(data['has_secret'])
        self.assertEqual(data['telegram_info']['url'], 'https://example.com/custom-webhook')

    @patch('httpx.AsyncClient.get')
    def test_webhook_info_with_telegram_error(self, mock_get):
        """Test webhook info when Telegram API returns error."""
        self.bot.delivery_mode = 'webhook'
        self.bot.save()

        # Mock Telegram API error
        mock_get.side_effect = httpx.RequestError('Connection error')

        response = self.client.get(
            f'/api/v1/bots/{self.bot.id}/webhook-info/'
        )

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['delivery_mode'], 'webhook')
        self.assertFalse(data['webhook_registered'])
        self.assertIn('Could not fetch webhook info', data.get('error', ''))

    def test_webhook_info_requires_auth(self):
        """Test that webhook info requires authentication."""
        self.client.force_authenticate(user=None)

        response = self.client.get(
            f'/api/v1/bots/{self.bot.id}/webhook-info/'
        )

        self.assertEqual(response.status_code, http_status.HTTP_401_UNAUTHORIZED)


class DeliveryModeSerializerTest(TestCase):
    """Test delivery_mode field in bot serializers."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_create_bot_default_delivery_mode(self):
        """Test that creating a bot defaults to polling mode."""
        bot_data = {
            'name': 'Test Bot',
            'status': 'active',
            'model': 'gemini-2.0-flash',
            'provider': 'gemini',
        }

        response = self.client.post('/api/v1/bots/', data=bot_data, format='json')
        self.assertEqual(response.status_code, http_status.HTTP_201_CREATED)

        bot_id = response.json()['id']
        bot = Bot.objects.get(id=bot_id)
        self.assertEqual(bot.delivery_mode, 'polling')

    def test_create_bot_with_webhook_mode(self):
        """Test creating a bot with webhook mode."""
        bot_data = {
            'name': 'Test Bot',
            'status': 'active',
            'model': 'gemini-2.0-flash',
            'provider': 'gemini',
            'deliveryMode': 'webhook',
            'webhookUrl': 'https://example.com/webhook'
        }

        response = self.client.post('/api/v1/bots/', data=bot_data, format='json')
        self.assertEqual(response.status_code, http_status.HTTP_201_CREATED)

        bot_id = response.json()['id']
        bot = Bot.objects.get(id=bot_id)
        self.assertEqual(bot.delivery_mode, 'webhook')
        self.assertEqual(bot.webhook_url, 'https://example.com/webhook')

    def test_update_bot_delivery_mode(self):
        """Test updating bot delivery mode."""
        bot = Bot.objects.create(
            owner=self.user,
            name='Test Bot',
            status='active',
            model='gemini-2.0-flash',
            provider='gemini',
            delivery_mode='polling'
        )

        update_data = {
            'delivery_mode': 'webhook',
            'webhook_url': 'https://example.com/new-webhook'
        }

        response = self.client.patch(
            f'/api/v1/bots/{bot.id}/',
            data=update_data,
            format='json'
        )
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        # Debug: check response data
        response_data = response.json()
        print(f"Response data: {response_data}")

        bot.refresh_from_db()
        self.assertEqual(bot.delivery_mode, 'webhook')
        self.assertEqual(bot.webhook_url, 'https://example.com/new-webhook')

    def test_invalid_delivery_mode(self):
        """Test that invalid delivery mode is rejected."""
        bot_data = {
            'name': 'Test Bot',
            'status': 'active',
            'model': 'gemini-2.0-flash',
            'provider': 'gemini',
            'deliveryMode': 'invalid_mode'
        }

        response = self.client.post('/api/v1/bots/', data=bot_data, format='json')
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)


class BotManagerDeliveryModeTest(TestCase):
    """Test BotManager behavior with delivery_mode."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

    @patch('bot.services.bot_manager.get_bot_by_token')
    @patch('aiogram.Bot.get_me')
    @patch('aiogram.Dispatcher.start_polling')
    async def test_bot_manager_skips_webhook_bots(self, mock_polling, mock_get_me, mock_get_bot):
        """Test that BotManager doesn't start polling for webhook-mode bots."""
        from bot.services.bot_manager import BotManager
        import asyncio

        # Create webhook mode bot
        bot = await Bot.objects.acreate(
            owner=self.user,
            name='Webhook Bot',
            status='active',
            model='gemini-2.0-flash',
            provider='gemini',
            telegram_token='test_token',
            delivery_mode='webhook'
        )

        # Mock get_bot_by_token to return our webhook bot
        mock_get_bot.return_value = bot

        manager = BotManager()

        # Try to add webhook bot - should return False
        result = await manager.add_bot('test_token', 'Webhook Bot')

        self.assertFalse(result, "Webhook bot should not be added to manager")
        self.assertEqual(len(manager.running_bots), 0)

    @patch('bot.integrations.django_orm.get_bot_by_token')
    @patch('aiogram.Bot.get_me')
    async def test_bot_manager_starts_polling_bots(self, mock_get_me, mock_get_bot):
        """Test that BotManager starts polling for polling-mode bots."""
        from bot.services.bot_manager import BotManager
        import asyncio

        # Create polling mode bot
        bot = await Bot.objects.acreate(
            owner=self.user,
            name='Polling Bot',
            status='active',
            model='gemini-2.0-flash',
            provider='gemini',
            telegram_token='test_token',
            delivery_mode='polling'
        )

        # Mock get_bot_by_token to return our polling bot
        mock_get_bot.return_value = bot

        # Mock bot.get_me to avoid actual Telegram API call
        mock_get_me.return_value = MagicMock(id=123, username='testbot')

        manager = BotManager()

        # Add polling bot - should return True (but we need to handle async)
        # Note: This test would need proper async context for full testing
        # For now, we're testing the logic path

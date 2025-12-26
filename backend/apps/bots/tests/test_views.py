"""
Tests for bot CRUD operations.
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.bots.models import Bot
from apps.accounts.models import User


class BotCRUDTest(TestCase):
    """Test Bot CRUD operations."""
    
    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_create_bot_generates_webhook_secret(self):
        """Test that creating a bot does NOT auto-generate webhook_secret (only on register_webhook)."""
        bot_data = {
            'name': 'Test Bot',
            'description': 'A test bot',
            'status': 'active',
            'model': 'gemini-2.0-flash',
            'provider': 'gemini',
            'temperature': 0.7
        }
        
        response = self.client.post('/api/v1/bots/', data=bot_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check bot was created
        data = response.json()
        bot_id = data['id']
        bot = Bot.objects.get(id=bot_id)
        
        # webhook_secret should be empty until register_webhook is called
        self.assertEqual(bot.webhook_secret, '')
    
    def test_update_bot_preserves_webhook_secret(self):
        """Test that updating a bot preserves existing webhook_secret."""
        # Create bot with webhook secret
        bot = Bot.objects.create(
            owner=self.user,
            name='Original Bot',
            status='active',
            model='gemini-2.0-flash',
            provider='gemini',
            webhook_secret='existing_secret_123'
        )
        
        # Update bot
        update_data = {
            'name': 'Updated Bot',
            'description': 'Updated description',
            'status': 'active',
            'model': 'gemini-2.0-flash',
            'provider': 'gemini',
            'temperature': 0.8
        }
        
        response = self.client.patch(
            f'/api/v1/bots/{bot.id}/',
            data=update_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify webhook_secret preserved
        bot.refresh_from_db()
        self.assertEqual(bot.webhook_secret, 'existing_secret_123')
        self.assertEqual(bot.name, 'Updated Bot')
    
    def test_list_bots_requires_auth(self):
        """Test that listing bots requires authentication."""
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/v1/bots/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_bots_shows_only_user_bots(self):
        """Test that users only see their own bots."""
        # Create bot for current user
        Bot.objects.create(
            owner=self.user,
            name='My Bot',
            status='active',
            model='gemini-2.0-flash',
            provider='gemini'
        )
        
        # Create another user and bot
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123'
        )
        Bot.objects.create(
            owner=other_user,
            name='Other Bot',
            status='active',
            model='gemini-2.0-flash',
            provider='gemini'
        )
        
        # List bots for current user
        response = self.client.get('/api/v1/bots/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should only see own bot
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['name'], 'My Bot')

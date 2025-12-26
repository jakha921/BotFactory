"""
Tests for chat tasks (Celery).
"""
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock
from apps.chat.tasks import process_telegram_update, send_telegram_message
from apps.bots.models import Bot
from apps.telegram.models import TelegramUser
from apps.chat.models import ChatSession, ChatMessage
from apps.analytics.models import MessageEvent
from apps.accounts.models import User


class ProcessTelegramUpdateTaskTest(TestCase):
    """Test process_telegram_update Celery task."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.bot = Bot.objects.create(
            owner=self.user,
            name='Test Bot',
            status='active',
            telegram_token='test_token_123'
        )
    
    @patch('apps.chat.tasks.get_gemini_service')
    @patch('apps.chat.tasks.send_telegram_message')
    def test_process_update_creates_message(self, mock_send, mock_gemini_service):
        """Test that processing creates chat message."""
        # Mock Gemini response
        mock_gemini = MagicMock()
        mock_gemini.generate_response.return_value = {
            'text': 'Hello! How can I help you?',
            'usage': {'total_tokens': 50}
        }
        mock_gemini_service.return_value = mock_gemini
        
        update_data = {
            'message': {
                'text': 'Hello bot',
                'from': {
                    'id': 12345,
                    'first_name': 'Test User',
                    'username': 'testuser'
                },
                'chat': {'id': 12345}
            }
        }
        
        # Run task
        process_telegram_update(str(self.bot.id), update_data)
        
        # Verify user message saved
        self.assertTrue(
            ChatMessage.objects.filter(content='Hello bot', role='user').exists()
        )
        
        # Verify bot response saved
        self.assertTrue(
            ChatMessage.objects.filter(
                content='Hello! How can I help you?',
                role='model'
            ).exists()
        )
    
    @patch('apps.chat.tasks.get_gemini_service')
    @patch('apps.chat.tasks.send_telegram_message')
    def test_process_update_tracks_analytics(self, mock_send, mock_gemini_service):
        """Test that processing tracks MessageEvent."""
        mock_gemini = MagicMock()
        mock_gemini.generate_response.return_value = {
            'text': 'Response',
            'usage': {'total_tokens': 25}
        }
        mock_gemini_service.return_value = mock_gemini
        
        update_data = {
            'message': {
                'text': 'Test',
                'from': {'id': 12345, 'first_name': 'User'},
                'chat': {'id': 12345}
            }
        }
        
        process_telegram_update(str(self.bot.id), update_data)
        
        # Verify MessageEvent created
        self.assertTrue(
            MessageEvent.objects.filter(
                bot=self.bot,
                event_type='sent',
                tokens_used=25
            ).exists()
        )


class SendTelegramMessageTaskTest(TestCase):
    """Test send_telegram_message task."""
    
    @patch('apps.chat.tasks.requests.post')
    def test_send_message_success(self, mock_post):
        """Test successful message sending."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'ok': True}
        mock_post.return_value = mock_response
        
        send_telegram_message('test_token', 12345, 'Test message')
        
        # Verify API called
        self.assertTrue(mock_post.called)
        args, kwargs = mock_post.call_args
        self.assertIn('sendMessage', args[0])

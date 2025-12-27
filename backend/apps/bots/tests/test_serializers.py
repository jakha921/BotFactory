"""
Tests for Bot serializers, focusing on telegram token masking.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.bots.models import Bot
from apps.bots.serializers import BotSerializer

User = get_user_model()


class BotSerializerTestCase(TestCase):
    """Test BotSerializer, especially telegram token masking."""
    
    def setUp(self):
        """Set up test user and bot."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
        
        self.bot = Bot.objects.create(
            owner=self.user,
            name='Test Bot',
            description='Test bot description',
            model='gemini-2.5-flash',
            provider='gemini',
            system_instruction='You are a helpful assistant'
        )
    
    def test_telegram_token_masking(self):
        """Test that telegram token is masked in serializer output."""
        # Set a telegram token
        plain_token = '1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi'
        self.bot.set_telegram_token(plain_token)
        self.bot.save()
        
        serializer = BotSerializer(self.bot)
        data = serializer.data
        
        # Token should be masked
        self.assertIn('telegramToken', data)
        self.assertNotEqual(data['telegramToken'], plain_token)
        
        # Should show ****...last8chars
        self.assertTrue(data['telegramToken'].startswith('****'))
        self.assertTrue(data['telegramToken'].endswith('abcdefghi'[-8:]))
    
    def test_has_telegram_token_flag(self):
        """Test that hasTelegramToken flag is set correctly."""
        # Bot without token
        serializer = BotSerializer(self.bot)
        data = serializer.data
        self.assertFalse(data.get('hasTelegramToken', False))
        
        # Bot with token
        self.bot.set_telegram_token('1234567890:TestToken123456789')
        self.bot.save()
        
        serializer = BotSerializer(self.bot)
        data = serializer.data
        self.assertTrue(data['hasTelegramToken'])
    
    def test_updated_at_field_included(self):
        """Test that updatedAt field is included in serializer output."""
        serializer = BotSerializer(self.bot)
        data = serializer.data
        
        self.assertIn('updatedAt', data)
        self.assertIsNotNone(data['updatedAt'])
    
    def test_short_telegram_token_masking(self):
        """Test masking of short telegram tokens."""
        short_token = '1234567'
        self.bot.set_telegram_token(short_token)
        self.bot.save()
        
        serializer = BotSerializer(self.bot)
        data = serializer.data
        
        # Short tokens should still be masked
        self.assertEqual(data['telegramToken'], '****')

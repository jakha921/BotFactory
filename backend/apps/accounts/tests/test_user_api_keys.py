"""
Tests for User API Key model, serializers, and viewset.
Tests encryption, CRUD operations, and permissions.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import UserAPIKey
from cryptography.fernet import Fernet
from django.conf import settings

User = get_user_model()


class UserAPIKeyModelTestCase(TestCase):
    """Test UserAPIKey model encryption and methods."""
    
    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
    
    def test_encrypt_decrypt_key(self):
        """Test that API keys are encrypted and decrypted correctly."""
        api_key = UserAPIKey(
            user=self.user,
            name='Test OpenAI Key',
            provider='openai'
        )
        plain_key = 'sk-test1234567890abcdefghijklmnopqrstuvwxyz'
        
        # Encrypt
        api_key.encrypt_key(plain_key)
        api_key.save()
        
        # Verify it's encrypted (not the same as plain text)
        self.assertNotEqual(api_key.encrypted_key, plain_key)
        
        # Decrypt
        decrypted = api_key.decrypt_key()
        self.assertEqual(decrypted, plain_key)
    
    def test_masked_key_property(self):
        """Test that masked_key shows correct format."""
        api_key = UserAPIKey(
            user=self.user,
            name='Test Key',
            provider='gemini'
        )
        api_key.encrypt_key('sk-1234567890abcdefghij')
        api_key.save()
        
        masked = api_key.masked_key
        
        # Should show first 3 chars, ..., and last 4 chars
        self.assertTrue(masked.startswith('sk-'))
        self.assertIn('...', masked)
        self.assertTrue(masked.endswith('ghij'))
    
    def test_short_key_masking(self):
        """Test masking of short keys."""
        api_key = UserAPIKey(
            user=self.user,
            name='Short Key',
            provider='openai'
        )
        api_key.encrypt_key('short')
        api_key.save()
        
        masked = api_key.masked_key
        self.assertEqual(masked, '****')


class UserAPIKeyViewSetTestCase(TestCase):
    """Test UserAPIKey ViewSet endpoints."""
    
    def setUp(self):
        """Set up test client and users."""
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123',
            name='User One'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123',
            name='User Two'
        )
        
        # Create test API key for user1
        self.api_key1 = UserAPIKey(
            user=self.user1,
            name='User1 Key',
            provider='openai'
        )
        self.api_key1.encrypt_key('sk-user1key123456789')
        self.api_key1.save()
    
    def test_list_api_keys_requires_auth(self):
        """Test that listing API keys requires authentication."""
        url = '/api/v1/auth/api-keys/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_user_api_keys(self):
        """Test that user can list their own API keys."""
        self.client.force_authenticate(user=self.user1)
        
        url = '/api/v1/auth/api-keys/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'User1 Key')
        
        # Verify key is masked
        self.assertIn('...', response.data[0]['key'])
    
    def test_user_cannot_see_other_users_keys(self):
        """Test that user only sees their own API keys."""
        self.client.force_authenticate(user=self.user2)
        
        url = '/api/v1/auth/api-keys/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
    
    def test_create_api_key(self):
        """Test creating a new API key."""
        self.client.force_authenticate(user=self.user2)
        
        url = '/api/v1/auth/api-keys/'
        data = {
            'name': 'My Gemini Key',
            'provider': 'gemini',
            'key': 'AIzaSyTest1234567890abcdefghijk'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'My Gemini Key')
        self.assertEqual(response.data['provider'], 'gemini')
        
        # Verify key is encrypted in database
        api_key = UserAPIKey.objects.get(id=response.data['id'])
        self.assertNotEqual(api_key.encrypted_key, data['key'])
        self.assertEqual(api_key.decrypt_key(), data['key'])
    
    def test_create_api_key_requires_fields(self):
        """Test that creating API key validates required fields."""
        self.client.force_authenticate(user=self.user1)
        
        url = '/api/v1/auth/api-keys/'
        data = {'name': 'Incomplete Key'}  # Missing provider and key
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_delete_api_key(self):
        """Test deleting own API key."""
        self.client.force_authenticate(user=self.user1)
        
        url = f'/api/v1/auth/api-keys/{self.api_key1.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify key is deleted
        self.assertFalse(UserAPIKey.objects.filter(id=self.api_key1.id).exists())
    
    def test_cannot_delete_other_users_key(self):
        """Test that user cannot delete another user's API key."""
        self.client.force_authenticate(user=self.user2)
        
        url = f'/api/v1/auth/api-keys/{self.api_key1.id}/'
        response = self.client.delete(url)
        
        # Should return 404 since queryset is filtered by user
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Verify key still exists
        self.assertTrue(UserAPIKey.objects.filter(id=self.api_key1.id).exists())

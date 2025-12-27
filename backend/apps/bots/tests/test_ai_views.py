"""
Tests for AI-powered views in bots app.
Tests ImproveInstructionView and GenerateContentView endpoints.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

User = get_user_model()


class AIViewsTestCase(TestCase):
    """Test AI endpoints for instruction improvement and content generation."""
    
    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
        self.client.force_authenticate(user=self.user)
    
    @patch('apps.bots.ai_views.GeminiService')
    def test_improve_instruction_success(self, mock_gemini):
        """Test that authenticated user can improve instruction."""
        # Mock Gemini response
        mock_service = MagicMock()
        mock_service.generate_response.return_value = {
            'text': 'Improved instruction with better clarity',
            'usage': {'input_tokens': 10, 'output_tokens': 20}
        }
        mock_gemini.return_value = mock_service
        
        url = '/api/v1/bots/improve-instruction/'
        data = {'instruction': 'You are a helpful assistant'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('text', response.data)
        self.assertEqual(response.data['text'], 'Improved instruction with better clarity')
    
    def test_improve_instruction_requires_auth(self):
        """Test that improve instruction requires authentication."""
        self.client.force_authenticate(user=None)
        
        url = '/api/v1/bots/improve-instruction/'
        data = {'instruction': 'Test instruction'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_improve_instruction_empty_instruction(self):
        """Test that empty instruction returns error."""
        url = '/api/v1/bots/improve-instruction/'
        data = {'instruction': ''}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    @patch('apps.bots.ai_views.GeminiService')
    def test_generate_content_success(self, mock_gemini):
        """Test that authenticated user can generate content."""
        # Mock Gemini response
        mock_service = MagicMock()
        mock_service.generate_response.return_value = {
            'text': '# Test Title\n\nGenerated content here...',
            'usage': {'input_tokens': 10, 'output_tokens': 50}
        }
        mock_gemini.return_value = mock_service
        
        url = '/api/v1/bots/generate-content/'
        data = {'title': 'Test Title'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('text', response.data)
        self.assertIn('Test Title', response.data['text'])
    
    def test_generate_content_requires_auth(self):
        """Test that generate content requires authentication."""
        self.client.force_authenticate(user=None)
        
        url = '/api/v1/bots/generate-content/'
        data = {'title': 'Test'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_generate_content_empty_title(self):
        """Test that empty title returns error."""
        url = '/api/v1/bots/generate-content/'
        data = {'title': ''}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

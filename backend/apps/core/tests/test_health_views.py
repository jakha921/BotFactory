"""
Tests for health check endpoints.
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status


class HealthCheckViewTest(TestCase):
    """Test basic health check endpoint."""
    
    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
    
    def test_health_check_returns_healthy(self):
        """Test that health check returns healthy status."""
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'bot-factory')
    
    def test_health_check_no_auth_required(self):
        """Test that health check does not require authentication."""
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ReadinessCheckViewTest(TestCase):
    """Test readiness check endpoint."""
    
    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
    
    def test_readiness_check_returns_ready(self):
        """Test that readiness check returns ready when DB and cache are available."""
        response = self.client.get('/api/health/ready/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['status'], 'ready')
        self.assertIn('checks', data)
        self.assertTrue(data['checks']['database'])
        self.assertTrue(data['checks']['cache'])
    
    def test_readiness_check_no_auth_required(self):
        """Test that readiness check does not require authentication."""
        response = self.client.get('/api/health/ready/')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE])

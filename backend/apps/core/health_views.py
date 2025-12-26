"""
Health check views for monitoring system status.
"""
from rest_framework import views, status
from rest_framework.response import Response
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from drf_spectacular.utils import extend_schema, OpenApiResponse
import logging

logger = logging.getLogger(__name__)


class HealthCheckView(views.APIView):
    """
    Basic health check endpoint.
    
    GET /api/health/
    Returns 200 if the service is running.
    """
    authentication_classes = []
    permission_classes = []
    
    @extend_schema(
        summary="Health Check",
        description="Basic health check endpoint. Returns 200 if service is running.",
        responses={200: OpenApiResponse(description="Service is healthy")},
        tags=["Health"]
    )
    def get(self, request):
        """Simple health check."""
        return Response({
            'status': 'healthy',
            'service': 'bot-factory'
        }, status=status.HTTP_200_OK)


class ReadinessCheckView(views.APIView):
    """
    Readiness check endpoint.
    
    GET /api/health/ready/
    Returns 200 if the service is ready to accept traffic (DB + Cache available).
    """
    authentication_classes = []
    permission_classes = []
    
    @extend_schema(
        summary="Readiness Check",
        description="Check if service is ready to accept traffic. Verifies database and cache connectivity. Returns 503 if any check fails.",
        responses={
            200: OpenApiResponse(description="Service is ready"),
            503: OpenApiResponse(description="Service not ready"),
        },
        tags=["Health"]
    )
    def get(self, request):
        """Check if service is ready (DB + Cache)."""
        checks = {
            'database': self._check_database(),
            'cache': self._check_cache(),
        }
        
        all_healthy = all(checks.values())
        
        return Response({
            'status': 'ready' if all_healthy else 'not_ready',
            'checks': checks
        }, status=status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE)
    
    def _check_database(self) -> bool:
        """Check database connectivity."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False
    
    def _check_cache(self) -> bool:
        """Check cache connectivity."""
        try:
            cache.set('health_check', 'ok', 10)
            return cache.get('health_check') == 'ok'
        except Exception as e:
            logger.error(f"Cache health check failed: {str(e)}")
            return False

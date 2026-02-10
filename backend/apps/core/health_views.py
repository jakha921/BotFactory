"""
Health check views for monitoring system status.
"""
from rest_framework import views, status
from rest_framework.response import Response
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.utils import timezone
from datetime import timedelta
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


class WebhookHealthCheckView(views.APIView):
    """
    Webhook health check endpoint for monitoring webhook delivery status.

    GET /api/health/webhook/
    Returns webhook health metrics including recent delivery status, error rates,
    and processing times for webhook-mode bots.
    """
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        summary="Webhook Health Check",
        description="Check webhook delivery health. Returns metrics for all webhook-mode bots.",
        responses={
            200: OpenApiResponse(description="Webhook health status"),
        },
        tags=["Health"]
    )
    def get(self, request):
        """Check webhook health across all webhook-mode bots."""
        try:
            from apps.bots.models import Bot
            from apps.analytics.models import WebhookEvent

            # Get all webhook-mode bots
            webhook_bots = Bot.objects.filter(delivery_mode='webhook', status='active')

            # Check time window (last 15 minutes)
            check_window = timezone.now() - timedelta(minutes=15)

            bot_statuses = []
            total_events = 0
            total_errors = 0

            for bot in webhook_bots:
                # Get recent events for this bot
                recent_events = WebhookEvent.objects.filter(
                    bot=bot,
                    timestamp__gte=check_window
                )

                bot_total = recent_events.count()
                bot_errors = recent_events.filter(status='failed').count()

                total_events += bot_total
                total_errors += bot_errors

                # Calculate metrics
                error_rate = (bot_errors / bot_total) if bot_total > 0 else 0
                avg_processing = recent_events.filter(
                    processing_time_ms__isnull=False
                ).values_list('processing_time_ms', flat=True)

                avg_processing_ms = int(sum(avg_processing) / len(avg_processing)) if avg_processing else 0

                # Determine bot health status
                if bot_total == 0:
                    bot_health = 'no_traffic'
                elif error_rate > 0.1:  # More than 10% errors
                    bot_health = 'unhealthy'
                elif error_rate > 0.05:  # More than 5% errors
                    bot_health = 'degraded'
                else:
                    bot_health = 'healthy'

                bot_statuses.append({
                    'bot_id': str(bot.id),
                    'bot_name': bot.name,
                    'status': bot_health,
                    'events_last_15min': bot_total,
                    'errors_last_15min': bot_errors,
                    'error_rate': f"{error_rate:.1%}",
                    'avg_processing_time_ms': avg_processing_ms,
                })

            # Calculate overall health
            overall_error_rate = (total_errors / total_events) if total_events > 0 else 0

            if total_events == 0:
                overall_status = 'no_traffic'
            elif overall_error_rate > 0.1:
                overall_status = 'unhealthy'
            elif overall_error_rate > 0.05:
                overall_status = 'degraded'
            else:
                overall_status = 'healthy'

            return Response({
                'status': overall_status,
                'timestamp': timezone.now().isoformat(),
                'summary': {
                    'webhook_bots_count': webhook_bots.count(),
                    'total_events_last_15min': total_events,
                    'total_errors_last_15min': total_errors,
                    'overall_error_rate': f"{overall_error_rate:.1%}",
                },
                'bots': bot_statuses
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Webhook health check failed: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'error': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class BotWebhookHealthView(views.APIView):
    """
    Individual bot webhook health check.

    GET /api/health/webhook/<bot_id>/
    Returns webhook health metrics for a specific bot.
    """
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        summary="Bot Webhook Health",
        description="Check webhook health for a specific bot.",
        responses={
            200: OpenApiResponse(description="Bot webhook health status"),
            404: OpenApiResponse(description="Bot not found"),
        },
        tags=["Health"]
    )
    def get(self, request, bot_id):
        """Check webhook health for a specific bot."""
        try:
            from apps.bots.models import Bot
            from apps.analytics.models import WebhookEvent, WebhookMetrics

            bot = Bot.objects.get(id=bot_id)

            # Check time windows
            now = timezone.now()
            last_15_min = now - timedelta(minutes=15)
            last_hour = now - timedelta(hours=1)

            # Recent events (15 min)
            recent_events = WebhookEvent.objects.filter(
                bot=bot,
                timestamp__gte=last_15_min
            )

            recent_total = recent_events.count()
            recent_errors = recent_events.filter(status='failed').count()
            recent_error_rate = (recent_errors / recent_total) if recent_total > 0 else 0

            # Hourly metrics (from aggregated data)
            hourly_metrics = WebhookMetrics.objects.filter(
                bot=bot,
                date__gte=last_hour.date()
            ).order_by('-date', '-hour')[:24]  # Last 24 hours

            # Current hour metrics (real-time)
            current_events = WebhookEvent.objects.filter(
                bot=bot,
                timestamp__gte=now.replace(minute=0, second=0, microsecond=0)
            )

            current_total = current_events.count()
            current_errors = current_events.filter(status='failed').count()

            processing_times = current_events.filter(
                processing_time_ms__isnull=False
            ).values_list('processing_time_ms', flat=True)

            avg_processing = int(sum(processing_times) / len(processing_times)) if processing_times else 0

            # Build response
            return Response({
                'bot_id': str(bot.id),
                'bot_name': bot.name,
                'delivery_mode': bot.delivery_mode,
                'timestamp': now.isoformat(),
                'current_hour': {
                    'events': current_total,
                    'errors': current_errors,
                    'error_rate': f"{(current_errors / current_total):.1%}" if current_total > 0 else "0%",
                    'avg_processing_time_ms': avg_processing,
                },
                'last_15_minutes': {
                    'events': recent_total,
                    'errors': recent_errors,
                    'error_rate': f"{recent_error_rate:.1%}",
                },
                'status': 'healthy' if recent_error_rate < 0.05 else 'degraded' if recent_error_rate < 0.1 else 'unhealthy',
                'webhook_url': bot.webhook_url or 'Default',
                'webhook_registered': bot.webhook_secret is not None,
            }, status=status.HTTP_200_OK)

        except Bot.DoesNotExist:
            return Response({
                'status': 'error',
                'error': 'Bot not found'
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"Bot webhook health check failed: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'error': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

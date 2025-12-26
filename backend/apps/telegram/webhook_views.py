"""
Webhook views for Telegram integration.
"""
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from apps.bots.models import Bot
from apps.chat.tasks import process_telegram_update
import json
import logging
import hmac
import hashlib
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from rest_framework import serializers
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class TelegramUpdateSerializer(serializers.Serializer):
    """Serializer for Telegram update payload (for documentation)."""
    update_id = serializers.IntegerField()
    message = serializers.DictField(required=False)
    callback_query = serializers.DictField(required=False)



@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(ratelimit(key='ip', rate='100/m', method='POST'), name='dispatch')
class TelegramWebhookView(APIView):
    """
    Receive Telegram updates via webhook.
    
    POST /api/telegram/webhook/<bot_id>/
    
    Security:
    - Rate limited to 100 requests/minute per IP
    - Validates Telegram signature (if secret token set)
    - CSRF exempt (external API)
    """
    
    authentication_classes = []
    permission_classes = []
    
    @extend_schema(
        summary="Receive Telegram Update",
        description="""Webhook endpoint for receiving updates from Telegram Bot API.
        
**Security:** Rate limited to 100 req/min. Validates X-Telegram-Bot-Api-Secret-Token header.
**Processing:** Updates processed asynchronously via Celery.""",
        request=TelegramUpdateSerializer,
        responses={
            200: OpenApiResponse(description="Update received and queued"),
            400: OpenApiResponse(description="Invalid JSON"),
            401: OpenApiResponse(description="Invalid signature"),
            404: OpenApiResponse(description="Bot not found"), 
            429: OpenApiResponse(description="Rate limit exceeded"),
        },
        tags=["Telegram Webhook"]
    )
    def post(self, request, bot_id):
        """
        Handle incoming Telegram update.
        
        Args:
            request: Django request object
            bot_id: Bot UUID from URL
        """
        try:
            # Find bot by ID
            try:
                bot = Bot.objects.get(id=bot_id, status='active')
            except Bot.DoesNotExist:
                logger.warning(f"Bot not found or inactive: {bot_id}")
                return JsonResponse({'error': 'Bot not found'}, status=404)
            
            # Validate Telegram signature (optional but recommended)
            if hasattr(bot, 'webhook_secret'):
                if not self._verify_telegram_signature(request, bot.webhook_secret):
                    logger.warning(f"Invalid Telegram signature for bot {bot_id}")
                    return HttpResponse("Unauthorized", status=401)
            
            # Parse update data from Telegram
            try:
                update_data = json.loads(request.body)
            except json.JSONDecodeError:
                logger.error("Invalid JSON in webhook request")
                return JsonResponse({'error': 'Invalid JSON'}, status=400)
            
            # Send to Celery for async processing
            process_telegram_update.delay(str(bot.id), update_data)
            
            logger.info(f"Received update for bot {bot.name} (id={bot.id})")
            
            # Respond quickly to Telegram (must respond within 60 seconds)
            return HttpResponse("OK")
            
        except Exception as e:
            logger.error(f"Error in webhook: {str(e)}", exc_info=True)
            return HttpResponse("Error", status=500)
    
    def get(self, request, bot_id):
        """
        Handle GET requests (for testing/health checks).
        """
        return JsonResponse({
            'status': 'ok',
            'message': 'Telegram Webhook Endpoint',
            'bot_id': str(bot_id)
        })
    
    def _verify_telegram_signature(self, request, secret_token):
        """
        Verify Telegram webhook signature.
        
        Args:
            request: Django request
            secret_token: Secret token set when registering webhook
            
        Returns:
            bool: True if signature is valid
        """
        # Get signature from header
        telegram_signature = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
        
        if not telegram_signature:
            return True  # No signature required if not set
        
        # Compare with expected secret
        return hmac.compare_digest(telegram_signature, secret_token)

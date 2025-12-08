"""
Views for telegram app.
TelegramUserViewSet for managing Telegram users.
Webhook view for receiving Telegram updates from multiple bots.
"""
import json
import logging
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from asgiref.sync import sync_to_async
from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import Update
from aiogram.exceptions import TelegramBadRequest

from apps.telegram.models import TelegramUser
from apps.bots.models import Bot as BotModel
from apps.telegram.serializers import (
    TelegramUserSerializer,
    UpdateUserStatusSerializer,
)
from core.permissions import IsOwnerOrReadOnly
from services.bot_engine import get_shared_dispatcher
from services.webhook_helper import parse_webhook_update
from services.webhook_helper import parse_webhook_update

logger = logging.getLogger(__name__)


class TelegramUserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for managing Telegram users.
    
    list: GET /api/v1/bots/{bot_id}/users/ - List Telegram users for a bot
    retrieve: GET /api/v1/users/{id}/ - Get user details
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TelegramUserSerializer
    
    def get_queryset(self):
        """Filter users by bot and ensure user owns the bot."""
        bot_id = self.kwargs.get('bot_id')
        if bot_id:
            bot = get_object_or_404(BotModel, id=bot_id, owner=self.request.user)
            return TelegramUser.objects.filter(bot=bot).select_related('bot')
        return TelegramUser.objects.none()
    
    def list(self, request, bot_id=None):
        """List Telegram users for a bot."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='status')
    def update_status(self, request, pk=None):
        """
        Update user status endpoint.
        
        POST /api/v1/users/{id}/status/
        Body: { "status": "active" | "blocked" }
        """
        user = self.get_object()
        # Ensure user's bot belongs to current user
        if user.bot.owner != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = UpdateUserStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user.status = serializer.validated_data['status']
        user.save()
        
        return Response({
            'message': 'Status updated successfully',
            'user': TelegramUserSerializer(user).data
        }, status=status.HTTP_200_OK)


@sync_to_async
def get_bot_by_token(token: str):
    """
    Get active bot by telegram token (async wrapper).
    
    Args:
        token: Telegram bot token (plain text, will be compared against decrypted tokens)
        
    Returns:
        Bot instance or None
    """
    try:
        # Get all active bots with tokens
        active_bots = BotModel.objects.filter(
            status='active',
            telegram_token__isnull=False
        ).exclude(telegram_token='')
        
        # Find bot with matching decrypted token
        for bot in active_bots:
            if bot.decrypted_telegram_token == token:
                return bot
        
        return None
    except Exception as e:
        logger.error(f"Error getting bot by token: {e}", exc_info=True)
        return None


async def telegram_webhook(request, token: str):
    """
    Webhook endpoint for receiving Telegram updates.
    
    POST /webhook/<token>/
    
    Args:
        request: Django HTTP request (async)
        token: Telegram bot token from URL
        
    Returns:
        HTTP 200 OK if processed successfully
        HTTP 403 Forbidden if token is invalid
        HTTP 400 Bad Request if update is invalid
    """
    print(f"📥 ПОЛУЧЕН WEBHOOK для токена: {token}") # Лог 1
    # 1. Verify token exists in database
    bot_instance = await get_bot_by_token(token)
    print(f"🔍 НАЙДЕН БОТ: {bot_instance.name} (ID: {bot_instance.id})") # Лог 3
    if not bot_instance:
        logger.warning(f"Webhook request with invalid token: {token[:20]}...")
        print(f"🔒 НЕ НАЙДЕН БОТ ДЛЯ ТОКЕНА: {token[:20]}...") # Лог 2
        return HttpResponseForbidden("Invalid Token")
    
    logger.debug(f"Webhook request for bot: {bot_instance.name} (ID: {bot_instance.id})")
    print(f"🔍 WEBHOOK ДЛЯ БОТА: {bot_instance.name} (ID: {bot_instance.id})") # Лог 4
    # 2. Parse request body
    print("🔍 Тело запроса:", request.body.decode('utf-8')) # Лог 5: Что прислал Телеграм
    update_data = await parse_webhook_update(request)
    
    if not update_data:
        logger.error("Failed to parse webhook update")
        return HttpResponseBadRequest("Invalid JSON")
    
    # 3. Initialize Aiogram Bot instance (lightweight, per-request)
    bot = None
    try:
        # Use decrypted token
        decrypted_token = bot_instance.decrypted_telegram_token
        
        # Create bot instance with session
        bot = Bot(
            token=decrypted_token,
            session=AiohttpSession()
        )
        
        # 4. Reconstruct Update object
        try:
            update = Update(**update_data)
        except Exception as e:
            logger.error(f"Failed to create Update object: {e}", exc_info=True)
            return HttpResponseBadRequest("Invalid Update format")
        
        # 5. Get shared dispatcher and process update
        dp = get_shared_dispatcher()
        
        try:
            # Feed update to dispatcher with the specific bot instance
            await dp.feed_update(bot, update)
            logger.debug(f"Successfully processed update for bot: {bot_instance.name}")
        except TelegramBadRequest as e:
            logger.warning(f"Telegram API error processing update: {e}")
            # Still return 200 to prevent Telegram from retrying
        except Exception as e:
            logger.error(f"Error processing update for bot {bot_instance.name}: {e}", exc_info=True)
            # Return 200 to prevent Telegram from retrying on our errors
        
    finally:
        # Cleanup: close bot session
        if bot:
            try:
                await bot.session.close()
            except Exception as e:
                logger.error(f"Error closing bot session: {e}")
    
    return HttpResponse("OK", status=200)


# CSRF exemption for webhook (Telegram doesn't send CSRF tokens)
# Note: In Django 5.0+, async views work with decorators, but order matters
# We apply csrf_exempt and require_http_methods to the async function
webhook_view = csrf_exempt(require_http_methods(["POST"])(telegram_webhook))

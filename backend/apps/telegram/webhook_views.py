"""
Webhook views for Telegram integration.

This view handles incoming Telegram updates via webhook.
It uses the shared dispatcher from bot_engine.py to process updates
through the same handlers used by polling mode.

Includes webhook event logging and monitoring for analytics.
"""
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from asgiref.sync import sync_to_async
from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import Update
from aiogram.exceptions import TelegramBadRequest
import json
import logging
import hmac
import time
from datetime import datetime

from apps.bots.models import Bot as BotModel
from services.bot_engine import get_shared_dispatcher
from services.webhook_helper import parse_webhook_update

logger = logging.getLogger(__name__)


async def log_webhook_event(bot_instance, event_type, update_id, **kwargs):
    """
    Log a webhook event for monitoring and analytics.

    Args:
        bot_instance: Bot model instance
        event_type: Event type ('received', 'processed', 'error', etc.)
        update_id: Telegram update_id
        **kwargs: Additional event data
    """
    try:
        from apps.analytics.models import WebhookEvent

        await sync_to_async(WebhookEvent.objects.create)(
            bot=bot_instance,
            event_type=event_type,
            webhook_delivery_time=datetime.now(),
            update_id=update_id,
            **kwargs
        )
    except Exception as e:
        logger.error(f"Error logging webhook event: {e}", exc_info=True)


# CSRF exemption for webhook (Telegram doesn't send CSRF tokens)
# Note: In Django 5.0+, async views work with decorators
@csrf_exempt
@require_http_methods(["POST", "GET"])
async def telegram_webhook_by_id(request, bot_id):
    """
    Webhook endpoint for receiving Telegram updates by bot ID.

    POST /api/v1/telegram/webhook/<bot_id>/
    GET /api/v1/telegram/webhook/<bot_id>/ - Health check

    Args:
        request: Django HTTP request (async)
        bot_id: Bot UUID from URL

    Returns:
        HTTP 200 OK if processed successfully
        HTTP 403 Forbidden if token is invalid
        HTTP 400 Bad Request if update is invalid
    """
    if request.method == "GET":
        # Health check
        return JsonResponse({
            'status': 'ok',
            'message': 'Telegram Webhook Endpoint',
            'bot_id': str(bot_id)
        })

    # POST - handle update
    start_time = time.time()
    update_id = None
    bot_instance = None

    # Get client info for logging
    ip_address = await sync_to_async(lambda: request.META.get('REMOTE_ADDR'))()
    user_agent = await sync_to_async(lambda: request.META.get('HTTP_USER_AGENT', ''))()

    try:
        # 1. Get bot instance from database
        bot_instance = await sync_to_async(BotModel.objects.get)(id=bot_id, status='active')

        logger.debug(f"Webhook request for bot: {bot_instance.name} (ID: {bot_instance.id})")

        # 2. Validate delivery mode - only process webhook mode bots
        if bot_instance.delivery_mode != 'webhook':
            logger.warning(
                f"Bot {bot_instance.name} (ID: {bot_id}) is in {bot_instance.delivery_mode} mode, "
                f"not webhook mode. Skipping webhook processing."
            )
            # Still return 200 to prevent Telegram retries
            return HttpResponse("OK", status=200)

        # 3. Parse request body
        update_data = await parse_webhook_update(request)

        if not update_data:
            logger.error("Failed to parse webhook update")
            await log_webhook_event(
                bot_instance, 'error', 0,
                status='failed',
                error_type='InvalidJSON',
                error_message='Failed to parse webhook update',
                ip_address=ip_address,
                user_agent=user_agent,
                telegram_signature_valid=False
            )
            return HttpResponseBadRequest("Invalid JSON")

        update_id = update_data.get('update_id', 0)

        # Log webhook received
        await log_webhook_event(
            bot_instance, 'received', update_id,
            status='pending',
            ip_address=ip_address,
            user_agent=user_agent
        )

        # 4. Validate Telegram signature (optional but recommended)
        signature_valid = True
        if bot_instance.webhook_secret:
            telegram_signature = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
            if telegram_signature:
                signature_valid = hmac.compare_digest(telegram_signature, bot_instance.webhook_secret)
                if not signature_valid:
                    logger.warning(f"Invalid Telegram signature for bot {bot_id}")
                    await log_webhook_event(
                        bot_instance, 'error', update_id,
                        status='failed',
                        error_type='InvalidSignature',
                        error_message='Telegram signature validation failed',
                        ip_address=ip_address,
                        user_agent=user_agent,
                        telegram_signature_valid=False
                    )
                    return HttpResponseForbidden("Invalid signature")

        # 5. Initialize Aiogram Bot instance (lightweight, per-request)
        bot = None
        try:
            # Use decrypted token
            decrypted_token = bot_instance.decrypted_telegram_token

            # Create bot instance with session
            bot = Bot(
                token=decrypted_token,
                session=AiohttpSession()
            )

            # 6. Reconstruct Update object
            try:
                update = Update(**update_data)
            except Exception as e:
                logger.error(f"Failed to create Update object: {e}", exc_info=True)
                await log_webhook_event(
                    bot_instance, 'error', update_id,
                    status='failed',
                    error_type='InvalidUpdate',
                    error_message=str(e),
                    ip_address=ip_address,
                    user_agent=user_agent,
                    telegram_signature_valid=signature_valid
                )
                return HttpResponseBadRequest("Invalid Update format")

            # 7. Get shared dispatcher and process update
            dp = get_shared_dispatcher()

            processing_start = time.time()
            try:
                # Feed update to dispatcher with the specific bot instance
                await dp.feed_update(bot, update)
                processing_time_ms = int((time.time() - processing_start) * 1000)

                logger.debug(f"Successfully processed update for bot: {bot_instance.name}")

                # Log successful processing
                await log_webhook_event(
                    bot_instance, 'processed', update_id,
                    status='success',
                    processing_time_ms=processing_time_ms,
                    telegram_signature_valid=signature_valid
                )

            except TelegramBadRequest as e:
                processing_time_ms = int((time.time() - processing_start) * 1000)
                logger.warning(f"Telegram API error processing update: {e}")
                await log_webhook_event(
                    bot_instance, 'error', update_id,
                    status='failed',
                    error_type='TelegramBadRequest',
                    error_message=str(e),
                    processing_time_ms=processing_time_ms,
                    telegram_signature_valid=signature_valid
                )
                # Still return 200 to prevent Telegram from retrying
            except Exception as e:
                processing_time_ms = int((time.time() - processing_start) * 1000)
                logger.error(f"Error processing update for bot {bot_instance.name}: {e}", exc_info=True)
                await log_webhook_event(
                    bot_instance, 'error', update_id,
                    status='failed',
                    error_type='ProcessingError',
                    error_message=str(e),
                    processing_time_ms=processing_time_ms,
                    telegram_signature_valid=signature_valid
                )
                # Return 200 to prevent Telegram from retrying on our errors

        finally:
            # Cleanup: close bot session
            if bot:
                try:
                    await bot.session.close()
                except Exception as e:
                    logger.error(f"Error closing bot session: {e}")

        # Log total processing time
        total_time_ms = int((time.time() - start_time) * 1000)
        logger.info(f"Webhook for bot {bot_instance.name} processed in {total_time_ms}ms")

        return HttpResponse("OK", status=200)

    except BotModel.DoesNotExist:
        logger.warning(f"Bot not found or inactive: {bot_id}")
        return HttpResponseForbidden("Bot not found or inactive")

    except Exception as e:
        logger.error(f"Unexpected error in webhook: {str(e)}", exc_info=True)
        if bot_instance and update_id:
            await log_webhook_event(
                bot_instance, 'error', update_id,
                status='failed',
                error_type='UnexpectedError',
                error_message=str(e),
                ip_address=ip_address,
                user_agent=user_agent
            )
        return HttpResponse("Error", status=500)

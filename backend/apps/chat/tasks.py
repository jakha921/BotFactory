"""
Celery tasks for chat processing.
"""
from celery import shared_task
from apps.bots.models import Bot
from apps.chat.models import ChatSession, ChatMessage
from apps.telegram.models import TelegramUser
from apps.analytics.models import MessageEvent
from services.gemini import get_gemini_service
# Note: get_or_create_telegram_user is implemented inline below
import time
import logging
import requests

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_telegram_update(self, bot_id, update_data):
    """
    Process incoming Telegram update (message).
    
    Args:
        bot_id: Bot UUID string
        update_data: Telegram update dict from webhook
    """
    try:
        start_time = time.time()
        
        # Get bot
        bot = Bot.objects.get(id=bot_id)
        message = update_data.get('message', {})
        
        if not message:
            logger.warning(f"No message in update for bot {bot_id}")
            return
        
        # Track received event
        MessageEvent.objects.create(
            bot=bot,
            event_type='received',
            message_length=len(message.get('text', ''))
        )
        
        # Get or create telegram user
        from_user = message.get('from', {})
        telegram_user, _ = TelegramUser.objects.get_or_create(
            telegram_id=from_user.get('id'),
            bot=bot,
            defaults={
                'username': from_user.get('username'),
                'first_name': from_user.get('first_name', ''),
                'last_name': from_user.get('last_name'),
            }
        )
        
        # Update last_active
        from django.utils import timezone
        telegram_user.last_active = timezone.now()
        telegram_user.message_count += 1
        telegram_user.save(update_fields=['last_active', 'message_count'])
        
        # Get or create chat session
        session = ChatSession.objects.filter(
            bot=bot,
            user=telegram_user
        ).order_by('-updated_at').first()
        
        if not session:
            session = ChatSession.objects.create(bot=bot, user=telegram_user)
        
        # Save user message
        user_message = ChatMessage.objects.create(
            session=session,
            role='user',
            content=message.get('text', '')
        )
        
        # Get chat history
        history = list(
            ChatMessage.objects.filter(session=session)
            .order_by('-timestamp')[:10]
            .values_list('role', 'content')
        )
        history = [{'role': r, 'content': c} for r, c in reversed(history)]
        
        # Generate AI response
        gemini = get_gemini_service()
        response = gemini.generate_response(
            model_name=bot.model,
            prompt=message.get('text', ''),
            system_instruction=bot.system_instruction or "You are a helpful assistant.",
            history=history[:-1] if history else [],  # Exclude current message
            temperature=bot.temperature
        )
        
        response_time = int((time.time() - start_time) * 1000)
        
        # Save bot response
        bot_message = ChatMessage.objects.create(
            session=session,
            role='model',
            content=response.get('text', '')
        )
        
        # Send response via Telegram
        send_telegram_message.delay(
            bot.decrypted_telegram_token,
            message['chat']['id'],
            response.get('text', '')
        )
        
        # Track sent event
        MessageEvent.objects.create(
            bot=bot,
            telegram_user=telegram_user,
            session=session,
            event_type='sent',
            message_length=len(response.get('text', '')),
            response_time_ms=response_time,
            tokens_used=response.get('usage', {}).get('total_tokens', 0),
            used_rag=False  # Future feature: RAG with knowledge base (see apps/knowledge/models.py)
        )
        
        logger.info(f"Processed message for bot {bot.name}, response time: {response_time}ms")
        
    except Exception as e:
        logger.error(f"Error processing update: {str(e)}", exc_info=True)
        
        # Track error event
        try:
            MessageEvent.objects.create(
                bot_id=bot_id,
                event_type='error',
                error_message=str(e)
            )
        except:
            pass
        
        # Retry with exponential backoff
        self.retry(exc=e, countdown=5 * (2 ** self.request.retries))


@shared_task
def send_telegram_message(token, chat_id, text):
    """
    Send message via Telegram Bot API.
    
    Args:
        token: Bot token
        chat_id: Chat ID
        text: Message text
    """
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        response = requests.post(url, json={
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        })
        response.raise_for_status()
        logger.info(f"Sent message to chat {chat_id}")
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise

"""
Chat message handler with AI response generation.
"""
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.enums import ChatAction
from aiogram.filters import Command, CommandStart
import logging

from bot.integrations.django_orm import (
    get_bot_by_token,
    get_or_create_telegram_user,
    create_chat_session,
    save_chat_message,
    get_chat_history,
    get_bot_knowledge_base,
)
from bot.services.message_processor import process_message
from bot.services.gemini_client import generate_bot_response

logger = logging.getLogger(__name__)

chat_router = Router()


@chat_router.message(
    F.content_type.in_(['text', 'voice', 'audio', 'document', 'photo'])
)
async def handle_message(message: Message, state: FSMContext):
    """
    Handle incoming messages (text, audio, files).
    Commands are handled by start_router and commands_router (registered before),
    so they won't reach this handler.
    """
    try:
        logger.info(f"[CHAT_ROUTER] Received message: text={message.text}, content_type={message.content_type}, from_user={message.from_user.id}")
        
        # Additional check: skip if message is a command (shouldn't happen, but safety check)
        if message.text and (message.text.startswith('/start') or message.text.startswith('/help')):
            logger.warning(f"[CHAT_ROUTER] Received command '{message.text}' - should have been handled by start_router or commands_router")
            return
        
        user = message.from_user
        bot_token = message.bot.token
        
        # Get bot instance
        try:
            bot = await get_bot_by_token(bot_token)
        except Exception as e:
            logger.error(f"[CHAT_ROUTER] Error getting bot by token: {str(e)}", exc_info=True)
            await message.answer("❌ Ошибка при получении данных бота. Попробуйте позже.")
            return
        
        if not bot:
            logger.warning(f"[CHAT_ROUTER] Bot not found for token: {bot_token[:20]}...")
            await message.answer("Бот не найден или не активирован.")
            return
        
        # Get or create Telegram user
        try:
            telegram_user = await get_or_create_telegram_user(
                bot=bot,
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name or "",
                last_name=user.last_name
            )
        except Exception as e:
            logger.error(f"[CHAT_ROUTER] Error getting/creating telegram user: {str(e)}", exc_info=True)
            await message.answer("❌ Ошибка при получении данных пользователя. Попробуйте позже.")
            return
        
        # Check if user is blocked
        if telegram_user.status == 'blocked':
            await message.answer("Вы заблокированы. Обратитесь к администратору.")
            return
        
        # Check if user is in form mode - if yes, skip this handler
        # forms_router (registered before) should have handled it with FormModeFilter
        session_data = await state.get_data()
        if session_data.get('form_name') and session_data.get('form_config'):
            logger.info("[CHAT_ROUTER] User is in form mode, skipping chat handler (forms_router should have handled it)")
            # Return without answer - forms_router already handled this message with FormModeFilter
            # But wait - if forms_router didn't handle it, we should let echo_router handle it
            # Actually, in aiogram if we return here, message is marked as handled
            # So we need to not process it at all - forms_router should have handled it
            return
        
        # Get or create chat session
        try:
            if not session_data.get('chat_session_id'):
                # Create new session
                chat_session = await create_chat_session(bot, telegram_user)
                await state.update_data(chat_session_id=str(chat_session.id))
            else:
                from apps.chat.models import ChatSession
                from asgiref.sync import sync_to_async
                chat_session = await sync_to_async(ChatSession.objects.get)(
                    id=session_data['chat_session_id']
                )
        except Exception as e:
            logger.error(f"[CHAT_ROUTER] Error creating/getting chat session: {str(e)}", exc_info=True)
            await message.answer("❌ Ошибка при создании сессии. Попробуйте еще раз.")
            return
        
        # Show "typing..." indicator
        try:
            await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
        except Exception as e:
            logger.warning(f"[CHAT_ROUTER] Error sending chat action: {str(e)}")
        
        try:
            # Process message (extract text from text/audio/files)
            processed_content = await process_message(
                message=message,
                bot=bot
            )
            
            logger.info(f"[CHAT_ROUTER] Processed content: {processed_content[:50] if processed_content else 'None'}...")
            
            if not processed_content or not processed_content.strip():
                logger.warning("[CHAT_ROUTER] Failed to process message content")
                await message.answer("Не удалось обработать сообщение. Попробуйте еще раз.")
                return
            
            # Save user message
            await save_chat_message(
                session=chat_session,
                role='user',
                content=processed_content,
                attachments={
                    'has_audio': message.voice is not None or message.audio is not None,
                    'has_document': message.document is not None,
                    'has_photo': message.photo is not None
                }
            )
            
            # Get chat history
            history = await get_chat_history(chat_session, limit=10)
            
            # Generate bot response using Gemini
            response = await generate_bot_response(
                bot=bot,
                prompt=processed_content,
                history=history
            )
            
            # Save bot response
            await save_chat_message(
                session=chat_session,
                role='model',
                content=response.get('text', ''),
                attachments={
                    'grounding_chunks': response.get('groundingChunks', [])
                }
            )
            
            # Send response
            response_text = response.get('text', 'Извините, не удалось сгенерировать ответ.')
            logger.info(f"[CHAT_ROUTER] Sending response: {response_text[:50]}...")
            await message.answer(response_text)
            logger.info("[CHAT_ROUTER] Response sent successfully")
            
        except Exception as e:
            logger.error(f"[CHAT_ROUTER] Error processing message: {str(e)}", exc_info=True)
            try:
                await message.answer("❌ Произошла ошибка при обработке сообщения. Попробуйте позже.")
            except Exception as send_error:
                logger.error(f"[CHAT_ROUTER] Error sending error message: {str(send_error)}")
    
    except Exception as e:
        # Catch any unhandled exceptions at the top level
        logger.error(f"[CHAT_ROUTER] Unexpected error in handle_message: {str(e)}", exc_info=True)
        try:
            await message.answer("❌ Произошла непредвиденная ошибка. Попробуйте позже.")
        except Exception as send_error:
            logger.error(f"[CHAT_ROUTER] Error sending error message in top-level catch: {str(send_error)}")


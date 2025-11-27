"""
General commands handler with dynamic help message.
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from bot.integrations.django_orm import get_bot_by_token


commands_router = Router()


@commands_router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command with dynamic help message."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"[COMMANDS_ROUTER] Processing /help command: from_user={message.from_user.id}")
    
    bot_token = message.bot.token
    
    # Get bot instance
    bot = await get_bot_by_token(bot_token)
    if not bot:
        await message.answer("Бот не найден или не активирован.")
        return
    
    # Use dynamic help message from bot configuration
    help_text = bot.help_message or "Помощь по использованию бота.\n\nИспользуйте /start для начала работы."
    
    await message.answer(help_text)


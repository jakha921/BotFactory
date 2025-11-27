"""
Start command handler with dynamic welcome message and keyboard.
"""
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from bot.integrations.django_orm import (
    get_bot_by_token,
    get_or_create_telegram_user,
)
from bot.keyboards.dynamic import get_main_menu_keyboard


start_router = Router()


@start_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command with dynamic welcome message and keyboard."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"[START_ROUTER] Processing /start command: from_user={message.from_user.id}")
    
    user = message.from_user
    bot_token = message.bot.token
    
    # Get bot instance using Django ORM
    bot = await get_bot_by_token(bot_token)
    if not bot:
        await message.answer("Бот не найден или не активирован.")
        return
    
    # Get or create Telegram user
    telegram_user = await get_or_create_telegram_user(
        bot=bot,
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name or "",
        last_name=user.last_name
    )
    
    # Clear any existing state
    await state.clear()
    
    # Use dynamic welcome message from bot configuration
    if bot.welcome_message:
        welcome_text = bot.welcome_message.replace('{first_name}', user.first_name or '')
    else:
        welcome_text = f"Привет, {user.first_name or 'пользователь'}!\n\n"
        welcome_text += f"Я {bot.name}. {bot.description or 'Чем могу помочь?'}"
    
    # Get dynamic main menu keyboard
    keyboard = await get_main_menu_keyboard(bot_token)
    
    await message.answer(
        welcome_text,
        reply_markup=keyboard
    )


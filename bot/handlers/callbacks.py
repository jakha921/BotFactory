"""
Callback query handlers for dynamic keyboards.
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.integrations.django_orm import get_bot_by_token
from bot.keyboards.dynamic import get_dynamic_keyboard_by_token


callbacks_router = Router()


@callbacks_router.callback_query(F.data.startswith("action_"))
async def handle_dynamic_action(callback: CallbackQuery, state: FSMContext):
    """
    Handle dynamic callback actions.
    
    Supported actions:
    - action_start_chat: Start chat
    - action_settings: Show settings
    - action_help: Show help
    - action_form_<form_name>: Start a form
    """
    action = callback.data
    bot_token = callback.bot.token
    
    if action == "action_start_chat":
        await callback.answer()
        await callback.message.answer("Начнем чат! Напишите ваш вопрос.")
    
    elif action == "action_settings":
        await callback.answer()
        # Get settings keyboard
        keyboard = await get_dynamic_keyboard_by_token(bot_token, 'settings_menu')
        await callback.message.answer("Настройки:", reply_markup=keyboard)
    
    elif action == "action_help":
        await callback.answer()
        bot = await get_bot_by_token(bot_token)
        if bot:
            help_text = bot.help_message or "Помощь по использованию бота."
            await callback.message.answer(help_text)
    
    elif action.startswith("action_form_"):
        form_name = action.replace("action_form_", "")
        await callback.answer()
        # Import form handler
        from bot.handlers.forms import start_form
        await start_form(callback.message, state, bot_token, form_name)
    
    else:
        await callback.answer("Действие не найдено.")


"""
Dynamic keyboards based on bot configuration.
"""
from typing import Optional, List, Dict, Any
from aiogram.types import InlineKeyboardMarkup
from bot.utils.keyboard_builder import build_inline_keyboard
from bot.services.ui_config_service import get_ui_config_service
from bot.integrations.django_orm import get_bot_by_token, get_bot_by_id


async def get_main_menu_keyboard(bot_token: str) -> Optional[InlineKeyboardMarkup]:
    """
    Get main menu keyboard from bot configuration.
    
    Args:
        bot_token: Telegram bot token
        
    Returns:
        InlineKeyboardMarkup or None if not configured
    """
    bot = await get_bot_by_token(bot_token)
    if not bot:
        return None
    
    ui_service = get_ui_config_service()
    keyboard_config = await ui_service.get_keyboard(str(bot.id), 'main_menu')
    
    if keyboard_config:
        return build_inline_keyboard(keyboard_config)
    
    # Fallback to default inline keyboard
    if bot.default_inline_keyboard:
        return build_inline_keyboard(bot.default_inline_keyboard)
    
    return None


async def get_settings_keyboard(bot_token: str) -> Optional[InlineKeyboardMarkup]:
    """
    Get settings keyboard from bot configuration.
    
    Args:
        bot_token: Telegram bot token
        
    Returns:
        InlineKeyboardMarkup or None if not configured
    """
    bot = await get_bot_by_token(bot_token)
    if not bot:
        return None
    
    ui_service = get_ui_config_service()
    keyboard_config = await ui_service.get_keyboard(str(bot.id), 'settings_menu')
    
    if keyboard_config:
        return build_inline_keyboard(keyboard_config)
    
    return None


async def get_dynamic_keyboard(
    bot_id: str,
    keyboard_name: str
) -> Optional[InlineKeyboardMarkup]:
    """
    Get dynamic keyboard by name from bot configuration.
    
    Args:
        bot_id: Bot UUID string
        keyboard_name: Name of the keyboard
        
    Returns:
        InlineKeyboardMarkup or None if not found
    """
    ui_service = get_ui_config_service()
    keyboard_config = await ui_service.get_keyboard(bot_id, keyboard_name)
    
    if keyboard_config:
        return build_inline_keyboard(keyboard_config)
    
    return None


async def get_dynamic_keyboard_by_token(
    bot_token: str,
    keyboard_name: str
) -> Optional[InlineKeyboardMarkup]:
    """
    Get dynamic keyboard by name using bot token.
    
    Args:
        bot_token: Telegram bot token
        keyboard_name: Name of the keyboard
        
    Returns:
        InlineKeyboardMarkup or None if not found
    """
    bot = await get_bot_by_token(bot_token)
    if not bot:
        return None
    
    return await get_dynamic_keyboard(str(bot.id), keyboard_name)


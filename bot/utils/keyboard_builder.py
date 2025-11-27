"""
Keyboard builder utilities for generating Telegram keyboards from JSON configuration.
"""
from typing import List, Dict, Any, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def build_inline_keyboard(config: List[List[Dict[str, Any]]]) -> InlineKeyboardMarkup:
    """
    Build InlineKeyboardMarkup from JSON configuration.
    
    Args:
        config: List of rows, where each row is a list of button configs
                Each button config: {"text": "...", "callback_data": "..."} or {"text": "...", "url": "..."}
    
    Returns:
        InlineKeyboardMarkup instance
    """
    builder = InlineKeyboardBuilder()
    
    for row in config:
        for button_config in row:
            button = _create_inline_button(button_config)
            if button:
                builder.add(button)
        
        # Adjust: one button per row by default, or keep row structure
        # We'll adjust at the end based on row count
    
    # Adjust buttons: each row becomes a row in the keyboard
    builder.adjust(*[len(row) for row in config])
    
    return builder.as_markup()


def _create_inline_button(button_config: Dict[str, Any]) -> Optional[InlineKeyboardButton]:
    """
    Create InlineKeyboardButton from button configuration.
    
    Args:
        button_config: Button config dict with 'text' and either 'callback_data' or 'url'
    
    Returns:
        InlineKeyboardButton instance or None if invalid
    """
    if 'text' not in button_config:
        return None
    
    text = button_config['text']
    
    # Check for callback_data (priority)
    if 'callback_data' in button_config:
        return InlineKeyboardButton(text=text, callback_data=button_config['callback_data'])
    
    # Check for URL
    if 'url' in button_config:
        return InlineKeyboardButton(text=text, url=button_config['url'])
    
    # Check for web_app
    if 'web_app' in button_config:
        return InlineKeyboardButton(text=text, web_app=button_config['web_app'])
    
    # Check for switch_inline_query
    if 'switch_inline_query' in button_config:
        return InlineKeyboardButton(
            text=text,
            switch_inline_query=button_config['switch_inline_query']
        )
    
    # Check for switch_inline_query_current_chat
    if 'switch_inline_query_current_chat' in button_config:
        return InlineKeyboardButton(
            text=text,
            switch_inline_query_current_chat=button_config['switch_inline_query_current_chat']
        )
    
    # Check for pay
    if 'pay' in button_config and button_config['pay']:
        return InlineKeyboardButton(text=text, pay=True)
    
    return None


def build_reply_keyboard(
    config: List[List[Dict[str, Any]]],
    resize_keyboard: bool = True,
    one_time_keyboard: bool = False,
    input_field_placeholder: Optional[str] = None,
    selective: bool = False
) -> ReplyKeyboardMarkup:
    """
    Build ReplyKeyboardMarkup from JSON configuration.
    
    Args:
        config: List of rows, where each row is a list of button configs
                Each button config: {"text": "..."}
        resize_keyboard: Requests clients to resize the keyboard vertically
        one_time_keyboard: Requests clients to hide the keyboard after use
        input_field_placeholder: Placeholder for input field
        selective: Use for selective keyboards
    
    Returns:
        ReplyKeyboardMarkup instance
    """
    builder = ReplyKeyboardBuilder()
    
    for row in config:
        for button_config in row:
            if 'text' in button_config:
                button = KeyboardButton(text=button_config['text'])
                builder.add(button)
        
        # Adjust: keep row structure
        builder.adjust(len(row))
    
    return builder.as_markup(
        resize_keyboard=resize_keyboard,
        one_time_keyboard=one_time_keyboard,
        input_field_placeholder=input_field_placeholder,
        selective=selective
    )


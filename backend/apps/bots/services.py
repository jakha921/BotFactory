"""
Services for bots app.
BotService for business logic related to bots.
"""
from typing import Optional, Dict, Any
from apps.bots.models import Bot


class BotService:
    """Service for working with bots and their UI configuration."""
    
    @staticmethod
    def get_bot_ui_config(bot_id: str) -> Optional[Dict[str, Any]]:
        """
        Get UI configuration for a bot.
        
        Args:
            bot_id: Bot UUID string
            
        Returns:
            Dict with UI configuration or None if bot not found
        """
        try:
            bot = Bot.objects.get(id=bot_id)
            return {
                'inline_keyboards': bot.ui_config.get('inline_keyboards', {}) if bot.ui_config else {},
                'forms': bot.ui_config.get('forms', {}) if bot.ui_config else {},
                'welcome_message': bot.welcome_message or '',
                'help_message': bot.help_message or '',
                'default_inline_keyboard': bot.default_inline_keyboard if bot.default_inline_keyboard else [],
            }
        except Bot.DoesNotExist:
            return None
    
    @staticmethod
    def get_bot_keyboard(bot_id: str, keyboard_name: str) -> Optional[Dict[str, Any]]:
        """
        Get specific keyboard configuration for a bot.
        
        Args:
            bot_id: Bot UUID string
            keyboard_name: Name of the keyboard
            
        Returns:
            Keyboard configuration (list of rows) or None if not found
        """
        try:
            bot = Bot.objects.get(id=bot_id)
            if not bot.ui_config or 'inline_keyboards' not in bot.ui_config:
                return None
            
            keyboards = bot.ui_config.get('inline_keyboards', {})
            return keyboards.get(keyboard_name)
        except Bot.DoesNotExist:
            return None
    
    @staticmethod
    def get_bot_form_config(bot_id: str, form_name: str) -> Optional[Dict[str, Any]]:
        """
        Get specific form configuration for a bot.
        
        Args:
            bot_id: Bot UUID string
            form_name: Name of the form
            
        Returns:
            Form configuration or None if not found
        """
        try:
            bot = Bot.objects.get(id=bot_id)
            if not bot.ui_config or 'forms' not in bot.ui_config:
                return None
            
            forms = bot.ui_config.get('forms', {})
            return forms.get(form_name)
        except Bot.DoesNotExist:
            return None
    
    @staticmethod
    def validate_ui_config(config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate UI configuration structure.
        
        Args:
            config: UI configuration dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(config, dict):
            return False, "Configuration must be a dictionary"
        
        # Validate inline_keyboards if present
        if 'inline_keyboards' in config:
            keyboards = config['inline_keyboards']
            if not isinstance(keyboards, dict):
                return False, "inline_keyboards must be a dictionary"
            
            for keyboard_name, keyboard_rows in keyboards.items():
                if not isinstance(keyboard_rows, list):
                    return False, f"Keyboard '{keyboard_name}' must be a list of rows"
                
                for row in keyboard_rows:
                    if not isinstance(row, list):
                        return False, f"Keyboard '{keyboard_name}' rows must be lists"
                    
                    for button in row:
                        if not isinstance(button, dict):
                            return False, f"Keyboard '{keyboard_name}' buttons must be dictionaries"
                        
                        if 'text' not in button:
                            return False, f"Button in '{keyboard_name}' must have 'text' field"
                        
                        # Button must have either callback_data or url
                        if 'callback_data' not in button and 'url' not in button:
                            return False, f"Button in '{keyboard_name}' must have 'callback_data' or 'url'"
        
        # Validate forms if present
        if 'forms' in config:
            forms = config['forms']
            if not isinstance(forms, dict):
                return False, "forms must be a dictionary"
            
            for form_name, form_config in forms.items():
                if not isinstance(form_config, dict):
                    return False, f"Form '{form_name}' must be a dictionary"
                
                if 'steps' not in form_config:
                    return False, f"Form '{form_name}' must have 'steps' field"
                
                if not isinstance(form_config['steps'], list):
                    return False, f"Form '{form_name}' steps must be a list"
                
                for step in form_config['steps']:
                    if not isinstance(step, dict):
                        return False, f"Form '{form_name}' steps must be dictionaries"
                    
                    required_fields = ['field', 'type', 'prompt']
                    for field in required_fields:
                        if field not in step:
                            return False, f"Form '{form_name}' step must have '{field}' field"
        
        return True, None

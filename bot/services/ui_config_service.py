"""
UI Configuration Service for bot.
Handles caching and retrieval of UI configuration from Django backend.
"""
from typing import Optional, Dict, Any, List
import asyncio
from datetime import datetime, timedelta
from bot.integrations.django_orm import (
    get_bot_ui_config,
    get_bot_keyboard_config,
    get_bot_form_config,
)


class UIConfigService:
    """Service for managing UI configuration with caching."""
    
    def __init__(self, cache_ttl: int = 300):
        """
        Initialize UI config service.
        
        Args:
            cache_ttl: Cache TTL in seconds (default: 5 minutes)
        """
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
    
    async def get_ui_config(self, bot_id: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get UI configuration for a bot with caching.
        
        Args:
            bot_id: Bot UUID string
            force_refresh: Force refresh cache
            
        Returns:
            UI configuration dict or None if not found
        """
        cache_key = f"ui_config_{bot_id}"
        
        # Check cache if not forcing refresh
        if not force_refresh and cache_key in self._cache:
            timestamp = self._cache_timestamps.get(cache_key)
            if timestamp and datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                return self._cache[cache_key]
        
        # Fetch from database (async function)
        config = await get_bot_ui_config(bot_id)
        
        if config:
            # Update cache
            self._cache[cache_key] = config
            self._cache_timestamps[cache_key] = datetime.now()
        
        return config
    
    async def get_keyboard(self, bot_id: str, keyboard_name: str, force_refresh: bool = False) -> Optional[List]:
        """
        Get specific keyboard configuration with caching.
        
        Args:
            bot_id: Bot UUID string
            keyboard_name: Name of the keyboard
            force_refresh: Force refresh cache
            
        Returns:
            Keyboard configuration (list of rows) or None if not found
        """
        # First get full UI config (uses cache)
        ui_config = await self.get_ui_config(bot_id, force_refresh=force_refresh)
        
        if not ui_config or 'inline_keyboards' not in ui_config:
            return None
        
        keyboards = ui_config.get('inline_keyboards', {})
        return keyboards.get(keyboard_name)
    
    async def get_form(self, bot_id: str, form_name: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get specific form configuration with caching.
        
        Args:
            bot_id: Bot UUID string
            form_name: Name of the form
            force_refresh: Force refresh cache
            
        Returns:
            Form configuration or None if not found
        """
        # First get full UI config (uses cache)
        ui_config = await self.get_ui_config(bot_id, force_refresh=force_refresh)
        
        if not ui_config or 'forms' not in ui_config:
            return None
        
        forms = ui_config.get('forms', {})
        return forms.get(form_name)
    
    async def refresh_config(self, bot_id: str) -> Optional[Dict[str, Any]]:
        """
        Force refresh UI configuration for a bot.
        
        Args:
            bot_id: Bot UUID string
            
        Returns:
            Updated UI configuration
        """
        return await self.get_ui_config(bot_id, force_refresh=True)
    
    def clear_cache(self, bot_id: Optional[str] = None):
        """
        Clear cache for a specific bot or all bots.
        
        Args:
            bot_id: Bot UUID string, or None to clear all cache
        """
        if bot_id:
            cache_key = f"ui_config_{bot_id}"
            self._cache.pop(cache_key, None)
            self._cache_timestamps.pop(cache_key, None)
        else:
            self._cache.clear()
            self._cache_timestamps.clear()


# Global instance
_ui_config_service: Optional[UIConfigService] = None


def get_ui_config_service() -> UIConfigService:
    """Get global UI config service instance."""
    global _ui_config_service
    if _ui_config_service is None:
        _ui_config_service = UIConfigService()
    return _ui_config_service


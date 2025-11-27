"""
Configuration for bot.
"""
import os
from dotenv import load_dotenv
from typing import List

load_dotenv()


class Settings:
    """Bot settings from environment variables."""
    # BOT_TOKEN removed - will be loaded from database
    # ADMIN_IDS removed - will be loaded from database
    DJANGO_API_BASE_URL: str = os.getenv("DJANGO_API_BASE_URL", "http://localhost:8000/api/v1")
    DJANGO_SETTINGS_MODULE: str = os.getenv("DJANGO_SETTINGS_MODULE", "bot_factory.settings.development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # ADMIN_IDS will be loaded from database dynamically
    _admin_ids: List[int] = []

    @property
    def ADMIN_IDS(self) -> List[int]:
        """Get admin Telegram IDs from database."""
        return self._admin_ids
    
    @ADMIN_IDS.setter
    def ADMIN_IDS(self, value: List[int]):
        """Set admin Telegram IDs."""
        self._admin_ids = value


settings = Settings()

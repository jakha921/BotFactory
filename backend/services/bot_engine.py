"""
Bot Engine - Global Dispatcher for Webhook Gateway.
Initializes a shared Dispatcher with all routers from bot/handlers.
Uses Redis for FSM storage to support multiple bots.
"""
import sys
import os
import logging
from pathlib import Path
from typing import Optional
from django.conf import settings

# Add project root to Python path (CRITICAL for bot imports)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT_STR = str(PROJECT_ROOT)
if PROJECT_ROOT_STR not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_STR)
    logger_early = logging.getLogger(__name__)
    logger_early.debug(f"Added PROJECT_ROOT to sys.path: {PROJECT_ROOT_STR}")

# Setup Django before importing bot handlers (which import models)
# CRITICAL: Django must be configured before any bot imports (which import Django models)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bot_factory.settings.development')
import django
try:
    django.setup()
except RuntimeError:
    # Django already configured
    pass
except Exception as e:
    logger_early = logging.getLogger(__name__)
    logger_early.error(f"Failed to setup Django: {e}", exc_info=True)

from aiogram import Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

logger = logging.getLogger(__name__)

# Global dispatcher instance
_shared_dispatcher: Optional[Dispatcher] = None


def get_redis_storage() -> RedisStorage:
    """
    Get Redis storage for FSM.
    
    Reads Redis URL from Django settings:
    - REDIS_URL environment variable
    - Defaults to redis://localhost:6379/0
    """
    redis_url = getattr(settings, 'REDIS_URL', os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))
    
    # Parse Redis URL if needed
    # Format: redis://[:password@]host[:port][/db]
    logger.info(f"Initializing Redis storage: {redis_url}")
    
    try:
        storage = RedisStorage.from_url(redis_url)
        logger.info("Redis storage initialized successfully")
        return storage
    except Exception as e:
        logger.error(f"Failed to initialize Redis storage: {e}")
        raise


def get_shared_dispatcher() -> Dispatcher:
    """
    Get or create the shared Dispatcher instance.
    
    This dispatcher is used for all bots via webhook gateway.
    It includes all routers from bot/handlers and uses Redis for FSM storage.
    
    Returns:
        Configured Dispatcher instance with all routers
    """
    global _shared_dispatcher
    
    if _shared_dispatcher is not None:
        return _shared_dispatcher
    
    logger.info("Initializing shared Dispatcher for webhook gateway...")
    
    try:
        # Verify PROJECT_ROOT is in sys.path
        if PROJECT_ROOT_STR not in sys.path:
            sys.path.insert(0, PROJECT_ROOT_STR)
            logger.info(f"Re-added PROJECT_ROOT to sys.path: {PROJECT_ROOT_STR}")
        
        # Verify bot directory exists
        bot_dir = PROJECT_ROOT / 'bot'
        if not bot_dir.exists():
            raise FileNotFoundError(f"Bot directory not found: {bot_dir}")
        
        logger.info(f"PROJECT_ROOT: {PROJECT_ROOT_STR}")
        logger.info(f"Bot directory exists: {bot_dir.exists()}")
        
        # Initialize Redis storage for FSM
        storage = get_redis_storage()
        
        # Create dispatcher with Redis storage
        _shared_dispatcher = Dispatcher(storage=storage)
        
        # Import all routers from bot handlers
        # CRITICAL: Django must be setup before these imports (done above)
        logger.info("Importing bot handlers...")
        from bot.handlers.start import start_router
        logger.debug("✅ Imported start_router")
        from bot.handlers.commands import commands_router
        logger.debug("✅ Imported commands_router")
        from bot.handlers.callbacks import callbacks_router
        logger.debug("✅ Imported callbacks_router")
        from bot.handlers.forms import forms_router
        logger.debug("✅ Imported forms_router")
        from bot.handlers.chat import chat_router
        logger.debug("✅ Imported chat_router")
        
        # Register routers (order matters - more specific first)
        # IMPORTANT: forms_router must be BEFORE chat_router
        # forms_router uses FormModeFilter to only process messages when user is in form mode
        # chat_router will process normal messages (not in form mode)
        _shared_dispatcher.include_router(start_router)  # /start command
        _shared_dispatcher.include_router(commands_router)  # /help and other commands
        _shared_dispatcher.include_router(callbacks_router)  # Callback queries (buttons)
        _shared_dispatcher.include_router(forms_router)  # Form handlers (only processes if user in form mode)
        _shared_dispatcher.include_router(chat_router)  # Chat messages (text, audio, files)
        
        logger.info("Shared Dispatcher initialized successfully with all routers")
        logger.info(f"Registered routers: {[r.name for r in _shared_dispatcher.sub_routers]}")
        
    except Exception as e:
        logger.error(f"Failed to initialize shared Dispatcher: {e}", exc_info=True)
        # Clear dispatcher cache on error to allow retry on next request
        _shared_dispatcher = None
        raise
    
    return _shared_dispatcher


def clear_dispatcher_cache():
    """Clear the shared dispatcher cache (useful for testing or reloading)."""
    global _shared_dispatcher
    _shared_dispatcher = None
    logger.info("Shared Dispatcher cache cleared")


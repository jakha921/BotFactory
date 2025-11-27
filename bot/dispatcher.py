"""
Dispatcher factory for creating aiogram dispatcher with all routers.
"""
# Ensure Django is setup before importing handlers (which import models)
from bot.integrations.django_setup import setup_django
setup_django()

from aiogram import Dispatcher

from bot.handlers.start import start_router
from bot.handlers.commands import commands_router
from bot.handlers.callbacks import callbacks_router
from bot.handlers.forms import forms_router
from bot.handlers.chat import chat_router


def create_dispatcher() -> Dispatcher:
    """Create dispatcher with all routers."""
    dp = Dispatcher()
    
    # Register routers (order matters - more specific first)
    # IMPORTANT: forms_router must be BEFORE chat_router
    # forms_router uses FormModeFilter to only process messages when user is in form mode
    # chat_router will process normal messages (not in form mode)
    dp.include_router(start_router)  # /start command
    dp.include_router(commands_router)  # /help and other commands
    dp.include_router(callbacks_router)  # Callback queries (buttons)
    dp.include_router(forms_router)  # Form handlers (only processes if user in form mode - FormModeFilter)
    dp.include_router(chat_router)  # Chat messages (text, audio, files) - handles normal messages
    
    return dp


"""
Main entry point for bot.
Loads all active bots from database and starts polling for each.
"""
import asyncio
import logging
from typing import List
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramConflictError
from bot.config import settings
from bot.integrations.django_setup import setup_django
from bot.integrations.django_orm import get_all_active_bots, get_admin_telegram_ids
from bot.dispatcher import create_dispatcher
from bot.services.bot_manager import get_bot_manager
from bot.services.bot_monitor import get_bot_monitor

# Setup Django
setup_django()

# Setup logging with structured format
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


async def run_bot(telegram_token: str, bot_name: str) -> None:
    """
    Run a single bot instance.
    
    Args:
        telegram_token: Telegram bot token
        bot_name: Bot name for logging
    """
    bot = None
    try:
        # Initialize bot
        bot = Bot(
            token=telegram_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        
        # Get bot info
        bot_info = await bot.get_me()
        logger.info(f"Starting bot: @{bot_info.username} ({bot_name}) - ID: {bot_info.id}")
        
        # Create dispatcher
        dp = create_dispatcher()
        
        # Start polling
        await dp.start_polling(bot, skip_updates=True)
        
    except TelegramConflictError:
        logger.warning(f"Conflict: Another bot instance is likely running for {bot_name}. Skipping this bot.")
        # Don't re-raise - allow other bots to continue
    except Exception as e:
        logger.error(f"Error running bot {bot_name} (token: {telegram_token[:20]}...): {str(e)}", exc_info=True)
        # Don't re-raise - allow other bots to continue
    finally:
        if bot:
            try:
                await bot.session.close()
            except:
                pass


async def main():
    """Main function to run all active bots."""
    logger.info("Loading configuration from database...")
    
    # Load admin IDs from database
    admin_ids = await get_admin_telegram_ids()
    settings.ADMIN_IDS = admin_ids
    if admin_ids:
        logger.info(f"Loaded {len(admin_ids)} admin Telegram ID(s): {admin_ids}")
    else:
        logger.warning("No admin users with Telegram ID found in database")
    
    # Initialize bot manager
    bot_manager = get_bot_manager()
    
    # Get all active bots from database and add them to manager
    logger.info("Loading active bots from database...")
    bots = await get_all_active_bots()
    
    if not bots:
        logger.warning("No active bots found in database. Make sure you have at least one bot with status='active' and telegram_token set.")
    else:
        logger.info(f"Found {len(bots)} active bot(s): {[b.name for b in bots]}")
        
        # Add all bots to manager
        for bot in bots:
            # Use decrypted token
            telegram_token = bot.decrypted_telegram_token
            if not telegram_token or telegram_token.strip() == '':
                logger.warning(f"Bot '{bot.name}' (ID: {bot.id}) has no telegram_token. Skipping.")
                continue
            
            await bot_manager.add_bot(telegram_token, bot.name)
    
    # Start bot monitor for dynamic reloading
    bot_monitor = get_bot_monitor(check_interval=30)
    await bot_monitor.start()
    
    logger.info("Bot system initialized. Monitoring for changes...")
    
    try:
        # Keep main loop running
        while True:
            await asyncio.sleep(60)  # Check every minute
            # Monitor handles bot lifecycle automatically
    except KeyboardInterrupt:
        logger.info("Shutting down bots...")
        await bot_monitor.stop()
        await bot_manager.stop_all()
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {str(e)}", exc_info=True)
        await bot_monitor.stop()
        await bot_manager.stop_all()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")

"""
Bot Manager for managing bot lifecycle (start, stop, restart).
"""
import asyncio
import logging
from typing import Dict, Optional, Set
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramConflictError

from bot.integrations.django_orm import get_bot_by_token
from bot.dispatcher import create_dispatcher

logger = logging.getLogger(__name__)


class BotManager:
    """
    Manager for bot lifecycle operations.
    
    Tracks running bots and provides methods to start, stop, and restart them.
    """
    
    def __init__(self):
        """Initialize BotManager."""
        self.running_bots: Dict[str, asyncio.Task] = {}  # token -> task
        self.bot_instances: Dict[str, Bot] = {}  # token -> Bot instance
        self._lock = asyncio.Lock()
    
    async def add_bot(self, telegram_token: str, bot_name: str) -> bool:
        """
        Add and start a bot.
        
        Args:
            telegram_token: Telegram bot token
            bot_name: Bot name for logging
            
        Returns:
            True if bot was added successfully, False otherwise
        """
        async with self._lock:
            if telegram_token in self.running_bots:
                task = self.running_bots[telegram_token]
                if not task.done():
                    logger.info(f"Bot '{bot_name}' (token: {telegram_token[:20]}...) is already running")
                    return False
                else:
                    # Task completed, remove it
                    del self.running_bots[telegram_token]
                    if telegram_token in self.bot_instances:
                        del self.bot_instances[telegram_token]
            
            # Create task for new bot
            task = asyncio.create_task(self._run_bot(telegram_token, bot_name))
            self.running_bots[telegram_token] = task
            logger.info(f"Added bot '{bot_name}' (token: {telegram_token[:20]}...) to manager")
            return True
    
    async def remove_bot(self, telegram_token: str) -> bool:
        """
        Remove and stop a bot.
        
        Args:
            telegram_token: Telegram bot token
            
        Returns:
            True if bot was removed successfully, False otherwise
        """
        async with self._lock:
            if telegram_token not in self.running_bots:
                logger.warning(f"Bot with token {telegram_token[:20]}... is not running")
                return False
            
            task = self.running_bots[telegram_token]
            
            # Cancel task if still running
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    logger.error(f"Error while stopping bot {telegram_token[:20]}...: {str(e)}")
            
            # Close bot session
            if telegram_token in self.bot_instances:
                bot = self.bot_instances[telegram_token]
                try:
                    await bot.session.close()
                except:
                    pass
                del self.bot_instances[telegram_token]
            
            del self.running_bots[telegram_token]
            logger.info(f"Removed bot with token {telegram_token[:20]}... from manager")
            return True
    
    async def restart_bot(self, telegram_token: str) -> bool:
        """
        Restart a bot (stop and start again).
        
        Args:
            telegram_token: Telegram bot token
            
        Returns:
            True if bot was restarted successfully, False otherwise
        """
        # Get bot name before removing
        bot_name = "Unknown"
        try:
            bot = await get_bot_by_token(telegram_token)
            if bot:
                bot_name = bot.name
        except:
            pass
        
        # Stop bot
        stopped = await self.remove_bot(telegram_token)
        if not stopped:
            logger.warning(f"Could not stop bot {telegram_token[:20]}... for restart")
        
        # Wait a bit before restarting
        await asyncio.sleep(1)
        
        # Start bot again
        started = await self.add_bot(telegram_token, bot_name)
        if started:
            logger.info(f"Restarted bot '{bot_name}' (token: {telegram_token[:20]}...)")
        else:
            logger.warning(f"Could not restart bot '{bot_name}' (token: {telegram_token[:20]}...)")
        
        return started
    
    async def update_bot(self, telegram_token: str, new_token: Optional[str] = None) -> bool:
        """
        Update bot configuration (restart with new token if provided).
        
        Args:
            telegram_token: Current Telegram bot token
            new_token: New Telegram bot token (if changed)
            
        Returns:
            True if bot was updated successfully, False otherwise
        """
        if new_token and new_token != telegram_token:
            # Token changed - remove old, add new
            await self.remove_bot(telegram_token)
            bot_name = "Unknown"
            try:
                bot = await get_bot_by_token(new_token)
                if bot:
                    bot_name = bot.name
            except:
                pass
            return await self.add_bot(new_token, bot_name)
        else:
            # Just restart with same token
            return await self.restart_bot(telegram_token)
    
    def is_running(self, telegram_token: str) -> bool:
        """
        Check if a bot is currently running.
        
        Args:
            telegram_token: Telegram bot token
            
        Returns:
            True if bot is running, False otherwise
        """
        if telegram_token not in self.running_bots:
            return False
        
        task = self.running_bots[telegram_token]
        return not task.done()
    
    def get_running_bots(self) -> Set[str]:
        """
        Get set of running bot tokens.
        
        Returns:
            Set of telegram tokens for running bots
        """
        running = set()
        for token, task in self.running_bots.items():
            if not task.done():
                running.add(token)
        return running
    
    async def stop_all(self):
        """Stop all running bots."""
        async with self._lock:
            tokens = list(self.running_bots.keys())
            for token in tokens:
                await self.remove_bot(token)
            logger.info("Stopped all bots")
    
    async def _run_bot(self, telegram_token: str, bot_name: str) -> None:
        """
        Internal method to run a bot instance.
        
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
            
            # Store bot instance
            self.bot_instances[telegram_token] = bot
            
            # Get bot info
            bot_info = await bot.get_me()
            logger.info(f"Starting bot: @{bot_info.username} ({bot_name}) - ID: {bot_info.id}")
            
            # Create dispatcher
            dp = create_dispatcher()
            
            # Start polling
            await dp.start_polling(bot, skip_updates=True)
            
        except TelegramConflictError:
            logger.warning(f"Conflict: Another bot instance is likely running for {bot_name}. Skipping this bot.")
        except asyncio.CancelledError:
            logger.info(f"Bot '{bot_name}' (token: {telegram_token[:20]}...) was cancelled")
            raise
        except Exception as e:
            logger.error(f"Error running bot {bot_name} (token: {telegram_token[:20]}...): {str(e)}", exc_info=True)
        finally:
            if bot:
                try:
                    await bot.session.close()
                except:
                    pass
                # Remove from instances if still there
                if telegram_token in self.bot_instances:
                    del self.bot_instances[telegram_token]


# Global bot manager instance
_bot_manager: Optional[BotManager] = None


def get_bot_manager() -> BotManager:
    """Get global BotManager instance."""
    global _bot_manager
    if _bot_manager is None:
        _bot_manager = BotManager()
    return _bot_manager


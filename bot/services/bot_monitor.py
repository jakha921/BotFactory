"""
Bot Monitor for monitoring bot configuration changes in database.
"""
import asyncio
import logging
from typing import Set, Dict, Optional
from datetime import datetime, timedelta

from bot.integrations.django_orm import get_all_active_bots, get_bot_by_token
from bot.services.bot_manager import get_bot_manager

logger = logging.getLogger(__name__)


class BotMonitor:
    """
    Monitor for tracking bot configuration changes in database.
    
    Periodically checks for new, removed, or changed bots and updates
    the BotManager accordingly.
    """
    
    def __init__(self, check_interval: int = 30):
        """
        Initialize BotMonitor.
        
        Args:
            check_interval: Interval in seconds between checks (default: 30)
        """
        self.check_interval = check_interval
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self._last_bot_tokens: Set[str] = set()
        self._bot_timestamps: Dict[str, datetime] = {}  # token -> last update time
        self.bot_manager = get_bot_manager()
    
    async def start(self):
        """Start monitoring."""
        if self.running:
            logger.warning("BotMonitor is already running")
            return
        
        self.running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info(f"BotMonitor started (check interval: {self.check_interval}s)")
    
    async def stop(self):
        """Stop monitoring."""
        if not self.running:
            return
        
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("BotMonitor stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop."""
        logger.info("BotMonitor loop started")
        
        while self.running:
            try:
                await self._check_bots()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in BotMonitor loop: {str(e)}", exc_info=True)
                await asyncio.sleep(self.check_interval)
        
        logger.info("BotMonitor loop stopped")
    
    async def _check_bots(self):
        """Check for bot changes and update BotManager."""
        try:
            # Get current active bots from database
            current_bots = await get_all_active_bots()
            current_tokens: Set[str] = set()
            
            # Process current bots
            for bot in current_bots:
                # Use decrypted token
                telegram_token = bot.decrypted_telegram_token
                if not telegram_token or telegram_token.strip() == '':
                    continue
                
                token = telegram_token
                current_tokens.add(token)
                
                # Check if bot was updated (compare updated_at)
                bot_updated_at = bot.updated_at
                last_known_update = self._bot_timestamps.get(token)
                
                if token not in self._last_bot_tokens:
                    # New bot - add it
                    logger.info(f"Detected new bot: '{bot.name}' (token: {token[:20]}...)")
                    await self.bot_manager.add_bot(token, bot.name)
                    self._bot_timestamps[token] = bot_updated_at
                elif last_known_update and bot_updated_at > last_known_update:
                    # Bot was updated - restart it
                    logger.info(f"Detected update for bot: '{bot.name}' (token: {token[:20]}...)")
                    await self.bot_manager.restart_bot(token)
                    self._bot_timestamps[token] = bot_updated_at
                elif token not in self._bot_timestamps:
                    # First time seeing this bot - add timestamp
                    self._bot_timestamps[token] = bot_updated_at
                elif not self.bot_manager.is_running(token):
                    # Bot should be running but isn't - restart it
                    logger.warning(f"Bot '{bot.name}' (token: {token[:20]}...) should be running but isn't. Restarting...")
                    await self.bot_manager.add_bot(token, bot.name)
            
            # Remove bots that are no longer active
            removed_tokens = self._last_bot_tokens - current_tokens
            for token in removed_tokens:
                logger.info(f"Detected removed bot (token: {token[:20]}...)")
                await self.bot_manager.remove_bot(token)
                if token in self._bot_timestamps:
                    del self._bot_timestamps[token]
            
            # Update last known tokens
            self._last_bot_tokens = current_tokens
            
        except Exception as e:
            logger.error(f"Error checking bots: {str(e)}", exc_info=True)


# Global bot monitor instance
_bot_monitor: Optional[BotMonitor] = None


def get_bot_monitor(check_interval: int = 30) -> BotMonitor:
    """Get global BotMonitor instance."""
    global _bot_monitor
    if _bot_monitor is None:
        _bot_monitor = BotMonitor(check_interval=check_interval)
    return _bot_monitor


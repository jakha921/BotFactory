"""
Analytics tracking utilities for bot service.
Non-blocking tracking to avoid impacting bot response times.
"""
import logging
import time
from typing import Optional
from apps.chat.models import ChatSession
from apps.telegram.models import TelegramUser
from apps.analytics.tasks import track_message_event

logger = logging.getLogger(__name__)


async def track_event(
    bot_id: str,
    event_type: str,
    telegram_user: Optional[TelegramUser] = None,
    session: Optional[ChatSession] = None,
    message_length: int = 0,
    response_time_ms: Optional[int] = None,
    tokens_used: Optional[int] = None,
    used_rag: bool = False,
    error_message: str = ""
):
    """
    Track analytics event asynchronously (non-blocking).

    Args:
        bot_id: Bot UUID string
        event_type: 'received', 'sent', or 'error'
        telegram_user: TelegramUser instance
        session: ChatSession instance
        message_length: Length of message in characters
        response_time_ms: Response time in milliseconds
        tokens_used: Total tokens used
        used_rag: Whether RAG was used
        error_message: Error description (for error events)
    """
    try:
        # Prepare kwargs for Celery task
        kwargs = {
            'bot_id': bot_id,
            'event_type': event_type,
            'message_length': message_length,
            'used_rag': used_rag,
        }

        if telegram_user:
            kwargs['telegram_user_id'] = str(telegram_user.id)
        if session:
            kwargs['session_id'] = str(session.id)
        if response_time_ms is not None:
            kwargs['response_time_ms'] = response_time_ms
        if tokens_used is not None:
            kwargs['tokens_used'] = tokens_used
        if error_message:
            kwargs['error_message'] = error_message

        # Run Celery task asynchronously (non-blocking)
        track_message_event.apply_async(kwargs=kwargs)

    except Exception as e:
        # Never block bot operation for analytics
        logger.warning(f"Failed to track analytics event: {str(e)}")


class ResponseTimeTracker:
    """Context manager for tracking response time."""

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, *args):
        self.end_time = time.time()

    @property
    def elapsed_ms(self) -> Optional[int]:
        """Get elapsed time in milliseconds."""
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time) * 1000)
        return None

"""
Django ORM integration for bot.
Provides async wrappers for Django ORM operations.
"""
from asgiref.sync import sync_to_async
from typing import Optional, Dict, Any, List
import django.utils.timezone as timezone
from django.db.models import Q

# Import Django models (after Django setup)
from apps.bots.models import Bot
from apps.telegram.models import TelegramUser
from apps.chat.models import ChatSession, ChatMessage
from apps.knowledge.models import TextSnippet, Document
from apps.accounts.models import User


@sync_to_async
def get_all_active_bots() -> List[Bot]:
    """Get all active bots from database."""
    return list(Bot.objects.filter(status='active', telegram_token__isnull=False).exclude(telegram_token=''))


@sync_to_async
def get_admin_telegram_ids() -> List[int]:
    """
    Get list of Telegram IDs for admin users (is_staff=True or is_superuser=True).
    
    Returns:
        List of Telegram user IDs (integers) for admin users who have telegram_id set
    """
    admin_users = User.objects.filter(
        is_active=True,
        telegram_id__isnull=False
    ).filter(
        Q(is_staff=True) | Q(is_superuser=True)
    )
    
    return [user.telegram_id for user in admin_users if user.telegram_id]


@sync_to_async
def get_bot_by_token(telegram_token: str) -> Optional[Bot]:
    """
    Get active bot by telegram token.
    Since tokens are encrypted in DB, we need to check all active bots
    and compare decrypted tokens.
    """
    try:
        # Get all active bots with tokens
        active_bots = Bot.objects.filter(status='active', telegram_token__isnull=False).exclude(telegram_token='')
        
        # Find bot with matching decrypted token
        for bot in active_bots:
            if bot.decrypted_telegram_token == telegram_token:
                return bot
        
        return None
    except Exception:
        return None


@sync_to_async
def get_bot_by_id(bot_id: str) -> Optional[Bot]:
    """Get bot by UUID."""
    try:
        return Bot.objects.get(id=bot_id)
    except Bot.DoesNotExist:
        return None


@sync_to_async
def get_or_create_telegram_user(
    bot: Bot,
    telegram_id: int,
    username: Optional[str] = None,
    first_name: str = "",
    last_name: Optional[str] = None
) -> TelegramUser:
    """Get or create Telegram user."""
    user, created = TelegramUser.objects.get_or_create(
        telegram_id=telegram_id,
        bot=bot,
        defaults={
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'status': 'active'
        }
    )
    
    # Update last_active
    user.last_active = timezone.now()
    user.message_count += 1
    user.save(update_fields=['last_active', 'message_count'])
    
    return user


@sync_to_async
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


@sync_to_async
def get_bot_keyboard_config(bot_id: str, keyboard_name: str) -> Optional[List]:
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


@sync_to_async
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


@sync_to_async
def create_chat_session(bot: Bot, telegram_user: TelegramUser) -> ChatSession:
    """Create new chat session."""
    session = ChatSession.objects.create(
        bot=bot,
        user=telegram_user
    )
    return session


@sync_to_async
def save_chat_message(
    session: ChatSession,
    role: str,
    content: str,
    is_thinking: bool = False,
    attachments: Optional[Dict[str, Any]] = None
) -> ChatMessage:
    """Save chat message to database."""
    message = ChatMessage.objects.create(
        session=session,
        role=role,
        content=content,
        is_thinking=is_thinking,
        attachments=attachments or {}
    )
    return message


@sync_to_async
def get_chat_history(session: ChatSession, limit: int = 10) -> List[Dict[str, str]]:
    """Get chat history as list of {role, content} dicts."""
    messages = ChatMessage.objects.filter(
        session=session
    ).order_by('-timestamp')[:limit]
    
    history = []
    for msg in reversed(messages):  # Oldest first
        history.append({
            'role': msg.role,
            'content': msg.content
        })
    
    return history


@sync_to_async
def get_bot_knowledge_base(bot_id: str) -> Dict[str, Any]:
    """
    Get knowledge base (snippets and documents) for bot.
    
    Args:
        bot_id: Bot UUID
        
    Returns:
        Dict with 'snippets' and 'documents' lists
    """
    bot = Bot.objects.get(id=bot_id)
    
    snippets = list(
        TextSnippet.objects.filter(bot=bot).values(
            'title', 'content', 'tags'
        )
    )
    
    documents = list(
        Document.objects.filter(bot=bot, status='ready').values(
            'name', 'type'
        )
    )
    
    return {
        'snippets': snippets,
        'documents': documents
    }

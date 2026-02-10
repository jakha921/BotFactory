"""
Command Registry Service - Dynamic command loading from database.

This service loads bot commands from the database and provides them
to the bot handlers, enabling dynamic command configuration through the admin panel.
"""
import logging
from typing import Dict, Optional, Callable, Any
from asgiref.sync import sync_to_async
from django.utils import timezone
from aiogram.types import InlineKeyboardButton

from bot.integrations.django_orm import get_all_active_bots
from apps.commands.models import Command, ResponseType


logger = logging.getLogger(__name__)


# Global command registry: {bot_id: {command_name: command_config}}
_command_registry: Dict[str, Dict[str, Any]] = {}


def clear_command_registry():
    """Clear the command registry (useful for testing or reloading)."""
    global _command_registry
    _command_registry.clear()
    logger.info("Command registry cleared")


@sync_to_async
def load_commands_for_bot(bot_id: str) -> Dict[str, Dict[str, Any]]:
    """
    Load all active commands for a specific bot from the database.

    Args:
        bot_id: UUID of the bot

    Returns:
        Dictionary mapping command_name to command configuration:
        {
            'command_name': {
                'name': 'start',
                'description': 'Start the bot',
                'response_type': 'text',
                'text_response': 'Welcome!',
                'ai_prompt_override': 'You are a helpful assistant',
                'form_id': 'form1',
                'menu_config': {...},
                'priority': 10
            }
        }
    """
    from apps.bots.models import Bot

    try:
        bot = Bot.objects.get(id=bot_id, status='active')
        commands = Command.objects.filter(
            bot=bot,
            is_active=True
        ).order_by('-priority', 'name')

        command_dict = {}
        for cmd in commands:
            command_dict[cmd.name] = {
                'name': cmd.name,
                'description': cmd.description,
                'response_type': cmd.response_type,
                'text_response': cmd.text_response,
                'ai_prompt_override': cmd.ai_prompt_override,
                'form_id': cmd.form_id,
                'menu_config': cmd.menu_config or [],
                'priority': cmd.priority
            }

        logger.info(
            f"Loaded {len(command_dict)} commands for bot {bot.name} (ID: {bot_id})"
        )
        return command_dict

    except Bot.DoesNotExist:
        logger.error(f"Bot {bot_id} not found")
        return {}
    except Exception as e:
        logger.error(f"Error loading commands for bot {bot_id}: {e}", exc_info=True)
        return {}


@sync_to_async
def reload_commands_for_bot(bot_id: str) -> Dict[str, Dict[str, Any]]:
    """
    Reload commands for a specific bot (called by BotMonitor).

    This updates the in-memory command registry when commands are modified
    in the database.
    """
    logger.info(f"Reloading commands for bot {bot_id}")
    return load_commands_for_bot(bot_id)


async def get_commands_for_bot(bot_id: str) -> Dict[str, Dict[str, Any]]:
    """
    Get commands for a bot, loading from cache or database.

    Args:
        bot_id: UUID of the bot

    Returns:
        Dictionary mapping command_name to command configuration
    """
    # Check if commands are cached
    if bot_id not in _command_registry:
        _command_registry[bot_id] = await load_commands_for_bot(bot_id)

    return _command_registry.get(bot_id, {})


async def handle_dynamic_command(
    command_name: str,
    bot_id: str,
    message_obj: Any,
    user_obj: Any
) -> Optional[str]:
    """
    Handle a dynamic command from the database.

    Args:
        command_name: Name of the command (without /)
        bot_id: UUID of the bot
        message_obj: aiogram Message object
        user_obj: TelegramUser model instance

    Returns:
        Response text to send, or None if command not found
    """
    commands = await get_commands_for_bot(bot_id)

    if command_name not in commands:
        logger.warning(f"Command /{command_name} not found in registry for bot {bot_id}")
        return None

    cmd = commands[command_name]

    try:
        # Handle different response types
        if cmd['response_type'] == ResponseType.TEXT:
            # Static text response
            return cmd['text_response']

        elif cmd['response_type'] == ResponseType.AI:
            # AI-generated response
            from bot.services.ai_client import generate_bot_response
            from bot.integrations.django_orm import get_bot_by_id

            bot = await get_bot_by_id(bot_id)
            if not bot:
                return "Bot configuration error"

            # Get chat history for context
            from apps.chat.models import ChatMessage
            history = list(ChatMessage.objects.filter(
                session__bot_id=bot_id,
                session__user=user_obj
            ).order_by('-timestamp')[:10].values(
                'role', 'content'
            ))

            # Convert to format expected by AI service
            formatted_history = [
                {'role': msg['role'], 'content': msg['content']}
                for msg in history
            ]

            # Generate response
            result = await generate_bot_response(
                bot=bot,
                prompt=message_obj.text or "start",
                history=formatted_history,
                system_instruction=cmd['ai_prompt_override'] or bot.system_instruction
            )

            return result.get('text', 'AI response generation failed')

        elif cmd['response_type'] == ResponseType.FORM:
            # Form response - trigger form handler
            # This would integrate with forms system
            return f"Form: {cmd['form_id']} (form integration not yet implemented)"

        elif cmd['response_type'] == ResponseType.MENU:
            # Menu response - show inline keyboard
            from aiogram.types import InlineKeyboardMarkup

            # Build keyboard from menu_config
            keyboard_data = cmd['menu_config']
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        button['text'],
                        callback_data=button.get('callback_data', '')
                    )
                    for button in row.get('buttons', [])
                ]
                for row in keyboard_data.get('rows', [])
            ])

            # Send keyboard with message
            if message_obj:
                from aiogram.types import ReplyKeyboardMarkup
                reply_markup = ReplyKeyboardMarkup(
                    keyboard=keyboard,
                    resize_keyboard=True
                )
                await message_obj.reply(
                    cmd.get('text_response', 'Select an option:'),
                    reply_markup=reply_markup
                )
            return None  # Message already sent

        else:
            logger.warning(f"Unknown response type: {cmd['response_type']}")
            return None

    except Exception as e:
        logger.error(f"Error handling command /{command_name}: {e}", exc_info=True)
        return f"Error executing command: {str(e)}"


def get_all_bot_commands() -> Dict[str, Dict[str, Dict]]:
    """
    Get all commands for all active bots (for admin/debugging).

    Returns:
        Dictionary mapping bot_id to command dictionaries
    """
    bot_commands = {}
    active_bots = get_all_active_bots()

    for bot in active_bots:
        bot_id_str = str(bot.id)
        try:
            commands = Command.objects.filter(
                bot=bot,
                is_active=True
            ).order_by('-priority', 'name')

            command_dict = {}
            for cmd in commands:
                command_dict[cmd.name] = {
                    'name': cmd.name,
                    'description': cmd.description,
                    'response_type': cmd.response_type,
                    'text_response': cmd.text_response,
                    'ai_prompt_override': cmd.ai_prompt_override,
                    'form_id': cmd.form_id,
                    'menu_config': cmd.menu_config or [],
                    'priority': cmd.priority
                }

            bot_commands[bot_id_str] = command_dict

        except Exception as e:
            logger.error(f"Error loading commands for bot {bot.name}: {e}")

    return bot_commands


def reload_all_commands():
    """
    Reload commands for all active bots.

    Called by BotMonitor when database changes are detected.
    """
    logger.info("Reloading all commands from database")
    clear_command_registry()

    bot_commands = get_all_bot_commands()
    _command_registry.update(bot_commands)

    logger.info(f"Reloaded commands for {len(bot_commands)} bots")


@sync_to_async
def get_command_handler(command_name: str) -> Optional[Callable]:
    """
    Get a handler function for a specific command.

    This returns an async function that can be used as a command handler.

    Args:
        command_name: Name of the command (without /)

    Returns:
        Async handler function or None if command not found
    """
    async def handler(message, *args, **kwargs):
        """Dynamic command handler."""
        # Extract bot_id from message context
        bot_token = message.bot.token
        from bot.integrations.django_orm import get_bot_by_token

        bot = await get_bot_by_token(bot_token)
        if not bot:
            await message.answer("Bot configuration error")
            return

        # Get user
        from apps.telegram.models import TelegramUser
        user, created = await TelegramUser.objects.aget_or_create(
            telegram_id=message.from_user.id,
            defaults={
                'username': message.from_user.username or '',
                'first_name': message.from_user.first_name or '',
                'last_active': timezone.now()
            }
        )

        # Handle the command
        response = await handle_dynamic_command(
            command_name=command_name,
            bot_id=str(bot.id),
            message_obj=message,
            user_obj=user
        )

        if response:
            await message.answer(response)

    return handler


def register_dynamic_commands(dp):
    """
    Register all dynamic commands with the dispatcher.

    This is called during bot initialization to register handlers
    for all commands found in the database.

    Args:
        dp: aiogram Dispatcher instance
    """
    from aiogram import Router
    from aiogram.filters import Command

    # Get all active bots
    active_bots = get_all_active_bots()

    for bot in active_bots:
        bot_id_str = str(bot.id)

        try:
            commands = Command.objects.filter(
                bot=bot,
                is_active=True
            ).order_by('-priority', 'name')

            if not commands.exists():
                logger.info(f"No active commands found for bot {bot.name}")
                continue

            # Create a router for this bot's commands
            router = Router()
            router.name = f"bot_{bot_id_str[:8]}_commands"

            # Register each command as a handler
            for cmd in commands:
                cmd_name = cmd.name

                # Create a dynamic handler
                async def dynamic_handler(message, cmd_name=cmd_name, *args, **kwargs):
                    """Dynamic command handler wrapper."""
                    return await get_command_handler(cmd_name)(message, *args, **kwargs)

                # Register with Command filter
                router.message(Command(cmd_name))(dynamic_handler)

            # Include router in dispatcher
            dp.include_router(router)
            logger.info(
                f"Registered {len(commands)} dynamic commands for bot {bot.name}"
            )

        except Exception as e:
            logger.error(f"Error registering commands for bot {bot.name}: {e}", exc_info=True)

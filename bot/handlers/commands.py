"""
General commands handler with dynamic command loading from database.

This module integrates with the command_registry to provide dynamic command
handling. Commands are loaded from the database and can be configured through
the admin panel without requiring bot restart.
"""
import logging
from django.utils import timezone
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from bot.integrations.django_orm import get_bot_by_token
from bot.services.command_registry import (
    get_commands_for_bot,
    handle_dynamic_command,
    register_dynamic_commands
)


logger = logging.getLogger(__name__)

commands_router = Router()


@commands_router.message(Command("help"))
async def cmd_help(message: Message):
    """
    Handle /help command with dynamic command listing.

    This command shows all available commands for the bot, dynamically
    loaded from the database.
    """
    logger.info(
        f"[COMMANDS_ROUTER] Processing /help command: "
        f"from_user={message.from_user.id}"
    )

    bot_token = message.bot.token

    # Get bot instance
    bot = await get_bot_by_token(bot_token)
    if not bot:
        await message.answer("Бот не найден или не активирован.")
        return

    # Get all commands for this bot
    commands = await get_commands_for_bot(str(bot.id))

    if not commands:
        # No commands configured, show default help
        help_text = (
            bot.help_message
            or "Помощь по использованию бота.\n\nИспользуйте /start для начала работы."
        )
        await message.answer(help_text)
        return

    # Build dynamic help message
    help_parts = ["📋 *Доступные команды:*\n"]

    for cmd_name, cmd_config in commands.items():
        # Format: /command - Description
        desc = cmd_config.get('description', 'Нет описания')
        help_parts.append(f"/{cmd_name} - {desc}")

    help_parts.append("\n" + (bot.help_message or "Выберите команду из списка выше."))

    await message.answer("\n".join(help_parts), parse_mode="Markdown")


@commands_router.message(F.text.startswith('/'))
async def cmd_dynamic(message: Message):
    """
    Dynamic command handler that processes all commands registered in the database.

    This handler is a catch-all for commands that are defined in the database
    but not explicitly registered as handlers. It checks the command registry
    and processes the command if found.
    """
    # Extract command name from message
    # The message.text is like "/command" or "/command args"
    text = message.text or ""
    if not text.startswith('/'):
        return

    # Split to get command name (first word after /)
    parts = text.split(maxsplit=1)
    command_name = parts[0][1:]  # Remove leading /

    logger.info(
        f"[COMMANDS_ROUTER] Processing dynamic command /{command_name}: "
        f"from_user={message.from_user.id}"
    )

    bot_token = message.bot.token

    # Get bot instance
    bot = await get_bot_by_token(bot_token)
    if not bot:
        await message.answer("Бот не найден или не активирован.")
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

    # Handle the command via registry
    response = await handle_dynamic_command(
        command_name=command_name,
        bot_id=str(bot.id),
        message_obj=message,
        user_obj=user
    )

    if response:
        await message.answer(response)
    else:
        # Command not found in registry
        await message.answer(f"Неизвестная команда: /{command_name}\nИспользуйте /help для списка команд.")


@commands_router.message(Command("webhook_status"))
async def cmd_webhook_status(message: Message):
    """
    Handle /webhook_status command (admin only).

    This command shows the current delivery mode and webhook status
    for the bot. Only available to admin users.
    """
    from apps.accounts.models import User

    logger.info(
        f"[COMMANDS_ROUTER] Processing /webhook_status command: "
        f"from_user={message.from_user.id}"
    )

    bot_token = message.bot.token

    # Get bot instance
    bot = await get_bot_by_token(bot_token)
    if not bot:
        await message.answer("Бот не найден или не активирован.")
        return

    # Check if user is admin (by telegram_id)
    try:
        admin_user = await User.objects.aget(
            telegram_id=message.from_user.id,
            is_staff=True
        )
    except Exception:
        await message.answer("❌ Эта команда доступна только администраторам.")
        return

    # Build status message
    mode_emoji = "🔗" if bot.delivery_mode == 'webhook' else "🔄"
    mode_name = "Webhook" if bot.delivery_mode == 'webhook' else "Polling"

    status_parts = [
        f"{mode_emoji} *Статус бота:* {bot.name}\n",
        f"📡 *Режим доставки:* {mode_name}\n",
    ]

    if bot.delivery_mode == 'webhook':
        from django.conf import settings
        base_url = getattr(settings, 'WEBHOOK_BASE_URL', 'http://localhost:8000')
        webhook_url = bot.webhook_url or f"{base_url}/api/v1/telegram/webhook/{bot.id}/"

        status_parts.extend([
            f"🌐 *Webhook URL:* `{webhook_url}`\n",
            f"🔐 *Secret:* {'✅ Установлен' if bot.webhook_secret else '❌ Не установлен'}\n",
        ])

        # Try to get webhook info from Telegram
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                telegram_url = f"https://api.telegram.org/bot{bot.decrypted_telegram_token}/getWebhookInfo"
                response = await client.get(telegram_url, timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('ok'):
                        webhook_info = data.get('result', {})
                        status_parts.append(f"\n📊 *Telegram Webhook Info:*\n")
                        status_parts.append(f"URL: {webhook_info.get('url', 'Не установлен')}\n")
                        status_parts.append(f"Pending updates: {webhook_info.get('pending_update_count', 0)}\n")
                        if webhook_info.get('last_error_date'):
                            import datetime
                            error_date = datetime.datetime.fromtimestamp(webhook_info['last_error_date'])
                            status_parts.append(f"⚠️ Last error: {webhook_info.get('last_error_message', 'Unknown')} ({error_date})\n")
                        else:
                            status_parts.append("✅ No errors\n")
        except Exception as e:
            status_parts.append(f"\n⚠️ Не удалось получить статус у Telegram: {str(e)}\n")

    await message.answer("\n".join(status_parts), parse_mode="Markdown")


def register_commands(dp):
    """
    Register dynamic commands from database to dispatcher.

    This function should be called during bot initialization to register
    all commands defined in the database as explicit handlers.

    Args:
        dp: aiogram Dispatcher instance
    """
    register_dynamic_commands(dp)
    logger.info("Dynamic commands registered from database")


# Generated migration for encrypting telegram tokens

from django.db import migrations, models
from core.utils import encrypt_token


def encrypt_existing_tokens(apps, schema_editor):
    """
    Encrypt existing telegram tokens in the database.
    This migration is optional - tokens will be encrypted on save automatically.
    """
    Bot = apps.get_model('bots', 'Bot')
    
    for bot in Bot.objects.filter(telegram_token__isnull=False).exclude(telegram_token=''):
        if bot.telegram_token:
            # Only encrypt if not already encrypted (check for Fernet prefix)
            if not bot.telegram_token.startswith('gAAAAAB'):
                try:
                    encrypted = encrypt_token(bot.telegram_token)
                    bot.telegram_token = encrypted
                    bot.save(update_fields=['telegram_token'])
                except Exception:
                    # If encryption fails, leave token as-is
                    pass


def reverse_encryption(apps, schema_editor):
    """
    Reverse encryption - cannot decrypt without the key, so we do nothing.
    Tokens will be decrypted automatically when accessed via model property.
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('bots', '0002_add_ui_config'),
    ]

    operations = [
        # First, alter the field to allow longer encrypted values
        migrations.AlterField(
            model_name='bot',
            name='telegram_token',
            field=models.CharField(blank=True, max_length=500),
        ),
        # Then encrypt existing tokens (optional, can be skipped if preferred)
        # migrations.RunPython(encrypt_existing_tokens, reverse_encryption),
    ]


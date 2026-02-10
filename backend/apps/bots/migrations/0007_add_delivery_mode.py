# Generated manually for webhook migration
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('bots', '0006_add_rag_enabled_to_bot'),
    ]

    operations = [
        migrations.AddField(
            model_name='bot',
            name='delivery_mode',
            field=models.CharField(
                choices=[('polling', 'Polling'), ('webhook', 'Webhook')],
                default='polling',
                help_text='How Telegram updates are delivered: polling (bot service) or webhook (HTTP callback)',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='bot',
            name='webhook_url',
            field=models.URLField(
                blank=True,
                help_text='Custom webhook URL (optional, uses default if empty)',
                max_length=500
            ),
        ),
        migrations.AddIndex(
            model_name='bot',
            index=models.Index(fields=['delivery_mode'], name='bots_deliver_mode_idx'),
        ),
    ]

# Generated manually for UserNotificationPreferences

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_add_user_api_keys'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserNotificationPreferences',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email_alerts', models.BooleanField(default=True)),
                ('push_notifications', models.BooleanField(default=False)),
                ('weekly_digest', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='notification_prefs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Notification Preferences',
                'verbose_name_plural': 'Notification Preferences',
            },
        ),
    ]

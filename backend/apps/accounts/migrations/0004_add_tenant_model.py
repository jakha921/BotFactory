# Generated manually for Tenant model and User.tenant foreign key

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_add_notification_preferences'),
    ]

    operations = [
        # Create Tenant model
        migrations.CreateModel(
            name='Tenant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
                ('slug', models.SlugField(unique=True, max_length=100)),
                ('plan', models.CharField(
                    choices=[('FREE', 'Free'), ('STARTER', 'Starter'), ('PRO', 'Pro'), ('ENTERPRISE', 'Enterprise')],
                    default='FREE',
                    max_length=20,
                    verbose_name='Plan'
                )),
                ('plan_expires_at', models.DateTimeField(
                    blank=True,
                    null=True,
                    verbose_name='Plan expires at'
                )),
                ('max_bots', models.IntegerField(
                    default=1,
                    verbose_name='Max bots',
                    help_text='Maximum number of bots allowed'
                )),
                ('max_messages_per_month', models.IntegerField(
                    default=1000,
                    verbose_name='Max messages per month'
                )),
                ('messages_used', models.IntegerField(
                    default=0,
                    verbose_name='Messages used'
                )),
                ('openai_api_key', models.CharField(
                    blank=True,
                    max_length=500,
                    null=True,
                    verbose_name='OpenAI API Key',
                    help_text='Encrypted API key for OpenAI'
                )),
                ('use_platform_key', models.BooleanField(
                    default=True,
                    verbose_name='Use platform key',
                    help_text="Use platform's API key instead of custom"
                )),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
            ],
            options={
                'verbose_name': 'Tenant',
                'verbose_name_plural': 'Tenants',
                'ordering': ['-created_at'],
                'db_table': 'accounts_tenant',
            },
        ),

        # Add tenant field to User (nullable initially for migration)
        migrations.AddField(
            model_name='user',
            name='tenant',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='users',
                to='accounts.tenant',
                null=True,
                blank=True,
                verbose_name='Organization'
            ),
        ),

        # Remove old plan field from User if it exists
        migrations.RemoveField(
            model_name='user',
            name='plan',
        ),
    ]

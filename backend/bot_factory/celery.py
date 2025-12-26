"""
Celery configuration for Bot Factory.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bot_factory.settings.development')

app = Celery('bot_factory')

# Load config from Django settings with CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    'aggregate-daily-analytics': {
        'task': 'apps.analytics.tasks.aggregate_daily_analytics',
        'schedule': crontab(hour=0, minute=5),  # Every day at 00:05
    },
    'calculate-retention': {
        'task': 'apps.analytics.tasks.calculate_retention',
        'schedule': crontab(hour=1, minute=0),  # Every day at 01:00
    },
}

app.conf.timezone = 'UTC'


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery."""
    print(f'Request: {self.request!r}')

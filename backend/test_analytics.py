import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bot_factory.settings.development')
import django
django.setup()

from apps.analytics.models import BotAnalytics, MessageEvent, TokenUsage
from apps.bots.models import Bot
from django.utils import timezone

# Test BotAnalytics creation
bot = Bot.objects.first()
if bot:
    analytics = BotAnalytics.objects.create(
        bot=bot,
        date=timezone.now().date(),
        messages_received=10,
        messages_sent=10,
        unique_users=5,
        tokens_used=1500,
        positive_feedback=8,
        negative_feedback=2
    )
    print(f'✅ Created BotAnalytics: {analytics}')
    print(f'   Feedback ratio: {analytics.feedback_ratio:.1f}%')
    
    # Test TokenUsage
    token_usage = TokenUsage.objects.create(
        bot=bot,
        date=timezone.now().date(),
        input_tokens=1000,
        output_tokens=500
    )
    print(f'✅ Created TokenUsage: {token_usage}')
    print(f'   Total tokens: {token_usage.total_tokens}')
    print(f'   Estimated cost: ${token_usage.estimated_cost_cents / 100:.4f}')
else:
    print('❌ No bot found')

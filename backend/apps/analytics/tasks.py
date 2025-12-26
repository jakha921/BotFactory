"""
Celery tasks for analytics.
"""
from celery import shared_task
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from datetime import timedelta
from apps.analytics.models import BotAnalytics, MessageEvent, UserRetention
from apps.bots.models import Bot
from apps.telegram.models import TelegramUser
import logging

logger = logging.getLogger(__name__)


@shared_task
def aggregate_daily_analytics():
    """
    Aggregate analytics for yesterday.
    Runs daily at 00:05 via Celery Beat.
    """
    yesterday = timezone.now().date() - timedelta(days=1)
    logger.info(f"Aggregating analytics for {yesterday}")
    
    # Optimize query - only fetch needed fields
    bots = Bot.objects.filter(status='active').only('id', 'name')
    
    for bot in bots:
        try:
            # Get events with optimized query
            events = MessageEvent.objects.filter(
                bot=bot,
                timestamp__date=yesterday
            ).select_related('telegram_user')
            
            # Get unique users who messaged yesterday
            unique_user_ids = events.filter(
                event_type='received'
            ).values_list('telegram_user_id', flat=True).distinct()
            
            unique_users_count = len(set(filter(None, unique_user_ids)))
            
            # Count new users (first message yesterday)
            new_users = TelegramUser.objects.filter(
                bot=bot,
                first_seen__date=yesterday
            ).count()
            
            # Count returning users
            returning_users = unique_users_count - new_users
            
            # Aggregate stats
            BotAnalytics.objects.update_or_create(
                bot=bot,
                date=yesterday,
                defaults={
                    'messages_received': events.filter(event_type='received').count(),
                    'messages_sent': events.filter(event_type='sent').count(),
                    'unique_users': unique_users_count,
                    'new_users': new_users,
                    'returning_users': max(0, returning_users),
                    'tokens_used': events.aggregate(Sum('tokens_used'))['tokens_used__sum'] or 0,
                    'avg_response_time_ms': int(events.aggregate(Avg('response_time_ms'))['response_time_ms__avg'] or 0),
                    'rag_queries': events.filter(used_rag=True).count(),
                }
            )
            
            logger.info(f"Aggregated analytics for bot {bot.name}: {unique_users_count} users, {events.count()} events")
            
        except Exception as e:
            logger.error(f"Error aggregating analytics for bot {bot.name}: {str(e)}", exc_info=True)


@shared_task
def calculate_retention():
    """
    Calculate retention rates for cohorts.
    Runs daily at 01:00 via Celery Beat.
    """
    today = timezone.now().date()
    logger.info(f"Calculating retention for {today}")
    
    for bot in Bot.objects.filter(status='active'):
        try:
            # Calculate for cohorts: 1 day ago, 7 days ago, 30 days ago
            for days_ago in [1, 7, 30]:
                cohort_date = today - timedelta(days=days_ago)
                
                # Get users from this cohort (first message on cohort_date)
                cohort_users = TelegramUser.objects.filter(
                    bot=bot,
                    first_seen__date=cohort_date
                )
                
                total_users = cohort_users.count()
                if total_users == 0:
                    continue
                
                # Count retained users (messaged after cohort_date)
                retained_user_ids = MessageEvent.objects.filter(
                    bot=bot,
                    telegram_user__in=cohort_users,
                    timestamp__date__gt=cohort_date
                ).select_related('telegram_user').values_list('telegram_user_id', flat=True).distinct()
                
                retained_count = len(set(retained_user_ids))
                
                # Update retention record
                retention, created = UserRetention.objects.get_or_create(
                    bot=bot,
                    cohort_date=cohort_date,
                    defaults={'total_users_in_cohort': total_users}
                )
                
                # Update appropriate day_X_retained field
                if days_ago == 1:
                    retention.day_1_retained = retained_count
                elif days_ago == 7:
                    retention.day_7_retained = retained_count
                elif days_ago == 30:
                    retention.day_30_retained = retained_count
                
                retention.save()
                
                logger.info(f"Retention for bot {bot.name}, cohort {cohort_date}, day {days_ago}: {retained_count}/{total_users}")
                
        except Exception as e:
            logger.error(f"Error calculating retention for bot {bot.name}: {str(e)}", exc_info=True)


@shared_task
def track_message_event(bot_id, event_type, **kwargs):
    """
    Track a message event for analytics.
    
    Args:
        bot_id: Bot UUID
        event_type: 'received', 'sent', or 'error'
        **kwargs: Additional event data
    """
    try:
        MessageEvent.objects.create(
            bot_id=bot_id,
            event_type=event_type,
            **kwargs
        )
    except Exception as e:
        logger.error(f"Error tracking message event: {str(e)}")

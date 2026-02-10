"""
Celery tasks for analytics.
"""
from celery import shared_task
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from datetime import timedelta
from apps.analytics.models import BotAnalytics, MessageEvent, UserRetention, TokenUsage
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


@shared_task
def aggregate_token_usage(bot_id: str, date: str, input_tokens: int = 0, output_tokens: int = 0, total_tokens: int = 0):
    """
    Aggregate token usage for a bot on a specific date.

    Args:
        bot_id: Bot UUID
        date: Date string (YYYY-MM-DD)
        input_tokens: Input tokens used (optional, if total_tokens is provided)
        output_tokens: Output tokens used (optional, if total_tokens is provided)
        total_tokens: Total tokens used (optional, takes precedence if input/output not provided)
    """
    try:
        from datetime import datetime

        bot = Bot.objects.get(id=bot_id)
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()

        # If total_tokens is provided but not input/output, split it 50/50 (rough estimate)
        if total_tokens > 0 and input_tokens == 0 and output_tokens == 0:
            input_tokens = total_tokens // 2
            output_tokens = total_tokens - input_tokens

        token_usage, created = TokenUsage.objects.get_or_create(
            bot=bot,
            date=date_obj,
            defaults={
                'input_tokens': input_tokens,
                'output_tokens': output_tokens
            }
        )

        if not created:
            # Update existing record
            token_usage.input_tokens += input_tokens
            token_usage.output_tokens += output_tokens
            token_usage.save()

        logger.info(f"Aggregated token usage for bot {bot.name} on {date}: {token_usage.total_tokens} tokens")

    except Exception as e:
        logger.error(f"Error aggregating token usage: {str(e)}")


@shared_task
def aggregate_webhook_metrics():
    """
    Aggregate webhook metrics for the previous hour.
    Runs every hour via Celery Beat.
    """
    from apps.analytics.models import WebhookEvent, WebhookMetrics
    from datetime import datetime, timedelta
    from django.db.models import Avg, Count, Q
    import statistics

    now = timezone.now()
    # Aggregate for the previous hour
    hour_start = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
    hour_end = hour_start + timedelta(hours=1)

    logger.info(f"Aggregating webhook metrics for {hour_start} - {hour_end}")

    # Get all webhook-mode bots
    webhook_bots = Bot.objects.filter(delivery_mode='webhook', status='active')

    for bot in webhook_bots:
        try:
            # Get events for this hour
            events = WebhookEvent.objects.filter(
                bot=bot,
                timestamp__gte=hour_start,
                timestamp__lt=hour_end
            )

            total_events = events.count()
            if total_events == 0:
                continue

            # Calculate metrics
            successful = events.filter(status='success').count()
            failed = events.filter(status='failed').count()

            processing_times = list(events.filter(
                processing_time_ms__isnull=False
            ).values_list('processing_time_ms', flat=True))

            avg_processing = int(sum(processing_times) / len(processing_times)) if processing_times else 0

            # Calculate percentiles
            p95_processing = int(statistics.quantiles(processing_times, n=20)[18]) if len(processing_times) >= 20 else avg_processing
            p99_processing = int(statistics.quantiles(processing_times, n=100)[98]) if len(processing_times) >= 100 else avg_processing

            # Response metrics
            responses = events.filter(response_sent=True)
            response_times = list(responses.filter(
                response_time_ms__isnull=False
            ).values_list('response_time_ms', flat=True))
            avg_response = int(sum(response_times) / len(response_times)) if response_times else 0

            # Error breakdown
            signature_failures = events.filter(
                error_type='InvalidSignature'
            ).count()
            processing_errors = events.filter(
                error_type__in=['ProcessingError', 'TelegramBadRequest']
            ).count()
            timeout_errors = events.filter(
                error_type='Timeout'
            ).count()

            # Update or create metrics record
            WebhookMetrics.objects.update_or_create(
                bot=bot,
                date=hour_start.date(),
                hour=hour_start.hour,
                defaults={
                    'requests_received': total_events,
                    'requests_processed': successful,
                    'requests_failed': failed,
                    'avg_processing_time_ms': avg_processing,
                    'p95_processing_time_ms': p95_processing,
                    'p99_processing_time_ms': p99_processing,
                    'responses_sent': responses.count(),
                    'avg_response_time_ms': avg_response,
                    'signature_validation_failures': signature_failures,
                    'processing_errors': processing_errors,
                    'timeout_errors': timeout_errors,
                }
            )

            logger.info(
                f"Webhook metrics for {bot.name}: "
                f"{successful}/{total_events} successful, "
                f"avg {avg_processing}ms processing time"
            )

        except Exception as e:
            logger.error(f"Error aggregating webhook metrics for bot {bot.name}: {str(e)}", exc_info=True)


@shared_task
def check_webhook_health_alerts():
    """
    Check webhook health and send alerts if issues detected.
    Runs every 5 minutes via Celery Beat.
    """
    from apps.analytics.models import WebhookMetrics, WebhookEvent
    from datetime import timedelta
    from django.core.cache import cache
    from django.conf import settings
    from django.core.mail import send_mail

    now = timezone.now()
    check_window = now - timedelta(minutes=15)  # Check last 15 minutes

    logger.info("Checking webhook health alerts")

    for bot in Bot.objects.filter(delivery_mode='webhook', status='active'):
        try:
            # Get recent events
            recent_events = WebhookEvent.objects.filter(
                bot=bot,
                timestamp__gte=check_window
            )

            total = recent_events.count()
            failed = recent_events.filter(status='failed').count()

            if total == 0:
                # Check if this is unusual (bot should be receiving traffic)
                cache_key = f"webhook_no_traffic_{bot.id}"
                if not cache.get(cache_key):
                    cache.set(cache_key, True, timeout=3600)  # Alert once per hour
                    logger.warning(f"Bot {bot.name} - No webhook traffic in last 15 minutes")

            # Check error rate threshold (default: 10%)
            error_rate_threshold = getattr(settings, 'WEBHOOK_ERROR_RATE_THRESHOLD', 0.1)

            if total > 10:  # Only check if we have enough samples
                error_rate = failed / total
                if error_rate > error_rate_threshold:
                    cache_key = f"webhook_high_error_{bot.id}"
                    if not cache.get(cache_key):
                        cache.set(cache_key, True, timeout=1800)  # Alert once per 30 minutes

                        # Send alert email
                        send_mail(
                            f'⚠️ High Webhook Error Rate: {bot.name}',
                            f'Bot "{bot.name}" has {error_rate:.1%} error rate ({failed}/{total} failed) in the last 15 minutes.\n\n'
                            f'Bot ID: {bot.id}\n'
                            f'Time: {now}',
                            settings.DEFAULT_FROM_EMAIL,
                            [settings.ADMIN_EMAIL],
                            fail_silently=True
                        )
                        logger.warning(
                            f"Alert sent for bot {bot.name}: "
                            f"{error_rate:.1%} error rate ({failed}/{total})"
                        )

            # Check for specific error patterns
            signature_failures = recent_events.filter(
                error_type='InvalidSignature'
            ).count()
            if signature_failures > 5:
                cache_key = f"webhook_signature_fail_{bot.id}"
                if not cache.get(cache_key):
                    cache.set(cache_key, True, timeout=1800)
                    logger.error(
                        f"Security alert for bot {bot.name}: "
                        f"{signature_failures} signature validation failures in last 15 minutes"
                    )

        except Exception as e:
            logger.error(f"Error checking webhook health for bot {bot.name}: {str(e)}", exc_info=True)


@shared_task
def cleanup_old_webhook_events(days_to_keep=7):
    """
    Clean up old webhook events to prevent database bloat.
    Runs daily via Celery Beat.

    Args:
        days_to_keep: Number of days of events to keep (default: 7)
    """
    from apps.analytics.models import WebhookEvent
    from datetime import timedelta

    cutoff_date = timezone.now() - timedelta(days=days_to_keep)

    try:
        deleted_count = WebhookEvent.objects.filter(timestamp__lt=cutoff_date).delete()[0]
        logger.info(f"Cleaned up {deleted_count} old webhook events (older than {days_to_keep} days)")
    except Exception as e:
        logger.error(f"Error cleaning up old webhook events: {str(e)}", exc_info=True)

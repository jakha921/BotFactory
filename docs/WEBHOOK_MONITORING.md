# Webhook Monitoring Documentation

## Overview

Webhook monitoring provides real-time visibility into webhook delivery status, error rates, and performance metrics for all webhook-mode bots.

## Components

### 1. WebhookEvent Model

Logs individual webhook events for detailed tracking:

**Fields:**
- `bot` - Related Bot
- `event_type` - Event type (received, processed, error, response_sent, retry)
- `status` - Status (success, failed, pending)
- `update_id` - Telegram update_id
- `processing_time_ms` - Processing time in milliseconds
- `response_time_ms` - Response time in milliseconds
- `error_type` - Error type (InvalidSignature, ProcessingError, etc.)
- `error_message` - Error message
- `ip_address` - Client IP address
- `telegram_signature_valid` - Whether Telegram signature was valid

### 2. WebhookMetrics Model

Aggregated hourly metrics for webhook performance:

**Fields:**
- `bot` - Related Bot
- `date` - Date
- `hour` - Hour (0-23)
- `requests_received` - Total webhook requests
- `requests_processed` - Successfully processed
- `requests_failed` - Failed requests
- `avg_processing_time_ms` - Average processing time
- `p95_processing_time_ms` - 95th percentile
- `p99_processing_time_ms` - 99th percentile
- `responses_sent` - Responses sent
- `signature_validation_failures` - Signature failures
- `processing_errors` - Processing errors

### 3. Health Check Endpoints

**Overall Webhook Health:**
```
GET /api/health/webhook/
```

Returns:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-10T20:00:00Z",
  "summary": {
    "webhook_bots_count": 5,
    "total_events_last_15min": 150,
    "total_errors_last_15min": 2,
    "overall_error_rate": "1.3%"
  },
  "bots": [...]
}
```

**Individual Bot Health:**
```
GET /api/health/webhook/<bot_id>/
```

Returns bot-specific metrics for current hour and last 15 minutes.

### 4. Celery Tasks

**Aggregate Webhook Metrics** (Hourly):
```python
aggregate_webhook_metrics.delay()
```
Aggregates metrics for the previous hour.

**Check Webhook Health Alerts** (Every 5 minutes):
```python
check_webhook_health_alerts.delay()
```
Sends email alerts if:
- Error rate exceeds `WEBHOOK_ERROR_RATE_THRESHOLD` (default: 10%)
- No traffic in 15 minutes
- Signature validation failures (>5 in 15 minutes)

**Cleanup Old Events** (Daily):
```python
cleanup_old_webhook_events(days_to_keep=7)
```
Deletes events older than retention period.

## Configuration

### Environment Variables

```bash
# Webhook Monitoring Settings
WEBHOOK_ERROR_RATE_THRESHOLD=0.1  # 10% error rate triggers alert
ADMIN_EMAIL=admin@example.com
DEFAULT_FROM_EMAIL=noreply@botfactory.com
WEBHOOK_ALERTS_ENABLED=True
WEBHOOK_EVENT_RETENTION_DAYS=7
WEBHOOK_PROCESSING_TIMEOUT=30
```

### Celery Beat Schedule

Add to your Celery Beat configuration:

```python
CELERY_BEAT_SCHEDULE = {
    'aggregate-webhook-metrics': {
        'task': 'apps.analytics.tasks.aggregate_webhook_metrics',
        'schedule': crontab(minute=5),  # Every hour at :05
    },
    'check-webhook-health': {
        'task': 'apps.analytics.tasks.check_webhook_health_alerts',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'cleanup-webhook-events': {
        'task': 'apps.analytics.tasks.cleanup_old_webhook_events',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}
```

## Admin Interface

View webhook events and metrics in Django Admin:
- `/admin/analytics/webevent/` - Individual webhook events
- `/admin/analytics/webhookmetrics/` - Aggregated metrics

## Monitoring Dashboard

For a comprehensive monitoring dashboard, integrate with:
- Grafana + Prometheus
- Datadog
- Sentry for error tracking

## Alert Examples

### High Error Rate Alert
```
Subject: ⚠️ High Webhook Error Rate: MyBot

Bot "MyBot" has 15.0% error rate (15/100 failed) in the last 15 minutes.

Bot ID: 123e4567-e89b-12d3-a456-426614174000
Time: 2026-02-10 20:00:00
```

### Security Alert
```
Security alert for bot MyBot: 7 signature validation failures in last 15 minutes
```

## Troubleshooting

### No Traffic Alert
If you receive "no traffic" alerts:
1. Check if bot is actually receiving messages
2. Verify webhook is registered with Telegram
3. Check webhook URL accessibility

### High Error Rate
If error rate is high:
1. Check admin panel for WebhookEvent details
2. Look for specific error types
3. Verify webhook_secret matches Telegram configuration
4. Check bot service logs

### Slow Processing
If processing times are high:
1. Check Celery worker capacity
2. Monitor AI provider response times
3. Check database query performance

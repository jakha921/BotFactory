# Webhook Gateway Setup Guide

## Overview

The Django backend now serves as a unified Webhook Gateway for multiple Telegram bots. All bots receive updates through a single endpoint: `POST /webhook/<token>/`

## Architecture

### Components

1. **Global Dispatcher** (`backend/services/bot_engine.py`)
   - Singleton Dispatcher with all routers from `bot/handlers`
   - Uses Redis for FSM storage (supports multiple bots)
   - Shared across all webhook requests

2. **Webhook View** (`backend/apps/telegram/views.py`)
   - Async Django view: `telegram_webhook(request, token)`
   - Validates token against `Bot` model
   - Creates lightweight Bot instance per request
   - Feeds update to shared Dispatcher

3. **URL Routing** (`backend/bot_factory/urls.py`)
   - Route: `POST /webhook/<str:token>/`

## Setup Instructions

### 1. Install Redis

```bash
# macOS (Homebrew)
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Docker
docker run -d -p 6379:6379 redis:7-alpine
```

### 2. Configure Redis URL

Add to `.env` file in `backend/`:

```env
REDIS_URL=redis://localhost:6379/0
# Or with password:
# REDIS_URL=redis://:password@localhost:6379/0
```

Default: `redis://localhost:6379/0` (if not set)

### 3. Install Dependencies

```bash
cd backend
uv pip install -r requirements/base.txt
```

This will install:
- `redis>=5.0.0` - Redis client
- `aiogram` with Redis support

### 4. Set Up Webhook for Telegram Bots

For each bot, you need to set the webhook URL:

```python
import requests

BOT_TOKEN = "your_bot_token"
WEBHOOK_URL = "https://your-domain.com/webhook/{}/".format(BOT_TOKEN)

response = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
    json={"url": WEBHOOK_URL}
)
print(response.json())
```

Or via Django management command (create if needed):

```bash
python manage.py set_webhook <bot_id>
```

## How It Works

1. **Telegram sends update** → `POST /webhook/<token>/`
2. **Backend validates token** → Checks `Bot` model in database
3. **Creates Bot instance** → Lightweight Aiogram Bot for this request
4. **Reconstructs Update** → From JSON payload
5. **Feeds to Dispatcher** → Shared Dispatcher processes update
6. **Returns 200 OK** → Telegram doesn't retry

## Testing

### Test Webhook Locally (using ngrok or similar)

```bash
# Install ngrok
brew install ngrok  # macOS
# or download from https://ngrok.com

# Start Django server
cd backend
python manage.py runserver 0.0.0.0:8000

# In another terminal, expose local server
ngrok http 8000

# Set webhook using ngrok URL
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-ngrok-url.ngrok.io/webhook/<TOKEN>/"}'
```

### Test with curl

```bash
# Simulate Telegram webhook
curl -X POST http://localhost:8000/webhook/<TOKEN>/ \
  -H "Content-Type: application/json" \
  -d '{
    "update_id": 123456789,
    "message": {
      "message_id": 1,
      "from": {
        "id": 123456,
        "is_bot": false,
        "first_name": "Test"
      },
      "chat": {
        "id": 123456,
        "type": "private"
      },
      "date": 1609459200,
      "text": "/start"
    }
  }'
```

## Migration from Polling

If you're currently using polling (`bot/main.py`), you can:

1. **Keep polling** for development/testing
2. **Switch to webhooks** for production
3. **Run both** (not recommended - causes conflicts)

To disable polling, comment out or remove the polling code in `bot/main.py`.

## Troubleshooting

### Redis Connection Error

```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Solution:**
- Ensure Redis is running: `redis-cli ping` (should return `PONG`)
- Check `REDIS_URL` in `.env`
- Verify Redis is accessible from Django

### Token Not Found

```
HTTP 403: Invalid Token
```

**Solution:**
- Ensure bot exists in database with `status='active'`
- Token in URL must match `decrypted_telegram_token` in database
- Check token encryption/decryption

### Update Processing Errors

Check Django logs for detailed error messages. Common issues:
- Missing dependencies
- Django setup not initialized
- Handler errors (check bot/handlers)

## Production Considerations

1. **Use HTTPS** - Telegram requires HTTPS for webhooks
2. **Rate Limiting** - Consider adding rate limiting middleware
3. **Monitoring** - Monitor Redis and webhook endpoint
4. **Error Handling** - Always return 200 OK to prevent retries
5. **Scaling** - Redis allows horizontal scaling (multiple Django instances)

## API Reference

### Webhook Endpoint

**POST** `/webhook/<token>/`

**Headers:**
- `Content-Type: application/json`

**Body:**
Telegram Update JSON (as sent by Telegram)

**Responses:**
- `200 OK` - Update processed successfully
- `400 Bad Request` - Invalid JSON or Update format
- `403 Forbidden` - Invalid token


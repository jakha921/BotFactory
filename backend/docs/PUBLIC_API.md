# Bot Factory Public API

## Overview

The Public API allows external services to interact with bots without requiring user authentication. It uses API keys for authentication.

## Authentication

Use the `X-API-Key` header to authenticate:

```
X-API-Key: <your_api_key>
```

API keys are generated per bot and can be managed through the bot settings in the admin panel.

## Endpoints

### Generate Bot Response

Send a message to a bot and get an AI-generated response.

**Endpoint**: `POST /api/v1/public/chat/`

**Headers**:
```
X-API-Key: <bot_api_key>
Content-Type: application/json
```

**Request Body**:
```json
{
  "message": "Hello, how are you?",
  "session_id": "optional-session-id-for-context"
}
```

**Response**:
```json
{
  "text": "Hello! I'm doing well, thank you for asking. How can I help you today?",
  "session_id": "generated-session-id",
  "grounding_chunks": []
}
```

**Error Responses**:

- `401 Unauthorized`: Invalid or missing API key
- `400 Bad Request`: Invalid request body
- `404 Not Found`: Bot not found or inactive
- `429 Too Many Requests`: Rate limit exceeded

### Rate Limiting

Public API endpoints have rate limits:
- **Default**: 100 requests per minute per API key
- **Burst**: Up to 10 requests per second

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Getting an API Key

1. Log in to Bot Factory
2. Navigate to your bot settings
3. Go to the "Integrations" tab
4. Generate or view your API key
5. Copy the key and use it in the `X-API-Key` header

## Example Usage

### cURL

```bash
curl -X POST http://localhost:8000/api/v1/public/chat/ \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the weather today?",
    "session_id": "my-session-123"
  }'
```

### Python

```python
import requests

url = "http://localhost:8000/api/v1/public/chat/"
headers = {
    "X-API-Key": "your-api-key-here",
    "Content-Type": "application/json"
}
data = {
    "message": "What is the weather today?",
    "session_id": "my-session-123"
}

response = requests.post(url, json=data, headers=headers)
result = response.json()
print(result["text"])
```

### JavaScript/Node.js

```javascript
const fetch = require('node-fetch');

const url = 'http://localhost:8000/api/v1/public/chat/';
const headers = {
  'X-API-Key': 'your-api-key-here',
  'Content-Type': 'application/json'
};
const body = {
  message: 'What is the weather today?',
  session_id: 'my-session-123'
};

fetch(url, {
  method: 'POST',
  headers: headers,
  body: JSON.stringify(body)
})
  .then(res => res.json())
  .then(data => console.log(data.text));
```

## Session Management

Sessions allow maintaining conversation context across multiple requests. If you don't provide a `session_id`, a new session will be created automatically.

To continue a conversation:
1. Use the `session_id` from the first response
2. Include it in subsequent requests
3. The bot will use the conversation history for context

## Best Practices

1. **Store API keys securely** - Never commit API keys to version control
2. **Use environment variables** - Store keys in environment variables or secure vaults
3. **Handle rate limits** - Implement exponential backoff when rate limited
4. **Use sessions** - Maintain session context for better conversation quality
5. **Error handling** - Always check response status codes and handle errors gracefully


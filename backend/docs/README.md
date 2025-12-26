# Bot Factory API Documentation

## Overview

Bot Factory provides a comprehensive REST API for creating and managing AI bots with Telegram integration and Google Gemini AI.

## API Documentation

### Interactive Documentation

Once the server is running, you can access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema (JSON)**: http://localhost:8000/api/schema/

### Authentication

The API uses JWT (JSON Web Tokens) for authentication.

1. **Register** a new user:
   ```
   POST /api/v1/auth/register/
   Body: { "email": "user@example.com", "password": "password123", "name": "User Name" }
   ```

2. **Login** to get access and refresh tokens:
   ```
   POST /api/v1/auth/login/
   Body: { "email": "user@example.com", "password": "password123" }
   Response: { "user": {...}, "tokens": { "access": "...", "refresh": "..." } }
   ```

3. **Use the access token** in subsequent requests:
   ```
   Authorization: Bearer <access_token>
   ```

4. **Refresh the access token** when it expires:
   ```
   POST /api/v1/auth/refresh/
   Body: { "refresh": "<refresh_token>" }
   ```

### Rate Limiting

- **Login**: 5 attempts per minute per IP
- **Register**: 3 registrations per hour per IP
- **API endpoints**: 100 requests per minute per user

### Main Endpoints

#### Bots
- `GET /api/v1/bots/` - List all bots for current user
- `POST /api/v1/bots/` - Create a new bot
- `GET /api/v1/bots/{id}/` - Get bot details
- `PATCH /api/v1/bots/{id}/` - Update bot
- `DELETE /api/v1/bots/{id}/` - Delete bot
- `GET /api/v1/bots/{id}/test-telegram-connection/` - Test Telegram token
- `GET /api/v1/bots/{id}/bot-status/` - Get bot running status
- `POST /api/v1/bots/{id}/restart-bot/` - Restart bot

#### Knowledge Base
- `GET /api/v1/bots/{bot_id}/documents/` - List documents
- `POST /api/v1/bots/{bot_id}/documents/` - Upload document
- `DELETE /api/v1/documents/{id}/` - Delete document
- `GET /api/v1/snippets/?bot_id={bot_id}` - List text snippets
- `POST /api/v1/snippets/` - Create snippet
- `PATCH /api/v1/snippets/{id}/` - Update snippet
- `DELETE /api/v1/snippets/{id}/` - Delete snippet

#### Chat
- `GET /api/v1/bots/{bot_id}/sessions/` - List chat sessions
- `GET /api/v1/sessions/{session_id}/messages/` - Get messages
- `POST /api/v1/chat/generate/` - Generate bot response
- `POST /api/v1/chat/transcribe/` - Transcribe audio
- `POST /api/v1/chat/process-file/` - Process file

#### Analytics
- `GET /api/v1/stats/?period={period}` - Get dashboard stats
- `GET /api/v1/stats/chart/?period={period}` - Get chart data
- `GET /api/v1/stats/activity/` - Get recent activity

### Public API (for external services)

See [Public API Documentation](./PUBLIC_API.md) for details on using the public API with API keys.

### Error Responses

All errors follow this format:

```json
{
  "error": {
    "message": "Error description",
    "code": "ERROR_CODE",
    "status": 400
  }
}
```

Common error codes:
- `validation_error` - Validation failed
- `authentication_failed` - Invalid credentials
- `permission_denied` - Insufficient permissions
- `not_found` - Resource not found
- `rate_limit_exceeded` - Too many requests

### Examples

See the interactive Swagger UI at `/api/docs/` for detailed request/response examples and to test the API directly.


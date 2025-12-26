# Bot Factory - AI Agent Documentation

> **Purpose**: This document helps AI assistants (Gemini, Claude, etc.) understand the Bot Factory SaaS platform architecture and provide effective assistance.

## 🏗️ Project Architecture

```
bot-factory/
├── backend/          # Django REST Framework API (Python 3.11+)
├── bot/              # Telegram Bot Service (aiogram 3.x)
├── frontend/         # Admin Panel (React + TypeScript + Vite)
└── docker-compose.yml  # PostgreSQL + Redis for production
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Backend | Django 5.0 + DRF | REST API, Admin Panel, Data Models |
| Bot | aiogram 3.x | Multi-bot Telegram polling service |
| Frontend | React 19 + TypeScript | Admin dashboard for bot management |
| Database | PostgreSQL 15 (pgvector) or SQLite | Data storage, vector embeddings |
| AI | Google Gemini API | Response generation |
| Cache | Redis | Rate limiting, session storage |

---

## 📊 Data Models

### Core Models

```
User (apps/accounts)
├── id: UUID (PK)
├── email: EmailField (unique)
├── name: CharField
├── plan: Free/Pro/Enterprise
├── telegram_id: BigIntegerField (for admin access to bots)
├── is_staff, is_superuser: BooleanField
└── created_at, updated_at

Bot (apps/bots)
├── id: UUID (PK)
├── owner: FK(User)
├── name: CharField
├── status: draft/active/paused/error
├── model: varchar (gemini-2.0-flash, gpt-4, etc.)
├── provider: gemini/openai/anthropic
├── temperature: FloatField (0-2)
├── system_instruction: TextField
├── telegram_token: CharField (ENCRYPTED with Fernet)
├── ui_config: JSONField (keyboards, forms)
├── welcome_message, help_message: TextField
└── created_at, updated_at

TelegramUser (apps/telegram)
├── id: UUID (PK)
├── telegram_id: BigIntegerField
├── bot: FK(Bot)
├── username, first_name, last_name
├── status: active/blocked
├── message_count: IntegerField
└── first_seen, last_active

ChatSession (apps/chat)
├── id: UUID (PK)
├── bot: FK(Bot)
├── user: FK(TelegramUser)
├── sentiment: positive/neutral/negative
├── is_flagged: BooleanField
└── created_at, updated_at

ChatMessage (apps/chat)
├── id: UUID (PK)
├── session: FK(ChatSession)
├── role: user/model
├── content: TextField
├── is_thinking: BooleanField
├── attachments: JSONField
└── timestamp

Document (apps/knowledge)
├── id: UUID (PK)
├── bot: FK(Bot)
├── file: FileField
└── uploaded_at

TextSnippet (apps/knowledge)
├── id: UUID (PK)
├── bot: FK(Bot)
├── title: CharField
├── content: TextField
├── tags: JSONField
├── embedding: VectorField(768) - for RAG
└── created_at, updated_at
```

---

## 🔄 Message Flow

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   Telegram App   │────▶│   aiogram Bot    │────▶│  Django Backend  │
│   (User sends    │     │   (Polling)      │     │  (ORM + Gemini)  │
│    message)      │◀────│                  │◀────│                  │
└──────────────────┘     └──────────────────┘     └──────────────────┘

1. User sends message to Telegram bot
2. aiogram polling receives update
3. chat_router.handle_message() processes it
4. get_bot_by_token() finds bot config (decrypts tokens to match)
5. get_or_create_telegram_user() creates/updates user
6. process_message() extracts text (supports text/audio/files)
7. generate_bot_response() calls GeminiService with:
   - Bot's system_instruction
   - Knowledge base (snippets + documents)
   - Chat history (last 10 messages)
8. Response saved to ChatMessage
9. Response sent to user via Telegram
```

---

## 🔑 Key Files

### Backend (Django)

| File | Purpose |
|------|---------|
| `backend/bot_factory/settings/` | Django settings (base, development, production) |
| `backend/apps/bots/models.py` | Bot model with encrypted tokens |
| `backend/apps/accounts/models.py` | User model with telegram_id |
| `backend/services/gemini.py` | Google Gemini API integration |
| `backend/core/utils.py` | Token encryption/decryption utilities |

### Bot (aiogram)

| File | Purpose |
|------|---------|
| `bot/main.py` | Entry point, starts all active bots |
| `bot/dispatcher.py` | Creates dispatcher with all routers |
| `bot/services/bot_manager.py` | Manages bot lifecycle (start/stop) |
| `bot/services/bot_monitor.py` | Watches DB for config changes (30s) |
| `bot/handlers/chat.py` | Main message handler |
| `bot/services/gemini_client.py` | Generates AI responses |
| `bot/integrations/django_orm.py` | Async wrappers for Django ORM |

### Frontend (React)

| File | Purpose |
|------|---------|
| `frontend/App.tsx` | Main app with custom routing |
| `frontend/store/` | Zustand stores for state management |
| `frontend/services/api.ts` | API client with mock/real toggle |

---

## ⚙️ Configuration

### Environment Variables

**Backend** (`backend/.env`):
```bash
SECRET_KEY=your-secret-key
DEBUG=True
DB_NAME=db.sqlite3  # or PostgreSQL config
GEMINI_API_KEY=your-gemini-key
ALLOWED_HOSTS=localhost,127.0.0.1
```

**Bot** (`bot/.env`):
```bash
DJANGO_API_BASE_URL=http://localhost:8000/api/v1
DJANGO_SETTINGS_MODULE=bot_factory.settings.development
LOG_LEVEL=INFO
```

---

## 🚀 Running the Project

### Start Backend
```bash
cd backend
source .venv/bin/activate
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### Start Bot Service
```bash
cd bot-factory  # from project root
export PYTHONPATH="$(pwd):$PYTHONPATH"
cd bot
source .venv/bin/activate
python main.py
```

### Start Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 👤 Admin User Identification

Admins are identified by matching their Telegram ID with `User.telegram_id`:

1. User creates account in admin panel
2. User adds their Telegram ID to profile (`User.telegram_id`)
3. When bot starts, `get_admin_telegram_ids()` fetches all admin IDs
4. Admin IDs stored in `settings.ADMIN_IDS` for bot runtime

Query logic:
```python
User.objects.filter(
    is_active=True,
    telegram_id__isnull=False
).filter(
    Q(is_staff=True) | Q(is_superuser=True)
)
```

---

## 🔐 Token Security

Telegram bot tokens are encrypted before storage:

1. **Encryption**: `core.utils.encrypt_token()` uses Fernet (AES)
2. **Storage**: Encrypted token stored in `Bot.telegram_token`
3. **Detection**: Encrypted tokens start with `gAAAAAB`
4. **Decryption**: `Bot.decrypted_telegram_token` property decrypts on-demand
5. **Key**: Uses `settings.SECRET_KEY` to derive encryption key

---

## 🧠 AI Response Generation

The bot uses Google Gemini for responses:

1. **Service**: `backend/services/gemini.py` → `GeminiService`
2. **Client**: `bot/services/gemini_client.py` → `generate_bot_response()`
3. **Features**:
   - System instruction from bot configuration
   - Knowledge base context (snippets + documents)
   - Chat history (last 10 messages)
   - Configurable temperature and thinking budget

---

## 📁 Creating a Working Bot

1. **Create Bot in Django Admin** (`http://localhost:8000/admin/`)
   - Go to Bots → Add Bot
   - Set Name, Status=Active, Model, Provider=Gemini
   - Add Telegram Token from @BotFather

2. **Add Admin Telegram ID**
   - Go to Users → Select your user
   - Add your Telegram ID to `telegram_id` field
   - Set `is_staff=True` or `is_superuser=True`

3. **Configure Bot Settings**
   - Set `system_instruction` for bot personality
   - Add `welcome_message` for /start
   - Add `help_message` for /help

4. **Start Bot Service**
   - Run `python main.py` in bot directory
   - BotMonitor will automatically detect and start the bot

5. **Test in Telegram**
   - Find your bot by username
   - Send `/start` to see welcome message
   - Send any message to get AI response

---

## ❓ Troubleshooting

| Issue | Solution |
|-------|----------|
| "No active bots found" | Ensure bot has `status='active'` and `telegram_token` is set |
| "Bot not found for token" | Token encryption/decryption issue - check SECRET_KEY |
| "TelegramConflictError" | Another bot instance is running - stop all processes |
| "ModuleNotFoundError: bot" | Set PYTHONPATH to project root before running |
| Vector embeddings fail | Switch from SQLite to PostgreSQL with pgvector |

---

## 📚 API Endpoints

### Authentication
- `POST /api/v1/auth/register/` - User registration
- `POST /api/v1/auth/login/` - JWT login
- `POST /api/v1/auth/refresh/` - Refresh JWT token
- `GET /api/v1/auth/profile/` - Current user profile

### Bots
- `GET/POST /api/v1/bots/` - List/Create bots
- `GET/PUT/DELETE /api/v1/bots/{id}/` - Bot CRUD
- `POST /api/v1/bots/{id}/test-telegram-connection/` - Test token
- `GET /api/v1/bots/{id}/bot-status/` - Bot running status

### Knowledge Base
- `GET/POST /api/v1/bots/{id}/documents/` - Documents
- `GET/POST /api/v1/bots/{id}/snippets/` - Text snippets

### Chat
- `GET /api/v1/bots/{id}/sessions/` - Chat sessions
- `GET /api/v1/sessions/{id}/messages/` - Session messages

---

*This documentation is designed for AI assistants to quickly understand and work with the Bot Factory codebase.*

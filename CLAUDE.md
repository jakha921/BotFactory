# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bot Factory is a SaaS platform for creating and managing AI-powered Telegram bots. The project is a monorepo with three main components:

- **backend/** - Django REST Framework API server (Python 3.11+)
- **bot/** - Telegram bot service using aiogram 3.x for multi-bot polling
- **frontend/** - React admin panel (React 19, TypeScript, Vite)

### Key Architecture Pattern: Multi-Bot System
- All active bots (`status='active'`) are loaded at startup from the database
- BotMonitor checks the database every 30 seconds for configuration changes
- Each bot runs in an isolated asyncio.Task - crashes don't affect other bots
- BotManager in [bot/services/bot_manager.py](bot/services/bot_manager.py) handles lifecycle
- Admin access determined by `User.telegram_id` matching staff/superuser users

## Common Development Commands

### Starting All Services
```bash
# Master script to start all services (backend, frontend, bot, docker services)
./start_all.sh

# Stop all services
./stop_all.sh
```

### Backend (Django)
```bash
cd backend

# Install dependencies (using uv)
make install
# or: uv venv && source .venv/bin/activate && uv pip install -r requirements/base.txt

# Run development server
make runserver
# or: ./runserver.sh

# Run Django management commands
./run.sh <command>  # e.g., ./run.sh migrate, ./run.sh createsuperuser

# Create superuser
make superuser

# Run tests
make test

# Clean Python cache
make clean
```

### Bot Service
```bash
# IMPORTANT: Must be run from project root with PYTHONPATH set
cd /path/to/bot-factory
export PYTHONPATH="$(pwd):$PYTHONPATH"
cd bot
./run_uv.sh  # or python main.py
```

### Frontend
```bash
cd frontend

# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build

# Run tests
npm run test
npm run test:ui
npm run test:coverage

# Linting
npm run lint
npm run lint:fix

# Format code
npm run format
```

### Docker Services (PostgreSQL, Redis)
```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d
```

## Architecture Highlights

### Multi-Bot System
The bot service ([bot/main.py](bot/main.py)) implements a dynamic multi-bot system:
- All active bots (`status='active'`) are loaded at startup
- BotMonitor checks the database every 30 seconds for configuration changes
- Each bot runs in an isolated asyncio.Task
- Bot crashes don't affect other bots
- Uses `BotManager` in [bot/services/bot_manager.py](bot/services/bot_manager.py) for lifecycle management

### Backend Django Apps
Located in [backend/apps/](backend/apps/):
- **accounts/** - Custom User model with JWT auth, API keys, subscription plans
- **bots/** - Bot configuration, AI model settings, encrypted Telegram tokens
- **chat/** - Chat sessions, messages, sentiment analysis
- **telegram/** - Telegram users, statistics, status tracking
- **knowledge/** - Documents and text snippets with vector embeddings (RAG)
- **analytics/** - Usage statistics, bot performance metrics
- **ai_settings/** - AI provider configurations, usage limits

### Token Encryption
Telegram bot tokens are encrypted using Fernet (AES):
- Encryption key derived from `settings.SECRET_KEY`
- Encrypted tokens start with `gAAAAAB`
- Access via `Bot.decrypted_telegram_token` property in [backend/apps/bots/models.py](backend/apps/bots/models.py)

### AI Integration
Multiple AI providers supported (Gemini, OpenAI, Anthropic):
- Configuration per bot (model, temperature, system instruction)
- Thinking budget support for Gemini 2.5/3.0 models
- RAG (Retrieval-Augmented Generation) with pgvector for knowledge base
- Grounding with Google Search integration

### Frontend State Management
Uses Zustand with persist middleware ([frontend/store/](frontend/store/)):
- `useAuthStore` - Authentication state (JWT tokens)
- `useAppStore` - Bots, selected bot ID
- `useChatStore` - Chat messages and sessions
- `useThemeStore` - Theme (dark/light), sidebar state

### API Response Format
The frontend uses a custom routing system (no React Router):
```tsx
type View = 'login' | 'dashboard' | 'bots' | 'bot-chat' | 'settings' | 'knowledge' | 'monitoring' | 'users' | 'subscription';
```

Bot context system: `selectedBotId` filters data across pages. Reset it when navigating to non-bot-specific pages.

## Environment Configuration

### Root .env
Required for start_all.sh:
```bash
# Database
DB_NAME=bot_factory_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost

# Admin
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=admin123

# API Keys
GEMINI_API_KEY=your-gemini-key
```

### Backend .env
See [backend/.env.example](backend/.env.example)

### Frontend .env
```bash
VITE_API_URL=http://localhost:8000/api
```

## Code Style Conventions

### Backend (Python/Django)
- Line length: 100 characters
- Format with: `black`
- Lint with: `ruff` (or `flake8`)
- Type check with: `mypy`
- Follow PEP 8
- Use async views for external API calls (Gemini, Telegram)
- Implement rate limiting using Django cache (login: 5/min, register: 3/hour)
- Business logic goes in services/, not views

### Frontend (TypeScript/React)
- Strict TypeScript mode enabled
- Use named exports for components
- Use `cn()` utility for conditional classes
- Avoid `any` type - use `unknown` if needed
- Functional components only (no class components)
- Glassmorphism design pattern (Apple HIG inspired)
- Implement error boundaries and offline detection for robust UX
- Use retry logic for API calls with exponential backoff

## Testing

### Backend
```bash
cd backend
make test  # Run pytest-django tests
```

### Frontend
```bash
cd frontend
npm run test              # Run Vitest
npm run test:ui           # Run Vitest UI
npm run test:coverage     # Coverage report
```

### Running Single Test
```bash
# Backend - specific app
cd backend
python manage.py test apps.bots

# Frontend - specific file
cd frontend
npm run test -- BotSelector.test.tsx
```

## Important Files

- [start_all.sh](start_all.sh) - Master startup script
- [PROJECT.md](PROJECT.md) - Comprehensive project documentation (Russian)
- [backend/.cursorrules](backend/.cursorrules) - Backend coding conventions
- [frontend/.cursorrules](frontend/.cursorrules) - Frontend coding conventions
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guide

## Troubleshooting

### Bot service "No module named 'bot'" error
```bash
# Must run from project root with PYTHONPATH set
export PYTHONPATH="$(pwd):$PYTHONPATH"
cd bot
python main.py
```

### TelegramConflictError
Another bot instance is running. Stop with:
```bash
./stop_all.sh
```

### Frontend - "Cannot read property of undefined"
Use optional chaining and null checks:
```tsx
const bot = bots.find(b => b.id === selectedBotId);
if (!bot) return <EmptyState />;
console.log(bot.name);  // Safe now
```

### Frontend - Dark mode not working
Ensure:
1. `initializeTheme()` is called in Layout
2. HTML element has `class="dark"`
3. Tailwind config has `darkMode: 'class'`

### Rate Limiting
Backend implements rate limiting for sensitive endpoints:
- Login: 5 attempts/minute per IP
- Register: 3 attempts/hour per IP
- Password reset: 3 attempts/hour per IP
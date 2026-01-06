# 🤖 BotFactory SaaS — Архитектура платформы

## 📋 Обзор проекта

**BotFactory** — SaaS платформа для создания AI-ботов в мессенджерах. Пользователи подключают токен бота, настраивают AI-инструкции, команды и формы — всё работает через единый бэкенд.

---

## 🏗️ Высокоуровневая архитектура

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              КЛИЕНТЫ                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  Dashboard (React/Next.js)  │  Landing Page  │  API для интеграций         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY (FastAPI)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  Auth  │  Rate Limiting  │  Tenant Resolution  │  Request Routing           │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
          ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
          │   Bot Manager   │ │  AI Processor   │ │  Form Builder   │
          │     Service     │ │    Service      │ │    Service      │
          └─────────────────┘ └─────────────────┘ └─────────────────┘
                    │                 │                 │
                    └─────────────────┼─────────────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MESSAGE BROKER (Redis/RabbitMQ)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  Incoming Messages Queue  │  AI Processing Queue  │  Outgoing Messages      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
          ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
          │    Telegram     │ │    WhatsApp     │ │    Discord      │
          │    Workers      │ │    Workers      │ │    Workers      │
          │   (Aiogram)     │ │    (Future)     │ │    (Future)     │
          └─────────────────┘ └─────────────────┘ └─────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  PostgreSQL (Main DB)  │  Redis (Cache/Sessions)  │  S3 (Files/Media)      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Структура проекта

```
botfactory/
├── 📁 api/                          # FastAPI Backend
│   ├── 📁 app/
│   │   ├── 📁 core/
│   │   │   ├── config.py            # Настройки приложения
│   │   │   ├── security.py          # JWT, шифрование
│   │   │   └── dependencies.py      # Dependency injection
│   │   │
│   │   ├── 📁 models/               # SQLAlchemy модели
│   │   │   ├── user.py
│   │   │   ├── tenant.py            # Организации/Тарифы
│   │   │   ├── bot.py
│   │   │   ├── command.py
│   │   │   ├── form.py
│   │   │   ├── conversation.py
│   │   │   └── message.py
│   │   │
│   │   ├── 📁 schemas/              # Pydantic схемы
│   │   │   ├── bot.py
│   │   │   ├── command.py
│   │   │   └── form.py
│   │   │
│   │   ├── 📁 api/
│   │   │   ├── 📁 v1/
│   │   │   │   ├── auth.py
│   │   │   │   ├── bots.py
│   │   │   │   ├── commands.py
│   │   │   │   ├── forms.py
│   │   │   │   ├── analytics.py
│   │   │   │   └── webhooks.py
│   │   │   └── router.py
│   │   │
│   │   ├── 📁 services/
│   │   │   ├── bot_manager.py       # Управление ботами
│   │   │   ├── ai_processor.py      # Обработка AI
│   │   │   ├── form_processor.py    # Обработка форм
│   │   │   └── analytics.py
│   │   │
│   │   └── main.py
│   │
│   ├── 📁 workers/                  # Celery/Background tasks
│   │   ├── telegram_worker.py
│   │   └── ai_worker.py
│   │
│   ├── 📁 migrations/               # Alembic
│   └── requirements.txt
│
├── 📁 bot_gateway/                  # Telegram Gateway
│   ├── 📁 handlers/
│   │   ├── message_handler.py
│   │   ├── command_handler.py
│   │   └── callback_handler.py
│   ├── 📁 middlewares/
│   │   ├── tenant_middleware.py     # Определение бота/тенанта
│   │   └── rate_limit.py
│   ├── dispatcher.py
│   └── main.py
│
├── 📁 dashboard/                    # Frontend (Next.js)
│   ├── 📁 app/
│   │   ├── 📁 (auth)/
│   │   │   ├── login/
│   │   │   └── register/
│   │   ├── 📁 dashboard/
│   │   │   ├── bots/
│   │   │   ├── commands/
│   │   │   ├── forms/
│   │   │   ├── analytics/
│   │   │   └── settings/
│   │   └── layout.tsx
│   │
│   └── 📁 components/
│       ├── BotCard.tsx
│       ├── CommandBuilder.tsx
│       ├── FormBuilder.tsx
│       └── AIPromptEditor.tsx
│
├── 📁 shared/                       # Общий код
│   ├── 📁 types/
│   └── 📁 utils/
│
├── docker-compose.yml
├── docker-compose.prod.yml
└── README.md
```

---

## 🗄️ Модели базы данных

### Основные сущности

```python
# models/tenant.py
class Tenant(Base):
    """Организация/Компания — владелец ботов"""
    __tablename__ = "tenants"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True)
    
    # Тарифный план
    plan = Column(Enum(PlanType), default=PlanType.FREE)
    plan_expires_at = Column(DateTime)
    
    # Лимиты
    max_bots = Column(Integer, default=1)
    max_messages_per_month = Column(Integer, default=1000)
    messages_used = Column(Integer, default=0)
    
    # Настройки AI
    openai_api_key = Column(String, nullable=True)  # Encrypted
    use_platform_key = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    users = relationship("User", back_populates="tenant")
    bots = relationship("Bot", back_populates="tenant")


# models/bot.py
class Bot(Base):
    """Telegram бот"""
    __tablename__ = "bots"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=False)
    
    # Telegram данные
    token = Column(String, nullable=False)  # Encrypted
    username = Column(String(100))
    telegram_id = Column(BigInteger, unique=True)
    
    # Настройки
    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # AI настройки
    ai_enabled = Column(Boolean, default=True)
    system_prompt = Column(Text)  # Инструкция для AI
    ai_model = Column(String(50), default="gpt-4o-mini")
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=1000)
    
    # Поведение
    welcome_message = Column(Text)
    fallback_message = Column(Text)  # Когда AI не может ответить
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    tenant = relationship("Tenant", back_populates="bots")
    commands = relationship("Command", back_populates="bot")
    forms = relationship("Form", back_populates="bot")
    conversations = relationship("Conversation", back_populates="bot")


# models/command.py
class Command(Base):
    """Команды бота (например /start, /help)"""
    __tablename__ = "commands"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    bot_id = Column(UUID, ForeignKey("bots.id"), nullable=False)
    
    # Команда
    name = Column(String(100), nullable=False)  # без /
    description = Column(String(255))
    
    # Тип ответа
    response_type = Column(Enum(ResponseType))  # TEXT, AI, FORM, MENU
    
    # Контент в зависимости от типа
    text_response = Column(Text)  # Для TEXT
    ai_prompt_override = Column(Text)  # Для AI - переопределить промпт
    form_id = Column(UUID, ForeignKey("forms.id"))  # Для FORM
    menu_config = Column(JSON)  # Для MENU - inline кнопки
    
    # Настройки
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)  # Для сортировки
    
    # Relations
    bot = relationship("Bot", back_populates="commands")
    form = relationship("Form")


# models/form.py
class Form(Base):
    """Форма для сбора данных"""
    __tablename__ = "forms"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    bot_id = Column(UUID, ForeignKey("bots.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Поля формы
    fields = Column(JSON)  # [{name, type, label, required, options, validation}]
    
    # Действия после заполнения
    on_complete_action = Column(Enum(FormAction))  # NOTIFY, SAVE, WEBHOOK, AI
    webhook_url = Column(String)
    notification_chat_id = Column(BigInteger)
    completion_message = Column(Text)
    
    is_active = Column(Boolean, default=True)
    
    # Relations
    bot = relationship("Bot", back_populates="forms")
    submissions = relationship("FormSubmission", back_populates="form")


# models/conversation.py
class Conversation(Base):
    """История разговоров"""
    __tablename__ = "conversations"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    bot_id = Column(UUID, ForeignKey("bots.id"), nullable=False)
    
    # Telegram пользователь
    telegram_user_id = Column(BigInteger, nullable=False)
    telegram_username = Column(String(100))
    telegram_first_name = Column(String(255))
    
    # Состояние
    state = Column(String(100))  # Для FSM (например: filling_form:form_id)
    context = Column(JSON)  # Контекст для AI
    
    # Метаданные
    started_at = Column(DateTime, default=datetime.utcnow)
    last_message_at = Column(DateTime)
    messages_count = Column(Integer, default=0)
    
    # Relations
    bot = relationship("Bot", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")


# models/message.py
class Message(Base):
    """Сообщения в разговоре"""
    __tablename__ = "messages"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    conversation_id = Column(UUID, ForeignKey("conversations.id"), nullable=False)
    
    # Направление
    direction = Column(Enum(MessageDirection))  # INBOUND, OUTBOUND
    
    # Контент
    content = Column(Text, nullable=False)
    message_type = Column(Enum(MessageType))  # TEXT, PHOTO, DOCUMENT, etc.
    
    # Telegram данные
    telegram_message_id = Column(BigInteger)
    
    # AI метаданные
    ai_processed = Column(Boolean, default=False)
    tokens_used = Column(Integer)
    processing_time_ms = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    conversation = relationship("Conversation", back_populates="messages")
```

### Enums

```python
# models/enums.py
from enum import Enum

class PlanType(str, Enum):
    FREE = "free"           # 1 бот, 1000 сообщений/мес
    STARTER = "starter"     # 3 бота, 10000 сообщений/мес
    PRO = "pro"             # 10 ботов, 50000 сообщений/мес
    ENTERPRISE = "enterprise"  # Unlimited

class ResponseType(str, Enum):
    TEXT = "text"           # Простой текст
    AI = "ai"               # AI генерирует ответ
    FORM = "form"           # Запустить форму
    MENU = "menu"           # Показать inline кнопки
    WEBHOOK = "webhook"     # Вызвать внешний API

class FormFieldType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    EMAIL = "email"
    PHONE = "phone"
    DATE = "date"
    SELECT = "select"       # Выбор из списка
    MULTISELECT = "multiselect"
    PHOTO = "photo"
    LOCATION = "location"

class FormAction(str, Enum):
    SAVE = "save"           # Только сохранить
    NOTIFY = "notify"       # Уведомить админа
    WEBHOOK = "webhook"     # Отправить на webhook
    AI = "ai"               # Обработать AI

class MessageDirection(str, Enum):
    INBOUND = "inbound"     # От пользователя
    OUTBOUND = "outbound"   # От бота
```

---

## 🔄 Поток обработки сообщений

```
┌──────────────────────────────────────────────────────────────────┐
│                    INCOMING MESSAGE FLOW                          │
└──────────────────────────────────────────────────────────────────┘

1. Telegram Update
       │
       ▼
┌─────────────────┐
│  Bot Gateway    │ ← Единая точка входа для всех ботов
│  (Webhook/Poll) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Tenant Resolver │ ← Определяем какой бот по telegram_id
│   Middleware    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Rate Limiter   │ ← Проверяем лимиты тенанта
│   Middleware    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Command Router  │────►│ Command Handler │ ← Если это /команда
└────────┬────────┘     └─────────────────┘
         │
         │ (если не команда)
         ▼
┌─────────────────┐     ┌─────────────────┐
│  State Router   │────►│  Form Handler   │ ← Если в состоянии формы
└────────┬────────┘     └─────────────────┘
         │
         │ (если просто сообщение)
         ▼
┌─────────────────┐
│ AI Message      │
│ Processor       │
│                 │
│ 1. Load context │
│ 2. Build prompt │
│ 3. Call LLM     │
│ 4. Save history │
│ 5. Send reply   │
└─────────────────┘
```

---

## 🧠 AI Processing Service

```python
# services/ai_processor.py
from openai import AsyncOpenAI
from typing import Optional

class AIProcessor:
    def __init__(self, settings: Settings):
        self.default_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def process_message(
        self,
        bot: Bot,
        conversation: Conversation,
        user_message: str,
        tenant: Tenant
    ) -> str:
        # 1. Получаем клиент (свой ключ тенанта или платформенный)
        client = self._get_client(tenant)
        
        # 2. Загружаем историю последних N сообщений
        history = await self._load_conversation_history(
            conversation.id, 
            limit=10
        )
        
        # 3. Собираем промпт
        messages = self._build_messages(
            system_prompt=bot.system_prompt,
            history=history,
            user_message=user_message
        )
        
        # 4. Вызываем LLM
        response = await client.chat.completions.create(
            model=bot.ai_model,
            messages=messages,
            temperature=bot.temperature,
            max_tokens=bot.max_tokens
        )
        
        # 5. Сохраняем сообщения и метрики
        await self._save_messages(
            conversation_id=conversation.id,
            user_message=user_message,
            ai_response=response.choices[0].message.content,
            tokens_used=response.usage.total_tokens
        )
        
        # 6. Обновляем счётчик использования тенанта
        await self._increment_usage(tenant.id)
        
        return response.choices[0].message.content
    
    def _build_messages(
        self, 
        system_prompt: str, 
        history: list[Message],
        user_message: str
    ) -> list[dict]:
        messages = []
        
        # System prompt
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # History
        for msg in history:
            role = "user" if msg.direction == MessageDirection.INBOUND else "assistant"
            messages.append({
                "role": role,
                "content": msg.content
            })
        
        # Current message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        return messages
```

---

## 📱 Telegram Gateway (Multi-bot support)

```python
# bot_gateway/main.py
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web
import asyncio

class BotGateway:
    """
    Единый gateway для обработки всех Telegram ботов.
    Использует webhook с динамическим определением бота.
    """
    
    def __init__(self, settings: Settings, db: Database):
        self.settings = settings
        self.db = db
        self.bots: dict[int, Bot] = {}  # telegram_id -> Bot instance
        self.dp = Dispatcher()
        
        # Регистрируем handlers
        self._setup_handlers()
    
    async def start(self):
        """Загружаем все активные боты и запускаем gateway"""
        
        # Загружаем боты из БД
        active_bots = await self.db.get_active_bots()
        
        for bot_config in active_bots:
            await self._register_bot(bot_config)
        
        # Запускаем webhook server
        app = web.Application()
        
        # Единый endpoint для всех ботов
        app.router.add_post(
            "/webhook/{bot_token}", 
            self._handle_webhook
        )
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", self.settings.WEBHOOK_PORT)
        await site.start()
    
    async def _register_bot(self, bot_config: BotModel):
        """Регистрируем бота и устанавливаем webhook"""
        bot = Bot(token=bot_config.token)
        bot_info = await bot.get_me()
        
        self.bots[bot_info.id] = bot
        
        # Устанавливаем webhook
        webhook_url = f"{self.settings.WEBHOOK_BASE_URL}/webhook/{bot_config.token}"
        await bot.set_webhook(webhook_url)
        
        print(f"✅ Bot @{bot_info.username} registered")
    
    async def _handle_webhook(self, request: web.Request):
        """Обрабатываем webhook от любого бота"""
        bot_token = request.match_info["bot_token"]
        
        # Находим бота по токену
        bot = self._get_bot_by_token(bot_token)
        if not bot:
            return web.Response(status=404)
        
        # Парсим update
        data = await request.json()
        update = types.Update(**data)
        
        # Обрабатываем через dispatcher
        await self.dp.feed_update(bot, update)
        
        return web.Response()
    
    def _setup_handlers(self):
        """Настраиваем обработчики сообщений"""
        
        @self.dp.message(Command("start"))
        async def handle_start(message: types.Message, bot: Bot):
            bot_config = await self._get_bot_config(bot)
            
            if bot_config.welcome_message:
                await message.answer(bot_config.welcome_message)
        
        @self.dp.message()
        async def handle_message(message: types.Message, bot: Bot):
            """Основной handler для всех текстовых сообщений"""
            
            # Получаем конфиг бота
            bot_config = await self._get_bot_config(bot)
            tenant = await self._get_tenant(bot_config.tenant_id)
            
            # Проверяем лимиты
            if not await self._check_limits(tenant):
                await message.answer(
                    "⚠️ Достигнут лимит сообщений. "
                    "Обратитесь к владельцу бота."
                )
                return
            
            # Получаем или создаём conversation
            conversation = await self._get_or_create_conversation(
                bot_config.id,
                message.from_user
            )
            
            # Проверяем состояние (может быть в процессе заполнения формы)
            if conversation.state:
                await self._handle_state(
                    conversation, 
                    message, 
                    bot_config
                )
                return
            
            # Обрабатываем AI
            if bot_config.ai_enabled:
                response = await self.ai_processor.process_message(
                    bot=bot_config,
                    conversation=conversation,
                    user_message=message.text,
                    tenant=tenant
                )
                await message.answer(response)
            else:
                # Fallback если AI выключен
                if bot_config.fallback_message:
                    await message.answer(bot_config.fallback_message)
```

---

## 🎨 Dashboard API Endpoints

```python
# api/v1/bots.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List

router = APIRouter(prefix="/bots", tags=["bots"])

@router.get("/", response_model=List[BotResponse])
async def list_bots(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить все боты тенанта"""
    bots = await bot_service.get_bots_by_tenant(
        db, 
        current_user.tenant_id
    )
    return bots


@router.post("/", response_model=BotResponse)
async def create_bot(
    bot_data: BotCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создать нового бота"""
    
    # Проверяем лимит ботов
    tenant = await tenant_service.get_tenant(db, current_user.tenant_id)
    bots_count = await bot_service.count_bots(db, tenant.id)
    
    if bots_count >= tenant.max_bots:
        raise HTTPException(
            status_code=403,
            detail=f"Достигнут лимит ботов ({tenant.max_bots}). Обновите тариф."
        )
    
    # Валидируем токен Telegram
    try:
        bot_info = await telegram_service.validate_token(bot_data.token)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Неверный токен Telegram бота"
        )
    
    # Создаём бота
    bot = await bot_service.create_bot(
        db,
        tenant_id=tenant.id,
        token=bot_data.token,
        telegram_id=bot_info.id,
        username=bot_info.username,
        name=bot_data.name,
        system_prompt=bot_data.system_prompt
    )
    
    # Регистрируем webhook
    await bot_gateway.register_bot(bot)
    
    return bot


@router.patch("/{bot_id}", response_model=BotResponse)
async def update_bot(
    bot_id: UUID,
    bot_data: BotUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновить настройки бота"""
    bot = await bot_service.get_bot(db, bot_id, current_user.tenant_id)
    
    if not bot:
        raise HTTPException(status_code=404, detail="Бот не найден")
    
    updated_bot = await bot_service.update_bot(db, bot, bot_data)
    return updated_bot


@router.post("/{bot_id}/test-prompt")
async def test_prompt(
    bot_id: UUID,
    test_data: TestPromptRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Тестировать промпт без реального бота"""
    bot = await bot_service.get_bot(db, bot_id, current_user.tenant_id)
    
    response = await ai_processor.test_prompt(
        system_prompt=test_data.system_prompt or bot.system_prompt,
        user_message=test_data.message,
        model=bot.ai_model
    )
    
    return {"response": response}
```

---

## 📊 Form Builder & Processing

```python
# services/form_processor.py

class FormProcessor:
    """Обработка форм с состоянием"""
    
    async def start_form(
        self, 
        form: Form, 
        conversation: Conversation,
        bot: Bot
    ) -> str:
        """Начать заполнение формы"""
        
        # Устанавливаем состояние
        conversation.state = f"form:{form.id}:0"
        conversation.context = {
            "form_id": str(form.id),
            "current_field": 0,
            "answers": {}
        }
        await self.db.commit()
        
        # Отправляем первый вопрос
        first_field = form.fields[0]
        return self._format_question(first_field)
    
    async def process_answer(
        self,
        conversation: Conversation,
        message: str,
        bot_instance: Bot
    ) -> tuple[str, bool]:
        """
        Обработать ответ на вопрос формы.
        Возвращает (ответ, завершена ли форма)
        """
        
        context = conversation.context
        form = await self.db.get(Form, context["form_id"])
        current_idx = context["current_field"]
        current_field = form.fields[current_idx]
        
        # Валидируем ответ
        is_valid, error = self._validate_answer(current_field, message)
        
        if not is_valid:
            return error, False
        
        # Сохраняем ответ
        context["answers"][current_field["name"]] = message
        
        # Проверяем есть ли ещё вопросы
        if current_idx + 1 >= len(form.fields):
            # Форма завершена
            await self._complete_form(form, conversation, context["answers"])
            
            conversation.state = None
            conversation.context = {}
            await self.db.commit()
            
            return form.completion_message or "✅ Спасибо! Форма заполнена.", True
        
        # Переходим к следующему вопросу
        context["current_field"] = current_idx + 1
        await self.db.commit()
        
        next_field = form.fields[current_idx + 1]
        return self._format_question(next_field), False
    
    def _format_question(self, field: dict) -> str:
        """Форматируем вопрос"""
        question = field["label"]
        
        if field["type"] == "select":
            options = "\n".join(
                f"{i+1}. {opt}" 
                for i, opt in enumerate(field["options"])
            )
            question += f"\n\n{options}"
        
        if not field.get("required", True):
            question += "\n\n(Необязательно, отправьте '-' чтобы пропустить)"
        
        return question
    
    def _validate_answer(self, field: dict, answer: str) -> tuple[bool, str]:
        """Валидируем ответ"""
        
        # Пропуск необязательного поля
        if answer == "-" and not field.get("required", True):
            return True, ""
        
        field_type = field["type"]
        
        if field_type == "email":
            if "@" not in answer:
                return False, "❌ Введите корректный email"
        
        elif field_type == "phone":
            if not answer.replace("+", "").replace(" ", "").isdigit():
                return False, "❌ Введите корректный номер телефона"
        
        elif field_type == "number":
            try:
                float(answer)
            except ValueError:
                return False, "❌ Введите число"
        
        elif field_type == "select":
            options = field["options"]
            if answer not in options and not answer.isdigit():
                return False, f"❌ Выберите один из вариантов: {', '.join(options)}"
        
        return True, ""
    
    async def _complete_form(
        self, 
        form: Form, 
        conversation: Conversation,
        answers: dict
    ):
        """Действия после заполнения формы"""
        
        # Сохраняем submission
        submission = FormSubmission(
            form_id=form.id,
            conversation_id=conversation.id,
            answers=answers
        )
        self.db.add(submission)
        
        # Выполняем действие
        if form.on_complete_action == FormAction.NOTIFY:
            await self._notify_admin(form, answers)
        
        elif form.on_complete_action == FormAction.WEBHOOK:
            await self._send_webhook(form.webhook_url, answers)
        
        elif form.on_complete_action == FormAction.AI:
            # AI анализирует ответы
            pass
```

---

## 💰 Тарифные планы

```python
# services/billing.py

PLANS = {
    PlanType.FREE: {
        "name": "Free",
        "price": 0,
        "max_bots": 1,
        "max_messages": 1000,
        "features": [
            "1 бот",
            "1,000 сообщений/мес",
            "Базовые команды",
            "История 7 дней"
        ]
    },
    PlanType.STARTER: {
        "name": "Starter",
        "price": 19,
        "max_bots": 3,
        "max_messages": 10000,
        "features": [
            "3 бота",
            "10,000 сообщений/мес",
            "Формы",
            "Webhooks",
            "История 30 дней"
        ]
    },
    PlanType.PRO: {
        "name": "Pro",
        "price": 49,
        "max_bots": 10,
        "max_messages": 50000,
        "features": [
            "10 ботов",
            "50,000 сообщений/мес",
            "Свой API ключ OpenAI",
            "Аналитика",
            "Priority support"
        ]
    },
    PlanType.ENTERPRISE: {
        "name": "Enterprise",
        "price": None,  # Custom
        "max_bots": -1,  # Unlimited
        "max_messages": -1,
        "features": [
            "Безлимитные боты",
            "Безлимитные сообщения",
            "Dedicated support",
            "Custom integrations",
            "SLA"
        ]
    }
}
```

---

## 🚀 Docker Compose для разработки

```yaml
# docker-compose.yml
version: '3.8'

services:
  # PostgreSQL
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: botfactory
      POSTGRES_USER: botfactory
      POSTGRES_PASSWORD: secret
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # Redis
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # API
  api:
    build:
      context: ./api
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql+asyncpg://botfactory:secret@postgres:5432/botfactory
      REDIS_URL: redis://redis:6379
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      SECRET_KEY: ${SECRET_KEY}
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    volumes:
      - ./api:/app

  # Bot Gateway
  bot_gateway:
    build:
      context: ./bot_gateway
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql+asyncpg://botfactory:secret@postgres:5432/botfactory
      REDIS_URL: redis://redis:6379
      WEBHOOK_BASE_URL: ${WEBHOOK_BASE_URL}
      WEBHOOK_PORT: 8080
    ports:
      - "8080:8080"
    depends_on:
      - postgres
      - redis
      - api

  # Dashboard (Next.js)
  dashboard:
    build:
      context: ./dashboard
      dockerfile: Dockerfile
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    ports:
      - "3000:3000"
    volumes:
      - ./dashboard:/app
      - /app/node_modules

volumes:
  postgres_data:
  redis_data:
```

---

## 📋 Roadmap

### Phase 1: MVP (4-6 недель)
- [ ] Базовая авторизация (JWT)
- [ ] CRUD для ботов
- [ ] AI обработка сообщений
- [ ] Команды (/start, /help)
- [ ] Простой dashboard

### Phase 2: Core Features (4-6 недель)
- [ ] Form Builder
- [ ] Inline кнопки и меню
- [ ] История разговоров
- [ ] Базовая аналитика

### Phase 3: Growth (4-6 недель)
- [ ] Тарифные планы и биллинг
- [ ] Webhooks
- [ ] Свой API ключ OpenAI
- [ ] Расширенная аналитика

### Phase 4: Scale (ongoing)
- [ ] WhatsApp интеграция
- [ ] Discord интеграция
- [ ] AI function calling
- [ ] Мультиязычность

---

## 🔐 Безопасность

1. **Шифрование токенов** — все токены ботов хранятся зашифрованными (Fernet)
2. **Rate Limiting** — защита от DDoS
3. **Tenant Isolation** — строгая изоляция данных между клиентами
4. **JWT с refresh tokens** — безопасная аутентификация
5. **Input validation** — Pydantic для всех входных данных

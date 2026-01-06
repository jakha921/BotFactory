# План реализации: Missing Features для Bot Factory

## 📋 Обзор

Добавление недостающих функций из архитектурного документа в текущий Django бэкенд.

**Оценка времени:** 2-3 недели
**Приоритет:** Tenant → Commands → Forms → Gateway

---

## 🎯 Phase 1: Мульти-тенантность (2-3 дня)

### Цель
Добавить модель Tenant для изоляции данных между клиентами/организациями.

### Задачи

#### 1.1 Создать модель Tenant
**Файл:** `backend/apps/accounts/models.py`

```python
class Tenant(models.Model):
    """Организация/клиент платформы."""
    name = models.CharField(max_length=255, verbose_name="Название")
    slug = models.SlugField(unique=True, max_length=100)

    # Тарифный план
    PLAN_CHOICES = [
        ('FREE', 'Free'),
        ('STARTER', 'Starter'),
        ('PRO', 'Pro'),
        ('ENTERPRISE', 'Enterprise'),
    ]
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='FREE')
    plan_expires_at = models.DateTimeField(null=True, blank=True)

    # Лимиты
    max_bots = models.IntegerField(default=1)
    max_messages_per_month = models.IntegerField(default=1000)
    messages_used = models.IntegerField(default=0)

    # AI настройки
    openai_api_key = models.EncryptedCharField(null=True, blank=True)
    use_platform_key = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"
        ordering = ['-created_at']
```

#### 1.2 Обновить модель User
**Файл:** `backend/apps/accounts/models.py`

```python
class User(AbstractUser):
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='users',
        null=True,  # Временно для миграции
        verbose_name="Организация"
    )
    # ... остальные поля
```

#### 1.3 Создать миграцию
```bash
cd backend
uv run python manage.py makemigrations accounts
uv run python manage.py migrate accounts
```

#### 1.4 Миграция существующих пользователей
**Файл:** создать data migration для создания default tenant

```python
# backend/apps/accounts/migrations/0004_migrate_to_tenants.py
def migrate_users_to_tenants(apps, schema_editor):
    Tenant = apps.get_model('accounts', 'Tenant')
    User = apps.get_model('accounts', 'User')

    # Создаем default tenant
    default_tenant = Tenant.objects.create(
        name="Default",
        slug="default",
        plan="PRO",  # Дать PRO существующим пользователям
        max_bots=10,
        max_messages_per_month=50000
    )

    # Привязываем всех пользователей к default tenant
    User.objects.update(tenant=default_tenant)
```

#### 1.5 Добавить TenantMiddleware
**Файл:** `backend/core/middleware.py` (создать)

```python
from django.utils.deprecation import MiddlewareMixin
from .models import Tenant

class TenantMiddleware(MiddlewareMixin):
    """Определяет tenant из slug в URL или JWT токена."""

    def process_request(self, request):
        # Если пользователь аутентифицирован
        if request.user.is_authenticated:
            request.tenant = request.user.tenant
        else:
            # Для API - определить из slug или header
            tenant_slug = request.META.get('HTTP_X_TENANT_SLUG')
            if tenant_slug:
                try:
                    request.tenant = Tenant.objects.get(slug=tenant_slug)
                except Tenant.DoesNotExist:
                    request.tenant = None
            else:
                request.tenant = None
```

#### 1.6 Обновить настройки
**Файл:** `backend/bot_factory/settings/base.py`

```python
MIDDLEWARE = [
    # ...
    'core.middleware.TenantMiddleware',
    # ...
]
```

#### 1.7 Обновить ViewSets с tenant фильтрацией
**Файлы:**
- `backend/apps/bots/views.py`
- `backend/apps/chat/views.py`
- `backend/apps/telegram/views.py`

Пример:
```python
class BotViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Bot.objects.filter(owner__tenant=self.request.tenant)
```

---

## 🎯 Phase 2: Command System (2-3 дня)

### Цель
Добавить модель Command для управления командами бота (/start, /help, и т.д.)

### Задачи

#### 2.1 Создать Django app "commands"
```bash
cd backend
mkdir -p apps/commands
touch apps/commands/__init__.py apps/commands/apps.py apps/commands/models.py
touch apps/commands/admin.py apps/commands/serializers.py apps/commands/views.py
touch apps/commands/urls.py
```

#### 2.2 Создать модель Command
**Файл:** `backend/apps/commands/models.py`

```python
from django.db import models
from apps.bots.models import Bot

class ResponseType(models.TextChoices):
    TEXT = 'text', 'Текст'
    AI = 'ai', 'AI ответ'
    FORM = 'form', 'Форма'
    MENU = 'menu', 'Меню с кнопками'

class Command(models.Model):
    """Команды бота (например /start, /help)."""
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name='commands')

    # Команда
    name = models.CharField(max_length=100, help_text="Без / например: start, help")
    description = models.CharField(max_length=255, blank=True)

    # Тип ответа
    response_type = models.CharField(
        max_length=20,
        choices=ResponseType.choices,
        default=ResponseType.TEXT
    )

    # Контент в зависимости от типа
    text_response = models.TextField(blank=True, help_text="Для TEXT типа")
    ai_prompt_override = models.TextField(blank=True, help_text="Для AI типа")
    form_id = models.CharField(max_length=255, blank=True, help_text="Для FORM типа")
    menu_config = models.JSONField(default=list, blank=True, help_text="Для MENU типа")

    # Настройки
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0, help_text="Для сортировки")

    created_at = models.DateTimeField(auto_auto_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Command"
        verbose_name_plural = "Commands"
        ordering = ['-priority', 'name']
        unique_together = [['bot', 'name']]

    def __str__(self):
        return f"/{self.name} ({self.bot.name})"
```

#### 2.3 Создать админку
**Файл:** `backend/apps/commands/admin.py`

```python
from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Command

@admin.register(Command)
class CommandAdmin(ModelAdmin):
    list_display = ['name', 'bot', 'response_type', 'is_active', 'priority']
    list_filter = ['response_type', 'is_active', 'bot']
    search_fields = ['name', 'description']
    fieldsets = (
        ('Основное', {
            'fields': ('bot', 'name', 'description', 'is_active', 'priority')
        }),
        ('Тип ответа', {
            'fields': ('response_type',)
        }),
        ('Контент', {
            'fields': (
                'text_response',
                'ai_prompt_override',
                'form_id',
                'menu_config'
            )
        }),
    )
```

#### 2.4 Создать ViewSet
**Файл:** `backend/apps/commands/views.py`

```python
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Command
from .serializers import CommandSerializer

class CommandViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CommandSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['bot', 'response_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['priority', 'name', 'created_at']
    ordering = ['-priority', 'name']

    def get_queryset(self):
        return Command.objects.filter(bot__owner=self.request.user)

    def perform_create(self, serializer):
        # Проверяем что бот принадлежит пользователю
        bot = serializer.validated_data['bot']
        if bot.owner != self.request.user:
            raise PermissionError("You don't own this bot")
        serializer.save()
```

#### 2.5 Создать Serializer
**Файл:** `backend/apps/commands/serializers.py`

```python
from rest_framework import serializers
from .models import Command

class CommandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Command
        fields = [
            'id', 'bot', 'name', 'description', 'response_type',
            'text_response', 'ai_prompt_override', 'form_id', 'menu_config',
            'is_active', 'priority', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        response_type = data.get('response_type')

        # Валидация в зависимости от типа
        if response_type == 'text' and not data.get('text_response'):
            raise serializers.ValidationError("text_response required for TEXT type")
        if response_type == 'form' and not data.get('form_id'):
            raise serializers.ValidationError("form_id required for FORM type")

        return data
```

#### 2.6 Интегрировать с bot handlers
**Файл:** `bot/handlers/commands.py` (создать или обновить)

```python
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from bot.integrations.django_orm import get_bot_by_token, get_commands

commands_router = Router()

@commands_router.message(Command())
async def handle_command(message: Message, bot_token: str):
    """Обработчик всех команд бота."""
    bot = await get_bot_by_token(bot_token)
    if not bot:
        return

    # Получаем команду из базы
    command_name = message.text[1:]  # Убираем /
    commands = await get_commands(bot.id)
    command = next((c for c in commands if c.name == command_name), None)

    if not command or not command.is_active:
        await message.answer("❌ Команда не найдена")
        return

    # Обрабатываем в зависимости от типа
    if command.response_type == 'text':
        await message.answer(command.text_response)

    elif command.response_type == 'ai':
        # Вызываем AI processor
        pass

    elif command.response_type == 'form':
        # Запускаем форму
        pass

    elif command.response_type == 'menu':
        # Показываем меню
        pass
```

---

## 🎯 Phase 3: Form Builder (3-5 дней)

### Цель
Добавить модели Form и FormSubmission для создания форм через админку.

### Задачи

#### 3.1 Создать Django app "forms" (или использовать существующее)
**ВНИМАНИЕ:** Проверить нет ли конфликта с `chat` app который имеет формы

```bash
cd backend
mkdir -p apps/form_builder
touch apps/form_builder/__init__.py apps/form_builder/apps.py
touch apps/form_builder/models.py apps/form_builder/admin.py
touch apps/form_builder/serializers.py apps/form_builder/views.py
touch apps/form_builder/urls.py
```

#### 3.2 Создать модели
**Файл:** `backend/apps/form_builder/models.py`

```python
from django.db import models
from apps.bots.models import Bot

class FormFieldType(models.TextChoices):
    TEXT = 'text', 'Текст'
    NUMBER = 'number', 'Число'
    EMAIL = 'email', 'Email'
    PHONE = 'phone', 'Телефон'
    DATE = 'date', 'Дата'
    SELECT = 'select', 'Выбор из списка'
    MULTISELECT = 'multiselect', 'Множественный выбор'
    PHOTO = 'photo', 'Фото'
    LOCATION = 'location', 'Локация'

class FormAction(models.TextChoices):
    SAVE = 'save', 'Сохранить'
    NOTIFY = 'notify', 'Уведомить админа'
    WEBHOOK = 'webhook', 'Отправить на webhook'
    AI = 'ai', 'Обработать AI'

class Form(models.Model):
    """Форма для сбора данных."""
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name='forms')

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Поля формы (JSON конфигурация)
    fields = models.JSONField(
        default=list,
        help_text='[{"name": "email", "type": "email", "label": "Email", "required": true}]'
    )

    # Действия после заполнения
    on_complete_action = models.CharField(
        max_length=20,
        choices=FormAction.choices,
        default=FormAction.SAVE
    )
    webhook_url = models.URLField(blank=True)
    notification_chat_id = models.BigIntegerField(null=True, blank=True)
    completion_message = models.TextField(
        default="✅ Спасибо! Форма заполнена."
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Form"
        verbose_name_plural = "Forms"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.bot.name})"


class FormSubmission(models.Model):
    """Заполненная форма."""
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='submissions')

    # Telegram пользователь
    telegram_user_id = models.BigIntegerField()
    telegram_username = models.CharField(max_length=255, blank=True)
    telegram_first_name = models.CharField(max_length=255, blank=True)

    # Ответы
    answers = models.JSONField()

    # Метаданные
    submitted_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = "Form Submission"
        verbose_name_plural = "Form Submissions"
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.form.name} - {self.telegram_username or self.telegram_user_id}"
```

#### 3.3 Создать админку с визуальным редактором
**Файл:** `backend/apps/form_builder/admin.py`

```python
from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Form, FormSubmission

@admin.register(Form)
class FormAdmin(ModelAdmin):
    list_display = ['name', 'bot', 'is_active', 'submissions_count']
    list_filter = ['is_active', 'bot', 'on_complete_action']
    search_fields = ['name', 'description']

    fieldsets = (
        ('Основное', {
            'fields': ('bot', 'name', 'description', 'is_active')
        }),
        ('Поля формы', {
            'fields': ('fields',),
            'description': 'JSON конфигурация полей формы'
        }),
        ('Действия после заполнения', {
            'fields': ('on_complete_action', 'webhook_url', 'notification_chat_id', 'completion_message')
        }),
    )

    def submissions_count(self, obj):
        return obj.submissions.count()
    submissions_count.short_description = 'Заполнений'


@admin.register(FormSubmission)
class FormSubmissionAdmin(ModelAdmin):
    list_display = ['form', 'telegram_username', 'telegram_user_id', 'submitted_at']
    list_filter = ['form', 'submitted_at']
    search_fields = ['telegram_username', 'telegram_first_name']
    readonly_fields = ['form', 'telegram_user_id', 'answers', 'submitted_at']
```

#### 3.4 Создать API endpoints
**Файл:** `backend/apps/form_builder/views.py`

```python
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Form, FormSubmission
from .serializers import FormSerializer, FormSubmissionSerializer

class FormViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = FormSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['bot', 'is_active']
    search_fields = ['name', 'description']

    def get_queryset(self):
        return Form.objects.filter(bot__owner=self.request.user)


class FormSubmissionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = FormSubmissionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['form']

    def get_queryset(self):
        return FormSubmission.objects.filter(
            form__bot__owner=self.request.user
        )
```

---

## 🎯 Phase 4: Unified Gateway (3-5 дней)

### Цель
Создать единый webhook endpoint для всех ботов вместо индивидуальных.

### Задачи

#### 4.1 Единый webhook endpoint
**Файл:** `backend/apps/telegram/views.py` (обновить существующий)

Уже есть: `/webhook/<token>/`

Нужно добавить:
- Bot discovery по токену
- Кеширование активных ботов
- Rate limiting per tenant

#### 4.2 Bot discovery service
**Файл:** `backend/services/bot_discovery.py` (создать)

```python
from django.core.cache import cache
from apps.bots.models import Bot

class BotDiscovery:
    """Сервис для поиска ботов по токену с кешированием."""

    CACHE_KEY_PREFIX = "bot_token:"
    CACHE_TIMEOUT = 300  # 5 минут

    @classmethod
    def get_bot_by_token(cls, token: str) -> Bot | None:
        """Найти бота по токену с кешированием."""
        cache_key = f"{cls.CACHE_KEY_PREFIX}{token}"

        # Проверяем кеш
        bot_id = cache.get(cache_key)
        if bot_id:
            try:
                return Bot.objects.get(id=bot_id, status='active')
            except Bot.DoesNotExist:
                cache.delete(cache_key)

        # Ищем в базе
        try:
            bot = Bot.objects.get(telegram_token__contains=token, status='active')
            # Кешируем только ID (без токена)
            cache.set(cache_key, bot.id, cls.CACHE_TIMEOUT)
            return bot
        except Bot.DoesNotExist:
            return None

    @classmethod
    def invalidate_bot(cls, bot: Bot):
        """Сбросить кеш для бота."""
        token = bot.decrypted_telegram_token
        cache_key = f"{cls.CACHE_KEY_PREFIX}{token}"
        cache.delete(cache_key)
```

#### 4.3 Rate limiting per tenant
**Файл:** `backend/core/rate_limit.py` (обновить)

```python
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from rest_framework import HTTP_STATUS_429_TOO_MANY_REQUESTS

class TenantRateLimit:
    """Rate limiting per tenant."""

    @classmethod
    def check_rate_limit(cls, tenant, limit=100, window=60):
        """
        Проверить лимит запросов для tenant.

        Args:
            tenant: Tenant объект
            limit: Максимум запросов
            window: Окно времени в секундах

        Returns:
            bool: True если лимит не превышен
        """
        key = f"rate_limit:tenant:{tenant.id}"

        # Получаем текущий счётчик
        current = cache.get(key, 0)

        if current >= limit:
            raise PermissionError("Rate limit exceeded")

        # Увеличиваем счётчик
        cache.set(key, current + 1, window)

        return True
```

---

## 📋 Порядок выполнения

### Неделя 1
1. **Пн-Вт:** Phase 1 - Мульти-тенантность
   - Создать модели
   - Миграции
   - Middleware

2. **Ср-Чт:** Phase 2 - Command System
   - Создать app
   - Модели и админка
   - API endpoints

3. **Пт:** Интеграция commands с bot handlers
   - Тестирование

### Неделя 2
1. **Пн-Ср:** Phase 3 - Form Builder
   - Создать models
   - Админка
   - API endpoints

2. **Чт-Пт:** Phase 4 - Unified Gateway
   - Bot discovery
   - Rate limiting
   - Тестирование

### Неделя 3
1. **Пн-Вт:** Финальное тестирование
2. **Ср-Чт:** Документация
3. **Пт:** Деплой на staging

---

## 🔗 Связанные файлы

### Backend
- `backend/apps/accounts/models.py` - Tenant модель
- `backend/core/middleware.py` - TenantMiddleware
- `backend/apps/commands/` - Command app
- `backend/apps/form_builder/` - Form app
- `backend/services/bot_discovery.py` - Bot discovery
- `bot/handlers/commands.py` - Command handlers

### Frontend (обновления)
- `frontend/pages/Commands.tsx` - Управление командами
- `frontend/pages/Forms.tsx` - Конструктор форм
- `frontend/pages/Tenants.tsx` - Управление тенантами

---

## ✅ Checklist

### Phase 1: Tenant
- [ ] Создать модель Tenant
- [ ] Обновить модель User с tenant FK
- [ ] Создать миграции
- [ ] Создать data migration для существующих users
- [ ] Создать TenantMiddleware
- [ ] Обновить settings.py
- [ ] Обновить ViewSets с tenant фильтрацией
- [ ] Админка для Tenant
- [ ] Тестирование

### Phase 2: Commands
- [ ] Создать commands app
- [ ] Создать модель Command
- [ ] Админка для Command
- [ ] Serializer для Command
- [ ] ViewSet для Command
- [ ] URL routing
- [ ] Интеграция с bot handlers
- [ ] Тестирование

### Phase 3: Forms
- [ ] Создать form_builder app
- [ ] Создать модели Form/FormSubmission
- [ ] Админка с визуальным редактором
- [ ] Serializer для форм
- [ ] ViewSet для форм
- [ ] URL routing
- [ ] Интеграция с bot handlers
- [ ] Тестирование

### Phase 4: Gateway
- [ ] Bot discovery service
- [ ] Кеширование ботов
- [ ] Rate limiting per tenant
- [ ] Единый webhook endpoint
- [ ] Мониторинг
- [ ] Тестирование нагрузки

---

## 📝 Заметки

- Все модели должны иметь `created_at` и `updated_at`
- Использовать `EncryptedCharField` для чувствительных данных
- Все ViewSet должны проверять ownership
- Кешировать часто запрашиваемые данные (bot discovery)
- Логировать все ошибки для отладки
- Добавить тесты для критических путей

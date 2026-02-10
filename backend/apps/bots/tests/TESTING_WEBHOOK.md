# Тестирование Webhook миграции

## Обзор

Этот документ описывает тесты, созданные для миграции с polling на webhook.

## Структура тестов

### 1. Webhook API Tests (`apps/bots/tests/test_webhook_api.py`)

Тестирует endpoints управления webhook:

#### `WebhookAPITest`
- `test_set_webhook_success` - успешная регистрация webhook
- `test_set_webhook_default_url` - регистрация с URL по умолчанию
- `test_set_webhook_telegram_api_error` - обработка ошибок Telegram API
- `test_set_webhook_requires_auth` - проверка аутентификации
- `test_set_webhook_requires_ownership` - проверка прав владельца
- `test_delete_webhook_success` - успешное удаление webhook
- `test_delete_webhook_telegram_api_error` - ошибки при удалении
- `test_delete_webhook_when_in_polling_mode` - идемпотентность операции
- `test_webhook_info_polling_mode` - информация в режиме polling
- `test_webhook_info_webhook_mode` - информация в режиме webhook
- `test_webhook_info_with_telegram_error` - обработка ошибок API
- `test_webhook_info_requires_auth` - проверка аутентификации

#### `DeliveryModeSerializerTest`
- `test_create_bot_default_delivery_mode` - по умолчанию polling
- `test_create_bot_with_webhook_mode` - создание в webhook режиме
- `test_update_bot_delivery_mode` - обновление режима
- `test_invalid_delivery_mode` - отклонение неверного режима

#### `BotManagerDeliveryModeTest`
- `test_bot_manager_skips_webhook_bots` - BotManager пропускает webhook ботов
- `test_bot_manager_starts_polling_bots` - BotManager запускает polling ботов

### 2. Webhook Views Tests (`apps/telegram/tests/test_webhook_views.py`)

Тестирует webhook endpoint с фильтрацией по delivery_mode:

#### `TelegramWebhookViewTest`
Обновлено для работы с новым URL (`/api/telegram/webhook/<bot_id>/`)
- Проверка валидации бота
- Проверка валидации подписи
- Проверка JSON формата
- Прием валидных обновлений
- GET endpoint для health check

#### `DeliveryModeWebhookTest` (новый класс)
- `test_webhook_rejects_polling_mode_bots` - отклонение polling ботов
- `test_webhook_accepts_webhook_mode_bots` - прием webhook ботов
- `test_switching_to_webhook_mode_enables_webhook` - переключение на webhook
- `test_switching_to_polling_mode_disables_webhook` - переключение на polling

## Запуск тестов

### Предварительные требования

```bash
# Запустить Docker сервисы (PostgreSQL с pgvector, Redis)
docker-compose up -d
```

### Запуск всех тестов webhook

```bash
cd backend

# Все webhook тесты
uv run python manage.py test apps.bots.tests.test_webhook_api apps.telegram.tests.test_webhook_views

# Только API тесты
uv run python manage.py test apps.bots.tests.test_webhook_api

# Только webhook views тесты
uv run python manage.py test apps.telegram.tests.test_webhook_views

# С подробным выводом
uv run python manage.py test apps.bots.tests.test_webhook_api --verbosity=2

# С покрытием
uv run pytest apps/bots/tests/test_webhook_api.py --cov=apps.bots --cov-report=html
```

### Запуск отдельного теста

```bash
# Конкретный тест
uv run python manage.py test apps.bots.tests.test_webhook_api.WebhookAPITest.test_set_webhook_success

# Все тесты в классе
uv run python manage.py test apps.bots.tests.test_webhook_api.WebhookAPITest
```

## Покрытие тестами

| Функционал | Тесты | Покрытие |
|------------|-------|----------|
| API: set-webhook | ✅ | Полное |
| API: delete-webhook | ✅ | Полное |
| API: webhook-info | ✅ | Полное |
| Serializer: delivery_mode | ✅ | Полное |
| Webhook endpoint: delivery_mode | ✅ | Полное |
| Webhook endpoint: signature | ✅ | Полное |
| BotManager integration | ✅ | Базовое |
| Celery task execution | ⏳ | TBD |

## Известные ограничения

1. **Требуется PostgreSQL** - Тесты используют test database, которая создаётся в PostgreSQL
2. **Mock для Telegram API** - Внешние запросы к Telegram API мокаются
3. **Async тесты** - BotManager тесты требуют правильного async context

## Следующие шаги

1. **Интеграционные тесты** - Тест полного цикла: webhook → Celery → bot response
2. **Load тесты** - Тест на 1000+ сообщений через webhook
3. **E2E тесты** - Тест с реальным Telegram ботом

## Отладка тестов

### Просмотр output

```bash
# С print statements
uv run python manage.py test apps.bots.tests.test_webhook_api --verbosity=2

# С pdb debugger
uv run python manage.py test apps.bots.tests.test_webhook_api --debug-mode
```

### Очистка test database

```bash
# Удалить test database
uv run python manage.py test --keepdb false

# Пересоздать test database
docker-compose exec postgres psql -U postgres -c "DROP DATABASE IF EXISTS test_bot_factory_db;"
```

## Результаты тестов

Ожидаемые результаты:
- **WebhookAPITest**: 12 тестов
- **DeliveryModeSerializerTest**: 4 теста
- **DeliveryModeWebhookTest**: 4 теста

Всего: **20 тестов** для webhook миграции.

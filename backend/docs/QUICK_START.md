# Bot Factory - Quick Start Guide

## Быстрый старт

### 1. Установка зависимостей

**Backend:**
```bash
cd backend
source .venv/bin/activate
pip install -r requirements/base.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### 2. Настройка окружения

Создайте `.env` файл в `backend/`:
```bash
SECRET_KEY=your-secret-key
DEBUG=True
GEMINI_API_KEY=your-gemini-api-key
DB_NAME=bot_factory_db
DB_USER=postgres
DB_PASSWORD=postgres
```

### 3. Запуск сервисов

**Backend (порт 8000):**
```bash
cd backend
source .venv/bin/activate
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

**Frontend (порт 3000):**
```bash
cd frontend
npm run dev
```

**Bot:**
```bash
cd bot
source .venv/bin/activate
PYTHONPATH=/path/to/bot-factory python main.py
```

### 4. Доступ к документации

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

## Основные функции

### Создание бота

1. Откройте http://localhost:3000
2. Войдите или зарегистрируйтесь
3. Создайте нового бота
4. Настройте:
   - **General**: Имя, описание
   - **Model & AI**: Модель, температура, system instruction
   - **Knowledge Base**: Загрузите документы или создайте сниппеты
   - **Integrations**: Добавьте Telegram токен
   - **UI & Buttons**: Настройте клавиатуры и формы

### Создание API ключа

1. Откройте настройки бота
2. Перейдите на вкладку "Integrations"
3. В секции "Public API Keys" нажмите "Create Key"
4. Введите имя ключа
5. **Сохраните ключ** - он показывается только один раз!

### Использование публичного API

```bash
curl -X POST http://localhost:8000/api/v1/public/chat/ \
  -H "X-API-Key: bf_your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello!",
    "session_id": "optional-session-id"
  }'
```

### Тестирование Telegram подключения

1. Получите токен от @BotFather в Telegram
2. Вставьте токен в настройках бота (вкладка "Integrations")
3. Нажмите "Test Connection"
4. Если тест успешен, активируйте бота

## RAG (Retrieval Augmented Generation)

### Как это работает

1. **Загрузка документов:**
   - Загрузите PDF, DOCX или TXT файл
   - Документ автоматически разбивается на chunks
   - Для каждого chunk создаётся embedding

2. **Создание сниппетов:**
   - Создайте текстовый сниппет в Knowledge Base
   - Embedding создаётся автоматически

3. **Использование в ответах:**
   - При генерации ответа ищутся релевантные chunks
   - Найденный контекст добавляется в system instruction
   - Бот использует эту информацию для ответа

### Требования

- **PostgreSQL** с расширением `pgvector`
- **GEMINI_API_KEY** для генерации embeddings

## Troubleshooting

### Токен не сохраняется
- Проверьте формат: `123456789:ABC...`
- Проверьте консоль браузера на ошибки

### RAG не работает
- Убедитесь что используется PostgreSQL (не SQLite)
- Проверьте что GEMINI_API_KEY установлен
- Проверьте что документы обработаны (есть chunks)

### API ключ не работает
- Убедитесь что ключ скопирован полностью
- Проверьте заголовок: `X-API-Key` (не `Authorization`)
- Проверьте что бот активен

### Бот не отвечает
- Проверьте что бот запущен
- Проверьте статус бота в настройках
- Проверьте логи бота

## Полезные ссылки

- [Полная документация API](./README.md)
- [Документация публичного API](./PUBLIC_API.md)
- [Руководство по тестированию](./TESTING.md)
- [Итоги реализации](./IMPLEMENTATION_SUMMARY.md)


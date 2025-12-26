#!/bin/bash
# Мастер-скрипт для запуска всех компонентов Bot Factory
# Использование: ./start_all.sh

set -e

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Получаем корневую директорию проекта
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Bot Factory - Запуск всех сервисов${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Проверка .env файла
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${RED}❌ Файл .env не найден в корне проекта!${NC}"
    echo -e "${YELLOW}Создайте его на основе .env.example${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Файл .env найден${NC}"

# Clear all DB_ environment variables to avoid conflicts
unset DB_ENGINE DB_NAME DB_USER DB_PASSWORD DB_HOST DB_PORT

# Load .env file with explicit export to override any existing variables
set -a  # Automatically export all variables
source "$PROJECT_ROOT/.env"
set +a  # Stop auto-export

# Проверка Docker сервисов (PostgreSQL и Redis)
echo ""
echo -e "${BLUE}Проверка Docker сервисов...${NC}"

if ! docker ps | grep -q "bot-factory-postgres"; then
    echo -e "${YELLOW}⚠ PostgreSQL не запущен. Запускаю Docker services...${NC}"
    cd "$PROJECT_ROOT"
    docker-compose up -d postgres redis
    echo -e "${GREEN}✓ Ожидание готовности PostgreSQL (10 сек)...${NC}"
    sleep 10
else
    echo -e "${GREEN}✓ PostgreSQL уже запущен${NC}"
fi

if ! docker ps | grep -q "bot-factory-redis"; then
    echo -e "${YELLOW}⚠ Redis не запущен. Запускаю...${NC}"
    cd "$PROJECT_ROOT"
    docker-compose up -d redis
else
    echo -e "${GREEN}✓ Redis уже запущен${NC}"
fi

# Проверка и установка зависимостей Backend
echo ""
echo -e "${BLUE}Подготовка Backend...${NC}"
cd "$PROJECT_ROOT/backend"

if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}⚠ Виртуальное окружение не найдено. Создаю...${NC}"
    uv venv
fi

echo -e "${GREEN}✓ Установка/обновление зависимостей Backend...${NC}"
uv pip install -q -r requirements/development.txt || uv pip install -q -e .

# Применение миграций
echo -e "${GREEN}✓ Применение миграций базы данных...${NC}"
# Clear any existing DB environment variables
unset DB_NAME DB_USER DB_PASSWORD DB_HOST DB_PORT DB_ENGINE_
export $(cat "$PROJECT_ROOT/.env" | grep '^DB_' | xargs)
echo "  DB_HOST: $DB_HOST, DB_PORT: $DB_PORT, DB_NAME: $DB_NAME"
uv run python manage.py migrate --noinput

# Создание суперпользователя (если не существует)
echo -e "${GREEN}✓ Проверка суперпользователя...${NC}"
uv run python manage.py shell -c "
from apps.accounts.models import User
if not User.objects.filter(email='${ADMIN_EMAIL:-admin@example.com}').exists():
    User.objects.create_superuser(
        email='${ADMIN_EMAIL:-admin@example.com}',
        password='${ADMIN_PASSWORD:-admin123}',
        name='Admin'
    )
    print('Создан новый суперпользователь')
else:
    print('Суперпользователь уже существует')
" 2>/dev/null || echo "Суперпользователь уже существует"

# Проверка и установка зависимостей Bot
echo ""
echo -e "${BLUE}Подготовка Bot...${NC}"
cd "$PROJECT_ROOT/bot"

if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}⚠ Виртуальное окружение для бота не найдено. Создаю...${NC}"
    uv venv
fi

echo -e "${GREEN}✓ Установка/обновление зависимостей Bot...${NC}"
uv pip install -q -r requirements.txt

# Проверка и установка зависимостей Frontend
echo ""
echo -e "${BLUE}Подготовка Frontend...${NC}"
cd "$PROJECT_ROOT/frontend"

if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠ Node modules не найдены. Устанавливаю...${NC}"
    npm install
else
    echo -e "${GREEN}✓ Node modules уже установлены${NC}"
fi

# Запуск всех сервисов
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Запуск сервисов...${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Создаем директорию для логов
mkdir -p "$PROJECT_ROOT/logs"

# Запуск Backend
echo -e "${GREEN}🚀 Запуск Backend (Django) на порту ${BACKEND_PORT:-8000}...${NC}"
cd "$PROJECT_ROOT/backend"
uv run python manage.py runserver ${BACKEND_PORT:-8000} > "$PROJECT_ROOT/logs/backend.log" 2>&1 &
BACKEND_PID=$!
echo "$BACKEND_PID" > "$PROJECT_ROOT/logs/backend.pid"
echo -e "${GREEN}   PID: $BACKEND_PID${NC}"

# Ждем запуска Backend
sleep 3

# Запуск Frontend
echo -e "${GREEN}🚀 Запуск Frontend (Vite) на порту ${FRONTEND_PORT:-5173}...${NC}"
cd "$PROJECT_ROOT/frontend"
npm run dev > "$PROJECT_ROOT/logs/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "$FRONTEND_PID" > "$PROJECT_ROOT/logs/frontend.pid"
echo -e "${GREEN}   PID: $FRONTEND_PID${NC}"

# Запуск Bot (опционально, если есть настроенные боты)
echo -e "${GREEN}🚀 Запуск Bot Service...${NC}"
cd "$PROJECT_ROOT/bot"
./run_uv.sh > "$PROJECT_ROOT/logs/bot.log" 2>&1 &
BOT_PID=$!
echo "$BOT_PID" > "$PROJECT_ROOT/logs/bot.pid"
echo -e "${GREEN}   PID: $BOT_PID${NC}"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✨ Все сервисы успешно запущены!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}📍 Адреса сервисов:${NC}"
echo -e "   🔹 Backend API:  ${GREEN}http://localhost:${BACKEND_PORT:-8000}${NC}"
echo -e "   🔹 Admin Panel:  ${GREEN}http://localhost:${BACKEND_PORT:-8000}/admin/${NC}"
echo -e "   🔹 Frontend:     ${GREEN}http://localhost:${FRONTEND_PORT:-5173}${NC}"
echo -e "   🔹 API Docs:     ${GREEN}http://localhost:${BACKEND_PORT:-8000}/api/v1/schema/swagger-ui/${NC}"
echo ""
echo -e "${YELLOW}👤 Учетные данные админа:${NC}"
echo -e "   Email:    ${GREEN}${ADMIN_EMAIL:-admin@example.com}${NC}"
echo -e "   Password: ${GREEN}${ADMIN_PASSWORD:-admin123}${NC}"
echo ""
echo -e "${YELLOW}📝 Логи:${NC}"
echo -e "   Backend:  tail -f $PROJECT_ROOT/logs/backend.log"
echo -e "   Frontend: tail -f $PROJECT_ROOT/logs/frontend.log"
echo -e "   Bot:      tail -f $PROJECT_ROOT/logs/bot.log"
echo ""
echo -e "${YELLOW}🛑 Остановка:${NC}"
echo -e "   ./stop_all.sh"
echo ""
echo -e "${GREEN}Нажмите Ctrl+C для остановки мониторинга логов${NC}"
echo ""

# Мониторинг логов (опционально)
# tail -f "$PROJECT_ROOT/logs/backend.log" "$PROJECT_ROOT/logs/frontend.log" "$PROJECT_ROOT/logs/bot.log"

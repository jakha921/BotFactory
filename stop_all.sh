#!/bin/bash
# Скрипт для остановки всех компонентов Bot Factory
# Использование: ./stop_all.sh

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Bot Factory - Остановка сервисов${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Остановка Backend
if [ -f "$PROJECT_ROOT/logs/backend.pid" ]; then
    BACKEND_PID=$(cat "$PROJECT_ROOT/logs/backend.pid")
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}🛑 Остановка Backend (PID: $BACKEND_PID)...${NC}"
        kill $BACKEND_PID
        rm "$PROJECT_ROOT/logs/backend.pid"
        echo -e "${GREEN}✓ Backend остановлен${NC}"
    else
        echo -e "${YELLOW}⚠ Backend уже не запущен${NC}"
        rm "$PROJECT_ROOT/logs/backend.pid"
    fi
else
    echo -e "${YELLOW}⚠ PID файл Backend не найден${NC}"
fi

# Остановка Frontend
if [ -f "$PROJECT_ROOT/logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat "$PROJECT_ROOT/logs/frontend.pid")
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}🛑 Остановка Frontend (PID: $FRONTEND_PID)...${NC}"
        kill $FRONTEND_PID
        rm "$PROJECT_ROOT/logs/frontend.pid"
        echo -e "${GREEN}✓ Frontend остановлен${NC}"
    else
        echo -e "${YELLOW}⚠ Frontend уже не запущен${NC}"
        rm "$PROJECT_ROOT/logs/frontend.pid"
    fi
else
    echo -e "${YELLOW}⚠ PID файл Frontend не найден${NC}"
fi

# Остановка Bot
if [ -f "$PROJECT_ROOT/logs/bot.pid" ]; then
    BOT_PID=$(cat "$PROJECT_ROOT/logs/bot.pid")
    if ps -p $BOT_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}🛑 Остановка Bot (PID: $BOT_PID)...${NC}"
        kill $BOT_PID
        rm "$PROJECT_ROOT/logs/bot.pid"
        echo -e "${GREEN}✓ Bot остановлен${NC}"
    else
        echo -e "${YELLOW}⚠ Bot уже не запущен${NC}"
        rm "$PROJECT_ROOT/logs/bot.pid"
    fi
else
    echo -e "${YELLOW}⚠ PID файл Bot не найден${NC}"
fi

# Дополнительная проверка и остановка всех процессов по именам
echo ""
echo -e "${YELLOW}Проверка оставшихся процессов...${NC}"

# Остановка всех процессов Django
DJANGO_PIDS=$(pgrep -f "manage.py runserver" || true)
if [ -n "$DJANGO_PIDS" ]; then
    echo -e "${YELLOW}🛑 Найдены дополнительные процессы Django: $DJANGO_PIDS${NC}"
    kill $DJANGO_PIDS 2>/dev/null || true
    echo -e "${GREEN}✓ Процессы Django остановлены${NC}"
fi

# Остановка всех процессов bot main.py
BOT_PIDS=$(pgrep -f "bot/main.py\|run_uv.sh" || true)
if [ -n "$BOT_PIDS" ]; then
    echo -e "${YELLOW}🛑 Найдены дополнительные процессы Bot: $BOT_PIDS${NC}"
    kill $BOT_PIDS 2>/dev/null || true
    echo -e "${GREEN}✓ Процессы Bot остановлены${NC}"
fi

# Остановка Vite dev server
VITE_PIDS=$(pgrep -f "vite.*dev" || true)
if [ -n "$VITE_PIDS" ]; then
    echo -e "${YELLOW}🛑 Найдены дополнительные процессы Vite: $VITE_PIDS${NC}"
    kill $VITE_PIDS 2>/dev/null || true
    echo -e "${GREEN}✓ Процессы Vite остановлены${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ Все сервисы остановлены!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Для остановки Docker сервисов (PostgreSQL, Redis):${NC}"
echo -e "   cd $PROJECT_ROOT && docker-compose down"
echo ""

#!/bin/bash
# Script to run bot from project root

set -e

# Get project root directory
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BOT_DIR="$PROJECT_ROOT/bot"

# Change to project root
cd "$PROJECT_ROOT"

# Load environment variables from bot/.env if exists (optional)
if [ -f "$BOT_DIR/.env" ]; then
    export $(cat "$BOT_DIR/.env" | grep -v '^#' | grep -v 'TELEGRAM_BOT_TOKEN' | grep -v 'ADMIN_IDS' | xargs)
fi

# BOT_TOKEN and ADMIN_IDS are now loaded from database, not from .env

# Activate virtual environment if exists
if [ -d "$BOT_DIR/.venv" ]; then
    source "$BOT_DIR/.venv/bin/activate"
elif [ -d "$BOT_DIR/venv" ]; then
    source "$BOT_DIR/venv/bin/activate"
fi

# Install dependencies if needed (use python from venv if activated)
if ! python -c "import aiogram" 2>/dev/null; then
    echo "Warning: aiogram not found. Installing bot dependencies..."
    cd "$BOT_DIR"
    pip install -r requirements.txt
    cd "$PROJECT_ROOT"
fi

# Add project root to PYTHONPATH (CRITICAL for imports)
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Run bot
echo "Starting bot..."
cd "$BOT_DIR"
python main.py


#!/bin/bash
# Script to run bot using uv

set -e

# Get project root directory
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BOT_DIR="$PROJECT_ROOT/bot"

# Change to project root (CRITICAL for imports)
cd "$PROJECT_ROOT"

# Load environment variables from bot/.env if exists (optional)
if [ -f "$BOT_DIR/.env" ]; then
    export $(cat "$BOT_DIR/.env" | grep -v '^#' | grep -v 'TELEGRAM_BOT_TOKEN' | grep -v 'ADMIN_IDS' | xargs)
fi

# BOT_TOKEN and ADMIN_IDS are now loaded from database, not from .env

# Add project root to PYTHONPATH (CRITICAL for imports)
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Check/install dependencies using uv
if [ ! -d "$BOT_DIR/.venv" ]; then
    echo "Creating virtual environment and installing dependencies..."
    cd "$BOT_DIR"
    uv venv
    source .venv/bin/activate
    echo "Installing bot dependencies..."
    uv pip install -r requirements.txt
    cd "$PROJECT_ROOT"
else
    cd "$BOT_DIR"
    if [ -f .venv/bin/activate ]; then
        source .venv/bin/activate
    fi
    # Check if critical dependencies are installed
    if ! python -c "import rest_framework_simplejwt" 2>/dev/null; then
        echo "Installing/updating bot dependencies..."
        uv pip install -r requirements.txt
    fi
    cd "$PROJECT_ROOT"
fi

# Run bot from project root (so Python can find 'bot' module)
echo "Starting bot with uv..."
cd "$PROJECT_ROOT"
python "$BOT_DIR/main.py"


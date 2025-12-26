#!/bin/bash
# Script to run bot using uv

set -e

# Get project root directory (one level up from bot/)
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BOT_DIR="$PROJECT_ROOT/bot"

# Change to project root (CRITICAL for imports)
cd "$PROJECT_ROOT"

# Load environment variables from root .env file
if [ -f "$PROJECT_ROOT/.env" ]; then
    echo "Loading environment from $PROJECT_ROOT/.env"
    export $(cat "$PROJECT_ROOT/.env" | grep -v '^#' | grep -v '^$' | xargs)
fi

# Clear PYTHONPATH first, then add only project root (CRITICAL for imports)
# This prevents system site-packages from polluting the venv
unset PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT"

# Check/install dependencies using uv
if [ ! -d "$BOT_DIR/.venv" ]; then
    echo "Creating virtual environment and installing dependencies..."
    cd "$BOT_DIR"
    uv venv
    uv pip install -r requirements.txt
    cd "$PROJECT_ROOT"
else
    cd "$BOT_DIR"
    # Check if critical dependencies are installed
    if ! .venv/bin/python -c "import aiogram" 2>/dev/null; then
        echo "Installing/updating bot dependencies..."
        uv pip install -r requirements.txt
    fi
    cd "$PROJECT_ROOT"
fi

# Run bot from project root using venv python directly
echo "Starting bot with uv..."
cd "$PROJECT_ROOT"
"$BOT_DIR/.venv/bin/python" "$BOT_DIR/main.py"

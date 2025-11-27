#!/bin/bash
# Setup script for bot - creates venv and installs dependencies

set -e

# Get project root directory
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BOT_DIR="$PROJECT_ROOT/bot"

echo "Setting up bot environment..."

# Change to bot directory
cd "$BOT_DIR"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ] && [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv .venv
fi

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing bot dependencies..."
pip install -r requirements.txt

echo "✅ Bot environment setup complete!"
echo ""
echo "To activate the virtual environment, run:"
if [ -d ".venv" ]; then
    echo "  source bot/.venv/bin/activate"
else
    echo "  source bot/venv/bin/activate"
fi
echo ""
echo "To run the bot, use:"
echo "  ./bot/run.sh"
echo "  or"
echo "  ./bot/run_bot.sh"



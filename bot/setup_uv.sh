#!/bin/bash
# Setup script for bot using uv

set -e

# Get project root directory
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BOT_DIR="$PROJECT_ROOT/bot"

echo "Setting up bot environment with uv..."

# Change to bot directory
cd "$BOT_DIR"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed!"
    echo "Please install uv first: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
fi

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "Virtual environment activated: .venv"
else
    echo "Error: Virtual environment not found. Please create it manually."
    exit 1
fi

# Install dependencies using uv (fast installation)
echo "Installing dependencies with uv..."
uv pip install -r requirements.txt

echo "✅ Bot environment setup complete with uv!"
echo ""
echo "To run the bot, use:"
echo "  cd bot"
echo "  source .venv/bin/activate"
echo "  export PYTHONPATH=\"\$(cd .. && pwd):\$PYTHONPATH\""
echo "  python main.py"
echo ""
echo "Or use the script (recommended):"
echo "  ./run_uv.sh"


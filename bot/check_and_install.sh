#!/bin/bash
# Script to check and install all bot dependencies

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BOT_DIR="$PROJECT_ROOT/bot"

echo "Checking bot dependencies..."

cd "$BOT_DIR"

# Create venv if doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
fi

# Activate venv
if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Error: Cannot activate virtual environment"
    exit 1
fi

# Install/update dependencies
echo "Installing/updating dependencies..."
uv pip install --upgrade -r requirements.txt

echo ""
echo "✅ All dependencies installed successfully!"
echo ""
echo "Checking critical imports..."

# Check critical dependencies
python -c "import aiogram; print('✅ aiogram')" || echo "❌ aiogram"
python -c "import django; print('✅ Django')" || echo "❌ Django"
python -c "import rest_framework; print('✅ DRF')" || echo "❌ DRF"
python -c "import rest_framework_simplejwt; print('✅ DRF SimpleJWT')" || echo "❌ DRF SimpleJWT"
python -c "import unfold; print('✅ django-unfold')" || echo "❌ django-unfold"

echo ""
echo "Done! You can now run the bot using:"
echo "  ./bot/run_uv.sh"



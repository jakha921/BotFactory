#!/bin/bash
# Script to run Django backend with uv

set -e

# Change to backend directory
cd "$(dirname "$0")"

# Activate uv environment if not already activated
if [ -z "$VIRTUAL_ENV" ]; then
    # Try to find .venv or create it
    if [ ! -d ".venv" ]; then
        echo "Creating virtual environment with uv..."
        uv venv
    fi
    
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Install dependencies (check if needed)
if [ ! -f ".venv/.installed" ] || [ requirements/base.txt -nt .venv/.installed ]; then
    echo "Installing/updating dependencies with uv..."
    uv pip install -r requirements/base.txt
    touch .venv/.installed
fi

# Run Django management command
python manage.py "$@"


.PHONY: help install migrate runserver shell test clean

help:
	@echo "Bot Factory Backend - Makefile Commands"
	@echo ""
	@echo "  make install     - Install dependencies with uv"
	@echo "  make migrate     - Run database migrations"
	@echo "  make runserver   - Run development server"
	@echo "  make shell       - Open Django shell"
	@echo "  make superuser   - Create superuser"
	@echo "  make test        - Run tests"
	@echo "  make clean       - Clean Python cache files"
	@echo ""

install:
	@echo "Installing dependencies with uv..."
	@if [ ! -d ".venv" ]; then \
		uv venv; \
	fi
	@source .venv/bin/activate && uv pip install -r requirements/base.txt

migrate:
	@echo "Running migrations..."
	@source .venv/bin/activate && python manage.py migrate

runserver:
	@echo "Starting development server..."
	@source .venv/bin/activate && python manage.py runserver 0.0.0.0:8000

shell:
	@source .venv/bin/activate && python manage.py shell

superuser:
	@source .venv/bin/activate && python manage.py createsuperuser

test:
	@source .venv/bin/activate && python manage.py test

clean:
	@echo "Cleaning Python cache files..."
	@find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@echo "Done!"


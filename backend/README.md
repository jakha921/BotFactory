# Bot Factory Backend

Django REST Framework backend for Bot Factory platform.

## Setup with uv

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager

### Installation

1. **Install dependencies:**
   ```bash
   cd backend
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -r requirements/base.txt
   ```
   
   **Or use uv sync (if you have uv.lock):**
   ```bash
   uv sync
   ```

2. **Setup environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

4. **Create superuser:**
   ```bash
   python manage.py createsuperuser
   ```

5. **Run development server:**
   ```bash
   # Using script
   ./runserver.sh
   
   # Or directly
   python manage.py runserver 0.0.0.0:8000
   ```

## Using uv scripts

### Run any Django management command:
```bash
./run.sh <command>
# Examples:
./run.sh migrate
./run.sh createsuperuser
./run.sh shell
./run.sh test
```

### Run development server:
```bash
./runserver.sh
```

## Alternative: Direct uv usage

You can also use uv directly:

```bash
# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows

# Install dependencies
uv pip install -r requirements/base.txt

# Run Django commands
python manage.py migrate
python manage.py runserver
python manage.py createsuperuser
```

Or with `uv run` (without activation):

```bash
# Install dependencies first (one time)
uv pip install -r requirements/base.txt

# Run Django commands directly
uv run python manage.py migrate
uv run python manage.py runserver
```

## Quick Start (All-in-one)

```bash
# Linux/macOS - Using scripts
cd backend
./runserver.sh

# Linux/macOS - Using Makefile
make install
make migrate
make runserver

# Windows PowerShell
cd backend
.\runserver.ps1
```

## Project Structure

```
backend/
├── apps/              # Django applications
├── bot_factory/       # Django project settings
├── core/              # Shared utilities
├── services/          # External service integrations
├── requirements/      # Legacy requirements files (for reference)
├── pyproject.toml     # uv project configuration
├── manage.py          # Django management script
└── run.sh             # Helper script for Django commands
```

## Development

### Add new dependency:
```bash
uv add <package-name>
```

### Add development dependency:
```bash
uv add --dev <package-name>
```

### Update dependencies:
```bash
uv sync
```

## API Endpoints

- API Base: `http://localhost:8000/api/v1/`
- Admin: `http://localhost:8000/admin/`

## Environment Variables

See `.env.example` for required environment variables.


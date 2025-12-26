#!/bin/bash
# PostgreSQL setup script for Bot Factory
# This script creates the database and enables pgvector extension

set -e

# Configuration (can be overridden with environment variables)
DB_NAME="${DB_NAME:-bot_factory_db}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

echo "=== Bot Factory PostgreSQL Setup ==="
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo "Host: $DB_HOST:$DB_PORT"
echo ""

# Check if PostgreSQL is running
if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" > /dev/null 2>&1; then
    echo "ERROR: PostgreSQL is not running on $DB_HOST:$DB_PORT"
    echo "Please start PostgreSQL first:"
    echo "  brew services start postgresql@14"
    exit 1
fi

echo "✓ PostgreSQL is running"

# Check if pgvector extension is available
if ! psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "SELECT * FROM pg_available_extensions WHERE name = 'vector';" | grep -q "vector"; then
    echo ""
    echo "WARNING: pgvector extension not found!"
    echo "To install pgvector on macOS:"
    echo "  brew install pgvector"
    echo ""
    echo "Then restart PostgreSQL:"
    echo "  brew services restart postgresql@14"
    echo ""
    echo "Continuing without pgvector (vector fields will not work)..."
fi

# Create database if not exists
echo ""
echo "Creating database '$DB_NAME'..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || echo "Database already exists"

# Enable pgvector extension
echo "Enabling pgvector extension..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null || echo "pgvector extension not available"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Add these to your .env file:"
echo ""
echo "DB_NAME=$DB_NAME"
echo "DB_USER=$DB_USER"
echo "DB_PASSWORD=$DB_PASSWORD"
echo "DB_HOST=$DB_HOST"
echo "DB_PORT=$DB_PORT"
echo ""
echo "Then run migrations:"
echo "  cd backend && python manage.py migrate"


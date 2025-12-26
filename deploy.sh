#!/bin/bash
# Production deployment script for Bot Factory

set -e

echo "🚀 Deploying Bot Factory to Production..."

# Load environment variables
if [ -f .env.prod ]; then
    export $(cat .env.prod | grep -v '^#' | xargs)
fi

# Build and start services
echo "📦 Building Docker images..."
docker-compose -f docker-compose.prod.yml build

echo "🔄 Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for PostgreSQL
echo "⏳ Waiting for PostgreSQL..."
sleep 10

# Run migrations
echo "🔧 Running migrations..."
docker-compose -f docker-compose.prod.yml exec -T web python manage.py migrate

# Collect static files
echo "📁 Collecting static files..."
docker-compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

# Create superuser (if needed)
echo "👤 Creating superuser..."
docker-compose -f docker-compose.prod.yml exec -T web python manage.py shell << EOF
from apps.accounts.models import User
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        email='${ADMIN_EMAIL:-admin@botfactory.com}',
        password='${ADMIN_PASSWORD:-changeme123}',
        name='Admin'
    )
    print('Superuser created!')
else:
    print('Superuser already exists')
EOF

echo "✅ Deployment complete!"
echo ""
echo "Access your application at: http://localhost"
echo "Admin panel: http://localhost/admin"
echo ""
echo "View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "Stop services: docker-compose -f docker-compose.prod.yml down"

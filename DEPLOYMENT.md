# Bot Factory - Production Deployment Guide

## Prerequisites

- Docker & Docker Compose installed
- Domain name pointing to your server
- SSL certificates (optional, can use Certbot)

## Quick Start

1. **Clone repository:**
```bash
git clone https://github.com/your-org/bot-factory.git
cd bot-factory
```

2. **Configure environment:**
```bash
cp .env.prod.example .env.prod
nano .env.prod  # Update all values
```

3. **Deploy:**
```bash
chmod +x deploy.sh
./deploy.sh
```

4. **Setup SSL (optional):**
```bash
# Request certificate
docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot --webroot-path=/var/www/certbot \
  -d your-domain.com -d www.your-domain.com

# Update nginx/conf.d/default.conf to enable HTTPS
# Restart nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

## Architecture

```
┌──────────┐
│  Nginx   │ :80, :443 (reverse proxy)
└────┬─────┘
     │
┌────┴──────────────────────────────────┐
│                                       │
│  ┌──────┐  ┌────────┐  ┌──────────┐  │
│  │ Web  │  │ Celery │  │  Celery  │  │
│  │      │  │ Worker │  │   Beat   │  │
│  └──┬───┘  └───┬────┘  └────┬─────┘  │
│     │          │            │        │
│     └──────────┴────────────┘        │
│                │                     │
├────────────────┼─────────────────────┤
│     ┌──────────┴────────┐            │
│     │                   │            │
│  ┌──▼──────┐      ┌─────▼────┐      │
│  │ PostgreSQL│      │  Redis   │      │
│  │ +pgvector │      │          │      │
│  └───────────┘      └──────────┘      │
└───────────────────────────────────────┘
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| nginx | 80, 443 | Reverse proxy, SSL termination |
| web | 8000 | Django API (gunicorn) |
| celery-worker | - | Async task processing |
| celery-beat | - | Periodic tasks (analytics) |
| postgres | 5432 | Database + pgvector |
| redis | 6379 | Celery broker + cache |

## Management Commands

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart service
docker-compose -f docker-compose.prod.yml restart web

# Django shell
docker-compose -f docker-compose.prod.yml exec web python manage.py shell

# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Create superuser
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Backup database
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U botfactory_user botfactory > backup.sql

# Restore database
cat backup.sql | docker-compose -f docker-compose.prod.yml exec -T postgres psql -U botfactory_user botfactory
```

## Monitoring

### Health Checks
- Django: `http://your-domain.com/admin/`
- Celery: Check logs for task processing

### Logs Location
- Django: `backend/logs/django.log`
- Containers: `docker-compose -f docker-compose.prod.yml logs`

## Scaling

### Horizontal Scaling (Multiple Servers)

1. **Separate services:**
```yaml
# On server 1 (web only)
docker-compose -f docker-compose.prod.yml up -d web nginx

# On server 2 (workers only)
docker-compose -f docker-compose.prod.yml up -d celery-worker celery-beat
```

2. **Update DATABASE_URL and REDIS_URL** to point to shared instances

### Vertical Scaling

Increase worker concurrency:
```bash
# In docker-compose.prod.yml
celery-worker:
  command: celery -A bot_factory worker -l info -c 8  # 4 → 8
```

## Troubleshooting

### Webhook not working
1. Check domain is accessible: `curl https://your-domain.com/api/telegram/webhook/test/`
2. Register webhook: See admin or BotService.register_webhook()

### Celery tasks not running
```bash
# Check worker is running
docker-compose -f docker-compose.prod.yml ps celery-worker

# Check logs
docker-compose -f docker-compose.prod.yml logs celery-worker

# Restart worker
docker-compose -f docker-compose.prod.yml restart celery-worker
```

### Database connection errors
```bash
# Check PostgreSQL is running
docker-compose -f docker-compose.prod.yml ps postgres

# Check connection
docker-compose -f docker-compose.prod.yml exec web python manage.py dbshell
```

## Security Checklist

- [ ] Change all default passwords in `.env.prod`
- [ ] Set strong `SECRET_KEY`
- [ ] Enable SSL/HTTPS
- [ ] Configure firewall (allow only 80, 443)
- [ ] Set up regular database backups
- [ ] Enable Django's security settings
- [ ] Review `ALLOWED_HOSTS`
- [ ] Configure email for error notifications

## Updates

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
```

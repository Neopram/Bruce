# Deployment Guide

## Prerequisites

Before deploying BruceWayneV1, ensure the following are available on the target system:

- **Docker** 24.0+ and **Docker Compose** v2.20+
- **Minimum hardware**: 4 CPU cores, 8 GB RAM, 50 GB disk
- **Recommended hardware**: 8 CPU cores, 16 GB RAM, 100 GB SSD
- **Domain name** with DNS configured (for TLS)
- **TLS certificate** (Let's Encrypt or commercial)
- **Ports 80 and 443** open for inbound traffic

---

## Docker Deployment

### 1. Clone and Configure

```bash
# Clone the repository
git clone https://github.com/your-org/BruceWayneV1.git
cd BruceWayneV1

# Create the environment file from the example
cp .env.example .env
```

### 2. Set Environment Variables

Edit the `.env` file with production values:

```bash
# Database
POSTGRES_PASSWORD=<strong-random-password>
DATABASE_URL=postgresql://bruce:<password>@postgres:5432/brucewayne

# Redis
REDIS_URL=redis://redis:6379/0

# Authentication
JWT_SECRET=<strong-random-secret-min-64-chars>

# AI Keys
DEEPSEEK_API_KEY=<your-api-key>

# Application
ENVIRONMENT=production
LOG_LEVEL=info
CORS_ORIGINS=https://yourdomain.com
```

Generate strong secrets:

```bash
openssl rand -hex 32    # For JWT_SECRET
openssl rand -hex 24    # For POSTGRES_PASSWORD
```

### 3. Configure Nginx

Place your TLS certificate and key:

```bash
mkdir -p infrastructure/nginx/ssl
cp /path/to/fullchain.pem infrastructure/nginx/ssl/
cp /path/to/privkey.pem infrastructure/nginx/ssl/
```

Verify the Nginx configuration at `infrastructure/nginx/nginx.conf` matches your domain and certificate paths.

### 4. Build and Start

```bash
# Build all images
docker compose -f docker-compose.prod.yml build

# Start services in detached mode
docker compose -f docker-compose.prod.yml up -d

# Verify all services are running
docker compose -f docker-compose.prod.yml ps
```

### 5. Verify Deployment

```bash
# Check health endpoint
curl -s http://localhost/health | python -m json.tool

# Check logs for errors
docker compose -f docker-compose.prod.yml logs --tail=50 backend
docker compose -f docker-compose.prod.yml logs --tail=50 frontend

# Monitor all services
docker compose -f docker-compose.prod.yml logs -f
```

---

## Environment Configuration

### Required Variables

| Variable            | Description                       | Example                              |
|---------------------|-----------------------------------|--------------------------------------|
| `POSTGRES_PASSWORD` | Database password                 | (generated secret)                   |
| `JWT_SECRET`        | Token signing key                 | (generated secret)                   |
| `DEEPSEEK_API_KEY`  | DeepSeek API key                  | `sk-...`                             |

### Optional Variables

| Variable            | Description                       | Default                              |
|---------------------|-----------------------------------|--------------------------------------|
| `ENVIRONMENT`       | Runtime environment               | `production`                         |
| `LOG_LEVEL`         | Log verbosity                     | `info`                               |
| `CORS_ORIGINS`      | Allowed CORS origins              | `*`                                  |
| `WORKERS`           | Uvicorn worker count              | `4`                                  |

---

## Database Setup

### Initial Setup

The PostgreSQL container automatically creates the database on first startup using the `POSTGRES_DB` environment variable.

### Running Migrations

```bash
# Execute migrations inside the backend container
docker compose -f docker-compose.prod.yml exec backend \
    python -m alembic upgrade head
```

### Manual Database Access

```bash
# Connect to the database
docker compose -f docker-compose.prod.yml exec postgres \
    psql -U bruce -d brucewayne
```

### Creating a Backup

```bash
# Dump the database
docker compose -f docker-compose.prod.yml exec postgres \
    pg_dump -U bruce brucewayne > backup_$(date +%Y%m%d_%H%M%S).sql
```

---

## Monitoring Setup

### Health Checks

The application provides a `/health` endpoint that returns the status of all subsystems. Configure your monitoring tool to poll this endpoint:

```bash
# Example: simple cron-based check
*/5 * * * * curl -sf http://localhost/health > /dev/null || echo "BruceWayne health check failed" | mail -s "Alert" admin@example.com
```

### Docker Metrics

Monitor container resource usage:

```bash
# Real-time resource usage
docker stats bruce-backend bruce-frontend bruce-postgres bruce-redis bruce-nginx

# Check container health status
docker inspect --format='{{.State.Health.Status}}' bruce-backend
```

### Log Aggregation

Docker logs are configured with JSON file driver and rotation. To integrate with an external logging system:

```bash
# Stream logs to a file for ingestion
docker compose -f docker-compose.prod.yml logs -f --no-color > /var/log/brucewayne/all.log &

# Or configure Docker daemon for syslog/fluentd driver globally
```

### Recommended Monitoring Stack

For production, consider deploying:

1. **Prometheus** -- Scrape the `/health` endpoint and Docker metrics.
2. **Grafana** -- Dashboard visualization for system metrics.
3. **Loki** -- Log aggregation from Docker containers.
4. **Alertmanager** -- Alerts for health check failures, resource thresholds.

---

## Backup Strategy

### Database Backups

Schedule automated backups using cron:

```bash
# Add to crontab: daily backup at 2:00 AM
0 2 * * * /opt/brucewayne/scripts/backup-db.sh
```

Example backup script:

```bash
#!/bin/bash
BACKUP_DIR="/backups/brucewayne/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

docker compose -f /opt/brucewayne/docker-compose.prod.yml exec -T postgres \
    pg_dump -U bruce brucewayne | gzip > "$BACKUP_DIR/backup_$TIMESTAMP.sql.gz"

# Keep only the last 30 days of backups
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete
```

### Redis Backups

Redis is configured with AOF persistence. The data volume persists across container restarts. For explicit snapshots:

```bash
# Trigger a Redis snapshot
docker compose -f docker-compose.prod.yml exec redis redis-cli BGSAVE
```

### Volume Backups

Back up Docker volumes for full disaster recovery:

```bash
# List volumes
docker volume ls | grep bruce

# Back up a volume
docker run --rm -v brucewaynev1_postgres-data:/data -v /backups:/backup \
    alpine tar czf /backup/postgres-volume-$(date +%Y%m%d).tar.gz /data
```

### Recovery Procedure

1. Stop services: `docker compose -f docker-compose.prod.yml down`
2. Restore the database volume from backup.
3. Restore the Redis volume if needed.
4. Start services: `docker compose -f docker-compose.prod.yml up -d`
5. Verify with health check: `curl http://localhost/health`

---

## Updating the Application

```bash
# Pull latest code
git pull origin main

# Rebuild and restart with zero downtime
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d --no-deps backend frontend

# Run any new migrations
docker compose -f docker-compose.prod.yml exec backend \
    python -m alembic upgrade head

# Verify
curl -s http://localhost/health
```

---

## Troubleshooting

### Common Issues

**Backend fails to start:**
- Check database connectivity: `docker compose exec backend python -c "import psycopg2; psycopg2.connect('$DATABASE_URL')"`
- Review logs: `docker compose logs backend`

**Frontend build fails:**
- Ensure `NEXT_PUBLIC_API_URL` is set correctly in the environment.
- Check Node memory: increase with `NODE_OPTIONS=--max-old-space-size=4096`

**Database connection refused:**
- Verify PostgreSQL is healthy: `docker compose ps postgres`
- Check the `POSTGRES_PASSWORD` matches between services.

**Redis connection errors:**
- Verify Redis is healthy: `docker compose exec redis redis-cli ping`
- Check memory limits in the compose file.

# Cookie Production Deployment Guide

This guide covers deploying Cookie to production environments using the official Docker image.

## Table of Contents

- [Quick Start](#quick-start)
- [Architecture Overview](#architecture-overview)
- [Docker Image](#docker-image)
- [Configuration](#configuration)
- [Deployment Options](#deployment-options)
- [Reverse Proxy Setup](#reverse-proxy-setup)
- [Backup & Restore](#backup--restore)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

```bash
# Pull and run with persistent data
docker run -d \
  --name cookie \
  -p 80:80 \
  -v cookie-data:/app/data \
  mndeaves/cookie:latest
```

The app will be available at `http://localhost`.

For network access from other devices, use your machine's IP address (e.g., `http://192.168.1.100`).

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                       Production Container                           │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                         nginx (port 80)                         │ │
│  │                                                                 │ │
│  │  /api/, /admin/, /legacy/  ───►  gunicorn (127.0.0.1:8000)      │ │
│  │  /static/                  ───►  /app/staticfiles/              │ │
│  │  /media/                   ───►  /app/data/media/               │ │
│  │  /                         ───►  React SPA (/app/frontend/dist/)│ │
│  │                                                                 │ │
│  │  Browser Detection: iOS <11, IE, Edge Legacy ───► /legacy/      │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                              │                                       │
│                              ▼                                       │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐       │
│  │   Gunicorn  │───▶│   Django    │───▶│  SQLite + WAL Mode  │       │
│  │  (2 workers │    │  (Python    │    │  (/app/data/db)     │       │
│  │  4 threads) │    │   3.12)     │    └─────────────────────┘       │
│  └─────────────┘    └─────────────┘                                  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
         │
         ▼ Port 80
      Internet / LAN

Optional: Add reverse proxy (Caddy, Traefik) for SSL/TLS
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Web Server** | nginx | Routing, static files, browser detection |
| **Runtime** | Python 3.12-slim | Minimal base image |
| **Framework** | Django 5.x | Web framework |
| **API** | Django Ninja | Fast async API endpoints |
| **WSGI Server** | Gunicorn 23.x | Production-grade Python server |
| **Database** | SQLite + WAL | Embedded database with concurrent reads |
| **Frontend** | React + TypeScript | Single-page application |
| **Legacy Frontend** | ES5 JavaScript | iOS 9+ compatibility |

### Why nginx in the Container?

The production container includes nginx for:

- **Static file serving** with proper cache headers (1-year for hashed assets)
- **Browser detection** to automatically redirect legacy browsers (iOS <11, IE, Edge Legacy) to `/legacy/`
- **Dev/prod parity** - both environments use nginx for routing
- **Efficient proxying** to gunicorn for Django requests

This single-container approach simplifies deployment while maintaining production-grade performance.

---

## Docker Image

### Image Details

| Property | Value |
|----------|-------|
| **Registry** | Docker Hub |
| **Repository** | `mndeaves/cookie` |
| **Architectures** | `linux/amd64`, `linux/arm64` |
| **Base Image** | `python:3.12-slim` |
| **Exposed Port** | `80` (nginx) |
| **Image Size** | ~420MB |
| **Processes** | nginx (foreground) + gunicorn (background) |

### Tags

| Tag | Description |
|-----|-------------|
| `latest` | Latest stable release from main/master branch |
| `<sha>` | Specific commit (e.g., `abc1234`) |

### Multi-Stage Build

The Dockerfile uses a 3-stage build for minimal image size:

1. **frontend-builder** (node:20-alpine): Compiles React/TypeScript to static assets
2. **python-deps** (python:3.12-slim): Installs Python dependencies with build tools
3. **production** (python:3.12-slim): Final minimal image with only runtime dependencies

### Security Features

- ✅ Non-root user (`app`, UID 1000)
- ✅ No build tools in final image
- ✅ No test files or dev dependencies
- ✅ Read-only filesystem compatible
- ✅ Health check endpoint for orchestrators

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable debug mode (never in production) |
| `SECRET_KEY` | Auto-generated | Django secret key (persisted to `/app/data/.secret_key`) |
| `ALLOWED_HOSTS` | `*` | Comma-separated list of allowed hostnames |
| `CSRF_TRUSTED_ORIGINS` | (empty) | Full URLs for CSRF protection (e.g., `https://cookie.example.com`) |
| `DATABASE_PATH` | `/app/data/db.sqlite3` | Path to SQLite database |
| `DATA_DIR` | `/app/data` | Base directory for persistent data |
| `GUNICORN_WORKERS` | `2` | Number of Gunicorn worker processes |
| `GUNICORN_THREADS` | `4` | Threads per worker |

AI features (OpenRouter API key) are configured through the Settings UI, not environment variables.

### Volume Mounts

| Container Path | Purpose | Required |
|----------------|---------|----------|
| `/app/data` | Database, media uploads, secret key | **Yes** |

**Important**: Always mount `/app/data` as a volume for data persistence.

---

## Deployment Options

### Option 1: Docker Run (Simplest)

```bash
# Run container on port 80
docker run -d \
  --name cookie \
  --restart unless-stopped \
  -p 80:80 \
  -v cookie-data:/app/data \
  mndeaves/cookie:latest
```

For custom domain with SSL (via reverse proxy):

```bash
docker run -d \
  --name cookie \
  --restart unless-stopped \
  -p 8080:80 \
  -v cookie-data:/app/data \
  -e ALLOWED_HOSTS=cookie.example.com \
  -e CSRF_TRUSTED_ORIGINS=https://cookie.example.com \
  mndeaves/cookie:latest
```

### Option 2: Docker Compose (Recommended)

Create `docker-compose.prod.yml`:

```yaml
services:
  cookie:
    image: mndeaves/cookie:latest
    container_name: cookie
    restart: unless-stopped
    ports:
      - "80:80"
    volumes:
      - cookie-data:/app/data
    environment:
      - ALLOWED_HOSTS=*
      # Optional: AI features
      # - OPENROUTER_API_KEY=sk-or-...
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/api/system/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

volumes:
  cookie-data:
```

Run with:

```bash
docker compose -f docker-compose.prod.yml up -d
```

Or use the helper script:

```bash
bin/prod up      # Start
bin/prod logs    # View logs
bin/prod update  # Pull latest and restart
```

### Option 3: Docker Compose with Caddy (SSL)

```yaml
services:
  cookie:
    image: mndeaves/cookie:latest
    restart: unless-stopped
    volumes:
      - cookie-data:/app/data
    environment:
      - ALLOWED_HOSTS=cookie.example.com
      - CSRF_TRUSTED_ORIGINS=https://cookie.example.com
    expose:
      - "80"

  caddy:
    image: caddy:2-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy-data:/data
      - caddy-config:/config

volumes:
  cookie-data:
  caddy-data:
  caddy-config:
```

Create `Caddyfile`:

```
cookie.example.com {
    reverse_proxy cookie:80
}
```

### Option 4: Kubernetes / Helm

Basic Kubernetes deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cookie
spec:
  replicas: 1  # SQLite doesn't support multiple replicas
  selector:
    matchLabels:
      app: cookie
  template:
    metadata:
      labels:
        app: cookie
    spec:
      containers:
      - name: cookie
        image: mndeaves/cookie:latest
        ports:
        - containerPort: 80
        env:
        - name: ALLOWED_HOSTS
          value: "cookie.example.com"
        - name: CSRF_TRUSTED_ORIGINS
          value: "https://cookie.example.com"
        volumeMounts:
        - name: data
          mountPath: /app/data
        livenessProbe:
          httpGet:
            path: /api/system/health/
            port: 80
          initialDelaySeconds: 15
          periodSeconds: 30
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: cookie-data
---
apiVersion: v1
kind: Service
metadata:
  name: cookie
spec:
  selector:
    app: cookie
  ports:
  - port: 80
    targetPort: 80
```

**Note**: SQLite with WAL mode works well for single-replica deployments. For multi-replica, you'd need PostgreSQL.

---

## Reverse Proxy Setup

Since the container already includes nginx on port 80, you typically don't need an additional reverse proxy for basic deployments. However, for SSL/TLS termination, you can add one:

### Nginx (External)

```nginx
upstream cookie {
    server 127.0.0.1:8080;  # Map container to 8080 to avoid conflict
}

server {
    listen 80;
    server_name cookie.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name cookie.example.com;

    ssl_certificate /etc/letsencrypt/live/cookie.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cookie.example.com/privkey.pem;

    location / {
        proxy_pass http://cookie;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    client_max_body_size 10M;
}
```

### Caddy (Automatic SSL)

```
cookie.example.com {
    reverse_proxy localhost:8080

    header {
        X-Frame-Options "SAMEORIGIN"
        X-Content-Type-Options "nosniff"
    }
}
```

### Traefik (Docker Labels)

```yaml
services:
  cookie:
    image: mndeaves/cookie:latest
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.cookie.rule=Host(`cookie.example.com`)"
      - "traefik.http.routers.cookie.entrypoints=websecure"
      - "traefik.http.routers.cookie.tls.certresolver=letsencrypt"
      - "traefik.http.services.cookie.loadbalancer.server.port=80"
```

---

## Backup & Restore

### Backup

The `/app/data` directory contains all persistent data:

```bash
# Stop container (recommended for consistency)
docker stop cookie

# Backup data volume
docker run --rm \
  -v cookie-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/cookie-backup-$(date +%Y%m%d).tar.gz -C /data .

# Restart container
docker start cookie
```

**What's backed up:**
- `db.sqlite3` - All recipes, profiles, collections, favorites
- `media/` - Cached recipe images
- `.secret_key` - Django secret key

### Restore

```bash
# Stop container
docker stop cookie

# Restore from backup
docker run --rm \
  -v cookie-data:/data \
  -v $(pwd):/backup \
  alpine sh -c "rm -rf /data/* && tar xzf /backup/cookie-backup-20240115.tar.gz -C /data"

# Start container
docker start cookie
```

### Automated Backups (Cron)

```bash
# /etc/cron.daily/cookie-backup
#!/bin/bash
BACKUP_DIR=/var/backups/cookie
mkdir -p $BACKUP_DIR
docker run --rm \
  -v cookie-data:/data:ro \
  -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/cookie-$(date +%Y%m%d).tar.gz -C /data .
# Keep last 7 days
find $BACKUP_DIR -name "cookie-*.tar.gz" -mtime +7 -delete
```

---

## Monitoring

### Health Check Endpoint

```bash
curl http://localhost/api/system/health/
# {"status": "healthy", "database": "ok"}
```

### Docker Health Status

```bash
docker inspect --format='{{.State.Health.Status}}' cookie
# healthy
```

### Logs

```bash
# Follow logs
docker logs -f cookie

# Last 100 lines
docker logs --tail 100 cookie
```

### Metrics to Monitor

| Metric | Warning | Critical |
|--------|---------|----------|
| Container memory | >400MB | >500MB |
| Database size | >500MB | >1GB |
| Response time (p95) | >500ms | >2000ms |
| Error rate (5xx) | >1% | >5% |

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs cookie

# Common issues:
# 1. Port 80 already in use - change -p 80:80 to -p 8080:80
# 2. Volume permissions - ensure /app/data is writable
```

### Permission Denied on Volume

```bash
# Fix volume permissions (container runs as UID 1000)
docker run --rm -v cookie-data:/data alpine chown -R 1000:1000 /data
```

### Database Locked Errors

SQLite is configured with WAL mode for concurrent reads, but if you see lock errors:

```bash
# Check for stuck transactions
docker exec cookie python manage.py dbshell
sqlite> .timeout 30000
sqlite> PRAGMA busy_timeout;
```

### Static Files Not Loading

```bash
# Re-run collectstatic
docker exec cookie python manage.py collectstatic --noinput
```

### Reset to Fresh State

```bash
# WARNING: This deletes all data
docker stop cookie
docker volume rm cookie-data
docker volume create cookie-data
docker start cookie
```

---

## Updating

Using the helper script:

```bash
bin/prod update  # Pulls latest and restarts
```

Or manually:

```bash
# Pull latest image
docker pull mndeaves/cookie:latest

# Recreate container
docker stop cookie
docker rm cookie
docker run -d \
  --name cookie \
  --restart unless-stopped \
  -p 80:80 \
  -v cookie-data:/app/data \
  mndeaves/cookie:latest
```

Or with Docker Compose:

```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

---

## Security Checklist

Before exposing to the internet:

- [ ] Set `ALLOWED_HOSTS` to your actual domain(s)
- [ ] Set `CSRF_TRUSTED_ORIGINS` to your full URL(s)
- [ ] Use HTTPS (via reverse proxy)
- [ ] Keep Docker and the host OS updated
- [ ] Set up automated backups
- [ ] Monitor logs for unusual activity
- [ ] Consider rate limiting at the reverse proxy level
- [ ] Consider a security audit / penetration test before public launch

---

## Support

- **GitHub Issues**: [github.com/mndeaves/cookie/issues](https://github.com/mndeaves/cookie/issues)
- **Documentation**: [github.com/mndeaves/cookie/docs](https://github.com/mndeaves/cookie/docs)

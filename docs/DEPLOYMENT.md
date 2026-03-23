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
# Create .env with a Postgres password
echo "POSTGRES_PASSWORD=changeme" > .env

# Download production compose file
curl -O https://raw.githubusercontent.com/matthewdeaves/cookie/master/docker-compose.prod.yml

# Start
docker compose -f docker-compose.prod.yml --env-file .env up -d
```

The app will be available at `http://localhost`.

For network access from other devices, set `ALLOWED_HOSTS` in your `.env`:

```bash
POSTGRES_PASSWORD=changeme
ALLOWED_HOSTS=192.168.1.100,localhost
```

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Web Container                                  │
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
│  ┌─────────────┐    ┌─────────────┐                                  │
│  │   Gunicorn  │───▶│   Django    │                                  │
│  │  (2 workers │    │  (Python    │                                  │
│  │  4 threads) │    │   3.12)     │                                  │
│  └─────────────┘    └─────────────┘                                  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
         │                              │
         ▼ Port 80                      ▼
      Internet / LAN          ┌──────────────────┐
                              │   PostgreSQL     │
                              │  (db container)  │
                              └──────────────────┘
                                        │
                                        ▼ (optional)
                              ┌──────────────────┐
                              │   OpenRouter AI  │
                              └──────────────────┘
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Web Server** | nginx | Routing, static files, browser detection |
| **Runtime** | Python 3.12-slim | Minimal base image |
| **Framework** | Django 5.x | Web framework |
| **API** | Django Ninja | Fast API endpoints |
| **WSGI Server** | Gunicorn | Production-grade Python server |
| **Database** | PostgreSQL | Relational database |
| **Frontend** | React 19 + TypeScript | Single-page application |
| **Legacy Frontend** | ES5 JavaScript | iOS 9+ compatibility |

---

## Docker Image

### Image Details

| Property | Value |
|----------|-------|
| **Registry** | GitHub Container Registry (ghcr.io) |
| **Repository** | `matthewdeaves/cookie` |
| **Architectures** | `linux/amd64`, `linux/arm64` |
| **Base Image** | `python:3.12-slim` |
| **Exposed Port** | `80` (nginx) |
| **Processes** | nginx (foreground) + gunicorn (background) |

### Tags

| Tag | Description |
|-----|-------------|
| `latest` | Latest stable release from master branch |
| `<version>` | Semantic version (e.g., `1.0.0`) |
| `<sha>` | Specific commit (e.g., `abc1234`) |

### Multi-Stage Build

The Dockerfile uses a 3-stage build for minimal image size:

1. **frontend-builder** (node:20-alpine): Compiles React/TypeScript to static assets
2. **python-deps** (python:3.12-slim): Installs Python dependencies with build tools
3. **production** (python:3.12-slim): Final minimal image with only runtime dependencies

### Security Features

- Non-root user (`app`, UID 1000)
- No build tools in final image
- No test files or dev dependencies
- Health check endpoint for orchestrators

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_PASSWORD` | (required) | Password for the PostgreSQL database |
| `DATABASE_URL` | (set by compose) | PostgreSQL connection string |
| `DEBUG` | `false` | Enable debug mode (never in production) |
| `SECRET_KEY` | Auto-generated | Django secret key |
| `ALLOWED_HOSTS` | `*` | Comma-separated list of allowed hostnames |
| `CSRF_TRUSTED_ORIGINS` | (empty) | Full URLs for CSRF protection (e.g., `https://cookie.example.com`) |
| `GUNICORN_WORKERS` | `2` | Number of Gunicorn worker processes |
| `GUNICORN_THREADS` | `4` | Threads per worker |

AI features (OpenRouter API key) are configured through the Settings UI, not environment variables.

### Docker Volumes

| Volume | Purpose |
|--------|---------|
| `cookie-postgres-data` | PostgreSQL database |
| `cookie-media` | Uploaded/cached recipe images |

---

## Deployment Options

### Option 1: Docker Compose (Recommended)

Use the provided `docker-compose.prod.yml`:

```bash
# Create .env
cat > .env << EOF
POSTGRES_PASSWORD=your-secure-password
ALLOWED_HOSTS=cookie.example.com,localhost
CSRF_TRUSTED_ORIGINS=https://cookie.example.com
EOF

# Start
docker compose -f docker-compose.prod.yml --env-file .env up -d
```

Or use the helper script:

```bash
bin/prod up      # Start
bin/prod logs    # View logs
bin/prod update  # Pull latest and restart
```

### Option 2: Docker Compose with Caddy (SSL)

```yaml
services:
  db:
    image: postgres:18-alpine
    restart: unless-stopped
    volumes:
      - cookie-postgres-data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: cookie
      POSTGRES_USER: cookie
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    expose:
      - "5432"

  cookie:
    image: ghcr.io/matthewdeaves/cookie:latest
    restart: unless-stopped
    volumes:
      - cookie-media:/app/data/media
    environment:
      - DATABASE_URL=postgres://cookie:${POSTGRES_PASSWORD}@db:5432/cookie
      - ALLOWED_HOSTS=cookie.example.com
      - CSRF_TRUSTED_ORIGINS=https://cookie.example.com
    depends_on:
      - db
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
  cookie-postgres-data:
  cookie-media:
  caddy-data:
  caddy-config:
```

Create `Caddyfile`:

```
cookie.example.com {
    reverse_proxy cookie:80
}
```

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
    image: ghcr.io/matthewdeaves/cookie:latest
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

Two volumes need backing up:

```bash
# Backup PostgreSQL database
docker compose -f docker-compose.prod.yml exec db \
  pg_dump -U cookie cookie > cookie-db-$(date +%Y%m%d).sql

# Backup media files
docker run --rm \
  -v cookie-media:/data:ro \
  -v $(pwd):/backup \
  alpine tar czf /backup/cookie-media-$(date +%Y%m%d).tar.gz -C /data .
```

### Restore

```bash
# Stop the web container
docker compose -f docker-compose.prod.yml stop web

# Restore database
cat cookie-db-20240115.sql | docker compose -f docker-compose.prod.yml exec -T db \
  psql -U cookie cookie

# Restore media
docker run --rm \
  -v cookie-media:/data \
  -v $(pwd):/backup \
  alpine sh -c "rm -rf /data/* && tar xzf /backup/cookie-media-20240115.tar.gz -C /data"

# Restart
docker compose -f docker-compose.prod.yml start web
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
docker inspect --format='{{.State.Health.Status}}' cookie-prod
# healthy
```

### Logs

```bash
# Follow logs
docker compose -f docker-compose.prod.yml logs -f

# Last 100 lines
docker compose -f docker-compose.prod.yml logs --tail 100 web
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose -f docker-compose.prod.yml logs web

# Common issues:
# 1. Port 80 already in use - change ports in compose file
# 2. Database not ready - check db container health
# 3. Missing POSTGRES_PASSWORD in .env
```

### Permission Denied on Volume

```bash
# Fix volume permissions (container runs as UID 1000)
docker run --rm -v cookie-media:/data alpine chown -R 1000:1000 /data
```

### Static Files Not Loading

```bash
# Re-run collectstatic
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### Reset to Fresh State

```bash
# WARNING: This deletes all data
docker compose -f docker-compose.prod.yml down -v
docker compose -f docker-compose.prod.yml --env-file .env up -d
```

---

## Updating

Using the helper script:

```bash
bin/prod update  # Pulls latest and restarts
```

Or manually:

```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml --env-file .env up -d
```

---

## Security Checklist

Before exposing to the internet:

- [ ] Set a strong `POSTGRES_PASSWORD`
- [ ] Set `ALLOWED_HOSTS` to your actual domain(s)
- [ ] Set `CSRF_TRUSTED_ORIGINS` to your full URL(s)
- [ ] Use HTTPS (via reverse proxy)
- [ ] Keep Docker and the host OS updated
- [ ] Set up automated backups
- [ ] Monitor logs for unusual activity

---

## Support

- **GitHub Issues**: [github.com/matthewdeaves/cookie/issues](https://github.com/matthewdeaves/cookie/issues)

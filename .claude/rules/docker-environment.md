---
description: Docker-only environment rules - NO commands run on host
---

# Docker Environment Rules

The host machine has NO Python/Django installed. ALL backend commands MUST run inside Docker containers.

## Critical Rule

❌ **NEVER run Python/Django/pytest commands directly on the host**
✅ **ALWAYS use `docker compose exec` to run commands inside containers**

## Command Translation Table

| Task | ❌ WRONG (host) | ✅ CORRECT (Docker) |
|------|----------------|---------------------|
| Run tests | `pytest` | `docker compose exec web python -m pytest` |
| Django shell | `python manage.py shell` | `docker compose exec web python manage.py shell` |
| Migrations | `python manage.py migrate` | `docker compose exec web python manage.py migrate` |
| Management cmd | `python manage.py <command>` | `docker compose exec web python manage.py <command>` |
| Install Python pkg | `pip install package` | `docker compose exec web pip install package` |
| Frontend tests | `npm test` | `docker compose exec frontend npm test` |
| Frontend install | `npm install` | `docker compose exec frontend npm install` |
| Frontend watch | `npm run dev` | `docker compose exec frontend npm run dev` |

## Detection Patterns

If you see these errors, you ran on the host by mistake:

```
ModuleNotFoundError: No module named 'django'
→ You forgot to use docker compose exec web

command not found: npm
→ You forgot to use docker compose exec frontend

command not found: pytest
→ You forgot to use docker compose exec web
```

## Container Architecture

Cookie has 3 containers:
- **web** - Django backend (Gunicorn, Python 3.x)
- **frontend** - React modern frontend (Vite dev server)
- **db** - PostgreSQL database

## Common Workflows

### Backend Development
```bash
# Run tests
docker compose exec web python -m pytest

# Run tests with coverage
docker compose exec web python -m pytest --cov

# Django shell
docker compose exec web python manage.py shell

# Create migrations
docker compose exec web python manage.py makemigrations

# Apply migrations
docker compose exec web python manage.py migrate

# Create superuser
docker compose exec web python manage.py createsuperuser

# Collect static files (usually automatic on container start)
docker compose exec web python manage.py collectstatic --noinput
```

### Frontend Development
```bash
# Run tests (run and exit)
docker compose exec frontend npm test

# Run tests in watch mode
docker compose exec frontend npm run test:watch

# Run tests with coverage
docker compose exec frontend npm run test:coverage

# Install new package
docker compose exec frontend npm install package-name

# Build production bundle
docker compose exec frontend npm run build

# Lint
docker compose exec frontend npm run lint
```

### Container Management
```bash
# Start containers
docker compose up -d

# Stop containers
docker compose down

# Restart containers (needed after legacy static file changes)
docker compose down && docker compose up -d

# View logs
docker compose logs -f web
docker compose logs -f frontend

# Rebuild after Dockerfile changes
docker compose build
docker compose up -d
```

## Why Docker Only?

1. **Consistency** - Same environment in dev, CI, and production
2. **Isolation** - No conflicts with host system packages
3. **Reproducibility** - Dockerfile defines exact dependencies
4. **No "works on my machine"** - Everyone runs identical containers

## Exception: Host Commands

These commands CAN run on host:
- `git` commands (git is on host)
- `docker` and `docker compose` commands
- `gh` (GitHub CLI) commands
- File operations: `ls`, `cat`, `grep`, etc.
- `curl` for HTTP requests

## References

- Docker Compose docs: https://docs.docker.com/compose/
- Project Dockerfile: `/Dockerfile`
- Compose config: `/docker-compose.yml`

# cookie Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-24

## Active Technologies
- Python 3.12, TypeScript 5.9, ES5 (legacy frontend) + Django 5.0, Django Ninja 1.0+, React 19, Vite 7, curl_cffi, WhiteNoise; new: django-ratelimit (001-production-readiness)
- PostgreSQL (production), SQLite (development) via dj-database-url (001-production-readiness)
- Python 3.12 (backend, minor changes), TypeScript 5.9 (React frontend), ES5 (legacy frontend) + React 19, Vite 7, Django 5.0, Django Ninja 1.0+ (002-ux-polish)
- PostgreSQL (production), SQLite (development) - no schema changes (002-ux-polish)
- CSS3 (constrained to iOS 9.3 Safari support), Bash (hook script) + None — pure CSS find-and-replace plus one Bash script update (004-ios9-css-compat)
- TypeScript 5.9 (React frontend), ES5 (legacy frontend) + React 19, Vite 7, Django 5.0 (backend unchanged) (005-fix-qa-audit-issues)
- PostgreSQL (production), SQLite (development) — no schema changes (005-fix-qa-audit-issues)
- Python 3.12 (Django settings, entrypoint script) + Django 5.0, dj-database-url, psycopg[binary] (006-enforce-postgresql-everywhere)
- PostgreSQL 16 (all environments) — removing SQLite fallback (006-enforce-postgresql-everywhere)
- Python 3.12 (backend), TypeScript 5.9 (React frontend), ES5 (legacy frontend) + Django 5.0, Django Ninja 1.0+, React 19, Vite 7, curl_cffi (web scraping) (007-fix-qa-audit-issues)
- Python 3.12 + Django 5.0, WhiteNoise, Gunicorn (008-security-audit-remediation)
- PostgreSQL (via dj-database-url) (008-security-audit-remediation)
- Python 3.12 (backend), TypeScript 5.9 (frontend config only), Bash (entrypoint scripts) + Django 5.0, Django Ninja 1.0+, django-ratelimit 4.1, openrouter SDK, WhiteNoise, Gunicorn (009-production-hardening)
- PostgreSQL 16+ (via dj-database-url), Django database cache (new) (009-production-hardening)
- Python 3.12 + Django 5.0, Django Ninja 1.0+, curl_cffi (web scraping) (010-fix-qa-audit-issues)
- PostgreSQL (via dj-database-url), Django database cache (`django_cache` table) (010-fix-qa-audit-issues)
- Python 3.12 + Django 5.0, Django Ninja 1.0+, BeautifulSoup4, curl_cffi (012-filter-search-results)
- PostgreSQL (no schema changes) (012-filter-search-results)

- Python 3.12, TypeScript 5.9, ES5 (legacy) + Django 5.0, Django Ninja, React 19, Vite 7, Vitest 4, pytest, Gunicorn, WhiteNoise, curl_cffi (001-production-readiness)

## Project Structure

```text
backend/
frontend/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.12, TypeScript 5.9, ES5 (legacy): Follow standard conventions

## Authentication

Cookie supports dual-mode authentication via `AUTH_MODE` environment variable:

- **`home`** (default): Profile-based sessions, no login required. All settings accessible.
- **`public`**: Full authentication with username/password, email verification, role-based access control.

### Key Files
- `apps/core/auth.py` — `SessionAuth` (mode-aware) and `AdminAuth` classes
- `apps/core/auth_api.py` — Auth endpoints: register, login, logout, verify-email, me, change-password
- `apps/core/email_service.py` — Transient email verification (email never stored)
- `apps/core/management/commands/cookie_admin.py` — Admin CLI (list-users, promote, demote, reset-password, activate, deactivate, cleanup-unverified)

### Auth Commands (Public Mode)
```bash
# Admin CLI
docker compose exec web python manage.py cookie_admin list-users
docker compose exec web python manage.py cookie_admin promote <username>
docker compose exec web python manage.py cookie_admin demote <username>
docker compose exec web python manage.py cookie_admin reset-password <username> --generate
docker compose exec web python manage.py cookie_admin deactivate <username>
docker compose exec web python manage.py cookie_admin activate <username>
docker compose exec web python manage.py cookie_admin cleanup-unverified --dry-run
```

### Auth Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `AUTH_MODE` | `home` | `home` or `public` |
| `SITE_URL` | `http://localhost:3000` | Base URL for verification email links |
| `EMAIL_BACKEND` | `django.core.mail.backends.console.EmailBackend` | Django email backend |
| `DEFAULT_FROM_EMAIL` | `noreply@cookie.local` | Sender address for verification emails |
| `LOG_FORMAT` | `text` | `text` (dev) or `json` (production) |
| `LOG_LEVEL` | `INFO` | Root log level |

## Recent Changes
- 012-filter-search-results: Added Python 3.12 + Django 5.0, Django Ninja 1.0+, BeautifulSoup4, curl_cffi
- 011-dual-mode-auth: Added dual-mode authentication (home/public), admin CLI, email verification, privacy policy, structured JSON logging, request correlation IDs
- 010-fix-qa-audit-issues: Added Python 3.12 + Django 5.0, Django Ninja 1.0+, curl_cffi (web scraping)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

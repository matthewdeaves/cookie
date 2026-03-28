# cookie Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-28

## Active Technologies
- **Backend**: Python 3.12, Django 5.0, Django Ninja 1.0+, Gunicorn, WhiteNoise, curl_cffi, BeautifulSoup4, django-ratelimit 4.1, openrouter SDK
- **Frontend**: TypeScript 5.9, React 19, Vite 7
- **Legacy Frontend**: ES5 (iOS 9.3 Safari compatible)
- **Database**: PostgreSQL 16+ (all environments, no SQLite fallback), Django database cache (`django_cache` table)
- **Testing**: pytest, Vitest 4
- **Email**: Django built-in SMTP backend, Mailpit (dev via `docker-compose.mailpit.yml`)
- Python 3.12, TypeScript 5.9, ES5 (legacy) + Django 5.0, Django Ninja 1.0+, py-webauthn 2.x (new), React 19, Vite 7 (013-passkey-auth)
- PostgreSQL 16+ (2 new tables: WebAuthnCredential, DeviceCode) (013-passkey-auth)

## Project Structure

```text
apps/           # Django application modules (core, recipes, profiles, ai, legacy)
cookie/         # Django project settings
frontend/       # React 19 frontend (Vite, TypeScript)
tests/          # pytest test suite
```

## Commands

```bash
# Backend
docker compose exec web python -m pytest
docker compose exec web ruff check .
docker compose exec web python manage.py migrate

# Frontend
docker compose exec frontend npm test
docker compose exec frontend npm run lint
```

## Code Style

Python 3.12, TypeScript 5.9, ES5 (legacy): Follow standard conventions

## Authentication

Cookie supports three authentication modes via `AUTH_MODE` environment variable:

- **`home`** (default): Profile-based sessions, no login required. All settings accessible.
- **`public`**: Full authentication with username/password, email verification, role-based access control.
- **`passkey`**: WebAuthn passkey-only authentication. No username, email, or password. Device code flow for legacy devices.

### Key Files
- `apps/core/auth.py` — `SessionAuth` (mode-aware: home/public/passkey) and `AdminAuth` classes
- `apps/core/auth_api.py` — Auth endpoints: register, login, logout, verify-email, me, change-password (public mode)
- `apps/core/passkey_api.py` — Passkey endpoints: register, login, credential management (passkey mode)
- `apps/core/device_code_api.py` — Device code flow: code generation, polling, authorization (passkey mode)
- `apps/core/email_service.py` — Transient email verification (email never stored, public mode only)
- `apps/core/management/commands/cookie_admin.py` — Admin CLI (public + passkey modes)
- `apps/core/management/commands/cleanup_device_codes.py` — Clean up expired device codes

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

### Auth Commands (Passkey Mode)
```bash
docker compose exec web python manage.py cookie_admin list-users
docker compose exec web python manage.py cookie_admin promote <pk_username>
docker compose exec web python manage.py cookie_admin demote <pk_username>
docker compose exec web python manage.py cookie_admin deactivate <pk_username>
docker compose exec web python manage.py cookie_admin activate <pk_username>
docker compose exec web python manage.py cleanup_device_codes --dry-run
```

### Auth Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `AUTH_MODE` | `home` | `home`, `public`, or `passkey` |
| `WEBAUTHN_RP_ID` | Request hostname | WebAuthn Relying Party ID (domain, passkey mode) |
| `WEBAUTHN_RP_NAME` | `Cookie` | Name shown in passkey prompts |
| `DEVICE_CODE_EXPIRY_SECONDS` | `600` | Device code lifetime (10 min default) |
| `DEVICE_CODE_MAX_ATTEMPTS` | `5` | Failed authorization attempts before code invalidation |
| `SITE_URL` | `http://localhost:3000` | Base URL for verification email links |
| `EMAIL_BACKEND` | `django.core.mail.backends.console.EmailBackend` | Django email backend |
| `DEFAULT_FROM_EMAIL` | `noreply@cookie.local` | Sender address for verification emails |
| `EMAIL_HOST` | `localhost` | SMTP server hostname (e.g., `email-smtp.eu-west-2.amazonaws.com` for AWS SES) |
| `EMAIL_PORT` | `25` | SMTP server port (e.g., `587` for TLS, `1025` for Mailpit) |
| `EMAIL_HOST_USER` | `""` | SMTP authentication username (e.g., AWS SES SMTP credentials) |
| `EMAIL_HOST_PASSWORD` | `""` | SMTP authentication password |
| `EMAIL_USE_TLS` | `False` | Enable TLS for SMTP connection (`True` for production) |
| `LOG_FORMAT` | `text` | `text` (dev) or `json` (production) |
| `LOG_LEVEL` | `INFO` | Root log level |

## Developer Responsibility

This project has a constitution at `.specify/memory/constitution.md` that defines immutable principles. All code changes MUST comply with these principles. When encountering pre-existing issues (broken linting, stale configs, tooling incompatibilities), fix them — do not work around them or skip hooks.

- **Fix pre-existing issues**: If a pre-commit hook, CI job, or linter is broken, fix the root cause. Never skip hooks with `--no-verify` or `SKIP=` as a permanent solution.
- **Respect the constitution**: Read `.specify/memory/constitution.md` before making architectural decisions. Every principle has a rationale — understand it before proposing exceptions.
- **Speckit workflow**: Feature specifications, plans, and tasks live in `.specify/` (tracked in git). Use `/speckit.*` commands for structured feature development. The constitution is the source of truth for project values.

## Recent Changes
- 013-passkey-auth: Added Python 3.12, TypeScript 5.9, ES5 (legacy) + Django 5.0, Django Ninja 1.0+, py-webauthn 2.x (new), React 19, Vite 7
- 012-mailpit-email-config: Added Python 3.12 (backend settings only) + Django 5.0 (built-in email framework), Mailpit (external Docker service)
- 012-filter-search-results: Added Python 3.12 + Django 5.0, Django Ninja 1.0+, BeautifulSoup4, curl_cffi


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

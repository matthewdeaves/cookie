# cookie Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-31

## Active Technologies
- **Backend**: Python 3.14, Django 5.0, Django Ninja 1.0+, Gunicorn, WhiteNoise, curl_cffi, BeautifulSoup4, django-ratelimit 4.1, openrouter SDK
- **Frontend**: TypeScript 5.9, React 19, Vite 7
- **Legacy Frontend**: ES5 (iOS 9.3 Safari compatible)
- **Database**: PostgreSQL 16+ (all environments, no SQLite fallback), Django database cache (`django_cache` table)
- **Testing**: pytest, Vitest 4
- Python 3.14, TypeScript 5.9, ES5 (legacy) + Django 5.0, Django Ninja 1.0+, py-webauthn 2.x, React 19, Vite 7
- PostgreSQL 16+ (tables: WebAuthnCredential, DeviceCode for passkey mode)
- Python 3.14, TypeScript 5.9 + Django 5.0, Django Ninja 1.0+, React 19, Vite 7 (015-reduce-complexity)
- PostgreSQL 16+ (no changes) (015-reduce-complexity)
- Python 3.14 (backend, unchanged), TypeScript 5.9 (modern frontend), ES5 (legacy frontend) + React 19, Vite 7 (modern); vanilla ES5 JS (legacy) (016-fix-stale-search-filters)
- N/A (no data changes) (016-fix-stale-search-filters)
- Python 3.14 (backend), TypeScript 5.9 (modern frontend), ES5 (legacy frontend) + Django 5.0, Django Ninja 1.0+, React 19, Vite 7, django-ratelimit 4.1 (017-ai-quotas)
- PostgreSQL 16+ (all environments), Django database cache (`django_cache` table) (017-ai-quotas)
- Python 3.14, TypeScript 5.9, ES5 (legacy) + Django 5.0, Django Ninja 1.0+, curl_cffi >=0.7, django-ratelimit 4.1, py-webauthn 2.x, Pillow (018-security-hardening)

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

Python 3.14, TypeScript 5.9, ES5 (legacy): Follow standard conventions

## Releases & Versioning

Tags and releases use **semver** (`vMAJOR.MINOR.PATCH`). Versions MUST increase monotonically — never create a patch release after a higher minor/major has been tagged.

- **MAJOR** — Breaking changes (API, data model, config).
- **MINOR** — New features, security hardening, dependency upgrades.
- **PATCH** — Bug fixes only.

Rules:
1. One release per deploy. Batch small fixes into a single release instead of tagging every commit.
2. Before tagging, check the latest existing tag (`gh release list --limit 1`) and increment from there.
3. Use `gh release create` with `--latest` so GitHub marks it correctly.
4. Release notes must summarise what changed since the previous release, not per-commit.

## Authentication

Cookie supports two authentication modes via `AUTH_MODE` environment variable:

- **`home`** (default): Profile-based sessions, no login required. All settings accessible.
- **`passkey`**: WebAuthn passkey-only authentication. No username, email, or password. Device code flow for legacy devices.

### Key Files
- `apps/core/auth.py` — `SessionAuth` (mode-aware: home/passkey) and `AdminAuth` classes
- `apps/core/auth_api.py` — Shared auth endpoints: logout, me (passkey mode)
- `apps/core/passkey_api.py` — Passkey endpoints: register, login, credential management (passkey mode)
- `apps/core/device_code_api.py` — Device code flow: code generation, polling, authorization (passkey mode)
- `apps/core/management/commands/cookie_admin.py` — Admin CLI: user management, status, audit (passkey mode only)
- `apps/core/management/commands/cleanup_device_codes.py` — Clean up expired device codes

### Admin CLI (Passkey Mode)
All subcommands support `--json` for structured output (automation-friendly).
```bash
# App status (post-deploy verification)
docker compose exec web python manage.py cookie_admin status --json

# Security audit (last 24h events)
docker compose exec web python manage.py cookie_admin audit --json

# User management
docker compose exec web python manage.py cookie_admin list-users --json
docker compose exec web python manage.py cookie_admin promote <pk_username> --json
docker compose exec web python manage.py cookie_admin demote <pk_username> --json
docker compose exec web python manage.py cookie_admin deactivate <pk_username> --json
docker compose exec web python manage.py cookie_admin activate <pk_username> --json

# Factory reset (CLI-only in passkey mode — disabled in web UI)
docker compose exec web python manage.py cookie_admin reset --json

# Device code cleanup
docker compose exec web python manage.py cleanup_device_codes --dry-run
```

### Auth Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `AUTH_MODE` | `home` | `home` or `passkey` |
| `OPENROUTER_API_KEY` | `""` | OpenRouter API key (overrides database value) |
| `WEBAUTHN_RP_ID` | Request hostname | WebAuthn Relying Party ID (domain, passkey mode) |
| `WEBAUTHN_RP_NAME` | `Cookie` | Name shown in passkey prompts |
| `DEVICE_CODE_EXPIRY_SECONDS` | `600` | Device code lifetime (10 min default) |
| `DEVICE_CODE_MAX_ATTEMPTS` | `5` | Failed authorization attempts before code invalidation |
| `LOG_FORMAT` | `text` | `text` (dev) or `json` (production) |
| `LOG_LEVEL` | `INFO` | Root log level |

## Developer Responsibility

This project has a constitution at `.specify/memory/constitution.md` that defines immutable principles. All code changes MUST comply with these principles. When encountering pre-existing issues (broken linting, stale configs, tooling incompatibilities), fix them — do not work around them or skip hooks.

- **Fix pre-existing issues**: If a pre-commit hook, CI job, or linter is broken, fix the root cause. Never skip hooks with `--no-verify` or `SKIP=` as a permanent solution.
- **Respect the constitution**: Read `.specify/memory/constitution.md` before making architectural decisions. Every principle has a rationale — understand it before proposing exceptions.
- **Speckit workflow**: Feature specifications, plans, and tasks live in `.specify/` (tracked in git). Use `/speckit.*` commands for structured feature development. The constitution is the source of truth for project values.

## Recent Changes
- 018-security-hardening: Added Python 3.14, TypeScript 5.9, ES5 (legacy) + Django 5.0, Django Ninja 1.0+, curl_cffi >=0.7, django-ratelimit 4.1, py-webauthn 2.x, Pillow
- 017-ai-quotas: Added Python 3.14 (backend), TypeScript 5.9 (modern frontend), ES5 (legacy frontend) + Django 5.0, Django Ninja 1.0+, React 19, Vite 7, django-ratelimit 4.1
- 016-fix-stale-search-filters: Added Python 3.14 (backend, unchanged), TypeScript 5.9 (modern frontend), ES5 (legacy frontend) + React 19, Vite 7 (modern); vanilla ES5 JS (legacy)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

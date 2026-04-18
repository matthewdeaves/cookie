# cookie Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-04-18

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
- Python 3.14 (backend), TypeScript 5.9 (modern frontend), ES5 (legacy frontend) + Django 5.0, Django Ninja 1.0+, `django-ratelimit` 4.1, py-webauthn 2.x (passkey mode only), React 19, Vite 7, Vitest 4, React Testing Library (existing) (013-admin-home-only)
- PostgreSQL 16+ (no schema changes; reads/writes existing `AppSettings`, `AIPrompt`, `SearchSource`, `Profile`, `User` tables) (013-admin-home-only)
- Python 3.14 (backend), TypeScript 5.9 (modern frontend), ES5 (legacy frontend) + Django 5.0, Django Ninja 1.0+, py-webauthn 2.x (passkey mode only), React 19, Vite 7, Vitest 4, React Testing Library, pytest 8 (014-remove-is-staff)
- PostgreSQL 16+ (no schema changes). `User.is_staff` column remains on the default Django User model (AbstractUser); value becomes always-False for application-created users. (014-remove-is-staff)

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
- `apps/core/auth.py` — `SessionAuth` (mode-aware) and `HomeOnlyAuth` (raises 404 in non-home modes BEFORE auth runs; used by 22 admin + profile endpoints)
- `apps/core/auth_api.py` — Shared auth endpoints: logout, me (passkey mode)
- `apps/core/passkey_api.py` — Passkey endpoints: register, login, credential management (passkey mode)
- `apps/core/device_code_api.py` — Device code flow: code generation, polling, authorization (passkey mode)
- `apps/core/management/commands/cookie_admin.py` — Admin CLI. User-lifecycle subcommands are passkey-only; app-config subcommands (api key, prompts, sources, quotas, rename, reset) work in both modes.
- `apps/core/management/commands/cleanup_device_codes.py` — Clean up expired device codes

### Admin surface by mode (v1.43.0+)
- **Home mode**: web admin UI fully available to any profile. CLI is equivalent.
- **Passkey mode**: all passkey users are peers — there is no in-app admin privilege. All 18 admin endpoints + all `/api/profiles/*` endpoints return 404; settings UI hides admin sections in both frontends. App configuration is reached exclusively via `cookie_admin` CLI. `is_staff` on the User model is inert and always `False` for application-created users.

### Admin CLI
All subcommands support `--json` for automation-friendly output.
```bash
# --- User lifecycle (requires AUTH_MODE=passkey) ---
docker compose exec web python manage.py cookie_admin list-users --json
docker compose exec web python manage.py cookie_admin create-user <pk_username> --json
docker compose exec web python manage.py cookie_admin delete-user <pk_username> --json
docker compose exec web python manage.py cookie_admin deactivate <pk_username> --json
docker compose exec web python manage.py cookie_admin activate <pk_username> --json

# --- App config (mode-agnostic) ---
docker compose exec web python manage.py cookie_admin status --json         # now includes a 'cache' block
docker compose exec web python manage.py cookie_admin audit --json

# API key (pipe from stdin — never hits shell history)
echo -n "sk-or-..." | docker compose exec -T web python manage.py cookie_admin set-api-key --stdin
echo -n "sk-or-..." | docker compose exec -T web python manage.py cookie_admin test-api-key --stdin --json

docker compose exec web python manage.py cookie_admin set-default-model anthropic/claude-haiku-4.5

# AI prompts (file-based content to avoid shell-escaping pain)
docker compose exec web python manage.py cookie_admin prompts list --json
docker compose exec web python manage.py cookie_admin prompts show recipe_remix --json
docker compose exec web python manage.py cookie_admin prompts set recipe_remix \
    --system-file /tmp/system.txt --user-file /tmp/user.txt \
    --model anthropic/claude-sonnet-4 --active true

# Search sources
docker compose exec web python manage.py cookie_admin sources list --json
docker compose exec web python manage.py cookie_admin sources list --attention --json
docker compose exec web python manage.py cookie_admin sources toggle 3
docker compose exec web python manage.py cookie_admin sources toggle-all --disable
docker compose exec web python manage.py cookie_admin sources set-selector 5 --selector 'article.recipe h1.title'
docker compose exec web python manage.py cookie_admin sources test --all --json
docker compose exec web python manage.py cookie_admin sources repair 5    # AI-assisted (requires API key)

# AI daily quotas
docker compose exec web python manage.py cookie_admin quota show --json
docker compose exec web python manage.py cookie_admin quota set tips 50

# Profile rename (passkey: by user_id|username; home: by profile_id)
docker compose exec web python manage.py cookie_admin rename alice --name "Alice Prime"

# Factory reset (works in both modes)
docker compose exec web python manage.py cookie_admin reset               # interactive
docker compose exec web python manage.py cookie_admin reset --json --confirm

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
- 014-remove-is-staff: Added Python 3.14 (backend), TypeScript 5.9 (modern frontend), ES5 (legacy frontend) + Django 5.0, Django Ninja 1.0+, py-webauthn 2.x (passkey mode only), React 19, Vite 7, Vitest 4, React Testing Library, pytest 8
- 013-admin-home-only: Added Python 3.14 (backend), TypeScript 5.9 (modern frontend), ES5 (legacy frontend) + Django 5.0, Django Ninja 1.0+, `django-ratelimit` 4.1, py-webauthn 2.x (passkey mode only), React 19, Vite 7, Vitest 4, React Testing Library (existing)
- 018-security-hardening: Added Python 3.14, TypeScript 5.9, ES5 (legacy) + Django 5.0, Django Ninja 1.0+, curl_cffi >=0.7, django-ratelimit 4.1, py-webauthn 2.x, Pillow


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

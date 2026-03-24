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

## Recent Changes
- 010-fix-qa-audit-issues: Added Python 3.12 + Django 5.0, Django Ninja 1.0+, curl_cffi (web scraping)
- 009-production-hardening: Added Python 3.12 (backend), TypeScript 5.9 (frontend config only), Bash (entrypoint scripts) + Django 5.0, Django Ninja 1.0+, django-ratelimit 4.1, openrouter SDK, WhiteNoise, Gunicorn
- 008-security-audit-remediation: Added Python 3.12 + Django 5.0, WhiteNoise, Gunicorn


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

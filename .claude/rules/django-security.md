---
paths:
  - "apps/**/*.py"
  - "cookie/**/*.py"
---

# Django Security Rules

## Hard Rules

- **ORM only** — never use string interpolation in SQL. `.raw()` MUST use `%s` placeholders, never f-strings.
- **No `|safe` on user content** — Django templates auto-escape by default. `|safe` and `{% autoescape off %}` MUST NOT be used on user-controlled content.
- **Use `json_script`** — never inject variables into `<script>` tags with `{{ var }}`. Use `{{ data|json_script:"id" }}`.
- **CSRF on all mutations** — all POST/PUT/DELETE requests include CSRF tokens. Django Ninja has `csrf=True` by default.
- **Validate URLs before scraping** — only `http://https://` schemes. Block localhost and internal IPs (SSRF protection).
- **Validate file uploads by content** — check with PIL/Pillow, not just extension. Enforce size limits.
- **No mass assignment** — use Django Ninja Schema classes to whitelist fields. Never `Model.objects.create(**request.POST.dict())`.
- **Use `constant_time_compare`** for secret comparison — prevents timing attacks.
- **No secrets in code** — SECRET_KEY, DB credentials, API keys via environment variables only.

## Auth Patterns

- Always verify resource ownership before returning data (check `recipe.profile == request.user.profile`)
- Use `SessionAuth` from `apps/core/auth.py` (mode-aware: home/passkey)

## CI Enforcement

Bandit (Python SAST), pip-audit (dependency vulnerabilities), and detect-secrets (pre-commit) run automatically.

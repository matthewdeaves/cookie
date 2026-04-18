# Quickstart: Verify the refactor

How to verify each success criterion after implementation, in order. All commands run via `docker compose exec …` per constitution Principle VI.

## 0. Prerequisites

- Branch `014-remove-is-staff` checked out.
- `docker compose up -d` for both `web` and `frontend` containers.
- Clean dev database (either a fresh `cookie_admin reset --confirm` or a newly-created dev DB).

## 1. Static regression guard passes

```bash
docker compose exec web python -m pytest tests/test_no_is_staff_reads.py -v
```

Expected: test passes. If it fails, the output names the file:line containing the residual `is_staff` read and what to do.

## 2. Full test suite passes

```bash
docker compose exec web python -m pytest -q
```

Expected: green. No skipped tests marked `@pytest.mark.skip` for is_staff-related reasons.

## 3. Frontend tests pass

```bash
docker compose exec frontend npm test -- --run
```

Expected: green. No residual references to `is_admin` in frontend types.

## 4. Home mode — full admin UI works

```bash
# Set home mode (default)
docker compose exec web env AUTH_MODE=home python manage.py check
# Or just restart with home mode in .env
```

Open the modern frontend → Settings → confirm all tabs render:

- API Key
- AI Prompts
- Search Sources
- AI Quotas
- Danger Zone (Reset)

Perform one admin action (e.g., save a dummy AI prompt) — should return 200 and persist.

Open the legacy frontend → `/legacy/settings/` → confirm every `{% if is_admin %}` block renders (API key form, prompts, sources, danger zone).

## 5. Passkey mode — admin + profile endpoints return 404

Set `AUTH_MODE=passkey` in `.env`, restart containers.

Register a passkey user (or use the device-code flow). Authenticate. Then probe every gated endpoint:

```bash
# Admin endpoints (18) — should all return 404
curl -s -o /dev/null -w "%{http_code}\n" -b "sessionid=<your-session>" \
  http://localhost:8000/api/system/reset-preview/
# expected: 404

# Profile endpoints (9) — should all return 404
curl -s -o /dev/null -w "%{http_code}\n" -b "sessionid=<your-session>" \
  http://localhost:8000/api/profiles/
# expected: 404
```

The response body for every 404 must be exactly `{"detail": "Not found"}`.

The automated variant of this check runs in `tests/test_gated_endpoints_passkey.py`.

## 6. Passkey mode — admin UI is hidden

Modern frontend: open Settings. Confirm:

- No API Key tab
- No AI Prompts tab
- No Search Sources tab
- No AI Quotas tab (admin version; user-facing "my usage" may still show)
- No Danger Zone

Legacy frontend: open `/legacy/settings/`. Confirm no `{% if is_admin %}` block renders.

## 7. Quota bypass works via `unlimited_ai` only

```bash
# Passkey mode
docker compose exec web python manage.py cookie_admin create-user alice --json
docker compose exec web python manage.py cookie_admin set-unlimited alice --json
docker compose exec web python manage.py cookie_admin list-users --json
```

Expected: `list-users` JSON shows `unlimited_ai: true` for alice and contains no `is_admin` field.

Log in as alice, exercise AI features past normal quota limits → requests succeed.

## 8. `is_staff=True` does NOT bypass quota

Create a second user and manually set `is_staff=True` via Django shell (simulating a stale deployment state):

```bash
docker compose exec web python manage.py shell -c "
from django.contrib.auth.models import User
u = User.objects.create_user('bob')
u.is_staff = True
u.set_unusable_password()
u.save()
"
```

Log in as bob (requires a passkey; alternatively use a pytest fixture). Exercise an AI feature past the quota limit → request must be rejected. This proves the `is_staff` bypass is gone.

## 9. CLI surface is trimmed

```bash
docker compose exec web python manage.py cookie_admin --help
```

Expected: output contains no `promote`, no `demote`, no `--admins-only`.

```bash
docker compose exec web python manage.py cookie_admin create-user --help
```

Expected: no `--admin` flag.

```bash
docker compose exec web python manage.py cookie_admin promote alice
```

Expected: argparse error "invalid choice: 'promote'".

Verify the `--help` output itself contains no forbidden tokens (covers SC-005):

```bash
docker compose exec web python manage.py cookie_admin --help | \
  grep -E 'promote|demote|--admins-only|is_staff|one-admin' && \
  echo "FAIL: forbidden token present" || echo "PASS: help output clean"
```

Expected: `PASS: help output clean`.

## 10. Informational CLI output is trimmed

```bash
docker compose exec web python manage.py cookie_admin status --json | jq '.users'
```

Expected: contains `total` and `active`; contains NO `admins` or `active_admins`.

```bash
docker compose exec web python manage.py cookie_admin list-users --json | jq '.[0]'
```

Expected: per-user object has no `is_admin` key.

```bash
docker compose exec web python manage.py cookie_admin audit --json | head -20
```

Expected: no `is_admin` fields anywhere in the output.

## 11. Code-quality gates pass

```bash
docker compose exec web ruff check apps/
docker compose exec web radon cc apps/ -a -nb
docker compose exec frontend npm run lint
```

Expected: clean. No new violations introduced.

## 12. Constitution updated

Open `.specify/memory/constitution.md`:

- Principle III passkey-mode paragraph reflects "peers, CLI-only, no in-app admin".
- Version header is `1.4.0`.
- Amendment history has a new row dated 2026-04-18.

## 13. Release preparation

Bump `COOKIE_VERSION` in `cookie/settings.py` to `1.43.0`. Commit.

```bash
git tag -a v1.43.0 -m "v1.43.0: Remove is_staff privilege signal; lock /api/profiles/* to home mode"
gh release create v1.43.0 --latest --notes-file - <<'EOF'
## v1.43.0 — is_staff removal + profile-API lockdown

### Security
- `User.is_staff` no longer grants any application privilege. AI quota bypass is
  now granted exclusively via `Profile.unlimited_ai` (already managed by the
  `cookie_admin set-unlimited` CLI).
- `/api/profiles/*` endpoints return 404 in passkey mode — matches the admin
  endpoint lockdown shipped in v1.42.0. Passkey-mode users cannot enumerate
  peer profiles or their metadata.

### Breaking CLI changes
- `cookie_admin promote` and `cookie_admin demote` subcommands removed.
- `--admin` flag removed from `cookie_admin create-user`.
- `--admins-only` flag removed from `cookie_admin list-users`.
- `cookie_admin status`, `audit`, and `list-users` outputs no longer include
  any `is_admin` / admin-count fields.

### Internal
- `HomeOnlyAdminAuth` renamed to `HomeOnlyAuth`. `AdminAuth` class deleted.
- Constitution Principle III amended to reflect peer-passkey-user model.

### Upgrade
This release is dev-mode only. Existing installs should run
`cookie_admin reset --confirm` or drop the database. No data migration is
provided.
EOF
```

## Rollback

If anything goes wrong post-deploy, `git revert` the merge commit. No data migration to unwind.

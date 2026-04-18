# Release Steps — v1.42.0

**Run these AFTER `013-admin-home-only` is merged to `master`.** I do NOT execute these during implementation because they are visible external actions (tag push, GitHub release).

## 1. Verify clean master

```bash
git checkout master
git pull --ff-only
git log --oneline -3          # Expect the 013-admin-home-only merge commit at HEAD
```

## 2. Confirm previous tag

```bash
gh release list --limit 1     # Expect v1.41.0
```

## 3. Tag and push

```bash
git tag v1.42.0
git push origin v1.42.0
```

## 4. Create the GitHub release

```bash
gh release create v1.42.0 --latest \
  --title "v1.42.0 — passkey-mode admin surface hardening" \
  --notes-file - <<'EOF'
## Security

- **18 admin REST endpoints return 404 in passkey mode.** Previously gated only by `AdminAuth()` and exposed to authenticated admins, they are now gated by a new `HomeOnlyAdminAuth` class that raises `HttpError(404)` before any cookie extraction. Passkey deployments reveal no admin surface to probes, authenticated or not. Gated endpoints:
  - `POST /api/ai/save-api-key`, `POST /api/ai/test-api-key`
  - `GET/PUT /api/ai/prompts` and `/api/ai/prompts/{type}`
  - `POST /api/ai/repair-selector`, `GET /api/ai/sources-needing-attention`
  - `PUT /api/ai/quotas`
  - `GET /api/system/reset-preview/`, `POST /api/system/reset/`
  - `POST /api/sources/{id}/toggle/`, `POST /api/sources/bulk-toggle/`
  - `PUT /api/sources/{id}/selector/`, `POST /api/sources/{id}/test/`, `POST /api/sources/test-all/`
  - `GET /api/recipes/cache/health/`
  - `POST /api/profiles/{id}/set-unlimited/`, `PATCH /api/profiles/{id}/rename/`
- **Admin settings UI is hidden in passkey mode** in both the React SPA and the legacy ES5 frontend. Admins perform all management via `python manage.py cookie_admin`.
- **`/api/system/mode/` no longer returns a `version` key**, removing a deployment fingerprinting vector.

## Operator changes (passkey-mode CLI parity)

`python manage.py cookie_admin` gains these mode-agnostic subcommands so passkey operators retain full admin capability without the web surface:

- `set-api-key`, `test-api-key`, `set-default-model`
- `prompts list|show|set` (file-based content to avoid shell-escaping)
- `sources list|toggle|toggle-all|set-selector|test|repair`
- `quota show|set`
- `rename` (accepts username or user-id in passkey; profile-id in home)

`status --json` now includes a `cache` block with image-cache health stats (parity with the now-gated `GET /api/recipes/cache/health/`).

The CLI's blanket passkey-only guard was replaced with a per-subcommand allowlist so `status`, `audit`, `reset`, and all new subcommands work in either mode. User-lifecycle subcommands (`list-users`, `promote`, `demote`, `activate`, `deactivate`, `set-unlimited`, `remove-unlimited`, `create-user`, `delete-user`, `usage`, `create-session`) remain passkey-only.

## Implementation notes

- Full feature spec, plan, tasks, research, contracts: `specs/013-admin-home-only/`
- Tests: backend 1304 pass / 85.9% coverage; frontend 516 pass.
- Pentest alignment handoff: `specs/013-admin-home-only/pentest-handoff.md` — apply in the appserver repo via `/pentest-align`.

## Follow-ups (tracked, out of scope for this release)

- `cookie_admin.py` package split (file is 1215 lines; pre-existing 710-line violation of Principle V was exacerbated by this feature's additions).
- Authenticated HexStrike re-scan against the hardened surface.
EOF
```

## 5. Trigger the deployment pipeline

(Environment-specific — run your deploy workflow or wait for the post-release CI to pick up the tag.)

## 6. Post-deploy verification

```bash
# From any client with network reach to the passkey deployment:
curl -is https://<deployment>/api/ai/save-api-key -X POST | head -1         # HTTP/1.1 404 Not Found
curl -is https://<deployment>/api/system/reset-preview/ | head -1           # HTTP/1.1 404 Not Found
curl -is https://<deployment>/api/sources/test-all/ -X POST | head -1       # HTTP/1.1 404 Not Found
curl -is https://<deployment>/api/recipes/cache/health/ | head -1           # HTTP/1.1 404 Not Found

# Fingerprint check
curl -s https://<deployment>/api/system/mode/ | jq
# Expected: {"mode":"passkey","registration_enabled":true}    (no 'version' key)
```

Then re-run HexStrike (or equivalent) unauthenticated scan. The admin paths should not appear in the discovered path inventory.

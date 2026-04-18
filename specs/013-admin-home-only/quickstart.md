# Quickstart — 013-admin-home-only

Operator walkthrough for verifying and operating the hardened passkey-mode deployment.

## Verify the 18 endpoints 404 in passkey mode

From any client with network reach to the deployment:

```bash
# Anonymous probe — should be 404, body {"detail":"Not found"}
curl -is https://<deployment>/api/ai/save-api-key -X POST | head -1
curl -is https://<deployment>/api/system/reset-preview/ | head -1
curl -is https://<deployment>/api/sources/test-all/ -X POST | head -1
curl -is https://<deployment>/api/recipes/cache/health/ | head -1
# ... repeat for all 18 from contracts/gated-endpoints.md
```

All should respond `HTTP/1.1 404 Not Found`. No `security.log` line should appear for these probes.

## Verify the admin UI is hidden

- Open the modern SPA at `https://<deployment>/app/settings` while logged in as an admin. Only `General`, `Passkeys`, `Delete Account`, and `AI Usage` sections should render. `API Key`, `Prompts`, `Selectors`, `Sources`, `AI Quota`, `Danger Zone`, and admin bits inside `User Profile` / `Users` should be absent from the DOM.
- Open the legacy settings at `https://<deployment>/settings`. Only the non-admin blocks should render.

## Verify the version fingerprint is gone

```bash
curl -s https://<deployment>/api/system/mode/ | jq
```

Expected:
```json
{"mode":"passkey","registration_enabled":true}
```
(no `version` key)

## CLI operations on a passkey deployment

SSH into the host running the web container, then shell into it:

```bash
docker compose exec web bash
```

### Set / test / rotate the OpenRouter API key

```bash
# Safest — read from stdin; key never hits shell history
echo -n "sk-or-..." | python manage.py cookie_admin set-api-key --stdin

# Validate without saving
echo -n "sk-or-..." | python manage.py cookie_admin test-api-key --stdin

# Or pass inline (avoid in shared shells)
python manage.py cookie_admin set-api-key --key "sk-or-..."
```

### Change the default AI model

```bash
python manage.py cookie_admin set-default-model anthropic/claude-haiku-4.5
```

### Edit an AI prompt from files

```bash
# Put multi-line content in files to avoid shell-escaping hell
cat > /tmp/remix-system.txt <<'EOF'
You are a recipe remixer. Respond with JSON...
EOF
cat > /tmp/remix-user.txt <<'EOF'
Remix this recipe: {recipe_text}
Target: {target_style}
EOF

python manage.py cookie_admin prompts set recipe_remix \
  --system-file /tmp/remix-system.txt \
  --user-file /tmp/remix-user.txt \
  --model anthropic/claude-sonnet-4 \
  --active true
```

### Manage search sources

```bash
# List
python manage.py cookie_admin sources list --json | jq

# Just the ones needing attention
python manage.py cookie_admin sources list --attention --json

# Toggle one, toggle many
python manage.py cookie_admin sources toggle 3
python manage.py cookie_admin sources toggle-all --disable

# Fix a selector
python manage.py cookie_admin sources set-selector 5 --selector 'article.recipe h1.title'

# Health check
python manage.py cookie_admin sources test --all --json

# AI-assisted selector repair (requires API key)
python manage.py cookie_admin sources repair 5
```

### Manage daily AI quotas

```bash
python manage.py cookie_admin quota show
python manage.py cookie_admin quota set tips 50
```

### Rename a user's profile

```bash
# By username
python manage.py cookie_admin rename pk-abc123 --name "Alice"

# By user-id
python manage.py cookie_admin rename 42 --name "Bob"
```

### Read cache health

```bash
python manage.py cookie_admin status --json | jq .cache
```

## Release the new version

```bash
# 1. Confirm previous tag
gh release list --limit 1     # expect v1.41.0

# 2. Bump default COOKIE_VERSION in cookie/settings.py to "1.42.0"
#    (deploy pipelines also set COOKIE_VERSION env; both in sync)

# 3. Commit all spec + code changes, push, open PR, merge

# 4. Tag + release
git tag v1.42.0
git push origin v1.42.0

gh release create v1.42.0 --latest --title "v1.42.0 — passkey-mode admin surface hardening" --notes-file - <<'EOF'
## Security

- Admin-only REST endpoints return 404 in passkey mode (18 endpoints). Previously exposed via `AdminAuth()`; now gated by `HomeOnlyAdminAuth` so passkey deployments reveal no admin surface to probes, authenticated or not.
- Admin settings UI is hidden in passkey mode in both the React SPA and the legacy ES5 frontend. Admins perform all management via `python manage.py cookie_admin`.
- The `/api/system/mode/` endpoint no longer returns a `version` key, removing a fingerprinting vector.

## Operator changes

- `python manage.py cookie_admin` gains `set-api-key`, `test-api-key`, `set-default-model`, `prompts list/show/set`, `sources list/toggle/toggle-all/set-selector/test/repair`, `quota show/set`, and `rename`. `status --json` now includes a `cache` block.
- New subcommands work in both home and passkey mode; user-lifecycle subcommands remain passkey-only.

See `specs/013-admin-home-only/` for full details.
EOF
```

## Post-release verification

Re-run the HexStrike unauthenticated scan (or equivalent) against the passkey deployment. The admin paths listed in `contracts/gated-endpoints.md` should not appear in the discovered path inventory. The `/api/system/mode/` probe should not return a version string.

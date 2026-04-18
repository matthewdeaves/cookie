# Quickstart — Manual Verification of Security Review Fixes (Round 2)

End-to-end manual verification after merge. Every step maps to one or more functional requirements or user stories in [spec.md](./spec.md). Expected run time on a developer laptop: ~45 minutes.

## Prerequisites

- Docker + docker compose
- `gh` CLI authenticated against the `matthewdeaves/cookie` repo
- A working checkout on the `015-security-review-fixes` branch (or merged to master)
- `curl` and `jq` available on the host
- A WebAuthn-capable browser (Chrome ≥ 120 or Safari ≥ 17) for Story 5 verification

---

## Step 1 — Build the production image locally

```bash
docker build --file Dockerfile.prod --tag cookie:015-verify .
```

**Expected**: Build completes. The `sha256sum -c` step against the supercronic binary passes. No errors about a missing `cron` package during entrypoint (the package is gone).

**Maps to**: FR-001, FR-002a, FR-002b

---

## Step 2 — Exec into the production container and confirm no secrets on disk

```bash
docker run --rm -d \
  --name cookie-verify \
  -e SECRET_KEY=dummy-for-verify \
  -e DATABASE_URL=postgres://dummy:dummy@host.docker.internal:5432/dummy \
  -e AUTH_MODE=passkey \
  cookie:015-verify

sleep 10
docker exec cookie-verify sh -c 'grep -rE "SECRET_KEY|DATABASE_URL" /etc/ /var/ 2>/dev/null || echo NONE'
docker exec cookie-verify ls -la /etc/cron.d/ 2>/dev/null || echo "no /etc/cron.d (expected)"
docker exec cookie-verify which cron || echo "cron not installed (expected)"
docker exec cookie-verify which supercronic
docker exec cookie-verify cat /app/crontab
```

**Expected**:
- `grep` returns `NONE` (no secrets on disk).
- `/etc/cron.d/` is either absent or empty — the old `cookie-cleanup` file is gone.
- `cron` binary is not installed.
- `supercronic` binary exists at `/usr/local/bin/supercronic`.
- `/app/crontab` contains three schedule+command lines with NO environment values.

**Maps to**: FR-001, FR-002a, FR-002b, FR-003, User Story 1 scenarios 1 & 2

---

## Step 3 — Confirm supercronic is running as the app user

```bash
docker exec cookie-verify ps -eo user,pid,comm | grep -E "supercronic|gunicorn|nginx"
```

**Expected**: `supercronic` and `gunicorn` run as `app`. `nginx` is still root (needs port 80).

**Maps to**: FR-003

---

## Step 4 — Trigger one of the cleanup jobs manually and confirm env flows through

```bash
docker exec cookie-verify su -s /bin/bash app -c 'DJANGO_SETTINGS_MODULE=cookie.settings python manage.py cleanup_device_codes'
```

**Expected**: Command runs successfully; logs mention no missing env vars. Stop the container: `docker stop cookie-verify`.

**Maps to**: FR-002, FR-004

---

## Step 5 — Verify `docker-compose.prod.yml` pins to a concrete version

```bash
grep -E "image:\s*ghcr\.io/matthewdeaves/cookie" docker-compose.prod.yml
grep ":latest" docker-compose.prod.yml | grep -v "^#" || echo "no :latest (expected)"
```

**Expected**: Line 27 reads `image: ghcr.io/matthewdeaves/cookie:v1.44.0` (or the current release tag). No `:latest` references outside comments.

**Maps to**: FR-008, SC-004, User Story 3

---

## Step 6 — Logout replay test (automated via pytest)

```bash
docker compose exec web python -m pytest tests/test_passkey_logout_replay.py -v
```

**Expected**: Both tests pass.
- `test_logged_out_cookie_cannot_hit_auth_me` — replayed cookie → 401.
- `test_logged_out_cookie_cannot_hit_recipes_favorites` — replayed cookie → 401.

**Maps to**: FR-005, FR-006, FR-007, User Story 2, SC-003

---

## Step 7 — CSRF coverage tests (automated)

```bash
docker compose exec web python -m pytest tests/test_csrf.py -v
```

**Expected**: three new tests pass — `test_list_profiles_*`, `test_create_profile_*`, `test_select_profile_*`. All assert 403 on POST without token, 200/201 with token.

**Maps to**: FR-010, FR-011, User Story 4, SC-005

---

## Step 8 — Display-name UX in the modern SPA (manual)

1. Bring up dev stack in passkey mode: `AUTH_MODE=passkey docker compose up -d`.
2. Open `http://localhost:5173/` (SPA).
3. Navigate to the device-pair page.
4. Confirm an optional text input labelled "Name this passkey" (or similar) is visible before the Register action.
5. Type `iPhone Work`; click Register; complete the WebAuthn ceremony.
6. Open Chrome's password manager (`chrome://settings/passkeys`).
7. Confirm the stored passkey is labelled `iPhone Work`.

**Expected**: The name you typed appears in the authenticator UI. If the field is left blank, the credential is labelled `Cookie — <today's date>`.

**Maps to**: FR-012, FR-013, FR-014, FR-016, FR-017, User Story 5, SC-006

---

## Step 9 — Display-name UX in the legacy frontend (manual)

1. With the stack still up, open `http://localhost/legacy/pair/` in the same browser.
2. Confirm the device-pair template has an optional text input (ES5-safe, plain HTML `<input type="text">`).
3. Enter `Old iPad`; submit; complete the pairing.
4. Check `chrome://settings/passkeys` again — confirm the new passkey is labelled `Old iPad`.

**Expected**: Legacy frontend presents the same UX; no JS upgrades; name makes it through to the authenticator.

**Maps to**: FR-015, FR-017, User Story 5 (legacy scenario)

---

## Step 10 — Legacy `innerHTML` chokepoint regression guard

```bash
docker compose exec web python -m pytest tests/test_legacy_innerhtml_chokepoint.py -v
```

Plus the grep sanity-check:

```bash
grep -rnE "\.innerHTML\s*(=|\+=)" apps/legacy/static/legacy/js/ | grep -v utils.js || echo "clean"
```

**Expected**: the test passes; the grep prints `clean`.

Then exercise the legacy search UI manually to confirm pagination still works:

1. In the legacy frontend (`http://localhost/legacy/`), run a search that returns > 20 results.
2. Scroll to the bottom; click Load More (or similar).
3. Confirm additional result cards appear, remain clickable, and are visually identical to the first page.

**Maps to**: FR-018, FR-019, FR-020, User Story 6, SC-007

---

## Step 11 — `cookie_admin create-session --confirm` parity

```bash
# In passkey mode, with user 'alice' existing:
docker compose exec web python manage.py cookie_admin create-session alice --json
# Expected: non-zero exit, JSON error to stderr mentioning --confirm

docker compose exec web python manage.py cookie_admin create-session alice --json --confirm
# Expected: exit 0, session JSON to stdout

docker compose exec web python manage.py cookie_admin create-session alice
# Expected: interactive prompt asking [y/N]; type 'n' to abort
```

**Expected**: Each scenario behaves per the contract in `contracts/cookie-admin-create-session.md`.

**Maps to**: FR-021, FR-022, FR-023, User Story 7, SC-008

---

## Step 12 — Dependabot config validator

```bash
gh api -H "Accept: application/vnd.github+json" /repos/matthewdeaves/cookie/dependabot/alerts --include | head -1
cat .github/dependabot.yml | head -80
```

Paste the config into GitHub's Dependabot config validator (Repo → Settings → Code security → Dependabot → View config). Confirm green.

**Expected**: validator passes. After merge, watch for the first weekly PR batch (or trigger manually via Repo → Insights → Dependency graph → Dependabot → Last checked → Check for updates).

**Maps to**: FR-024, FR-025, FR-026, FR-027, User Story 8, SC-009

---

## Step 13 — CC gate (ruff C901) enforcement

Passes on master:
```bash
docker compose exec web ruff check apps/ cookie/ --select C901
# Expected: "All checks passed!"
```

Fails on a planted violation (do this on a throwaway branch):
```bash
git switch -c smoke-test-cc-gate
# Add a function with CC=16 to any apps/ file:
cat >> apps/core/auth_helpers.py << 'EOF'

def _smoke_test_cc16(x):
    if x == 1: return 1
    elif x == 2: return 2
    elif x == 3: return 3
    elif x == 4: return 4
    elif x == 5: return 5
    elif x == 6: return 6
    elif x == 7: return 7
    elif x == 8: return 8
    elif x == 9: return 9
    elif x == 10: return 10
    elif x == 11: return 11
    elif x == 12: return 12
    elif x == 13: return 13
    elif x == 14: return 14
    elif x == 15: return 15
    else: return 0
EOF
docker compose exec web ruff check apps/ --select C901
# Expected: exit non-zero, message names _smoke_test_cc16
git checkout apps/core/auth_helpers.py  # revert
git switch master && git branch -D smoke-test-cc-gate
```

**Maps to**: FR-028, User Story 9, SC-010 (CC half)

---

## Step 14 — File-size gate enforcement

Passes on master:
```bash
docker compose exec web python -m pytest tests/test_code_quality.py -v
# Expected: 1 passed
```

Fails on a planted violation (throwaway branch):
```bash
git switch -c smoke-test-filesize-gate
python -c "print('x = 1\n' * 510)" > apps/core/smoke_large.py
docker compose exec web python -m pytest tests/test_code_quality.py -v
# Expected: test fails with apps/core/smoke_large.py named as offender
rm apps/core/smoke_large.py
git switch master && git branch -D smoke-test-filesize-gate
```

**Maps to**: FR-029, User Story 9, SC-010 (file-size half)

---

## Step 15 — Full test suite + CI parity

```bash
docker compose exec web python -m pytest
docker compose exec frontend npm test -- --run
```

**Expected**: every pre-existing test continues to pass; new tests pass; totals are at least the previous 1300+ backend and 516 frontend, plus the additions from this spec.

**Maps to**: FR-032, SC-011

---

## Step 16 — Release cut and compose pin

After the branch is merged to `master`:

```bash
# Tag and publish the release
git tag v1.44.0 && git push origin v1.44.0
gh release create v1.44.0 --latest --title "v1.44.0 — security review fixes round 2" \
  --notes-file release-notes-v1.44.0.md

# Confirm the image is published
gh api repos/matthewdeaves/cookie/packages/container/cookie/versions | jq '.[0].metadata.container.tags'
# Expected: includes "v1.44.0"

# Confirm docker-compose.prod.yml already pins to v1.44.0 (landed as part of the PR)
grep -n 'image: ghcr.io/matthewdeaves/cookie' docker-compose.prod.yml
```

**Expected**: release cut, image available, compose pin matches.

**Maps to**: FR-008, FR-009, FR-034, SC-012

---

## Wrap-up

If every step passes, the spec's twelve success criteria are all met. Proceed to close the milestone and announce the release.

If any step fails, the failure maps directly to the FR/SC it's tied to — triage by FR number against `spec.md`.

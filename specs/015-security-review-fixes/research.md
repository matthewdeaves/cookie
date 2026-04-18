# Phase 0 Research: Security Review Fixes (Round 2)

All open items resolved. Decisions below are load-bearing for `plan.md` and `tasks.md`.

Scope changed during `/speckit.analyze` remediation:
- **Dropped**: original User Story 5 (WebAuthn display name). Rationale: Cookie doesn't persist display name in `WebAuthnCredential`, so the UX win only materializes in platform credential-picker UIs — minimal payoff for a single-user-per-instance deployment model. Original review finding M4 accepted as low-impact.
- **Narrowed**: CSRF coverage. Dropped three near-identical tests in favor of one `select_profile` test; the middleware is global so additional tests would exercise framework behavior.
- **Narrowed**: CC+file-size gates. Ship gate infrastructure + full allowlist; refactors deferred to follow-up spec `016-code-quality-refactor`.
- **Added**: new User Story 7 — surface profile ID in passkey-mode Settings + `--profile-id` flag on unlimited CLI commands. Makes spec 014's "CLI is the admin surface" actually usable for multi-user deployments.

---

## Decision 1 — Replace Debian `cron` with supercronic

**Decision**: Install **supercronic v0.2.44** (amd64 + arm64) in `Dockerfile.prod`, pinned with **both** the upstream-published SHA1 **and** a locally-computed SHA256. Remove the `cron` apt package and all `/etc/cron.d/*` writing from `entrypoint.prod.sh`. Schedule file is `COPY`ed in at build time — a static file with schedule + command only, no secrets. Supercronic runs as the `app` user as a sibling of gunicorn/nginx under the existing `wait -n` supervisor.

**Pinning approach (defense-in-depth)**:
1. Download the binary once during implementation.
2. Verify against the upstream SHA1 (`6eb0a8e1e6673675dc67668c1a9b6409f79c37bc` for linux-amd64 v0.2.44; `6c6cba4cde1dd4a1dd1e7fb23498cde1b57c226c` for linux-arm64). This proves we have the exact binary aptible published.
3. Compute the SHA256 of that same binary locally.
4. Bake the SHA256 into `Dockerfile.prod`. CI builds verify with `sha256sum -c` — if upstream ever retags `v0.2.44` (tag mutability) or a CDN MITM attempts a swap, the build fails.
5. Record both hashes in an inline Dockerfile comment so a future auditor can re-verify.

**Rationale**:
1. No root daemon — supercronic runs as whichever user starts it. Debian `cron` runs as root.
2. Env inherited automatically from the parent process. No `/proc/1/environ` wrapper. No secrets written anywhere on the filesystem.
3. Structured stdout logging. No `>> /proc/1/fd/1 2>&1` redirection hacks.
4. Clean SIGTERM handling. Propagates signals to in-flight jobs and waits for them.

**Alternatives rejected**: keep `cron` with wrapper (leaves root daemon); sidecar container (doubles compose complexity); entrypoint Python loop (not a real scheduler).

**Net image-size impact**: **+~15 MB** (supercronic ~16.9 MB minus Debian cron ~260–400 KB). Acceptable.

**Footguns to avoid**:
1. Leaving `cron` in the apt install line — must remove explicitly.
2. Writing the crontab from the entrypoint. Must be a static `COPY`ed file.
3. `/etc/cron.d/*` 6-field format — supercronic silently ignores the user column. Use 5-field user-crontab format.
4. Adding `>> /proc/1/fd/1 2>&1` — supercronic captures job stdout; don't.
5. Running supercronic as root — forfeits the `app` user defense-in-depth.
6. Not running `supercronic -test /path/to/crontab` preflight in the entrypoint.

**References**:
- `aptible/supercronic` README: https://github.com/aptible/supercronic
- Release v0.2.44 upstream SHA1s as above.

---

## Decision 2 — Enforce CC ≤ 15 via ruff C901, not radon

**Decision**: Add `"C90"` to `select` and `max-complexity = 15` under `[tool.ruff.lint.mccabe]` in `pyproject.toml`. Leave the existing radon `backend-complexity` CI job in place — its HTML/MI/raw reports are useful telemetry, but the **gate** rides on `ruff check` (already a required status check via `backend-lint`). No new CI job needed.

**Rationale**:
1. Radon `cc` is display-only — exits 0 at every threshold. Verified empirically.
2. `xenon` (radon's enforcement wrapper) would be a new dep.
3. Ruff already runs in CI, already exits non-zero on findings, has `C901` (mccabe) baked in. Two-line config change.
4. Current max CC in `apps/` is **14** (`sanitize_recipe_data`, `_fetch_image_safe`). Shipping the gate at 15 is a zero-refactor change for CC. The gate ratchets against future regressions.

**Gate scope (per F1 clarification)**: both `apps/` AND `tests/`, migrations excluded.

**Config**:
```toml
[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "SIM", "DJ", "S", "C90"]

[tool.ruff.lint.mccabe]
max-complexity = 15

[tool.ruff.lint.per-file-ignores]
"*/migrations/*.py" = ["C901"]
```

**Alternatives rejected**: `xenon --max-absolute D` (new dep, new CI job); grep radon output (brittle).

---

## Decision 3 — File-size gate via pytest static test, with explicit allowlist

**Decision**: Add `tests/test_code_quality.py::test_py_file_size_under_limit`. Globs `apps/**/*.py` and `tests/**/*.py`, excludes `**/migrations/*.py`, reads each file, counts `\n`, fails on any file > 500 lines UNLESS the file is in an explicit `EXEMPT_FILES` allowlist. The test runs in the already-required `backend-test` CI job.

**Gate scope**: both `apps/` AND `tests/`, migrations excluded.

**Current violators** (audited 2026-04-18):

_Production code in `apps/`_ (3 files — grandfathered in allowlist, refactor in follow-up spec):
- `apps/core/management/commands/cookie_admin.py` — 1172 lines
- `apps/ai/api.py` — 534 lines
- `apps/recipes/services/scraper.py` — 517 lines

_Test code in `apps/`_ (2 files — also grandfathered):
- `apps/ai/tests.py` — 1852 lines
- `apps/recipes/tests.py` — 564 lines

_Top-level `tests/`_ (8 files — also grandfathered):
- `tests/test_passkey_api.py` — 903 lines
- `tests/test_recipes_api.py` — 799 lines
- `tests/test_cookie_admin.py` — 792 lines
- `tests/test_ai_quota.py` — 768 lines
- `tests/test_search.py` — 718 lines
- `tests/test_system_api.py` — 701 lines
- `tests/test_image_cache.py` — 674 lines
- `tests/test_ai_api.py` — 597 lines
- `tests/test_device_code_api.py` — 540 lines
- `tests/test_user_features.py` — 524 lines

Total: **13 files** (wait — that's 13 total counting all three groups: 3 + 2 + 10 = 15). Recounting top-level `tests/` at 10 entries. Updated total in FR-030 to match the precise allowlist.

Actually: 3 production + 2 apps/-tests + 10 top-level tests = **15 files**.

**Allowlist shape** (`tests/test_code_quality.py`):
```python
# Grandfathered file-size violators. Cleanup tracked in spec 016-code-quality-refactor.
# Every entry MUST list the file's line count at the time of grandfathering — this is
# the ceiling for that file. Adding lines to a grandfathered file moves the ceiling
# and fails CI ("no gaming the ratchet").
EXEMPT_FILES: dict[str, int] = {
    "apps/core/management/commands/cookie_admin.py": 1172,
    "apps/ai/api.py": 534,
    "apps/recipes/services/scraper.py": 517,
    "apps/ai/tests.py": 1852,
    "apps/recipes/tests.py": 564,
    "tests/test_passkey_api.py": 903,
    "tests/test_recipes_api.py": 799,
    "tests/test_cookie_admin.py": 792,
    "tests/test_ai_quota.py": 768,
    "tests/test_search.py": 718,
    "tests/test_system_api.py": 701,
    "tests/test_image_cache.py": 674,
    "tests/test_ai_api.py": 597,
    "tests/test_device_code_api.py": 540,
    "tests/test_user_features.py": 524,
}
```

**Gate algorithm**:
1. For each `*.py` under `apps/` and `tests/` (excluding migrations), compute line count.
2. If > 500 AND file path is NOT in `EXEMPT_FILES`, fail.
3. If > 500 AND file path IS in `EXEMPT_FILES`, compare current count to ceiling. If current > ceiling, fail with "grandfathered file added lines; ceiling is N, current is M — refactor or reduce the file".
4. If ≤ 500 AND file path IS in `EXEMPT_FILES`, fail with "grandfathered file is now under limit; remove its entry from EXEMPT_FILES".

This is the "no gaming the ratchet" enforcement.

**Refactors deferred**: follow-up spec `016-code-quality-refactor`. This spec ships ONLY gate infrastructure + allowlist. Zero production-code refactoring happens here so a security PR doesn't mix with a code-quality refactor PR.

**Alternatives rejected**:
- `check-added-large-files` (measures bytes, not lines)
- bash/awk in CI (terse failures)
- Refactor all 15 files in this spec (~3000 lines of churn, mixing concerns)
- Raise the limit (forbidden by Constitution Principle V)

---

## Decision 4 — Dependabot config with per-ecosystem grouping

**Decision**: `.github/dependabot.yml` covering five ecosystems (pip, npm, docker, docker-compose, github-actions). Weekly Monday 09:00 Australia/Sydney. One grouped PR per ecosystem per week for minor+patch; majors ungrouped. Security updates split automatically. Labels: `dependencies` + ecosystem label. Assignees: `["matthewdeaves"]`. PR limit: 5 for pip/npm, 3 for docker/actions.

**Rationale**:
1. `docker-compose` went GA as a separate ecosystem in Feb 2025 — list it separately.
2. Groups with `update-types: [minor, patch]` keep majors ungrouped (e.g., Django N→N+1 stays reviewable).
3. `@types/*` gets its own npm group — trivial bumps shouldn't pollute review queues.
4. Security PRs bypass grouping by default (no config needed).
5. Base-image digest pins (`@sha256:...`) handled natively by the docker ecosystem.

**Alternatives rejected**: one big everything-grouped PR (unreviewable); daily schedule (reviewer-fatigue burden).

**References**:
- GitHub Dependabot options reference
- Docker Compose GA announcement (Feb 2025)

---

## Decision 5 — Logout session flush + passkey-fallback audit

**Decision**:
1. Add `request.session.flush()` immediately after `logout(request)` in `apps/core/auth_api.py:33`.
2. Leave the passkey-fallback in `apps/core/auth.py:52-81` as-is. After the flush, `session.get("profile_id")` returns `None`, so the fallback can no longer re-authenticate a logged-out cookie. The fallback still bridges the login/middleware handoff.
3. Add `tests/test_passkey_logout_replay.py`: login → capture cookie → logout → replay → assert 401.

**Rationale**: `django.contrib.auth.logout()` clears only Django auth keys, not the whole session. `profile_id` survives. `session.flush()` deletes the session row entirely; the cookie the client holds is now invalid.

---

## Decision 6 — CSRF coverage: one test, not three

**Decision**:
1. Write a single integration test `tests/test_csrf.py::TestPreSessionProfileCsrf::test_select_profile_rejects_without_csrf`. POST `/api/profiles/{id}/select/` with no CSRF token → 403; same POST with token → 200.
2. Don't bother with `list_profiles` (GET — CSRF doesn't apply) or `create_profile` (structurally identical CSRF surface to `select_profile` — one test is sufficient regression coverage against future `@csrf_exempt` drift).

**Rationale**: Django's `CsrfViewMiddleware` is global in `cookie/settings.py`. It applies to every non-safe-method request regardless of the Ninja `auth=` parameter. Writing three tests that exercise framework behavior is redundant.

**Fix only if test fails**: if the test unexpectedly shows a token-less POST succeeding, add `@csrf_protect` explicitly. Expected: the test passes on master; zero code change needed.

---

## Decision 7 — Legacy `innerHTML` chokepoint: route through `setHtml` via DOM fragment

**Decision**:
1. Rewrite `apps/legacy/static/legacy/js/pages/search.js:260` pagination from `elements.resultsGrid.innerHTML += html` to: create a detached `div` via `document.createElement`, set its contents via `Cookie.utils.setHtml(div, html)` (audited chokepoint), then `while (div.firstChild) resultsGrid.appendChild(div.firstChild)`.
2. Add a static-test regression guard `tests/test_legacy_innerhtml_chokepoint.py` that greps `apps/legacy/static/legacy/js/` for `.innerHTML\s*(=|\+=)` outside `utils.js` and asserts zero matches.

**Rationale**: The chokepoint pattern's purpose is single-site auditability. Every bypass corrodes the pattern. `appendChild` preserves escape-safety, doesn't re-parse, stays ES5-compatible.

---

## Decision 8 — `cookie_admin create-session --confirm` parity

**Decision**: Follow the exact pattern used by `cookie_admin reset`:
1. Add `--confirm` argparse flag to `create-session` subparser.
2. At the top of `_handle_create_session`, if `options.get("as_json")` and not `options.get("confirm")`: call `self._error(...)` with a message like `"--confirm flag required for non-interactive create-session. Re-run with: cookie_admin create-session {options['username']} --json --confirm"`.
3. Interactive mode (no `--json`) unchanged — existing prompt stays.

---

## Decision 9 — Version bump and compose pin

**Decision**: Bump `COOKIE_VERSION` from `1.43.0` → `1.44.0` in `cookie/settings.py`. Update `docker-compose.prod.yml` image reference to `ghcr.io/matthewdeaves/cookie:v1.44.0`. Add a bullet to `CLAUDE.md`'s Releases & Versioning section: "When tagging a release, update the compose image pin in `docker-compose.prod.yml` to match."

**Rationale**: MINOR bump because this is security hardening + a breaking CLI change (`create-session --confirm`) with no data-model changes.

---

## Decision 10 — Surface profile ID in passkey-mode Settings (User Story 7)

**Decision**:
1. **Modern SPA**: in `frontend/src/components/settings/SettingsGeneral.tsx`, add a small read-only caption within the About section (or a dedicated "Account" panel at the top of Preferences). Only rendered when `mode === 'passkey'` (via the existing `useMode()` hook). Shows `profile.id` from the existing `useProfile()` context (already populated from `/api/auth/me`). Suggested copy: `"Account ID: 17 (share with your admin to request quota changes)"`.
2. **Legacy**: in `apps/legacy/templates/legacy/settings.html`, add a conditional `{% if auth_mode == 'passkey' %}` block displaying `{{ current_profile_id }}`. Data is already available via the template context (seen at line 11 of settings.html).
3. **CLI**: in `apps/core/management/commands/cookie_admin.py`, extend both `_handle_set_unlimited` and `_handle_remove_unlimited` to accept an optional `--profile-id N` that takes precedence over the positional `username` when both are absent. Update the subparser definitions to include `--profile-id` as a mutually-exclusive alternative. When `--profile-id` is given, fetch `Profile.objects.get(id=N)`, derive `user = profile.user`, then reuse the existing `user.profile.unlimited_ai = ...` code path.

**Rationale**:
- `profile.id` is already in `/api/auth/me` (confirmed: `apps/core/auth_helpers.py:16-23`). Zero new API changes.
- Integer is harder to typo over the phone than `pk_a3f91c2e`.
- No PII added to any data response — `profile.id` is already exposed to its owner.
- `--profile-id` is additive; existing `set-unlimited <username>` scripts keep working.
- Home mode deliberately does NOT show the ID — there's no admin concept, so the integer would be noise.

**Alternatives rejected**:
- Show `user.username` (the `pk_<uuid8>`): explicitly declined by user ("I don't want to record username etc").
- Show only in one frontend: breaks Principle I (multi-generational access — both frontends must support the feature).
- Rename `--profile-id` to `--id`: ambiguous with user ID vs profile ID.

**Sanitization**: none needed. `profile.id` is an integer; no string interpolation into the CLI or DOM.

**Security note**: `profile.id` is not a secret. It's returned to every authenticated user via `/auth/me`. Surfacing it in Settings is a display-only change with no new authz surface.

---

## Summary: Open clarifications from the spec — all resolved

| Spec clarification | Resolution | Decision # |
|---|---|---|
| Cron env-passing vs sidecar | supercronic in-container | 1 |
| Radon enforcement: audit now or later | Ruff C901 (threshold passes today); file-size gate with full allowlist; refactors in follow-up 016 | 2 + 3 |
| Dependabot grouping | Grouped per ecosystem, majors ungrouped | 4 |
| Logout replay hardening | session.flush() post-logout | 5 |
| CSRF test scope | One test (`select_profile`) | 6 |
| Display-name UX | **Dropped** (low payoff for Cookie's deployment model) | — |
| Multi-user identifier disclosure for CLI admin ops | Surface `profile.id` in passkey-mode Settings; add `--profile-id` to CLI | 10 |

Ready for Phase 1. No remaining NEEDS CLARIFICATION markers.

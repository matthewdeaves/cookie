# Implementation Plan: Security Review Fixes (Round 2)

**Branch**: `015-security-review-fixes` | **Date**: 2026-04-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification at `/home/matt/cookie/specs/015-security-review-fixes/spec.md`

## Summary

Close the nine verified findings from the v1.43.0 security review in a single release (`v1.44.0`). The one HIGH (secrets persisted in `/etc/cron.d/cookie-cleanup`) is resolved by swapping Debian `cron` for supercronic, which inherits env from the entrypoint process and reads a secret-free crontab. The four MEDIUMs resolve in-place: `session.flush()` on logout, `:latest` → `:v1.44.0` in `docker-compose.prod.yml`, CSRF-coverage tests for pre-session profile endpoints, and a user-supplied `display_name` on passkey registration surfaced in both frontends. The legacy innerHTML-chokepoint violation, `create-session --confirm` parity, Dependabot config, and a ruff-backed CC gate round out the three LOWs plus the file-size refactor work needed to enable the gate. No data-model changes; three `apps/` files refactored to hit the 500-line limit; both frontends remain fully functional in both auth modes.

## Technical Context

**Language/Version**: Python 3.14 (backend), TypeScript 5.9 (modern frontend), ES5 (legacy frontend)
**Primary Dependencies**: Django 5.0, Django Ninja 1.0+, py-webauthn 2.7+, React 19, Vite 7, supercronic v0.2.44 (new), ruff 0.15.9 (existing — reconfigured)
**Storage**: PostgreSQL 16+ (no schema changes)
**Testing**: pytest 8 (backend — adds `tests/test_csrf.py`, `tests/test_code_quality.py`, `tests/test_passkey_logout_replay.py`, `tests/test_legacy_innerhtml_chokepoint.py`, `tests/test_cookie_admin.py` additions), Vitest 4 (frontend — adds/updates DevicePair tests)
**Target Platform**: Linux server (Docker, linux/amd64 primary with linux/arm64 build support)
**Project Type**: Dual-frontend web application (Django backend, React SPA, legacy ES5 frontend)
**Performance Goals**: No change. Scheduler migration is user-invisible; login/logout flow unchanged in steady state.
**Constraints**: Both frontends MUST remain fully functional in both `AUTH_MODE=home` and `AUTH_MODE=passkey`. All 1300+ backend tests and 516 frontend tests pass. All CI gates remain green post-refactor. The three `apps/` file-size refactors must preserve all public APIs.
**Scale/Scope**: ~30 files touched (3 large refactors + ~27 small diffs + configs + tests). One semver MINOR bump (v1.43.0 → v1.44.0).

## Constitution Check

*GATE: must pass before Phase 0; re-checked after Phase 1.*

| Principle | Compliance | Notes |
|-----------|------------|-------|
| I. Multi-Generational Device Access | ✅ Pass | Legacy frontend receives the new display-name input (ES5 text field) and keeps the search pagination functional after the innerHTML-chokepoint refactor. All legacy JS remains ES5. |
| II. Privacy by Architecture | ✅ Pass | No new data collected. Display name is stored only in the WebAuthn credential, not in an app table. No email, no PII, no telemetry added. |
| III. Dual-Mode Operation | ✅ Pass | Home mode unchanged (profile selection, CSRF tests cover pre-session endpoints). Passkey mode gets session flush on logout + display-name at registration. CSRF tests are mode-agnostic. No mode switches introduced. |
| IV. AI as Enhancement, Not Dependency | ✅ Pass | No AI code changes. |
| V. Code Quality Gates Are Immutable | ✅ **Required by spec** | Spec FR-028/029/030/031 enforces the limits. Plan refactors the three `apps/` files currently over 500 lines; ruff C901 gate lands at CC ≤ 15 (current max is 14, so zero-refactor for CC). No thresholds raised. No `# noqa` / suppression comments added. |
| VI. Docker Is the Runtime | ✅ Pass | supercronic installed inside the production image; all new commands run via `docker compose exec`. |
| VII. Security by Default | ✅ **Directly advanced** | Every FR in this spec advances a Principle VII rule: no secrets on disk (cron), CSRF coverage, session flush on logout, pinned prod image, sanitized input (display name), safer CLI defaults (`--confirm`). |

**Gate result**: PASS. No justified violations; no Complexity Tracking entries required.

## Project Structure

### Documentation (this feature)

```text
specs/015-security-review-fixes/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 decisions (supercronic, ruff C901, sanitation, ...)
├── data-model.md        # Phase 1: schema deltas (tiny — crontab file, register-options input)
├── quickstart.md        # Phase 1: end-to-end manual verification
├── contracts/           # Phase 1: register-options contract, logout contract, CLI contract, dependabot contract
│   ├── passkey-register-options.md
│   ├── auth-logout.md
│   ├── cookie-admin-create-session.md
│   └── dependabot-config.md
├── checklists/
│   └── requirements.md  # Quality checklist (already passing)
└── tasks.md             # Phase 2 output (not created by /speckit.plan)
```

### Source Code (repository root)

```text
apps/
├── core/
│   ├── auth_api.py                      # MODIFY: session.flush() in logout_view
│   ├── auth_helpers.py                  # MODIFY: add sanitize_display_name()
│   ├── passkey_api.py                   # MODIFY: register-options accepts display_name; credential add pipes sanitizer; also REFACTOR to ≤500 lines
│   └── management/commands/
│       └── cookie_admin.py              # MODIFY: create-session --confirm; REFACTOR to ≤500 lines by extracting subcommand handlers
├── ai/
│   └── api.py                           # REFACTOR: consolidate remaining endpoints into existing api_*.py modules; get under 500 lines
├── recipes/
│   └── services/
│       └── scraper.py                   # REFACTOR: extract redirect chain helper into services/redirect.py; get under 500 lines
├── profiles/
│   └── api.py                           # NO CHANGE (CSRF fix is test-only if tests pass; decorators added only if needed)
└── legacy/
    ├── static/legacy/js/pages/
    │   └── search.js                    # MODIFY: replace innerHTML += with setHtml + appendChild pattern
    ├── templates/legacy/
    │   └── device_pair.html             # MODIFY: add optional display-name input
    └── views.py                         # NO CHANGE

frontend/
└── src/
    ├── pages/
    │   └── DevicePair.tsx               # MODIFY: add optional display-name input; wire into register-options fetch
    └── api/
        └── types.ts                     # MODIFY: add display_name to register-options request type

cookie/
└── settings.py                          # MODIFY: COOKIE_VERSION 1.43.0 → 1.44.0

tests/
├── test_csrf.py                         # ADD tests: list_profiles GET no-token OK; create_profile POST no-token 403, with-token 201; select_profile POST no-token 403, with-token 200
├── test_passkey_logout_replay.py        # ADD: login → capture cookie → logout → replay → assert 401
├── test_code_quality.py                 # ADD: apps/ file-size static test; asserts ≤ 500 lines per file (excluding migrations/tests)
├── test_legacy_innerhtml_chokepoint.py  # ADD: grep static test for .innerHTML\s*(=|\+=) outside utils.js
├── test_cookie_admin.py                 # MODIFY: add create-session --confirm cases
└── test_passkey_display_name.py         # ADD: register-options with display_name → name appears in options; sanitation cases
frontend/test/
└── DevicePair.test.tsx                  # MODIFY: test the display-name input renders and sends value in register-options request

Dockerfile.prod                          # MODIFY: install supercronic (pinned SHA1), remove cron package
entrypoint.prod.sh                       # MODIFY: remove /etc/cron.d/cookie-cleanup write, launch supercronic as app user, supervise alongside gunicorn/nginx
docker-compose.prod.yml                  # MODIFY: image :latest → :v1.44.0
crontab                                  # ADD (new top-level static file): three entries, no secrets
pyproject.toml                           # MODIFY: add C90 to ruff select, max-complexity=15, per-file-ignores for migrations
.github/dependabot.yml                   # ADD (or replace existing skeleton): five ecosystems, weekly, grouped, assignees
CLAUDE.md                                # MODIFY: add compose-pin step to release checklist
```

**Structure Decision**: dual-frontend Django layout — matches existing project shape. No new top-level directories except the root `crontab` file. The three `apps/` refactors stay within their current app boundaries (no cross-app dependencies introduced). Legacy frontend changes stay in `apps/legacy/`. Modern frontend changes stay in `frontend/src/`.

## Phase 0 Summary

All unknowns resolved. See `research.md` for decisions 1–10 with rationale, alternatives, and references. Headlines:

- Scheduler: **supercronic v0.2.44**, pinned by **locally-computed SHA256** (cross-verified once against upstream SHA1 `6eb0a8e1e6673675dc67668c1a9b6409f79c37bc` for linux-amd64 / `6c6cba4cde1dd4a1dd1e7fb23498cde1b57c226c` for linux-arm64 at implementation time), multi-arch, run as `app` user. Dockerfile uses `sha256sum -c` to enforce the pin on every build — a retagged upstream or CDN swap fails the build.
- CC gate: ruff `C901` + `max-complexity = 15` in `pyproject.toml`. Current `apps/` max CC is 14 — zero-refactor for CC.
- File-size gate: pytest static test `tests/test_code_quality.py` gated by existing `backend-test` CI job. Three `apps/` refactors required to pass.
- Display-name sanitation: NFC → strip `Cc`/`Cf`/`Cs`/`Co`/`Cn` → collapse whitespace → trim → 60-byte UTF-8-boundary truncate. Fallback `f"Cookie — {today.isoformat()}"`. Pass to **both** `user_name` and `user_display_name`.
- Logout: `request.session.flush()` post-`logout(request)`. Fallback code in `auth.py` stays — it's now de-fanged by the flush.
- CSRF: tests first. Fixes only if tests expose a gap.
- Dependabot: five ecosystems, weekly Monday, groups with `minor`+`patch`, majors ungrouped.
- Version: `v1.43.0` → `v1.44.0`; compose pin matches.

## Phase 1 Summary

Detailed artifacts written in this phase:

- **`data-model.md`** — the tiny schema deltas: register-options input gains `display_name: str | None`, crontab file is a new on-disk entity, ruff config picks up a key, pytest static test picks up a constant.
- **`contracts/`** — four contract documents for the externally-observable interfaces touched:
  1. `passkey-register-options.md` — the register-options request/response, sanitation, default fallback, credential-add flow.
  2. `auth-logout.md` — the logout endpoint's post-condition (session fully flushed, subsequent replay returns 401).
  3. `cookie-admin-create-session.md` — CLI flag parity, exit codes, JSON output shape.
  4. `dependabot-config.md` — the dependabot.yml schema the repo commits to.
- **`quickstart.md`** — 14-step end-to-end manual verification: cron→supercronic swap, logout replay, `:latest` pin grep, CSRF tests, display-name UX in both frontends, legacy pagination, CLI parity, Dependabot validator, CC and file-size gates, compose-pin release step.

## Post-Design Constitution Re-check

Re-evaluated against each principle after writing Phase 1 artifacts:

| Principle | Post-design verdict |
|-----------|---------------------|
| I. Multi-Generational Device Access | ✅ Confirmed — legacy `device_pair.html` gets an ES5-safe `<input>`, no JS syntax upgrades. |
| II. Privacy by Architecture | ✅ Confirmed — display_name stored only in WebAuthn credential (managed by authenticator), not in any DB table. |
| III. Dual-Mode Operation | ✅ Confirmed — no mode-selection changes; CSRF tests cover home-mode endpoints; session flush applies to passkey-mode logout (home mode has no logout). |
| IV. AI as Enhancement, Not Dependency | ✅ No AI touched. |
| V. Code Quality Gates Are Immutable | ✅ Three refactors planned to bring `apps/` under 500-line limit. Gate lands at the constitution's values, not raised. |
| VI. Docker Is the Runtime | ✅ All new commands (supercronic install, crontab COPY, ruff/pytest invocations) are containerized. |
| VII. Security by Default | ✅ Every user story advances a specific Principle VII rule. |

**Re-check result**: PASS. Plan is locked; proceeding to `/speckit.tasks`.

## Complexity Tracking

No violations to justify. Plan operates strictly within constitution bounds.

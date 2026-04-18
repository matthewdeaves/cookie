# Implementation Plan: Lock admin surface to home mode only; add CLI parity for passkey-mode ops

**Branch**: `013-admin-home-only` | **Date**: 2026-04-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/013-admin-home-only/spec.md`

## Summary

Harden Cookie's passkey-mode deployment by removing the web admin surface (18 endpoints + settings UI) from that mode, while keeping home mode unchanged. Operators manage passkey deployments exclusively via `python manage.py cookie_admin`, whose subcommand set is expanded to match the removed web features. Also remove the Cookie version string from `GET /api/system/mode/` (eliminates fingerprinting). Ship as v1.42.0 (MINOR — security hardening).

**Technical approach**

1. **Backend gate**: a thin `HomeOnlyAdminAuth(AdminAuth)` subclass in `apps/core/auth.py` overrides `__call__` to raise `ninja.errors.HttpError(404, "Not found")` when `AUTH_MODE != "home"`, otherwise delegates to `super().__call__(request)`. Swap `auth=AdminAuth()` → `auth=HomeOnlyAdminAuth()` on the 18 handlers across `apps/ai/api.py`, `apps/ai/api_quotas.py`, `apps/core/api.py`, `apps/recipes/api.py`, `apps/recipes/sources_api.py`, `apps/profiles/api.py`. (A plain `@wraps` decorator above `@router.*` does not work: Ninja's view wrapper resolves `auth=` before invoking the inner function, so the decorator would run too late to satisfy FR-002.)
2. **Backend cleanup**: delete the inline `if AUTH_MODE == "passkey"` 403 blocks in `apps/core/api.py` reset handlers; remove the `version` key from `get_mode` response; remove any helpers whose only caller was the deleted blocks.
3. **Frontend hide**: legacy templates extend `{% if is_admin %}` to `{% if is_admin and auth_mode == "home" %}` (context var already exists). SPA components guard admin sections with `useMode() === 'home'` from the existing `router.tsx::ModeContext`.
4. **CLI expansion**: add new subcommands to `apps/core/management/commands/cookie_admin.py`, refactor the blanket passkey-mode guard to apply only to user-lifecycle subcommands, and extend `status --json` with a cache block.
5. **Tests**: per-endpoint 404-in-passkey integration tests; unchanged home-mode tests; happy/error path tests per new CLI subcommand with `security_logger` assertions; one Vitest test for the SPA hide behavior.
6. **Release**: bump `COOKIE_VERSION` to `1.42.0` and publish a GitHub release with a Security section.

## Technical Context

**Language/Version**: Python 3.14 (backend), TypeScript 5.9 (modern frontend), ES5 (legacy frontend)
**Primary Dependencies**: Django 5.0, Django Ninja 1.0+, `django-ratelimit` 4.1, py-webauthn 2.x (passkey mode only), React 19, Vite 7, Vitest 4, React Testing Library (existing)
**Storage**: PostgreSQL 16+ (no schema changes; reads/writes existing `AppSettings`, `AIPrompt`, `SearchSource`, `Profile`, `User` tables)
**Testing**: pytest (backend), Vitest 4 + React Testing Library (frontend). All backend commands run via `docker compose exec web …`; frontend via `docker compose exec frontend …` per constitution Principle VI.
**Target Platform**: Linux container (docker compose); dual frontend (modern React + legacy ES5 on iOS 9 Safari)
**Project Type**: Django backend + React SPA + ES5 legacy frontend (the "web application" layout)
**Performance Goals**: No new perf targets. Decorator overhead is a single `settings.AUTH_MODE != "home"` comparison per gated request — negligible. No DB changes.
**Constraints**:
- Zero behavior change in home mode; all existing home-mode tests pass unmodified.
- Decorator MUST run before `AdminAuth` so that 404 probes produce no auth-failure log line.
- In passkey mode, 404 body MUST match `{"detail": "Not found"}` (Ninja default) so the endpoint is indistinguishable from a never-existed route.
- API key value MUST NEVER appear in logs; `security_logger.warning` only records that a change occurred.
- ES5 legacy templates stay ES5-compatible (server-side template logic only — no new JS).
**Scale/Scope**: Repo-local change. 18 endpoint decorations + ~18 new CLI subcommands + ~14 frontend component guards. Integration tests add ~18 passkey-mode 404 assertions + per-subcommand CLI tests (~40 tests).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Applies? | Compliance | Notes |
|-----------|----------|-----------|-------|
| I — Multi-Generational Device Access | Yes | PASS | Legacy templates get template-only edits (`{% if is_admin and auth_mode == "home" %}`). No new ES5 JS. Modern SPA uses existing `useMode()`. Both frontends hide admin UI identically in passkey mode. |
| II — Privacy by Architecture | Yes | PASS | No new data collected. `security_logger` warnings do NOT log API key values. Removing `version` from `/api/system/mode/` reduces fingerprinting surface. |
| III — Dual-Mode Operation | Yes | PASS (centerpiece) | Implements the "mode-specific endpoints MUST return 404; mode-specific UI MUST be hidden" rule concretely. |
| IV — AI as Enhancement, Not Dependency | Yes | PASS | `sources repair` CLI exits cleanly with a clear error when no API key is configured. Hiding admin UI does not affect non-admin AI-dependent features. |
| V — Code Quality Gates Are Immutable | Yes | PASS (with watch-point) | New CLI subcommands split by verb (`_handle_set_api_key`, `_handle_prompts_set`, etc.). `cookie_admin.py` is already 27.5 KB — if new subcommands push the file past 500 lines we split it into a `cookie_admin/` package. Decorator is <10 lines, trivially under the complexity cap. |
| VI — Docker Is the Runtime | Yes | PASS | All commands documented as `docker compose exec …`. No host-side Python/Node use. |
| VII — Security by Default | Yes | PASS (primary motivation) | Closes HexStrike-flagged admin surface, removes version fingerprint, tightens audit-log hygiene. |

**Gate result**: Pass. No justified violations. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/013-admin-home-only/
├── plan.md              # This file
├── spec.md              # Feature specification (with Clarifications section)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── cli-subcommands.md
│   └── gated-endpoints.md
├── checklists/
│   ├── requirements.md
│   └── security.md      # Produced by /speckit.checklist
└── tasks.md             # /speckit.tasks output
```

### Source Code (repository root)

```text
apps/
├── core/
│   ├── auth.py                       # ADD: HomeOnlyAdminAuth subclass of AdminAuth (mode gate before auth)
│   ├── api.py                        # EDIT: remove inline passkey-mode 403 blocks; remove version key from /mode/
│   └── management/
│       └── commands/
│           └── cookie_admin.py       # EDIT: refactor passkey-mode guard; add new subcommands; extend status --json with cache
├── ai/
│   ├── api.py                        # EDIT: auth=HomeOnlyAdminAuth() on 7 endpoints (save-api-key, test-api-key, prompts GET, prompts GET/{type}, prompts PUT/{type}, repair-selector, sources-needing-attention)
│   └── api_quotas.py                 # EDIT: auth=HomeOnlyAdminAuth() on PUT /quotas
├── recipes/
│   ├── api.py                        # EDIT: auth=HomeOnlyAdminAuth() on GET /cache/health/
│   └── sources_api.py                # EDIT: auth=HomeOnlyAdminAuth() on 5 endpoints (toggle, bulk-toggle, selector PUT, test, test-all)
├── profiles/
│   └── api.py                        # EDIT: auth=HomeOnlyAdminAuth() on 2 endpoints (set-unlimited, rename)
└── legacy/
    └── templates/legacy/
        ├── settings.html             # EDIT: every {% if is_admin %} → {% if is_admin and auth_mode == "home" %}
        └── partials/*                # EDIT: same pattern on any admin-only includes (verify with grep for is_admin)

frontend/src/
├── components/settings/
│   ├── APIKeySection.tsx             # EDIT: guard with useMode() === 'home' (early return null)
│   ├── SettingsPrompts.tsx           # EDIT
│   ├── PromptCard.tsx                # used only from admin container — container guards
│   ├── SettingsSelectors.tsx         # EDIT
│   ├── SelectorItem.tsx              # container guards
│   ├── SettingsSources.tsx           # EDIT
│   ├── SourceItem.tsx                # container guards
│   ├── ConfirmResetStep.tsx          # EDIT
│   ├── ResetPreviewStep.tsx          # EDIT
│   ├── DangerZoneInfo.tsx            # EDIT
│   ├── SettingsDanger.tsx            # EDIT
│   ├── AIQuotaSection.tsx            # EDIT
│   ├── UserProfileCard.tsx           # EDIT: admin controls inside mode-guarded
│   └── SettingsUsers.tsx             # EDIT: admin bits inside mode-guarded
├── screens/Settings.tsx              # EDIT: tab visibility guarded by useMode() === 'home'
└── test/
    └── Settings.passkey-hide.test.tsx # ADD: Vitest — mounts Settings with mode='passkey'; asserts admin-only components absent

tests/                                # pytest
└── test_home_mode_only_decorator.py  # ADD: 18 × 404-in-passkey assertions
apps/core/tests.py                    # EDIT: add decorator unit test (home pass-through)
apps/ai/tests.py                      # EDIT: remove any obsolete passkey-mode 403 assertions if present
apps/recipes/tests.py                 # EDIT: same
apps/profiles/tests.py                # EDIT: same
apps/core/tests.py (cookie_admin)     # EDIT: per-subcommand tests (happy, invalid, security log)

cookie/
└── settings.py                       # EDIT: bump COOKIE_VERSION default to "1.42.0"
```

**Structure Decision**: Use the existing multi-app Django + React SPA + legacy ES5 layout; no new top-level directories. The decorator lives in `apps/core/auth.py` alongside `SessionAuth` and `AdminAuth` so any future handler naturally discovers it alongside the authenticators.

## Phase 0: Outline & Research

See [research.md](./research.md). No unresolved `NEEDS CLARIFICATION`. Research items (all resolved):

- **R1 — Where the mode check runs**: A `@wraps` decorator attached to a Ninja view runs *inside* Ninja's view wrapper — AFTER `auth=…` resolution. That defeats FR-002. **Decision**: implement the gate as `HomeOnlyAdminAuth(AdminAuth)` whose `__call__` checks mode first and raises `HttpError(404)` before the base-class cookie extraction runs. See research.md for the full arc.
- **R2 — 404 body shape**: `ninja.errors.HttpError(404, "Not found")` produces `{"detail": "Not found"}` (Ninja's default shape). Raising preserves the declared response schema of each handler. **Decision**: raise, do not return.
- **R3 — SPA mode context**: `useMode()` already exists in `frontend/src/router.tsx` (`ModeContext`); consumers include `router.tsx` and `Settings.tsx`. **Decision**: reuse `useMode()`; do NOT add `mode` to `AuthContext`.
- **R4 — `AppSettings.openrouter_api_key` writes**: property setter handles encryption; `obj.openrouter_api_key = value; obj.save()` is the correct write pattern.
- **R5 — CLI passkey-mode guard refactor**: keep blanket guard? No — split into a class-level `PASSKEY_ONLY_SUBCOMMANDS` set consulted in dispatch. Existing user-lifecycle subcommands retain the guard; all others do not.
- **R6 — `--stdin` UX**: use `sys.stdin.read().strip()` for single-line key input; reject empty stdin with clear error.
- **R7 — File-based prompt content**: `--system-file PATH` and `--user-file PATH` read the file with UTF-8; missing/unreadable file aborts before DB write.

## Phase 1: Design & Contracts

**Prerequisites**: `research.md` complete.

1. **Data model** — [data-model.md](./data-model.md): no new entities. Documents how the existing `AppSettings`, `AIPrompt`, `SearchSource`, `Profile`, `User` are read/written by each new CLI subcommand, including which fields are affected and any constraints.

2. **Contracts** — [contracts/](./contracts/):
   - `cli-subcommands.md` — one row per new subcommand: name, flags, exit codes, example output (plain + `--json`), security log line template.
   - `gated-endpoints.md` — 18 endpoints × 3 caller states (anon, non-admin, admin) × 2 modes. In passkey, every cell is `404 {"detail":"Not found"}`. In home, every cell matches current behavior (linked to existing tests).

3. **Agent context update**: run `.specify/scripts/bash/update-agent-context.sh claude` after plan.md is written. Adds no new technology rows — all stack entries already tracked in `CLAUDE.md`.

4. **Quickstart** — [quickstart.md](./quickstart.md): operator walkthrough — how to run each new CLI subcommand on a passkey deployment; how to probe the 18 endpoints for 404; how to confirm the admin UI is hidden; how to tag and release `v1.42.0`.

**Post-design Constitution Re-check**: All rows remain PASS. Proceed to `/speckit.tasks`.

## Complexity Tracking

No violations of Constitution gates. No entries required.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |

# Implementation Plan: Remove is_staff; consolidate privilege on Profile.unlimited_ai

**Branch**: `014-remove-is-staff` | **Date**: 2026-04-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/014-remove-is-staff/spec.md`

## Summary

Eliminate `User.is_staff` as a privilege signal across all Cookie application code. The single remaining behavior it grants in production — AI quota bypass — consolidates onto the already-existing `Profile.unlimited_ai` field (which has CLI tooling). Home mode's full admin UI continues to work for any profile; passkey mode's admin surface remains CLI-only (v1.42.0 baseline). As compounding simplifications we also (a) rename `HomeOnlyAdminAuth` → `HomeOnlyAuth` and drop its admin-check responsibility (the admin concept disappears from the auth layer), (b) gate the entire `/api/profiles/*` namespace behind the same home-only pattern, (c) delete `AdminAuth` (0 direct call sites), (d) strip `promote`/`demote`/`--admin`/one-admin-floor from the CLI, (e) remove `is_admin` from `/auth/me`, (f) audit and trim all informational CLI subcommand outputs (`status`, `audit`, `list-users`), and (g) amend constitution Principle III to reflect that passkey users are peers and admin work is CLI-only. No data migration; `is_staff` column stays on the Django `AbstractUser` model but becomes inert metadata forever `False`. A pytest static test guards against regressions.

**Technical approach**

1. **Auth layer refactor** — rename `HomeOnlyAdminAuth` → `HomeOnlyAuth` (inherit from `SessionAuth`, not `AdminAuth`). Keep its `__call__` mode gate (`if AUTH_MODE != "home": raise HttpError(404)`). Delete `AdminAuth` (0 call sites per audit). Update imports, type hints, `__all__`.
2. **Endpoint gating — admin endpoints** — swap `auth=HomeOnlyAdminAuth()` → `auth=HomeOnlyAuth()` on the 18 existing admin endpoints. Mechanical rename; behavior unchanged.
3. **Endpoint gating — profile endpoints** — the 9 profile endpoints split into two gating patterns based on their existing auth shape (verified against `apps/profiles/api.py` lines 125–366):
   - **HomeOnlyAuth applied (6 endpoints)**: the 4 currently on `SessionAuth()` (get_profile, update_profile, get_deletion_preview, delete_profile) get their decorator swapped to `HomeOnlyAuth()`. The 2 currently on `HomeOnlyAdminAuth()` (set_unlimited, rename_profile) are picked up by the mass rename in step 1/T005.
   - **Inline mode check (3 endpoints)**: list_profiles, create_profile, select_profile cannot use `HomeOnlyAuth` because they must remain reachable in home mode WITHOUT a session (home-mode profile selection is chicken-and-egg: the user has no session yet when hitting the profile list). Each gets `raise HttpError(404, "Not found")` as the first handler statement; existing inline checks in create/select (currently returning `Status(404, …)`) are converted to `raise HttpError` for uniform body shape (`{"detail": "Not found"}`) across all 27 gated endpoints.
   - **Cleanup**: `list_profiles`'s `auth=[SessionAuth()] if AUTH_MODE=="passkey" else None` conditional auth is replaced with plain `auth=None`; the `if AUTH_MODE == "passkey":` block (lines 147–152) becomes unreachable and is deleted — that removes the `is_staff` filter at line 151. The `is_staff` admin-bypass branch in `_check_profile_ownership` (line 118) is also deleted; optionally the entire helper can be removed since its only remaining branch is unreachable post-refactor (all its call sites are now home-only).
4. **Quota-logic refactor** — drop the three `if profile.user and profile.user.is_staff: return (True, {})` blocks in `apps/ai/services/quota.py` (lines 65, 107, 153). Change `unlimited = profile.unlimited_ai or (profile.user and profile.user.is_staff)` → `unlimited = profile.unlimited_ai` in `apps/ai/api_quotas.py:56`.
5. **API response shape** — remove `is_admin` from `passkey_user_profile_response` in `apps/core/auth_helpers.py:16`. No frontend consumer reads it (audit confirmed); TypeScript types must be updated to drop the field.
6. **Legacy template cleanup** — rewrite `apps/legacy/views.py:48-50` so `is_admin` derives from `settings.AUTH_MODE == "home"` (the value is `True` in home mode, `False` in passkey mode regardless of `request.profile.user.is_staff`). Strip the redundant `and auth_mode == "home"` clause from the ~10 compound conditions in `apps/legacy/templates/legacy/settings.html`. Keep `is_admin` as a readable template label.
7. **CLI surgery** — delete `promote` and `demote` subcommands (both argparse registration and handler code), delete the one-admin-floor check, delete the `--admin` flag from `create-user` (default to `is_staff=False`), delete the ADMIN column from `list-users` (both text and `--json`), remove the `admins` aggregate counters. Rewrite `status` output to drop admin counts; rewrite `audit` output to drop per-user `is_admin` fields. Update `CLAUDE.md` command reference accordingly.
8. **Regression guard** — add `tests/test_no_is_staff_reads.py` that scans `apps/` for the `is_staff` token with an allowlist (migrations, Django stock AbstractUser internals, default-False user-creation writes, and the test itself). Fails CI if any new read is introduced.
9. **Test rewrite** — triage the 45 existing test matches. Delete tests whose sole purpose was `is_staff`-driven behavior (promote/demote/admin-floor/`/auth/me` `is_admin`). Rewrite quota-bypass tests (~7 in `test_ai_quota.py`) to use `Profile.unlimited_ai=True` instead of `User.is_staff=True`. Update fixtures that pass `is_staff=True` to `create_user`.
10. **Constitution amendment** — rewrite Principle III's passkey-mode paragraph to state: all passkey users are peers; there is no in-app admin privilege; site-wide settings are reached exclusively via the `cookie_admin` CLI.
11. **Release** — ship as v1.43.0 (MINOR — security hardening + breaking CLI surface change).

## Technical Context

**Language/Version**: Python 3.14 (backend), TypeScript 5.9 (modern frontend), ES5 (legacy frontend)
**Primary Dependencies**: Django 5.0, Django Ninja 1.0+, py-webauthn 2.x (passkey mode only), React 19, Vite 7, Vitest 4, React Testing Library, pytest 8
**Storage**: PostgreSQL 16+ (no schema changes). `User.is_staff` column remains on the default Django User model (AbstractUser); value becomes always-False for application-created users.
**Testing**: pytest (backend), Vitest 4 + React Testing Library (frontend). All backend commands run via `docker compose exec web …`; frontend via `docker compose exec frontend …` per constitution Principle VI.
**Target Platform**: Linux container (docker compose); dual frontend (modern React + legacy ES5 on iOS 9 Safari)
**Project Type**: Django backend + React SPA + ES5 legacy frontend (web application layout)
**Performance Goals**: No new perf targets. Removing a single boolean short-circuit per quota call is negligible. No DB changes.
**Constraints**:
- Zero behavior change in home mode; all existing home-mode tests pass unmodified.
- In passkey mode, the 9 profile endpoints produce `404 {"detail":"Not found"}` before any auth line is logged (same pattern as the 18 admin endpoints).
- `is_staff` must not be read in application code paths post-refactor. Pytest static test enforces this and runs in CI.
- No data migration — project is pre-1.0 dev mode with explicit "nuke and restart" posture for existing deploys.
- ES5 legacy templates stay ES5-compatible (template-only edits; no new JS).
**Scale/Scope**: Repo-local change. 18 auth= swaps, 9 profile endpoints newly gated, 19 `is_staff` reads removed, 14 redundant template conditions simplified, 2 CLI subcommands deleted, 3 CLI subcommands trimmed, ~15 test files touched, 1 static test added, 1 constitution paragraph amended. Release v1.43.0.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Applies? | Compliance | Notes |
|-----------|----------|-----------|-------|
| I — Multi-Generational Device Access | Yes | PASS | Legacy templates get template-only edits (strip redundant `and auth_mode == "home"` clauses; `is_admin` context variable preserved for readability). No new ES5 JS. Modern SPA already keys off `useMode() === 'home'` — no changes needed beyond deleting the `is_admin` field from the `/auth/me` TypeScript type. |
| II — Privacy by Architecture | Yes | PASS | Profile API lockdown in passkey mode eliminates a metadata-leak vector (username, unlimited_ai flag, profile names) between peers. `/auth/me` payload shrinks (removes `is_admin`). No new data collected; no new logs containing sensitive fields. |
| III — Dual-Mode Operation | Yes | PASS (principle amended) | This feature CODIFIES the constitutional amendment: passkey users are peers, CLI is the admin surface. The existing "mode-specific endpoints MUST return 404" rule extends cleanly to profile endpoints. Home mode behavior unchanged. |
| IV — AI as Enhancement, Not Dependency | Yes | PASS | Quota bypass simplifies to `unlimited_ai` alone; no AI feature gains or loses a dependency. Users without API keys are unaffected (existing AI-hidden behavior preserved). |
| V — Code Quality Gates Are Immutable | Yes | PASS (net reduction) | Net code surface SHRINKS. `AdminAuth` deleted (~28 LOC). Two CLI subcommands deleted (~20 LOC each). Quota short-circuits removed. Legacy view simplified. The only additions are: `HomeOnlyAuth` rename (0 net lines), 9 endpoint auth swaps, 1 static test file (~40 LOC). Total delta is strongly negative. |
| VI — Docker Is the Runtime | Yes | PASS | All verification commands documented as `docker compose exec …`. No host-side Python/Node use. |
| VII — Security by Default | Yes | PASS (primary motivation) | (a) Profile API in passkey mode becomes unreachable — reduces attack surface. (b) 18 admin endpoints retain their v1.42.0 404 behavior. (c) `is_staff` privilege signal removed eliminates a whole class of future "forgot to check is_staff" bugs. (d) Static test prevents regression. (e) `/auth/me` payload contains no privilege metadata. |

**Gate result**: Pass. No justified violations. Proceed to Phase 0.

Additional note: Principle III's current text says "Site-wide settings ... are restricted to administrators. Admin promotion is done exclusively via CLI." This feature AMENDS that text as part of its deliverables (FR-020). The amendment is not a constitution violation — it is the expected outcome and follows the documented Amendment Procedure (version bump, impact report, amendment history entry).

## Project Structure

### Documentation (this feature)

```text
specs/014-remove-is-staff/
├── plan.md              # This file
├── spec.md              # Feature specification (Clarifications Session 2026-04-18)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── auth-classes.md
│   ├── gated-endpoints.md
│   └── cli-output-shapes.md
├── checklists/
│   └── requirements.md  # From /speckit.specify
└── tasks.md             # /speckit.tasks output
```

### Source Code (repository root)

```text
apps/
├── core/
│   ├── auth.py                       # RENAME HomeOnlyAdminAuth → HomeOnlyAuth; make parent SessionAuth; DELETE AdminAuth class; update __all__
│   ├── auth_api.py                   # No changes (consumer of auth_helpers)
│   ├── auth_helpers.py               # EDIT: remove "is_admin" key from passkey_user_profile_response
│   ├── passkey_api.py                # No change (line 164 already sets is_staff=False)
│   └── management/
│       └── commands/
│           └── cookie_admin.py       # DELETE promote/demote subcommands; DELETE one-admin-floor; DELETE --admin flag on create-user; DELETE ADMIN column in list-users; DELETE admin counts in status; DELETE is_admin in audit; set is_staff=False in create-user
├── ai/
│   ├── api_quotas.py                 # EDIT line 56: drop is_staff from unlimited check; keep auth=HomeOnlyAuth() (renamed)
│   ├── api.py                        # EDIT: swap HomeOnlyAdminAuth → HomeOnlyAuth on 7 endpoints (mechanical import + call rename)
│   └── services/
│       └── quota.py                  # EDIT: delete is_staff short-circuits at lines 65, 107, 153
├── recipes/
│   ├── api.py                        # EDIT: rename import/usage on 1 endpoint (cache/health)
│   └── sources_api.py                # EDIT: rename import/usage on 5 endpoints
├── profiles/
│   └── api.py                        # EDIT: (a) rename import/usage on 2 endpoints (set-unlimited, rename) via T005; (b) apply HomeOnlyAuth to 4 endpoints currently on SessionAuth (get, update, deletion-preview, delete); (c) replace list_profiles auth= conditional with auth=None + inline raise HttpError(404) in passkey mode; delete the unreachable passkey-branch block (lines 147-152) including is_staff filter; (d) convert create_profile and select_profile inline mode checks from Status(404,...) to raise HttpError(404,"Not found") for uniform body shape; (e) delete is_staff branch in _check_profile_ownership (optionally delete whole helper if all callers are now home-only)
└── legacy/
    ├── views.py                      # EDIT: `request.is_admin = settings.AUTH_MODE == "home"` (drop is_staff read at line 48)
    └── templates/legacy/
        └── settings.html             # EDIT: strip redundant `and auth_mode == "home"` / `and auth_mode == 'passkey'` clauses from ~14 compound is_admin conditions; keep `{% if is_admin %}` as the canonical gate

frontend/src/
├── api/                              # EDIT: any TypeScript type for the /auth/me response — drop `is_admin: boolean` field
├── screens/Settings.tsx              # No change (already uses useMode())
└── hooks/useAuth.ts (or equivalent)  # EDIT if type contains is_admin

tests/                                # pytest
├── test_no_is_staff_reads.py         # ADD: static scan of apps/ for is_staff reads with allowlist
├── test_home_mode_only_decorator.py  # EDIT: rename class references AdminAuth → (deleted) and HomeOnlyAdminAuth → HomeOnlyAuth; add 9 profile-endpoint 404-in-passkey cases
├── test_ai_quota.py                  # EDIT: rewrite is_staff=True fixtures → unlimited_ai=True on profile; ~7 test functions
├── test_cookie_admin.py              # EDIT: delete test_promote_*, test_demote_*, test_demote_last_admin_refused; delete --admin flag tests on create-user; rewrite list-users/status/audit output assertions
├── test_auth_api.py                  # EDIT: delete assertions on /auth/me is_admin; keep profile/user shape assertions
├── test_permissions.py               # EDIT: delete is_staff-driven admin-access tests; keep profile ownership tests
├── test_gated_endpoints_passkey.py   # EDIT: re-verify 18 admin endpoints still 404 with renamed class; ADD 9 profile endpoints × 404 in passkey
├── test_system_api.py                # EDIT: remove is_staff fixture lines
├── test_profiles_api.py              # EDIT: remove is_staff admin fixtures; rewrite admin-visibility assertions to home-mode-only
├── test_passkey_api.py               # EDIT: drop is_staff in response assertions
├── test_legacy_auth.py               # EDIT: drop is_staff assertions; keep auth-mode assertions
└── test_ai_api.py                    # EDIT: drop is_staff admin fixtures where they pass unlimited_ai to profile instead

.specify/memory/
└── constitution.md                   # EDIT: Principle III rewrite (passkey paragraph) + amendment history entry + version bump

CLAUDE.md                             # EDIT: remove promote/demote/create-user --admin from CLI reference; amend admin-surface description

cookie/
└── settings.py                       # EDIT: bump COOKIE_VERSION default to "1.43.0"
```

**Structure Decision**: Use the existing multi-app Django + React SPA + legacy ES5 layout; no new top-level directories. The renamed `HomeOnlyAuth` stays in `apps/core/auth.py` alongside `SessionAuth`. The static-test regression guard goes in `tests/` alongside existing gate tests.

## Phase 0: Outline & Research

See [research.md](./research.md). No unresolved `NEEDS CLARIFICATION` remain — all four clarifications were resolved in the spec's Clarifications session; this phase turns them into concrete design decisions.

Research items:

- **R1 — HomeOnlyAuth class design**: inherit from `SessionAuth` (not `AdminAuth`, which is deleted). `__call__` checks mode first, raises `HttpError(404)` in non-home modes, else delegates to `SessionAuth.__call__`. 18+7=25 authenticated home-only endpoints use it. Decision: single class, no admin concept.
- **R2 — Gating unauthenticated profile endpoints**: POST `/api/profiles/` and POST `/api/profiles/{id}/select/` have `auth=None`. Rather than introduce a second auth class just for these, inline `if settings.AUTH_MODE != "home": raise HttpError(404, "Not found")` as the first statement of each handler. This is equivalent in effect to auth-class gating for unauthenticated endpoints (no auth-log line generated either way) and avoids a parallel class.
- **R3 — Pytest static test allowlist**: the static test greps `apps/` recursively for `is_staff`. Allowlist: (a) `apps/core/management/commands/cookie_admin.py` only for the literal `is_staff=False` write in create-user, (b) `apps/core/passkey_api.py` for the literal `is_staff=False` write on line 164. All other matches fail with a message pointing at file:line and recommending removal.
- **R4 — CLI informational output shapes**: `status --json` drops the `admins` / `active_admins` counter rows. `audit --json` drops `is_admin` from per-user event dicts. `list-users` drops the ADMIN column (text) and `is_admin` field (JSON), drops the "Admins: N" summary footer. `CLAUDE.md` reference section rewritten to match.
- **R5 — TypeScript type update**: grep `frontend/src/` for `is_admin`. If type exists in `auth/me` response interface, delete the field. If no consumer exists (audit suggests none), the delete is safe and prevents future accidental reads.
- **R6 — Test rewrite strategy**: three categories. (a) DELETE: tests whose sole purpose is `is_staff`-driven privilege — `test_promote_*`, `test_demote_*`, `test_demote_last_admin_refused`, `/auth/me is_admin` assertion, `list-users --admins-only` assertion. (b) REWRITE: tests asserting quota bypass via `is_staff=True` — swap to `Profile.unlimited_ai=True`, keeping the assertion shape. (c) UPDATE FIXTURES: tests that create admin users as scaffolding for non-privilege tests — remove `is_staff=True` from `create_user` calls; these tests don't assert on the flag so they just need the fixture line updated.
- **R7 — Constitution amendment wording**: Principle III passkey-mode paragraph changes from "Site-wide settings … are restricted to administrators. Admin promotion is done exclusively via CLI." to "All passkey users are peers — there is no in-app admin privilege. Site-wide settings (API keys, AI prompts, search sources, database reset, profile management) are reached exclusively via the `cookie_admin` CLI and are unreachable from the web UI." Version bump to 1.4.0 (MINOR: principle materially expanded/redefined). Amendment-history entry added.
- **R8 — Release version**: v1.42.0 was the admin-lockdown feature. This feature (a) consolidates quota privilege, (b) removes an auth class, (c) locks down `/api/profiles/*` further. That's MINOR (new security hardening + breaking CLI surface change), so **v1.43.0**.

## Phase 1: Design & Contracts

**Prerequisites**: `research.md` complete.

1. **Data model** — [data-model.md](./data-model.md): no schema changes. Documents the post-refactor semantic state of `User.is_staff` (inert metadata, always False) and `Profile.unlimited_ai` (the sole remaining privilege flag). Notes on test-fixture patterns.

2. **Contracts** — [contracts/](./contracts/):
   - `auth-classes.md` — Post-refactor auth-class inventory. `SessionAuth` (unchanged), `HomeOnlyAuth` (new name, simplified). `AdminAuth` and `HomeOnlyAdminAuth` listed as DELETED / RENAMED with migration notes for any custom code that might still reference them (there should be none in-repo; this is future-proofing).
   - `gated-endpoints.md` — 18 admin endpoints + 9 profile endpoints = 27 rows. For each: method, path, handler, auth-class (or inline check), behavior per mode × caller state (anon / authenticated).
   - `cli-output-shapes.md` — Before/after JSON shape for `status`, `audit --json`, `list-users --json`; before/after text shape for `list-users`. Diff-style, scannable.

3. **Agent context update**: run `.specify/scripts/bash/update-agent-context.sh claude` after plan.md is written. Likely no new technology rows (stack unchanged), but the script keeps the rolling "Active Technologies" list in `CLAUDE.md` accurate.

4. **Quickstart** — [quickstart.md](./quickstart.md): operator walkthrough — how to verify in a dev container that (a) home-mode admin UI still works, (b) passkey-mode 27 endpoints all 404, (c) quota bypass via `set-unlimited` works, (d) `is_staff=True` user does NOT bypass quota, (e) static test passes, (f) how to tag and release v1.43.0.

**Post-design Constitution Re-check**: All rows remain PASS. Proceed to `/speckit.tasks`.

## Complexity Tracking

No violations of Constitution gates. No entries required.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |

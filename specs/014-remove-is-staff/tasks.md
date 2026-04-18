---

description: "Task list for feature 014 — remove is_staff; consolidate privilege on Profile.unlimited_ai"
---

# Tasks: Remove is_staff; Consolidate Privilege on Profile.unlimited_ai

**Input**: Design documents from `/specs/014-remove-is-staff/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: INCLUDED. This refactor explicitly requires test rewrites (FR-018), a regression-guard static test (FR-021b), and quickstart verification. All commands run via `docker compose exec …` per constitution Principle VI.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User-story phase tasks only (US1-US5 from spec.md)

## Path Conventions

Cookie is a Django backend + React SPA + legacy ES5 frontend. Backend in `apps/`, modern frontend in `frontend/src/`, tests in `tests/` (pytest) and `frontend/src/**/*.test.tsx` (Vitest). All Docker-based per constitution Principle VI.

---

## Phase 1: Setup

**Purpose**: Verify branch and tooling preconditions.

- [x] T001 Verify branch `014-remove-is-staff` is checked out and working tree is clean. Run `docker compose up -d` for `web` and `frontend` containers. Confirm `docker compose exec web python -m pytest --collect-only -q` completes without collection errors on the current baseline.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Rename and simplify the auth class. Every subsequent US depends on the final auth-class names.

**⚠️ CRITICAL**: No user story work can begin until this phase completes.

- [x] T002 Rename `HomeOnlyAdminAuth` → `HomeOnlyAuth` in `apps/core/auth.py`. Change parent class from `AdminAuth` to `SessionAuth`. Keep the `__call__` mode gate (`if settings.AUTH_MODE != "home": raise HttpError(404, "Not found")`). Update docstring to drop any "admin" wording.

- [x] T003 Delete the `AdminAuth` class in `apps/core/auth.py` (lines 84–111). It has zero direct call sites post-T002.

- [x] T004 Update `__all__` in `apps/core/auth.py` to `["SessionAuth", "HomeOnlyAuth"]`. Remove `AdminAuth` and `HomeOnlyAdminAuth` references.

- [x] T005 [P] Rename all imports and constructor calls of `HomeOnlyAdminAuth` → `HomeOnlyAuth` across the 18 existing admin endpoints. Files: `apps/ai/api.py` (7 endpoints), `apps/ai/api_quotas.py` (1), `apps/core/api.py` (2), `apps/recipes/api.py` (1), `apps/recipes/sources_api.py` (5), `apps/profiles/api.py` (2 — set-unlimited, rename). Purely mechanical find-and-replace on the import line and the `auth=…()` argument. No behavior change.

**Checkpoint**: Auth layer contains exactly two classes: `SessionAuth` and `HomeOnlyAuth`. All 18 previously-gated admin endpoints continue to work (home mode 2xx; passkey mode 404). Run `docker compose exec web python -m pytest tests/test_gated_endpoints_passkey.py -q` to confirm no regression.

---

## Phase 3: User Story 1 - Home-mode self-hoster keeps full admin UI (Priority: P1) 🎯 MVP

**Goal**: Both frontends retain the full admin UI in home mode. Legacy template's `is_admin` context variable is preserved for readability but derived purely from auth mode.

**Independent Test**: Start in `home` mode; open both frontends; confirm every admin tab/section renders; perform one admin action (save an AI prompt) in each frontend.

### Implementation for User Story 1

- [x] T006 [US1] Simplify `apps/legacy/views.py` (around line 48). Replace the existing `if auth_mode == "passkey": request.is_admin = request.profile.user.is_staff; else: request.is_admin = True` logic with `request.is_admin = settings.AUTH_MODE == "home"`. Drop any `is_staff` read in this file.

- [x] T007 [US1] Edit `apps/legacy/templates/legacy/settings.html`. For every block matching `{% if is_admin and auth_mode == "home" %}`, simplify to `{% if is_admin %}`. There are ~10 such blocks (lines 19, 23, 47, 103, 201, 463, 570, 661 per audit, plus any others found). Keep the `is_admin` label for readability. Do NOT touch `{% if auth_mode == 'passkey' and not is_admin %}` blocks — those are passkey-mode user sections and must continue to render correctly (after T006, `not is_admin` is True in passkey mode).

- [x] T008 [US1] Restart containers per constitution Principle VI: `docker compose down && docker compose up -d` (required after `apps/legacy/static/` or templates change).

### Tests for User Story 1

- [x] T009 [P] [US1] Update `tests/test_legacy_auth.py`. Remove assertions that rely on `is_staff` granting admin view access in passkey mode. Add/keep assertions that in home mode, ANY profile session renders the admin template blocks.

- [x] T010 [P] [US1] Add or update integration test asserting that in home mode, a request to `GET /legacy/settings/` with any valid profile session returns a page containing the API-key form, prompts section, and danger zone. File: `tests/test_legacy_auth.py` (extend existing test class).

**Checkpoint**: Home-mode admin UI verified functional in both frontends. Legacy template context is mode-only.

---

## Phase 4: User Story 2 - Passkey user bypasses AI quotas via unlimited_ai only (Priority: P1)

**Goal**: Quota bypass is granted ONLY by `Profile.unlimited_ai=True`. `User.is_staff=True` has zero effect on quota logic.

**Independent Test**: Create two passkey users — one with `is_staff=True, unlimited_ai=False`, one with `is_staff=False, unlimited_ai=True`. The first hits quota limits; the second does not.

### Implementation for User Story 2

- [x] T011 [US2] Edit `apps/ai/services/quota.py`. Delete the three `if profile.user and profile.user.is_staff: return (True, {})` short-circuits at lines 65 (`check_quota`), 107 (`reserve_quota`), and 153 (`release_quota`). The `if profile.unlimited_ai: return (True, {})` branches remain as the sole bypass signal.

- [x] T012 [US2] Edit `apps/ai/api_quotas.py` line 56. Change `unlimited = profile.unlimited_ai or (profile.user and profile.user.is_staff)` to `unlimited = profile.unlimited_ai`.

### Tests for User Story 2

- [x] T013 [US2] Rewrite quota-bypass tests in `tests/test_ai_quota.py`. Locate the ~7 test functions that set up `User.objects.create_user(..., is_staff=True)` to exercise unlimited AI (lines 40, 76, 327, 365, 398, 680, 724 per audit). Replace each fixture with a Profile setup that sets `profile.unlimited_ai = True; profile.save()`. Keep the assertion shape identical.

- [x] T014 [P] [US2] Add two new explicit test cases in `tests/test_ai_quota.py`:
  - `test_is_staff_does_not_bypass_quota`: user with `is_staff=True, unlimited_ai=False` → quota-exceeded response past the normal limit.
  - `test_unlimited_ai_bypasses_quota_regardless_of_is_staff`: user with `is_staff=False, unlimited_ai=True` → all requests succeed past the limit.

**Checkpoint**: Quota code reads `unlimited_ai` only. `is_staff` no longer appears in `apps/ai/`.

---

## Phase 5: User Story 3 - Passkey-mode admin + profile API lockdown (Priority: P1)

**Goal**: All 18 admin endpoints AND all 9 profile endpoints return 404 in passkey mode, pre-auth. Home mode behavior unchanged.

**Independent Test**: In passkey mode, authenticate as any passkey user; curl each of the 27 endpoints; confirm every response is `404 {"detail":"Not found"}`. In home mode, all 27 work as before.

### Implementation for User Story 3

- [x] T015 [US3] Apply `HomeOnlyAuth()` to the **4** profile endpoints in `apps/profiles/api.py` that currently use `SessionAuth()`:
  - line 196 `get_profile` (GET /{profile_id}/)
  - line 208 `update_profile` (PUT /{profile_id}/)
  - line 224 `get_deletion_preview` (GET /{profile_id}/deletion-preview/)
  - line 282 `delete_profile` (DELETE /{profile_id}/)
  Change each decorator's `auth=SessionAuth()` → `auth=HomeOnlyAuth()`. (The two `set_unlimited`/`rename_profile` endpoints are already on `HomeOnlyAuth()` via T005. Do NOT apply `HomeOnlyAuth` to `list_profiles` — see T016 and the note below.)

- [x] T016 [US3] For the **3 unauthenticated** profile endpoints (`list_profiles` line 130, `create_profile` line 181, `select_profile` line 327), unify the passkey-mode gate as the first handler statement:
  - `list_profiles`: currently uses `auth=[SessionAuth()] if AUTH_MODE == "passkey" else None` so that home mode (profile-selection screen) is reachable without a session. **Keep `auth=None` (replace the conditional auth with just `auth=None`)**. Add as the first handler statement: `if settings.AUTH_MODE != "home": raise HttpError(404, "Not found")`. Then delete the entire `if settings.AUTH_MODE == "passkey":` block (lines 147–152) including the `_resolve_authenticated_user` call and the is_staff filter — it becomes unreachable.
  - `create_profile`: already has an inline mode check that returns `Status(404, {"error": "not_found", "message": "Not found"})`. Replace that return with `raise HttpError(404, "Not found")` so the body is uniform (`{"detail": "Not found"}`) across every gated endpoint.
  - `select_profile`: already has an inline check returning `Status(404, {"detail": "Not found"})`. Convert to `raise HttpError(404, "Not found")` for the same uniformity reason and short-circuit behavior.
  Ensure `from ninja.errors import HttpError` is imported in `apps/profiles/api.py`.

  **Why `HomeOnlyAuth` is NOT used for these three**: HomeOnlyAuth delegates to SessionAuth, which requires a profile-session cookie. In home mode these three endpoints must be reachable WITHOUT a session (the profile-selection flow is chicken-and-egg). The inline `raise HttpError(404)` provides identical security posture (404 before any logic runs) without demanding a session.

- [x] T017 [US3] Delete the `is_staff` admin-bypass branch in `apps/profiles/api.py::_check_profile_ownership` (line 118): remove `if user.is_staff: return None`. This function short-circuits to `return None` at line 113 when `AUTH_MODE != "passkey"`, so the deletion only affects passkey-mode behavior — but passkey-mode callers no longer reach these endpoints (they 404 via T015/T016), so the function becomes effectively dead code in the passkey branch. Consider also deleting `_check_profile_ownership` entirely and removing its call sites (T017a) — see optional T017a.

- [x] T017a [US3] (OPTIONAL CLEANUP) Since every caller of `_check_profile_ownership` is now a home-only endpoint (passkey-mode callers get 404 before reaching the handler), the helper's passkey-specific ownership check is unreachable. If confidence is high after T015 is done, delete `_check_profile_ownership` (lines 111–122) and remove its invocations in `get_profile`, `update_profile`, `get_deletion_preview`, `delete_profile`. Otherwise keep the helper — it's defensive and not harmful.

- [x] T018 [US3] In `apps/profiles/api.py::list_profiles` (after T016 has deleted the passkey-mode block), confirm the function body returns all profiles in home mode. Add a unit test in `tests/test_profiles_api.py::test_list_profiles_home_returns_all` that creates 3 profiles, invokes the endpoint with no session (home mode), and asserts all 3 are returned. This locks in the behavior the spec's edge case claims.

### Tests for User Story 3

- [x] T019 [P] [US3] Extend `tests/test_gated_endpoints_passkey.py`. For each of the 9 profile endpoints (7 authenticated + 2 with inline check), add a parameterized test asserting that in passkey mode with an authenticated passkey session, the endpoint returns `404` with body `{"detail": "Not found"}`. Reference `contracts/gated-endpoints.md` rows 17–25.

- [x] T020 [P] [US3] Update existing `tests/test_gated_endpoints_passkey.py` tests for the 18 admin endpoints to reference `HomeOnlyAuth` (renamed) — mostly import cleanup. Confirm all 18 still assert 404.

- [x] T021 [P] [US3] In `tests/test_profiles_api.py`, delete or rewrite tests that assert passkey-mode behavior of profile endpoints (e.g., admin users seeing all profiles). Replace with tests that confirm passkey-mode requests receive 404. For home mode, retain and where needed update tests that previously relied on admin bypass (now every home-mode request sees all profiles by default).

- [x] T022 [P] [US3] Add a Vitest test in `frontend/src/` (e.g. `frontend/src/screens/Settings.passkey-hide.test.tsx`) confirming admin tabs are not rendered when mode is 'passkey'. If an equivalent test already exists from v1.42.0 (feature 013), verify it still passes unchanged.

**Checkpoint**: All 27 gated endpoints return 404 in passkey mode. All 27 behave unchanged in home mode. Both frontends render correctly in both modes.

---

## Phase 6: User Story 4 - CLI surface simplifies (Priority: P2)

**Goal**: `cookie_admin` CLI has no `promote`, no `demote`, no `--admin` flag, no `--admins-only`, no admin column in `list-users`, no admin counts in `status`, no `is_admin` in `audit`. Deleting the last user succeeds.

**Independent Test**: Run `cookie_admin --help`; confirm zero references to promote/demote/admin. Run every surviving subcommand's `--help`; confirm no `--admin` / `--admins-only` flags. Run `cookie_admin list-users --json` and `cookie_admin status --json`; confirm outputs match `contracts/cli-output-shapes.md`.

### Implementation for User Story 4

- [x] T023 [US4] In `apps/core/management/commands/cookie_admin.py`, delete the `promote` subcommand: remove argparse registration (around lines 96–98) and the handler function (around lines 577–584). Remove any helper functions used only by `promote`.

- [x] T024 [US4] In `apps/core/management/commands/cookie_admin.py`, delete the `demote` subcommand: remove argparse registration (around lines 101–103) and the handler function (around lines 586–595), including the one-admin-floor check (`if User.objects.filter(is_staff=True).count() <= 1: …`).

- [x] T025 [US4] In `apps/core/management/commands/cookie_admin.py::create-user`, delete the `--admin` argparse flag (line 87) and change the user-creation write (line 547) from `is_staff=is_admin` to `is_staff=False` (or drop the kwarg entirely and let Django's default apply). Update the subcommand's `help` string to remove admin references.

- [x] T026 [US4] In `apps/core/management/commands/cookie_admin.py::list-users`, delete the `--admins-only` argparse flag and its `if admins_only: users = users.filter(is_staff=True)` branch (line 500). Remove the `ADMIN` column from the text output header and row formatter (line 525). Remove `is_admin` from the per-user JSON dict (line 510). Remove the `Admins: N` summary footer (line 530).

- [x] T027 [US4] In `apps/core/management/commands/cookie_admin.py::status`, remove the admin count queries (line 329: `User.objects.filter(is_staff=True, is_active=True).count()` and any `admins=…` / `active_admins=…` fields). Strip these keys from both text and `--json` output.

- [x] T028 [US4] In `apps/core/management/commands/cookie_admin.py::audit`, remove the `"is_admin": u.is_staff` field (line 443) from per-user event dicts. No other audit-event shape changes.

- [x] T029 [US4] In `apps/core/management/commands/cookie_admin.py::_user_dict` helper (line 278), remove the `"is_admin": user.is_staff` key. This helper is consumed by multiple subcommands; removing it propagates the field deletion.

### Tests for User Story 4

- [x] T030 [P] [US4] Delete the following tests from `tests/test_cookie_admin.py`: `test_demote_last_admin_refused` and any `test_promote_*`, `test_demote_*`, `test_create_user_admin_flag`, `test_list_users_admins_only`. These cover functionality that no longer exists.

- [x] T031 [P] [US4] Rewrite `list-users`, `status`, `audit` output assertion tests in `tests/test_cookie_admin.py` to expect the post-refactor shapes documented in `contracts/cli-output-shapes.md`. Specifically: assert no `is_admin` / `admins` / `active_admins` keys are present in `--json` output; assert `ADMIN` column is absent from text output.

- [x] T032 [P] [US4] Add `tests/test_cookie_admin.py::test_delete_last_user_succeeds` — asserts that deleting the only remaining user via `delete-user` succeeds (no one-admin-floor error).

- [x] T032a [P] [US4] Add `tests/test_cookie_admin.py::test_help_output_has_no_admin_tokens` — invokes `cookie_admin --help` via Django's `call_command`/`StringIO` capture and asserts the output contains none of: `promote`, `demote`, `--admins-only`, `--admin`, `is_staff`, `one-admin`. Also invokes `cookie_admin create-user --help` and `cookie_admin list-users --help` and runs the same token assertion on each. Locks in FR-012/FR-013/FR-014 and SC-005.

**Checkpoint**: CLI has no vestigial admin concept. All `cookie_admin` informational and lifecycle subcommands behave per `contracts/cli-output-shapes.md`.

---

## Phase 7: User Story 5 - API response shape + code surface trimmed (Priority: P2)

**Goal**: `/auth/me` response no longer carries `is_admin`. Constitution Principle III amended. Test fixtures that passed `is_staff=True` cleaned up. Frontend type no longer contains `is_admin`.

**Independent Test**: `curl /api/auth/me/` with a passkey session returns a JSON body with no `is_admin` key. Constitution file's Principle III states "all passkey users are peers". `grep -rn "is_staff" apps/ frontend/ tests/` returns only allowlisted lines.

### Implementation for User Story 5

- [x] T033 [US5] Edit `apps/core/auth_helpers.py`. In `passkey_user_profile_response()` (line 13+), remove the `"is_admin": user.is_staff` entry from the `user` dict. Retain all other fields.

- [x] T034 [P] [US5] Grep `frontend/src/` for `is_admin`. If any TypeScript type or interface describes the `/auth/me` response with an `is_admin: boolean` field, remove that field. Update any imports/re-exports. If no consumer exists (audit suggests none), the deletion is a no-op in behavior.

- [x] T035 [P] [US5] Strip `is_staff=True` from scaffold fixtures in the following test files (these tests don't assert on the flag; fixture cleanup only):
  - `tests/test_system_api.py` line 653
  - `tests/test_auth_api.py` line 106
  - `tests/test_gated_endpoints_passkey.py` lines 53, 146
  - `tests/test_permissions.py` (identify and drop admin-privilege fixtures; tests that depended on is_staff granting access become redundant with mode-based gating — delete if so)
  - `tests/test_ai_api.py` lines 71, 77
  - `tests/test_profiles_api.py` lines 104, 210, 424
  - `tests/test_passkey_api.py` lines 28, 196, 217
  - `tests/test_legacy_auth.py` lines 71, 170, 172

- [x] T036 [P] [US5] Delete `/auth/me is_admin` assertions in `tests/test_auth_api.py`. Update response-shape assertions to the post-refactor contract: `user` dict contains `id` only (or whatever fields remain per audit G) — no `is_admin`.

- [x] T037 [US5] Amend `.specify/memory/constitution.md`:
  - Rewrite Principle III passkey-mode paragraph per `research.md` R7 wording.
  - Update version header from `1.3.0` → `1.4.0`.
  - Update `Last Amended` to `2026-04-18`.
  - Add amendment-history row dated 2026-04-18 describing the change.
  - Update the sync-impact-report comment at the top of the file.

- [x] T038 [US5] In `apps/core/tests.py`, rename any `HomeOnlyAdminAuth` unit tests to `HomeOnlyAuth`. Delete tests asserting the admin check inside the old class (it's gone). Retain the home-pass-through and passkey-404 tests.

**Checkpoint**: API payload and code surface are cleaned. Constitution reflects new reality. No privilege metadata leaks through responses.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Regression guard, docs, release prep, full-suite verification.

- [x] T039 Add `tests/test_no_is_staff_reads.py` — static test that walks `apps/`, reads each `.py` file, and asserts `is_staff` appears only in allowlisted locations. Allowlist per `research.md` R3:
  - `apps/core/management/commands/cookie_admin.py` — the single `is_staff=False` write in `create-user`
  - `apps/core/passkey_api.py` — the `is_staff=False` write on line 164
  - `apps/core/migrations/**` (prefix-allow; no matches expected but defensive)
  Any other occurrence fails with a message naming file:line and pointing at this spec.

- [x] T040 Update `CLAUDE.md`:
  - Remove `promote` and `demote` example commands from the Admin CLI section.
  - Remove `--admin` flag from the `create-user` example.
  - Remove `--admins-only` flag from the `list-users` example.
  - Amend the "Admin surface by mode" section: passkey mode no longer has an admin concept; all users peers; CLI is the admin surface for app config only.

- [x] T041 Bump `COOKIE_VERSION` default in `cookie/settings.py` from `1.42.0` → `1.43.0`.

- [x] T042 [P] Run full backend test suite: `docker compose exec web python -m pytest -q`. Must be green. In particular, confirm these files pass unchanged (covers FR-023 "device-code and WebAuthn flows untouched"): `tests/test_passkey_api.py`, `tests/test_device_code_*.py` (if present). If any test in those files was touched by fixture cleanup (T035), verify that only fixture lines changed, not assertion logic.

- [x] T043 [P] Run frontend test suite: `docker compose exec frontend npm test -- --run`. Must be green.

- [x] T044 [P] Run linters: `docker compose exec web ruff check apps/` and `docker compose exec frontend npm run lint`. Both must be clean.

- [x] T045 [P] Run complexity check: `docker compose exec web radon cc apps/ -a -nb`. Confirm no function exceeds cyclomatic complexity 15 (constitution Principle V).

- [x] T046 Execute `quickstart.md` sections 4–6 in home mode (manual verification of both frontends).

- [x] T047 Execute `quickstart.md` sections 5–10 in passkey mode (manual verification of 404s, quota, CLI output).

- [x] T048 Create git commit(s) for the feature. Prefer logical groupings (auth refactor, quota, CLI, tests, constitution, release prep). Follow conventional commit style used in recent history.

- [x] T049 Tag `v1.43.0` and create GitHub release per `quickstart.md` section 13. Release notes headline from `research.md` R8.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup. BLOCKS all user-story phases because every endpoint referencing the auth class must use the renamed symbol.
- **User Stories (Phases 3–7)**: All depend on Foundational completing (T002–T005). Stories touch largely disjoint files and may proceed in parallel once Foundational is done.
- **Polish (Phase 8)**: Depends on all user stories. Regression guard (T039) must go last so that by the time it runs, every allowlisted location is known.

### User Story Dependencies

- **US1 (P1)** — Home admin UI preservation: Self-contained. Touches `apps/legacy/views.py`, `apps/legacy/templates/legacy/settings.html`, `tests/test_legacy_auth.py`. No dependency on other stories.
- **US2 (P1)** — Quota via unlimited_ai only: Self-contained. Touches `apps/ai/services/quota.py`, `apps/ai/api_quotas.py`, `tests/test_ai_quota.py`. No dependency on other stories.
- **US3 (P1)** — Passkey admin + profile API lockdown: Self-contained. Touches `apps/profiles/api.py`, `tests/test_gated_endpoints_passkey.py`, `tests/test_profiles_api.py`. No dependency on other stories (the 18 admin endpoints are already gated; T005 renamed the class).
- **US4 (P2)** — CLI simplification: Self-contained. Touches `apps/core/management/commands/cookie_admin.py` and `tests/test_cookie_admin.py`.
- **US5 (P2)** — API shape + code surface + constitution: Touches `apps/core/auth_helpers.py`, `frontend/src/**`, several `tests/*.py` files, `.specify/memory/constitution.md`. No functional dependency on US1–US4 but conceptually seals the refactor.

### Within Each User Story

- Implementation tasks within a single file are sequential (same-file conflicts).
- Test tasks [P] may run in parallel with implementation tasks in different files, but the test's assertion should be validated against the completed implementation.

### Parallel Opportunities

- T005 is marked [P] but inside Foundational: it's a mechanical rename across 6 files that don't conflict with each other; one developer can batch it, or multiple can split the files.
- Once Foundational completes, **all 5 user stories can run in parallel** — they touch disjoint files.
- Within US3, the endpoint edits (T015–T018) are sequential in `apps/profiles/api.py` but parallel with the tests (T019–T022).
- Within US4, the CLI edits (T023–T029) are sequential in `cookie_admin.py` but parallel with test file edits (T030–T032).
- Within US5, T033–T038 are largely independent (different files); run them in parallel.

---

## Parallel Example: After Foundational

```bash
# Team of 5 developers pick up one story each; all complete in parallel:
Developer A (US1):   T006, T007, T008, T009, T010
Developer B (US2):   T011, T012, T013, T014
Developer C (US3):   T015, T016, T017, T018, T019, T020, T021, T022
Developer D (US4):   T023, T024, T025, T026, T027, T028, T029, T030, T031, T032
Developer E (US5):   T033, T034, T035, T036, T037, T038
```

All five stories converge on Phase 8 for polish and release.

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 + 3 only)

All three P1 stories together form the MVP. They ensure:
- Home mode admin UI works (US1)
- Quota bypass correct (US2)
- Passkey mode properly locked down (US3)

P2 stories (US4, US5) are code-quality and shape-cleanup — mandatory for the final release but not blocking basic correctness.

Sequence:
1. Complete Phase 1 (Setup) + Phase 2 (Foundational).
2. Complete Phases 3, 4, 5 (all P1 stories).
3. Validate MVP via `quickstart.md` sections 4–10.
4. Complete Phases 6, 7 (P2 stories).
5. Complete Phase 8 (Polish + release).

### Incremental Delivery

Phases are structured so each user story is independently completable and testable. Merging a single story's branch would leave the system in a valid but mid-refactor state (e.g. after US2 only, `is_staff` is gone from quota code but still referenced in the CLI and `/auth/me`). For CI greenness, include T039 (regression guard) last and run T042–T045 after all phases complete.

### Solo Developer Strategy

Single-developer sequential path (recommended for this project):
1. Phase 1, 2 in order.
2. Phase 3 (US1) — verify home mode works.
3. Phase 4 (US2) — verify quota logic.
4. Phase 5 (US3) — verify passkey lockdown.
5. Phase 6 (US4) — CLI surgery.
6. Phase 7 (US5) — shape cleanup + constitution.
7. Phase 8 — polish, regression guard, release.

---

## Notes

- Every `is_staff` read removed in phases 3–7 must be matched by an allowlist entry in T039 (the regression guard) ONLY if that read survives as a legitimate write. The static test enforces "no application reads"; writes default-False are allowlisted.
- T005 is a mechanical file-wide rename. Use `grep -rln HomeOnlyAdminAuth apps/` to find all 6 files, then batch-edit.
- For every template edit in T007, verify in the browser that the block still renders in home mode (nothing accidentally removed).
- Every task that edits `apps/legacy/static/` or `apps/legacy/templates/` requires a `docker compose down && docker compose up -d` afterward (constitution Principle VI). T008 is the explicit restart for Phase 3; repeat ad-hoc if later phases touch those paths.
- Commit granularity: one commit per phase is appropriate for this refactor. Phases are naturally cohesive. Split further only if a single phase introduces an unrelated sub-change.
- Avoid `--no-verify` on hooks. If a pre-commit hook fails, fix the root cause (constitution Responsible Development).

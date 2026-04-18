---
description: "Task list for 013-admin-home-only"
---

# Tasks: Lock admin surface to home mode only; add CLI parity for passkey-mode ops

**Input**: Design documents in `/specs/013-admin-home-only/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: REQUIRED. The spec mandates integration tests per endpoint (FR-039, FR-040), CLI tests per new subcommand (FR-041), and a frontend component test (FR-042).

**Organization**: Tasks grouped by user story. Setup and Foundational phases come first; Polish is last. Use `[P]` for file-independent parallel tasks; `[Story]` labels US1..US4 for traceability.

## Format: `[ID] [P?] [Story] Description`

## Path Conventions

Django multi-app + React SPA + legacy ES5 templates. Paths absolute from repo root `/home/matt/cookie/`. Backend tests live in `tests/` and in `apps/*/tests.py`; frontend tests in `frontend/src/test/`.

---

## Phase 1: Setup

**Purpose**: Branch is already created and empty. Capture baseline test state before any edits.

- [X] **T001** Verify clean working tree and capture baseline test counts (baseline: backend 1253 tests pass, 87.62% coverage; frontend 513 tests pass across 34 files):
  - `git status` (expect clean on `013-admin-home-only`)
  - `docker compose exec web python -m pytest -q` (record pass count — home-mode behavior)
  - `docker compose exec frontend npm test -- --run` (record pass count)
  - Save both counts in a scratch note; after implementation these MUST NOT regress for home mode.

---

## Phase 2: Foundational (blocking)

**Purpose**: Add the core `HomeOnlyAdminAuth` class and the `home_mode_only` export. Every story that gates endpoints depends on this.

- [X] **T002** [Foundational] Add `HomeOnlyAdminAuth(AdminAuth)` subclass to `apps/core/auth.py`. Import `ninja.errors.HttpError` and `django.conf.settings`. Override `__call__` to raise `HttpError(404, "Not found")` when `settings.AUTH_MODE != "home"`; otherwise `return super().__call__(request)`. Do NOT modify `AdminAuth` (FR-006).
- [X] **T003** [Foundational] Add a pytest unit test `tests/test_home_only_admin_auth.py`:
  - In `AUTH_MODE=passkey`, instantiating and calling `HomeOnlyAdminAuth()` on a fake request raises `HttpError(404, "Not found")`.
  - In `AUTH_MODE=home`, it delegates to `AdminAuth.__call__` (use `unittest.mock` to assert `super().__call__` was reached).
  - In `AUTH_MODE=home`, `security_logger` receives NO new lines during the mode check itself (it can emit later from `AdminAuth.authenticate`; what matters is the pre-auth phase is silent).

**Checkpoint**: foundation ready — user story phases can proceed.

---

## Phase 3: User Story 1 — Endpoints 404 in passkey mode (P1) 🎯 MVP

**Goal**: All 18 gated endpoints return `404 {"detail": "Not found"}` in passkey mode with no `security_logger` auth-failure line. Home-mode behavior unchanged.

**Independent Test**: probe every row of `contracts/gated-endpoints.md` with pytest; all cells in passkey mode return 404; all home-mode tests still pass.

### Tests for User Story 1 (write FIRST; ensure they FAIL against current code)

- [X] **T004** [P] [US1] Create `tests/test_gated_endpoints_passkey.py` with an integration test that, under `@override_settings(AUTH_MODE="passkey")` (via pytest fixture / Django `override_settings`), probes each of the 18 endpoints enumerated in `contracts/gated-endpoints.md` for all 3 caller states (anon, non-admin, admin). Each probe asserts:
  - status == 404
  - body == `{"detail": "Not found"}`
  - `security_logger` captured no new lines during the probe (capture via pytest `caplog` with `propagate=True`).
  - Fixture provides admin and non-admin passkey sessions using existing test helpers (extend `apps/core/tests.py` helpers if needed).
- [X] **T005** [P] [US1] Review every existing test that currently expects `403 {"error":"disabled"}` from `GET /api/system/reset-preview/` or `POST /api/system/reset/` in passkey mode — update to expect `404 {"detail":"Not found"}` (these are pre-change tests that codified the old inline block). Locate via: `grep -rn "Database reset is disabled in passkey mode" /home/matt/cookie/apps /home/matt/cookie/tests`.

### Implementation for User Story 1

- [X] **T006** [P] [US1] Update `apps/ai/api.py`: change `auth=AdminAuth()` to `auth=HomeOnlyAdminAuth()` on 7 endpoints: `save-api-key` (POST), `test-api-key` (POST), `prompts` (GET), `prompts/{prompt_type}` (GET + PUT), `repair-selector` (POST), `sources-needing-attention` (GET). Update the single `AdminAuth` import to also import `HomeOnlyAdminAuth`.
- [X] **T007** [P] [US1] Update `apps/ai/api_quotas.py`: swap `AdminAuth()` → `HomeOnlyAdminAuth()` on `PUT /quotas`.
- [X] **T008** [P] [US1] Update `apps/recipes/api.py`: swap on `GET /cache/health/`.
- [X] **T009** [P] [US1] Update `apps/recipes/sources_api.py` — swap on 5 endpoints + reorder `/bulk-toggle/` and `/test-all/` above `/<source_id>/` to fix URL shadowing that surfaced during testing.: swap on 5 endpoints (`{source_id}/toggle/`, `bulk-toggle/`, `{source_id}/selector/` PUT, `{source_id}/test/`, `test-all/`).
- [X] **T010** [P] [US1] Update `apps/profiles/api.py`: swap on 2 endpoints (`{profile_id}/set-unlimited/` POST, `{profile_id}/rename/` PATCH).
- [X] **T011** [US1] Update `apps/core/api.py`: swap on `reset-preview/` (GET) and `reset/` (POST). Delete the two inline `if settings.AUTH_MODE == "passkey": return Status(403, …)` blocks (one at `reset_preview`, one at `reset_database`). Keep the rate-limit and `confirmation_text != "RESET"` checks. Audit for any helpers whose only caller was the deleted blocks — delete them too (FR-008). Run `grep -rn "Database reset is disabled in passkey mode" apps/` after edit; expect zero hits.
- [X] **T012** [US1] Run the new passkey-mode test file (full backend suite 1275 passed — +22 net over baseline 1253) (`tests/test_gated_endpoints_passkey.py`) — must pass. Then run the full backend test suite: `docker compose exec web python -m pytest -q`. No regressions vs. T001 baseline.

**Checkpoint**: US1 fully functional. Passkey deployment has no admin REST surface. Home mode unchanged.

---

## Phase 4: User Story 2 — Admin UI hidden in passkey mode (P1)

**Goal**: Both frontends (legacy Django templates + React SPA) render zero admin-only sections when `AUTH_MODE=passkey`. Home-mode UI unchanged.

**Independent Test**: Vitest component test asserts admin sections absent in SPA under `mode='passkey'`; manual template inspection confirms legacy template blocks.

### Tests for User Story 2

- [ ] **T013** [P] [US2] Create `frontend/src/test/Settings.passkey-hide.test.tsx`. Mount `Settings` with a provider wrapper that forces `useMode()` to return `'passkey'` and `useAuth()` to return `{isAdmin: true}`. Use `screen.queryByTestId(...)` for each of the admin-only component test-ids (see T014 for the list) and assert `.toBeNull()`. Cover at minimum: `api-key-section`, `settings-prompts`, `settings-selectors`, `settings-sources`, `ai-quota-section`, `settings-danger`, `settings-users-admin`, `user-profile-card-admin`. Also assert `settings-general`, `settings-passkeys`, `delete-account-section`, `ai-usage-section` ARE rendered (sanity check for FR-014).
- [ ] **T014** [P] [US2] Add stable `data-testid` attributes to the root element of each admin-only SPA component if not already present: `APIKeySection` (`data-testid="api-key-section"`), `SettingsPrompts` (`settings-prompts`), `SettingsSelectors` (`settings-selectors`), `SettingsSources` (`settings-sources`), `AIQuotaSection` (`ai-quota-section`), `SettingsDanger` (`settings-danger`), the admin-only wrapper inside `UserProfileCard` (`user-profile-card-admin`), and the admin-only block inside `SettingsUsers` (`settings-users-admin`). Also add to retained components: `SettingsGeneral` (`settings-general`), `SettingsPasskeys` (`settings-passkeys`), `DeleteAccountSection` (`delete-account-section`), `AIUsageSection` (`ai-usage-section`). Test-ids are semantic, do not affect visual output.

### Implementation — SPA (React)

- [ ] **T015** [P] [US2] Update `frontend/src/screens/Settings.tsx`: import `useMode` from `../router` alongside the existing `useAuth`. Compute `const showAdminUi = isAdmin && mode === 'home'` once at the top of the component. Replace all existing `isAdmin &&` guards on admin sections/tabs with `showAdminUi &&`. Preserve existing code paths that don't touch admin sections.
- [ ] **T016** [P] [US2] Update `frontend/src/components/settings/APIKeySection.tsx`: early return `null` when `useMode() !== 'home'`. (Belt-and-braces even if `Settings.tsx` guards at the container level — components can be rendered from other places.)
- [ ] **T017** [P] [US2] Update `frontend/src/components/settings/SettingsPrompts.tsx`: same guard.
- [ ] **T018** [P] [US2] Update `frontend/src/components/settings/SettingsSelectors.tsx`: same guard.
- [ ] **T019** [P] [US2] Update `frontend/src/components/settings/SettingsSources.tsx`: same guard.
- [ ] **T020** [P] [US2] Update `frontend/src/components/settings/AIQuotaSection.tsx`: same guard.
- [ ] **T021** [P] [US2] Update `frontend/src/components/settings/SettingsDanger.tsx`: same guard.
- [ ] **T022** [P] [US2] Update `frontend/src/components/settings/UserProfileCard.tsx`: wrap the admin-control subsection in `useMode() === 'home'` (keep non-admin content always visible).
- [ ] **T023** [P] [US2] Update `frontend/src/components/settings/SettingsUsers.tsx`: wrap admin-only bits in `useMode() === 'home'`.
- [ ] **T024** [P] [US2] Leave `PromptCard`, `SelectorItem`, `SourceItem`, `ConfirmResetStep`, `ResetPreviewStep`, `DangerZoneInfo` unchanged in their component bodies — their container parents already mode-gate them. Add a comment (one line each) noting they are rendered only by admin-mode containers. (No content edit beyond the single comment.)

### Implementation — legacy Django templates

- [ ] **T025** [US2] `apps/legacy/templates/legacy/settings.html`: replace every occurrence of `{% if is_admin %}` with `{% if is_admin and auth_mode == "home" %}`. Use a single targeted `sed` or confirm via `grep`. Count expected replacements: 10 (per earlier grep).
- [ ] **T026** [US2] `apps/legacy/templates/legacy/partials/*`: run `grep -n "is_admin" apps/legacy/templates/legacy/partials/` — update every match to the combined check. Preserve non-admin `auth_mode`-only blocks.
- [ ] **T027** [US2] `apps/legacy/templates/legacy/base.html`, `nav_header.html` (inside `partials/` or in `base.html`): any admin nav link or admin-dropdown entry gets the combined check. Search: `grep -n "is_admin" apps/legacy/templates/legacy/base.html` and any `nav_header.html`.
- [ ] **T028** [US2] Restart legacy containers to pick up static/template changes if needed: noted in CLAUDE.md — after changes to `apps/legacy/static/` restart with `docker compose down && docker compose up -d`. (Templates alone don't need `collectstatic` but restart confirms the picture.)

### Verification

- [ ] **T029** [US2] Run `docker compose exec frontend npm test -- --run Settings.passkey-hide` — must pass.
- [ ] **T030** [US2] Manual check: start the stack in `AUTH_MODE=passkey`, log in as admin, load `/app/settings` and `/settings` (legacy); visually confirm no admin sections render. Switch back to `AUTH_MODE=home`, reload; all admin sections render exactly as today.

**Checkpoint**: US2 fully functional in both frontends.

---

## Phase 5: User Story 3 — CLI parity (P1)

**Goal**: `python manage.py cookie_admin` covers every admin task removed from the web surface. Works in both modes (except the 11 user-lifecycle subcommands which remain passkey-only).

**Independent Test**: operator runs every new subcommand on a passkey deployment; every mutation logs a `security_logger.warning`; `--help` lists all new subcommands.

### Infrastructure / refactor

- [ ] **T031** [US3] Refactor the top-level passkey-mode guard in `apps/core/management/commands/cookie_admin.py::Command.handle` (line ~117). Replace the blanket check with a per-subcommand decision driven by a class-level `PASSKEY_ONLY_SUBCOMMANDS = {"list-users", "create-user", "delete-user", "promote", "demote", "activate", "deactivate", "set-unlimited", "remove-unlimited", "usage", "create-session"}`. Invariant: new subcommands work in either mode; legacy user-lifecycle subcommands retain the existing error text.
- [ ] **T032** [US3] Add a shared helper `get_cache_health_dict() -> dict` in `apps/recipes/api.py` (or a new `apps/recipes/services/cache_health.py`) that computes the cache-health payload. Refactor the existing `GET /api/recipes/cache/health/` handler to call it. Plan (FR-034) reuses this from `status --json` in T047.

### Tests for User Story 3 (one happy + one invalid + one security-log per mutation)

Add to `apps/core/tests.py` (or a new `apps/core/tests/test_cookie_admin.py` if the file grows past 500 lines — see Polish T058):

- [ ] **T033** [P] [US3] Tests for `set-api-key`: happy path (`--key` and `--stdin`), invalid (empty stdin, empty `--key`), `security_logger.warning` emitted on success with NO key-value in log output. Assert `AppSettings.openrouter_api_key` round-trip through the encrypted property.
- [ ] **T034** [P] [US3] Tests for `test-api-key`: happy path (mocked OpenRouter 200), invalid key (mocked 401), `--json` output schema. No security log line (read-only). Mock OpenRouter per `.claude/rules/ai-features.md`.
- [ ] **T035** [P] [US3] Tests for `set-default-model`: happy, invalid model id, security log emitted.
- [ ] **T036** [P] [US3] Tests for `prompts list`: plain + `--json` output shape.
- [ ] **T037** [P] [US3] Tests for `prompts show`: happy, unknown `prompt_type` → exit 2.
- [ ] **T038** [P] [US3] Tests for `prompts set`: happy (`--system-file` only), happy (all flags), invalid (missing file → exit 2 with no DB write), invalid `prompt_type`, invalid `--active` value. Security log emitted with `updated_fields` but not prompt bodies.
- [ ] **T039** [P] [US3] Tests for `sources list` (plain + `--json` + `--attention`).
- [ ] **T040** [P] [US3] Tests for `sources toggle` and `sources toggle-all` (mutually exclusive flags test; security log emitted).
- [ ] **T041** [P] [US3] Tests for `sources set-selector` (happy + security log; selector value NOT in log).
- [ ] **T042** [P] [US3] Tests for `sources test` (happy with `--id`, happy with `--all`, invalid: both flags, partial failure output shape per FR-027a).
- [ ] **T043** [P] [US3] Tests for `sources repair`: happy (mocked OpenRouter), error when API key absent (exit 2, no DB write), security log emitted on success.
- [ ] **T044** [P] [US3] Tests for `quota show` (read-only, no security log) and `quota set` (all 6 names; negative `N` → exit 2; security log emitted).
- [ ] **T045** [P] [US3] Tests for `rename`: passkey mode by username, passkey mode by user_id, home mode by profile_id, empty `--name` → exit 2, unknown target → exit 1; security log emitted with old/new names.
- [ ] **T046** [P] [US3] Tests for `status --json`: assert new `cache` block shape matches `get_cache_health_dict()` output.
- [ ] **T047** [P] [US3] Test that `PASSKEY_ONLY_SUBCOMMANDS` gate still rejects those subcommands in home mode (existing behavior for `list-users` etc.) and allows them in passkey mode.

### Implementation

- [ ] **T048** [US3] Implement `_handle_set_api_key` in `cookie_admin.py`. Read key from `--key` or `sys.stdin.read().strip()`. Reject empty → `CommandError` exit 2. Persist via `obj.openrouter_api_key = value; obj.save()`. Emit `security_logger.warning("cookie_admin set-api-key: key changed")`. Support `--json`.
- [ ] **T049** [US3] Implement `_handle_test_api_key`: call existing OpenRouter validator helper (use the helper the web handler uses — grep `apps/ai` for the validator call). Return `valid` bool and reason.
- [ ] **T050** [US3] Implement `_handle_set_default_model`: validate against `AIPrompt.AVAILABLE_MODELS`; set and save.
- [ ] **T051** [US3] Implement `_handle_prompts_list`, `_handle_prompts_show`, `_handle_prompts_set`. For `prompts set`, read `--system-file` / `--user-file` UTF-8; missing file → `CommandError` exit 2 BEFORE any DB write. Validate `--active`; parse as bool.
- [ ] **T052** [US3] Implement `_handle_sources_list` (with `--attention`), `_handle_sources_toggle`, `_handle_sources_toggle_all` (enforce `--enable` XOR `--disable`), `_handle_sources_set_selector`.
- [ ] **T053** [US3] Factor the per-source health-check logic in `apps/recipes/sources_api.py::test_source` and the `test-all` iteration out into `apps/recipes/services/source_health.py` (new file) exposing `check_source(source) -> dict` and `check_all_sources() -> list[dict]`. Refactor the HTTP handlers to call these. Then implement `_handle_sources_test` in the CLI to call the same helpers. This removes CLI↔HTTP duplication.
- [ ] **T054** [US3] Implement `_handle_sources_repair`. Guard: `AppSettings.get().openrouter_api_key` must be truthy; else `CommandError` exit 2 with the exact message in contracts/cli-subcommands.md. Call the same selector-repair flow as `POST /api/ai/repair-selector`.
- [ ] **T055** [US3] Implement `_handle_quota_show`, `_handle_quota_set`. For `set`, map the flag name to the field (hyphen → underscore). Negative / non-integer → exit 2.
- [ ] **T056** [US3] Implement `_handle_rename`. Branch by `settings.AUTH_MODE`. Passkey: look up `User` by `pk` (if arg is all digits) or `username`; fail with exit 1 if not found. Home: look up `Profile` by `pk`. Validate `--name` non-empty; reject if longer than `Profile._meta.get_field('name').max_length`. Update and save; log old→new.
- [ ] **T057** [US3] Extend `_handle_status` to include `cache` block from `get_cache_health_dict()` in both plain and `--json` output. Update help / module docstring to reflect the new subcommands.
- [~] **T058 DEFERRED** [US3] Split `apps/core/management/commands/cookie_admin.py` into a package. File is now 1215 lines (was 710 pre-change). The pre-existing 500-line ceiling violation predates this feature; splitting now risks regressing 68 passing CLI tests. Tracked as a follow-up PR: ship the security lockdown first, refactor the CLI module in a bounded cleanup PR afterward.

Split (DEFERRED — see follow-up PR): The file is already 710 lines (Principle V ceiling is 500); adding ~18 subcommands would push it past 1000. Create `apps/core/management/commands/cookie_admin/` with:
  - `__init__.py` defining the `Command` class (top-level dispatch + `add_arguments` wiring).
  - `_base.py` for shared helpers (e.g. `_error`, `_emit`, `_security_log`).
  - `handlers/` package with one module per subcommand group: `status.py`, `audit.py`, `users.py` (list/create/delete/promote/demote/activate/deactivate), `unlimited.py` (set-unlimited/remove-unlimited), `usage.py`, `session.py`, `reset.py`, plus NEW modules `api_key.py`, `default_model.py`, `prompts.py`, `sources.py`, `quota.py`, `rename.py`.
  - Each module exports `add_parser(sub)` and `handle(command, options)`.
  - Django discovers `cookie_admin` because the package has an `__init__.py` with `Command` defined (Django's management-command loader accepts packages).
  - Verify: `docker compose exec web python manage.py cookie_admin --help` and every existing subcommand test still passes unchanged.
  - Verify: `wc -l apps/core/management/commands/cookie_admin/*.py apps/core/management/commands/cookie_admin/handlers/*.py` — no file exceeds 500 lines.
- [ ] **T058a** [US3] Verify every subcommand sub-parser is wired in the split package. Run `python manage.py cookie_admin --help` and confirm the help lists all existing + new subcommands. Add a self-test (part of T059's suite) that iterates every subcommand name and asserts `parser.parse_args([name, '--help'])` exits 0.

### Verification

- [ ] **T059** [US3] Run the new CLI tests: `docker compose exec web python -m pytest -q apps/core/tests.py::CookieAdminTests`. Full suite must remain green.
- [ ] **T060** [US3] Sanity check `docker compose exec web python manage.py cookie_admin --help` shows every new subcommand.

**Checkpoint**: US3 fully functional. A passkey operator can perform every admin task via CLI alone.

---

## Phase 6: User Story 4 — Remove version fingerprint (P2)

**Goal**: `GET /api/system/mode/` no longer returns a `version` key.

### Tests

- [ ] **T061** [P] [US4] Update / add a test in `apps/core/tests.py` (or `tests/`) asserting `GET /api/system/mode/` response has keys `{"mode"}` (home) or `{"mode", "registration_enabled"}` (passkey) and NOT `"version"`.

### Implementation

- [ ] **T062** [US4] Edit `apps/core/api.py::get_mode`: remove `"version": settings.COOKIE_VERSION` from the `result` dict. Leave `get_token(request)` call alone (CSRF cookie priming). If `settings.COOKIE_VERSION` has no other consumers after this change, leave the import in place (it's in settings.py and harmless); do NOT remove from settings.py (used by deployment logging).

---

## Phase 7: Version bump & release prep

- [ ] **T063** Update `cookie/settings.py` default: `COOKIE_VERSION = os.environ.get("COOKIE_VERSION", "1.42.0")` (was `"dev"`). The env-var override at deploy time is unchanged.
- [ ] **T064** Run `docker compose exec web ruff check apps/ cookie/` — no new errors.
- [ ] **T065** Run `docker compose exec web radon cc apps/core/management/commands/cookie_admin.py apps/core/auth.py -a -nb` — no function over complexity 15. If any new handler exceeds, extract helpers.
- [ ] **T066** Run `docker compose exec frontend npm run lint` — no new errors.

---

## Phase 8: Polish

- [~] **T067 DEFERRED** [P] Verify the `cookie_admin` split from T058 compiled cleanly: no circular imports; every handler module is <500 lines; `docker compose exec web python -c "from apps.core.management.commands.cookie_admin import Command; print('ok')"` succeeds.
- [ ] **T068** [P] Update `CLAUDE.md` "Admin CLI (Passkey Mode)" section to (a) rename the section to "Admin CLI" since many subcommands now work in both modes, and (b) list the new subcommands with one-line descriptions. Preserve the manually-maintained blocks between the `<!-- MANUAL ADDITIONS START -->` / `<!-- MANUAL ADDITIONS END -->` markers if present.
- [ ] **T069** [P] Update README.md "Admin" section if present to note the passkey-mode CLI-only admin model. Do NOT create a new markdown file for this — reuse existing docs.
- [ ] **T070** Run `docker compose exec web python -m pytest -q` — full pass.
- [ ] **T071** Run `docker compose exec frontend npm test -- --run` — full pass.
- [ ] **T072** Walk through `quickstart.md` end-to-end on a local passkey deployment:
  - 18 endpoints return 404 (spot-check 4).
  - SPA + legacy settings show no admin sections.
  - `/api/system/mode/` has no `version` key.
  - CLI subcommands complete their example flows.
- [ ] **T073** Prepare the GitHub release draft: `gh release create v1.42.0 --draft --title "v1.42.0 — passkey-mode admin surface hardening"` with body per `quickstart.md`. Do NOT publish until the PR lands on `master` and the tag is pushed.

---

## Dependencies & Execution Order

### Phase dependencies

1. Phase 1 (Setup) — no deps.
2. Phase 2 (Foundational) — depends on Phase 1. BLOCKS Phase 3.
3. Phase 3 (US1) — depends on Phase 2. Required for US2 and US4 to ship (but not to implement).
4. Phase 4 (US2) — can proceed after Phase 2 (independent of US1 implementation; they share no files).
5. Phase 5 (US3) — can proceed in parallel with Phase 3 and Phase 4 (touches different files).
6. Phase 6 (US4) — can proceed after Phase 1 (one-file edit).
7. Phase 7 (version bump) — depends on Phases 3–6 (ships once all changes land).
8. Phase 8 (polish) — depends on Phase 7.

### Within-story

- Tests FIRST within each user story block (tests-first when feasible; they must fail against current code, then pass after implementation).
- Models before services before endpoints (generic guidance — minimal model work in this feature).

### Parallelisable hotspots

- All T006..T010 (`[P]` endpoint-swap tasks) touch different files.
- All T013..T014 (SPA test-id + hide test) independent files.
- All T016..T023 (SPA component hides) independent files.
- All T033..T047 (CLI tests) independent functions in the same file — run pytest in parallel if desired, but the file edit is serial.

## Notes

- `[P]` = different files, no deps.
- `[Story]` = US1..US4 traceability.
- Verify tests fail before implementing.
- Commit after each logical chunk (e.g. after T012, T030, T060, T062).
- Do NOT skip hooks. If pre-commit breaks on an unrelated pre-existing issue, fix the root cause per constitution "Responsible Development" section.

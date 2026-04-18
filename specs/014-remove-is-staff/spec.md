# Feature Specification: Remove is_staff; Consolidate Privilege on Profile.unlimited_ai

**Feature Branch**: `014-remove-is-staff`
**Created**: 2026-04-18
**Status**: Draft
**Input**: User description: "Eliminate `User.is_staff` as a privilege signal. Consolidate the single remaining privilege it grants (AI quota bypass) onto `Profile.unlimited_ai`, which already has CLI tooling. Both frontends must remain fully functional in both auth modes: home mode retains the full admin UI for any profile; passkey mode keeps admin surface CLI-only. Also audit adjacent code (AdminAuth class, promote/demote CLI, one-admin floor, `is_admin` in `/auth/me`, legacy template `is_admin` context) and rip anything else made vestigial by the removal."

## Clarifications

### Session 2026-04-18

- Q: How should the passkey-mode 404 gate be implemented for `/api/profiles/*`, given that the refactor also removes the admin concept from `HomeOnlyAdminAuth`? → A: Rename `HomeOnlyAdminAuth` → `HomeOnlyAuth`, drop its admin-checking logic, and use the single class for BOTH the 18 admin endpoints AND all `/api/profiles/*` endpoints.
- Q: What mechanism enforces the "no application code reads `is_staff`" regression guard? → A: Pytest static test that greps `apps/` for `is_staff` reads, with an allowlist of permitted files/patterns (migrations, model fields, user-creation defaults). Runs in CI; failure points at offending file:line.
- Q: How should the legacy template's `is_admin` gating be cleaned up, given it becomes equivalent to `auth_mode == "home"`? → A: Keep the `is_admin` context variable in templates for readability; derive it from `auth_mode == "home"` in the view; strip the now-redundant `and auth_mode == "home"` clauses from every template block.
- Q: Should the informational CLI subcommands (`status`, `audit`, any other) audit and strip their admin/`is_staff` output, or leave them as harmless stale fields? → A: Audit ALL informational CLI subcommands; strip every admin/`is_staff` field from their output; update CLI docs (CLAUDE.md) accordingly. No stale admin telemetry after the refactor.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Home-mode self-hoster keeps full admin UI (Priority: P1)

A person runs Cookie on their home server in the default `home` auth mode. They use the modern React frontend on their laptop and the legacy ES5 frontend on a family iPad. Every profile on the device should see and use the full admin UI (API key, AI prompts, search sources, quotas, factory reset, etc.). After the `is_staff` removal, this must continue to work unchanged — because home-mode admin privilege has never depended on `is_staff`; it has always keyed off auth mode.

**Why this priority**: Home mode is the default and primary deployment target. Breaking admin access here would regress the most common use of the app.

**Independent Test**: Start the stack in `home` mode, create a profile, open both frontends, confirm admin tabs (API Key, AI Prompts, Search Sources, Quotas, Reset) render and their endpoints respond 200.

**Acceptance Scenarios**:

1. **Given** `AUTH_MODE=home` and any profile session, **When** the user opens the modern settings screen, **Then** all admin tabs render and are interactive.
2. **Given** `AUTH_MODE=home` and any profile session, **When** the user opens the legacy settings page, **Then** every admin section renders (no sections hidden).
3. **Given** `AUTH_MODE=home`, **When** any admin endpoint (e.g. `POST /api/admin/api-key/`) is called with a profile session, **Then** it responds 200 and performs the operation.

---

### User Story 2 - Passkey user bypasses AI quotas via unlimited_ai only (Priority: P1)

A single-developer Cookie deployment runs in `passkey` mode. The developer wants to use AI features without being rate-limited. Today, this is achieved by having `is_staff=True`, which short-circuits quota checks. After this change, the ONLY way to grant quota bypass is `Profile.unlimited_ai=True`, set via `cookie_admin set-unlimited <username>`. `is_staff` must have zero effect on quota logic.

**Why this priority**: AI quota bypass is the single most consequential live use of `is_staff`. Getting this wrong means existing admin users suddenly hit quotas.

**Independent Test**: In `passkey` mode, create two users: one with `is_staff=True, unlimited_ai=False`, another with `is_staff=False, unlimited_ai=True`. The first MUST hit quota limits; the second MUST NOT.

**Acceptance Scenarios**:

1. **Given** a passkey user with `unlimited_ai=True` (regardless of `is_staff`), **When** they invoke an AI feature past the normal quota, **Then** the request succeeds.
2. **Given** a passkey user with `unlimited_ai=False` and `is_staff=True`, **When** they invoke an AI feature past the normal quota, **Then** the request is rejected with a quota-exceeded error.
3. **Given** a passkey user with `unlimited_ai=False` and `is_staff=False`, **When** they invoke an AI feature, **Then** normal per-user quota rules apply.
4. **Given** any running deployment, **When** an administrator runs `cookie_admin set-unlimited <username>`, **Then** quota bypass is granted to that user's profile without touching `is_staff`.

---

### User Story 3 - Passkey-mode admin surface remains CLI-only (Priority: P1)

In `passkey` mode, app configuration (API key, AI prompts, search sources, quotas, factory reset, profile rename) is performed exclusively via the `cookie_admin` CLI. The web admin surface returns 404, and both frontends hide admin UI. This behavior was established in v1.42.0 and must not regress when `is_staff` is removed.

**Why this priority**: A regression here would accidentally re-expose admin endpoints to passkey users, undoing a deliberate security boundary.

**Independent Test**: Start the stack in `passkey` mode, authenticate as any passkey user, confirm every admin REST endpoint returns 404 and both frontends render no admin UI.

**Acceptance Scenarios**:

1. **Given** `AUTH_MODE=passkey` and any authenticated passkey session, **When** any of the 18 admin endpoints is called, **Then** the response is 404.
2. **Given** `AUTH_MODE=passkey` and any authenticated passkey session, **When** the user opens the modern settings screen, **Then** no admin tabs appear.
3. **Given** `AUTH_MODE=passkey` and any authenticated passkey session, **When** the user opens the legacy settings page, **Then** no admin sections are rendered.
4. **Given** `AUTH_MODE=passkey`, **When** an operator runs any `cookie_admin` subcommand (prompts, sources, quota, set-api-key, reset, etc.), **Then** it succeeds identically to home mode.

---

### User Story 4 - CLI surface simplifies (no promote/demote, no admin floor) (Priority: P2)

An operator reading `cookie_admin --help` sees only user-lifecycle commands relevant to passkey mode (create, delete, list, activate, deactivate, set-unlimited, remove-unlimited, rename) plus app-config commands. `promote`, `demote`, and any "one-admin floor" logic are gone. `list-users` no longer reports an admin flag. `create-user` has no `--admin` option.

**Why this priority**: CLI simplification improves operator experience and eliminates dead code paths that could regress into subtle bugs. Secondary to functional correctness.

**Independent Test**: Run `cookie_admin --help` and every listed subcommand's `--help` in passkey mode; confirm no reference to promote/demote/admin exists in any surface.

**Acceptance Scenarios**:

1. **Given** a passkey-mode deployment, **When** the operator runs `cookie_admin --help`, **Then** the help output contains no `promote` or `demote` subcommands.
2. **Given** a passkey-mode deployment, **When** the operator runs `cookie_admin list-users --json`, **Then** the returned objects contain no `is_admin` / `is_staff` field.
3. **Given** a passkey-mode deployment, **When** the operator runs `cookie_admin create-user alice`, **Then** the new user is created with `is_staff=False` and the CLI rejects `--admin` as an unknown option.
4. **Given** a passkey-mode deployment with only one user, **When** the operator deletes that user via `cookie_admin delete-user`, **Then** the delete succeeds without a "cannot remove last admin" error (that floor no longer exists).

---

### User Story 5 - API response shape and code surface trimmed (Priority: P2)

The `/auth/me` response in passkey mode no longer carries an `is_admin` field. The legacy template context no longer sets `is_admin` from `is_staff`; it derives purely from auth mode. Any auth class, helper, or test rendered dead by these removals is deleted. The constitution is updated to reflect that passkey users are peers.

**Why this priority**: Code-surface cleanup is the "compounding simplification" the refactor is meant to deliver. It is strictly quality-of-life, not behavior-changing for end users.

**Independent Test**: After the refactor, `grep -rn "is_staff" apps/ frontend/ tests/` returns only (a) the default-False initialisation on user creation, (b) Django model/migration internals, (c) any retained explicit "set to False always" assertions. No branching logic should read the flag.

**Acceptance Scenarios**:

1. **Given** any authenticated session, **When** the client calls `/auth/me`, **Then** the response contains no `is_admin` key.
2. **Given** the legacy ES5 settings template rendering, **When** the page is generated in passkey mode, **Then** the server-side `is_admin` context value is `False` regardless of any user flag state.
3. **Given** the codebase post-change, **When** a developer searches for `AdminAuth` (distinct from `HomeOnlyAdminAuth`), **Then** it no longer exists if audit shows no usage.
4. **Given** the constitution, **When** a reader reaches Principle III, **Then** the text accurately reflects that in passkey mode all users are peers and admin work is CLI-only.

---

### Edge Cases

- **Existing passkey deployments with `is_staff=True` users**: After deploy, those users continue to function as peers; they lose no ability they still exercise in practice (quota bypass moves to `unlimited_ai`, which an operator can set in a single command).
- **A user has BOTH `is_staff=True` and `unlimited_ai=False`**: They must now hit quota limits. This is the deliberate behavior change and should be explicitly covered in tests.
- **A user has `is_staff=False` and `unlimited_ai=True`**: They bypass quotas. Already worked; must continue to work.
- **CLI reset / factory reset**: Resetting the database in either mode must not leave dangling `is_staff=True` rows that influence anything.
- **`delete-user` when only one user exists (passkey mode)**: Must succeed (no admin-floor check). The operator can recreate a user via device-code flow or `create-user`.
- **Profile list call in home mode**: Behavior unchanged — home mode already returns all profiles to all callers (there are no users to filter by).
- **Profile API calls in passkey mode**: All return 404. If a future feature legitimately needs profile data in passkey mode, it belongs on `/auth/me` or in the CLI, not on the public profile API.
- **Legacy template renders with stale cached page**: Templates are server-rendered, not cached across deploys, so a fresh request after deploy picks up new context.

## Requirements *(mandatory)*

### Functional Requirements

#### Quota logic

- **FR-001**: The system MUST grant AI quota bypass based solely on `Profile.unlimited_ai=True`. The `User.is_staff` flag MUST NOT influence quota decisions in any check/reserve/release path.
- **FR-002**: The CLI commands `set-unlimited <username>` and `remove-unlimited <username>` MUST remain available and MUST be the only supported mechanism for granting/revoking AI quota bypass.

#### Admin surface preservation

- **FR-003**: In `home` mode, all admin REST endpoints MUST respond successfully to any authenticated profile session, unchanged from current behavior.
- **FR-004**: In `passkey` mode, all admin REST endpoints MUST return 404 to any authenticated passkey session, unchanged from current v1.42.0 behavior.
- **FR-005**: In `home` mode, both the modern React frontend and legacy ES5 frontend MUST display and allow interaction with the full set of admin UI sections (API key, AI prompts, search sources, AI quotas, factory reset).
- **FR-006**: In `passkey` mode, both frontends MUST render no admin UI sections.
- **FR-007**: Admin UI visibility in both frontends MUST be determined by auth mode alone (`mode === 'home'` / `auth_mode == 'home'`), never by any per-user flag.

#### Profile API surface

- **FR-008**: In `home` mode, all existing `/api/profiles/*` endpoints (list, detail, create, rename, delete, delete-preview, set-unlimited and any other verbs) MUST continue to work unchanged.
- **FR-009**: In `passkey` mode, every `/api/profiles/*` endpoint MUST return 404, mirroring the home-only gating pattern applied to admin endpoints in v1.42.0. Research has confirmed that no frontend call site requires any of these endpoints in passkey mode (passkey users get their own profile data via `/auth/me` and rename via the CLI). If the implementation phase surfaces a legitimate passkey-mode caller, it MUST be replaced (e.g. with a response-body field on `/auth/me` or a dedicated CLI command) rather than preserving the endpoint.
- **FR-009a**: `HomeOnlyAdminAuth` MUST be renamed to `HomeOnlyAuth` and its admin-checking responsibility removed (admin is no longer a concept after this refactor). The single `HomeOnlyAuth` class MUST be applied to BOTH the 18 existing admin endpoints AND every `/api/profiles/*` endpoint. Its behavior MUST remain: raise `HttpError(404)` before downstream auth runs when `AUTH_MODE != "home"`, so the security boundary is uniform and auditable across all gated endpoints.

#### API response shape

- **FR-010**: The `/auth/me` response in both modes MUST NOT include an `is_admin` key.
- **FR-011**: No endpoint response or server-rendered page MUST surface `is_staff` or any derived "admin" flag at the per-user level. Frontend admin-visibility signals MUST be derived from auth mode only.

#### CLI surface

- **FR-012**: The `cookie_admin` CLI MUST NOT expose `promote` or `demote` subcommands.
- **FR-013**: The `cookie_admin create-user` subcommand MUST NOT accept an `--admin` option. All users created through the CLI MUST be created with `is_staff=False`.
- **FR-014**: The `cookie_admin list-users` subcommand output (both text and `--json`) MUST NOT include an admin column/field.
- **FR-015**: The `cookie_admin delete-user` subcommand MUST NOT enforce a minimum-admin-count floor. Deleting the last remaining user MUST succeed.
- **FR-016**: All other `cookie_admin` subcommands (set-api-key, test-api-key, set-default-model, prompts, sources, quota, set-unlimited, remove-unlimited, rename, reset, cleanup_device_codes) MUST continue to function unchanged in their core behavior.
- **FR-016a**: Informational `cookie_admin` subcommands (`status`, `audit`, and any other command that reports user or admin counts) MUST be audited and have every admin-related field stripped from their output (both text and `--json` shapes). Specifically: any field reporting the count of admins, the `is_staff` flag on a user record, or any "admin_concept" metadata MUST be removed — not retained-as-False and not replaced with a sentinel value. The post-refactor CLI output MUST contain no trace of the admin concept.
- **FR-016b**: `CLAUDE.md` and any other in-repo documentation that lists or describes CLI subcommands MUST be updated to reflect the removed subcommands (`promote`, `demote`), removed flags (`--admin` on `create-user`), and trimmed informational command outputs. No orphaned admin-concept references in docs.

#### Code-surface cleanup

- **FR-017**: `apps/core/auth.py::AdminAuth` MUST be deleted. Any remaining call sites MUST be migrated to `HomeOnlyAuth` (for endpoints that should be home-mode-only) or to `SessionAuth` (for endpoints that work in both modes). The "admin" concept no longer exists in the auth layer after this refactor.
- **FR-018**: Tests that asserted `is_staff`-driven behavior (e.g. `test_demote_last_admin_refused`, any `test_promote_*`, quota tests that covered `is_staff=True` bypass) MUST be deleted or rewritten so they assert only `unlimited_ai`-driven behavior.
- **FR-019**: The legacy settings template (`apps/legacy/templates/legacy/settings.html`) and its view context (`apps/legacy/views.py`) MUST derive `is_admin` purely from `auth_mode == "home"`. The `is_admin` context variable is retained as a readable template label (keeps existing `{% if is_admin %}` blocks idiomatic). Every compound condition like `{% if is_admin and auth_mode == "home" %}` in the template MUST be simplified to `{% if is_admin %}` because the two checks are now equivalent. No template block MUST depend on any per-user flag.
- **FR-020**: The project constitution (`.specify/memory/constitution.md`) Principle III MUST be amended to state explicitly that passkey users are peers, that there is no in-app admin privilege in passkey mode, and that app configuration is exclusively CLI-driven.

#### Data / schema posture

- **FR-021**: No data migration MUST be introduced for `is_staff`. The project is in development mode with no upgrade contract for existing deployments; operators can nuke and reinitialise.
- **FR-021a**: The `is_staff` column MUST stay on the User model (Django `AbstractUser` requires it; switching to a custom User model is explicitly out of scope). The refactor eliminates only the privilege semantics; the column becomes a Django-framework-only concern with a permanent value of `False` for application-created users.
- **FR-021b**: A pytest static test MUST be added that scans `apps/` for the string `is_staff`, failing the test suite if any match is found outside an explicit allowlist. The allowlist MUST permit: (a) Django model field declarations and migrations, (b) user-creation defaults that set `is_staff=False`, (c) the static test itself. Any other occurrence MUST fail the test with a message naming the file:line and the expected remediation. This test runs in CI and prevents future regressions without touching data.

#### Non-regression

- **FR-022**: All non-test application code that writes `is_staff` MUST set it to `False` (either explicitly or by accepting Django's default). No production code path MUST set `is_staff=True`. Test fixtures MAY set `is_staff=True` solely to assert that the flag has no effect on behavior (e.g. `test_is_staff_does_not_bypass_quota` in T014).
- **FR-023**: The device-code authorization flow and WebAuthn registration/login flows MUST be untouched by this change.
- **FR-024**: Home-mode profile creation, switching, and deletion MUST behave identically to today.

### Key Entities *(include if feature involves data)*

- **User**: Django `AbstractUser` subclass used only in passkey mode. Column `is_staff` remains on the table (Django requirement) but is no longer read by any application code path. After this change, `is_staff` is effectively metadata-only and always `False` for application-created users.
- **Profile**: Session-scoped identity in both modes. Owns `unlimited_ai: bool` — the single remaining privilege flag in the system. In home mode, profiles have no associated User; in passkey mode, each Profile has a FK to a User.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After the refactor, a code scan for `is_staff` reads in `apps/` returns zero results in quota logic, profile API filtering, auth helpers, auth classes, API response serializers, legacy template context, and CLI subcommands. The only permitted residual mentions in `apps/` are (a) the default-False set on user creation, (b) Django model / migration internals. The pytest regression guard (FR-021b / T039) enforces this invariant in CI. The frontend is governed by T034's one-time cleanup + TypeScript type checking + code review; no automated static guard is required on the frontend side because the type system catches consumer reads.
- **SC-002**: In `home` mode, on a fresh deployment, an unauthenticated user can create a profile and within 30 seconds reach every admin UI section in both the modern and legacy frontends, and perform a sample admin action (e.g. saving an AI prompt) in each, with 200 responses throughout.
- **SC-003**: In `passkey` mode, on a fresh deployment, an operator can grant unlimited AI to a non-staff user via a single CLI command, and that user's subsequent AI requests bypass quota limits. Meanwhile, a user with `is_staff=True` but `unlimited_ai=False` hits quota limits identically to any ordinary user.
- **SC-004**: In `passkey` mode, all 18 admin REST endpoints return 404 to authenticated passkey users, identical to pre-refactor v1.42.0 behavior. Both frontends render no admin UI.
- **SC-005**: `cookie_admin --help` output contains zero references to `promote`, `demote`, `admin`, `is_staff`, or any "one-admin floor" concept. `cookie_admin create-user --help` has no `--admin` flag.
- **SC-006**: The full test suite passes after the refactor. Tests that previously asserted `is_staff`-driven behavior are either deleted as no-longer-applicable or rewritten to assert `unlimited_ai`-driven behavior; no test stubs or `@pytest.mark.skip` markers are introduced.
- **SC-007**: A reader of the constitution's Principle III, without other context, correctly infers that passkey-mode users are peers and that admin work is CLI-only.
- **SC-008**: In passkey mode, every `/api/profiles/*` endpoint returns 404 to an authenticated passkey session; no response body is leaked; the endpoints behave as if they do not exist.

## Assumptions

- This repository's only active deployment (the developer's own) either has no `is_staff=True` users whose practical ability depends on flags beyond what this refactor preserves, or the developer is accepting the behavior change for their own account.
- `django.contrib.admin` remains in `INSTALLED_APPS` but no URL mount exists; this refactor does not touch that.
- The `Profile.unlimited_ai` field, its migrations, and its CLI tooling already exist and are correct; this refactor relies on them unchanged.
- Profile list scope decisions apply only to the passkey-mode API response shape; home mode already returns all profiles because there are no users to filter by.
- The constitution amendment is in-scope for this PR (single bundled change), not a separate follow-up.

## Dependencies

- Built on top of feature 013-admin-home-only (v1.42.0): that feature introduced `HomeOnlyAdminAuth` and moved admin UI gating to auth-mode-based checks. This refactor assumes those pieces are in place and correct.
- Constitution file `.specify/memory/constitution.md` must be modifiable within this feature's PR.

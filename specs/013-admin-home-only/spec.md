# Feature Specification: Lock admin surface to home mode only; add CLI parity for passkey-mode ops

**Feature Branch**: `013-admin-home-only`
**Created**: 2026-04-18
**Status**: Draft
**Input**: User description: "Lock the web admin surface so it is reachable only when Cookie is running in home mode. In passkey mode, every admin endpoint returns 404 and the admin UI is hidden. Operators on passkey deployments manage the application via `python manage.py cookie_admin`, whose coverage is expanded to match the web admin feature set."

## Clarifications

### Session 2026-04-18

Ambiguities identified by internal coverage scan were resolved inline using best-fit defaults. No user intervention required.

- Q: How does the mode gate produce the 404, and where does it run relative to authentication? → A: Implement it as a thin `AdminAuth` subclass (`HomeOnlyAdminAuth`) in `apps/core/auth.py` whose `__call__` raises `ninja.errors.HttpError(404, "Not found")` BEFORE invoking `super().__call__(request)` when `AUTH_MODE != "home"`. Gated endpoints change `auth=AdminAuth()` → `auth=HomeOnlyAdminAuth()`. The mode check runs inside Ninja's auth phase, before any cookie extraction or admin check — so no auth-failure log line is written for passkey-mode probes. A plain `@wraps` decorator above the `@router.*` line is NOT sufficient because Ninja's view wrapper resolves `auth=` before invoking the inner (decorated) function; the decorator would run too late. The file-level symbol name in the spec stays `home_mode_only` as shorthand for "the mode gate", but the runtime realisation is the auth subclass. (Resolved in FR-001 and US1 acceptance scenario 1.)
- Q: Can `set-api-key` be used to wipe the key (set it to empty)? → A: No. An empty key value (`--key ""` or empty stdin) is rejected with a clear error and no DB write. A dedicated wipe path is out of scope for this release — removing a configured key requires a DB console. (Recorded in FR-017a.)
- Q: What does `cookie_admin sources test --all` output when some sources fail? → A: Exit code 0 if the command ran to completion (regardless of per-source outcomes). `--json` returns a list of per-source objects with `ok: bool`, `source_id`, `status_code`, and `message`. Plain-text output prints one line per source plus a summary `N ok / M failed`. A nonzero exit is reserved for command-level errors (DB unreachable, invalid `--id`). (Recorded in FR-027a.)
- Q: Do the new `cookie_admin` subcommands work in home mode as well as passkey mode? → A: Yes, but scoped to the NEW subcommands only. The CLI's existing `require passkey mode` guard is kept for user-lifecycle subcommands (`list-users`, `promote`, `demote`, `activate`, `deactivate`, `create-user`, `delete-user`, `set-unlimited`, `remove-unlimited`, `usage`, `create-session`) because those operate on the Django `User` model that only exists in passkey mode. The new subcommands (`set-api-key`, `test-api-key`, `set-default-model`, `prompts *`, `sources *`, `quota *`, `rename`) MUST work in both modes because they operate on `AppSettings`, `AIPrompt`, `SearchSource`, and `Profile`, all of which exist identically in both modes. Implementation: the top-level passkey-mode guard in `cookie_admin.Command.handle` moves from a blanket check to a per-subcommand decision. (Recorded in FR-032a and FR-032b.)
- Q: Frontend test strategy for "SPA Settings does not render admin-only components in passkey mode" — component-level or end-to-end? → A: Component-level (Vitest + React Testing Library). The test mounts `Settings` with a mocked `AuthContext` where `mode === 'passkey'` and asserts the admin section queries resolve to `null`. No E2E test is required for acceptance. (Recorded in FR-042.)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Passkey deployment stops exposing admin endpoints (Priority: P1)

An operator runs Cookie internet-facing in passkey mode. Today, every admin-scoped REST endpoint still *exists* on the network — an authenticated regular user (or an attacker with a stolen session) can probe them, see an auth error, and learn that admin functionality is present. After this change, none of those endpoints exist on a passkey deployment: probing any of them returns the same `404 Not Found` that a nonexistent path returns, with no hint that the endpoint was ever there.

**Why this priority**: This is the direct security fix driving the feature. It closes the attack surface flagged by the external HexStrike scan on 2026-04-18 (API-key leakage, prompt-template tampering, SSRF via source-test, and the reset endpoint). Without it, an admin session compromise in passkey mode is catastrophic.

**Independent Test**: Deploy Cookie with `AUTH_MODE=passkey`. Hit each of the 18 admin endpoints enumerated below with every credential state (no session, authenticated non-admin session, authenticated admin session). Confirm all responses are indistinguishable from a 404 for a nonexistent path. No response body reveals that the endpoint ever existed; server logs show no authentication attempt.

**Acceptance Scenarios**:

1. **Given** a Cookie deployment in passkey mode, **When** an unauthenticated client requests `POST /api/ai/save-api-key`, **Then** the response is `404 Not Found` with body `{"detail": "Not found"}` and no security log entry about an auth failure is written.
2. **Given** a Cookie deployment in passkey mode with a logged-in non-admin user, **When** that user's browser requests `POST /api/sources/test-all/`, **Then** the response is `404 Not Found`; the request never reaches the handler and never invokes `AdminAuth`.
3. **Given** a Cookie deployment in passkey mode with a logged-in admin user, **When** that user's browser requests `GET /api/system/reset-preview/`, **Then** the response is `404 Not Found`; the endpoint is gone regardless of admin status.
4. **Given** a Cookie deployment in home mode, **When** any profile holder performs any admin action via the existing UI or API, **Then** the behavior is byte-for-byte identical to today: same status codes, same response shapes, same side effects.

---

### User Story 2 - Passkey deployment hides the admin UI (Priority: P1)

The two frontends (legacy ES5 templates and React SPA) each render admin controls in settings pages and nav menus. In passkey mode those controls become unreachable (their backing endpoints 404) and the only logged-in users who could ever see them are admins. After this change, the admin controls are also invisible in passkey mode — admins see only user-self-service sections. There are no 404 flashes, no broken toggles, no misleading "reset disabled" messaging.

**Why this priority**: Paired with Story 1. Even with the endpoints gone, a visible-but-broken admin UI (a) is confusing, (b) keeps attack-surface-sized symbols in the frontend bundle that can be targeted, and (c) invites regressions where the hide logic is accidentally lost. Hiding the UI at the same time locks the intent.

**Independent Test**: In passkey mode, log in as an admin user and load the settings page in both frontends. The only sections visible are user-owned: general preferences, passkeys, delete-my-account, the user's own AI usage, and the read-only AI status. Admin-only sections (API key, prompts, selectors, sources, AI quotas, danger zone, user admin controls) are absent from the DOM. In home mode, the same settings page renders identically to today.

**Acceptance Scenarios**:

1. **Given** a passkey-mode deployment with an admin user, **When** that user opens the modern SPA settings page, **Then** API-key, Prompts, Selectors, Sources, AI Quota, and Danger Zone sections are not in the rendered DOM; tabs or nav entries that only link to admin sections are also absent.
2. **Given** a passkey-mode deployment with an admin user, **When** that user opens the legacy settings page, **Then** the template renders only non-admin blocks — every `{% if is_admin %}` block is suppressed.
3. **Given** a home-mode deployment, **When** any profile opens either frontend's settings page, **Then** the admin UI is identical to the current implementation (admin is effectively "everyone" in home mode by design).

---

### User Story 3 - Operators can run every admin task from the CLI (Priority: P1)

With the web admin surface gone in passkey mode, the CLI (`python manage.py cookie_admin`) is the only admin path. The CLI today covers user lifecycle and factory reset but has gaps: no way to set or test the OpenRouter API key, no way to edit AI prompts, no way to manage search sources, no way to adjust AI quotas, no way to edit the default AI model, no way to rename an existing profile from the CLI (the `/rename/` endpoint exists in the web UI but has no CLI counterpart), and cache-health is only exposed via a gated HTTP endpoint. This story closes every gap so a passkey operator has full parity with yesterday's web admin.

**Why this priority**: Without this, Story 1 regresses operator capability: stopping endpoints that no one can replace removes legitimate functionality. The CLI must land in the same release as the endpoint lockdown.

**Independent Test**: In a passkey-mode environment, perform every admin task that used to require the web UI — set an API key, validate it, set the default model, list/edit/activate AI prompts, list sources, toggle individual and all sources, update selectors manually, run per-source and all-sources health tests, trigger AI-assisted selector repair, read and set any of the six AI quota fields, rename a user's profile, and read cache health. Every action completes via `python manage.py cookie_admin …`; every mutation emits a `security_logger.warning` entry; every command supports `--json` where the existing commands do.

**Acceptance Scenarios**:

1. **Given** a fresh passkey deployment with no API key set, **When** the operator runs `python manage.py cookie_admin set-api-key --stdin` and pipes a valid key on stdin, **Then** `AppSettings.openrouter_api_key` is persisted, the operator sees a success message, and `security_logger` logs a warning that the key was changed (without logging the key itself).
2. **Given** an operator wants to edit an AI prompt, **When** they run `python manage.py cookie_admin prompts set remix --system-file /tmp/system.txt --user-file /tmp/user.txt --model anthropic/claude-3.7`, **Then** the system prompt, user template, and model fields are updated from the file contents; other fields (e.g. active flag) remain unchanged; an `--active false` flag can deactivate the prompt in a separate call.
3. **Given** a source with a stale selector, **When** an operator runs `python manage.py cookie_admin sources repair 42`, **Then** the same AI selector-repair flow that backs `POST /api/ai/repair-selector` runs and reports the outcome in plain text or `--json`.
4. **Given** an operator wants to change the daily tips quota to 50, **When** they run `python manage.py cookie_admin quota set tips 50`, **Then** `AppSettings.daily_limit_tips` is updated to 50 and `quota show` reflects the new value.
5. **Given** an operator wants cache health on a passkey deployment, **When** they run `python manage.py cookie_admin status --json`, **Then** the JSON response includes a `cache` block with the same data that the now-gated `GET /api/recipes/cache/health/` returned.
6. **Given** an operator wants to rename user "pk-abc123" to "Alice", **When** they run `python manage.py cookie_admin rename pk-abc123 --name "Alice"`, **Then** the profile linked to that user is renamed and the change is visible in `list-users`.

---

### User Story 4 - Remove the version fingerprint from the mode endpoint (Priority: P2)

The public `GET /api/system/mode/` endpoint returns the deployed Cookie version string. An anonymous attacker uses this to fingerprint the deployment and look up known-vulnerable versions. Removing the key from the response eliminates that fingerprint without affecting the frontends (which use `/mode/` only to detect `home` vs `passkey`). This ships in the same release because it was flagged by the same HexStrike scan.

**Why this priority**: Small, orthogonal, low-risk, same security-scan origin. Bundling it avoids a second release cycle.

**Independent Test**: `curl https://<deployment>/api/system/mode/` returns a JSON body with `mode` and (in passkey mode) `registration_enabled`; it does not include a `version` key. The frontends continue to work unchanged because neither reads the version from this endpoint.

**Acceptance Scenarios**:

1. **Given** a running deployment in either mode, **When** any client calls `GET /api/system/mode/`, **Then** the JSON response omits the `version` key.
2. **Given** a passkey-mode deployment, **When** the SPA or legacy frontend boots, **Then** the mode-based UI decisions still work (home vs passkey layout) because they never depended on `version`.

---

### Edge Cases

- **Mode-switching mid-session**: an operator edits `AUTH_MODE` from `home` → `passkey` and restarts the container. Admin sessions carrying `profile_id` cookies now hit 404 on every admin endpoint. This is correct behavior — no new handling is required. Browser UI will hide admin sections on the next page load because `/api/system/mode/` reports `passkey`.
- **AUTH_MODE set to an unrecognised value**: per the constitution (Principle III), the system falls back to home mode. The decorator treats the fallback consistently — endpoints are reachable (home-mode behavior).
- **Decorator ordering**: the mode-check decorator must run BEFORE the authenticator. If stacked the wrong way, `AdminAuth` runs first in passkey mode and returns 401/403, leaking endpoint existence. Acceptance tests explicitly verify no auth-failure log line is written on a 404 probe.
- **Dead helpers**: after the inline "403 with hint" block is deleted from the reset endpoint handlers, any helper whose only caller was that block must be removed (not kept around "just in case"). No backwards-compatibility shims.
- **CLI output conventions**: every new mutating subcommand writes a `security_logger.warning` line even when `--json` is used. Structured output must not suppress audit logging.
- **Prompt file handling**: when `prompts set` is called with a `--system-file` or `--user-file` pointing at a missing or unreadable path, the command exits with a clear error and no DB write.
- **Legacy frontend admin views**: if an already-authenticated passkey admin navigates directly to an admin-only legacy view URL, the template-side hiding renders a mostly empty settings page rather than an error. That is acceptable — the endpoints would 404 anyway — but the spec requires the decision (template-only hide vs. decorator redirect) to be documented and chosen.
- **`sources repair` without an API key in passkey mode**: the CLI subcommand depends on OpenRouter. If `AppSettings.openrouter_api_key` is empty the command exits non-zero with a clear error and writes no DB changes.

## Requirements *(mandatory)*

### Functional Requirements

**Backend mode gate**

- **FR-001**: Introduce `HomeOnlyAdminAuth` in `apps/core/auth.py` as a thin subclass of `AdminAuth` that overrides `__call__` to raise `ninja.errors.HttpError(404, "Not found")` when `settings.AUTH_MODE != "home"`, otherwise delegates to `super().__call__(request)`. The mode check MUST execute before the cookie is extracted and before `authenticate()` is invoked. Ninja converts the raised error to HTTP `404 Not Found` with body `{"detail": "Not found"}`, matching the body it emits for undefined paths.
- **FR-002**: The mode check in `HomeOnlyAdminAuth.__call__` MUST run before the cookie is extracted and before `authenticate()` is invoked, so that in non-home modes no authentication attempt (and no `security_logger` auth-failure line) is produced for the gated paths. An integration test MUST assert this by probing each endpoint in passkey mode and verifying the security log captures no new lines.
- **FR-003**: The following endpoints MUST have `auth=AdminAuth()` replaced with `auth=HomeOnlyAdminAuth()` and MUST therefore return `404 Not Found` in passkey mode regardless of caller identity:
  1. `POST /api/ai/save-api-key`
  2. `POST /api/ai/test-api-key`
  3. `GET /api/ai/prompts`
  4. `GET /api/ai/prompts/{prompt_type}`
  5. `PUT /api/ai/prompts/{prompt_type}`
  6. `POST /api/ai/repair-selector` (note: path has no trailing slash in the current code)
  7. `GET /api/ai/sources-needing-attention`
  8. `PUT /api/ai/quotas`
  9. `GET /api/system/reset-preview/`
  10. `POST /api/system/reset/`
  11. `POST /api/sources/{source_id}/toggle/`
  12. `POST /api/sources/bulk-toggle/`
  13. `PUT /api/sources/{source_id}/selector/`
  14. `POST /api/sources/{source_id}/test/`
  15. `POST /api/sources/test-all/`
  16. `GET /api/recipes/cache/health/`
  17. `POST /api/profiles/{profile_id}/set-unlimited/`
  18. `PATCH /api/profiles/{profile_id}/rename/`
- **FR-004**: In home mode, every one of those 18 endpoints MUST respond exactly as it does today — identical status codes, response shapes, side effects, rate-limit behavior, and audit log output. Existing backend tests in home mode MUST pass without modification.
- **FR-005**: The inline `if AUTH_MODE == "passkey"` 403-with-hint blocks in `apps/core/api.py`'s reset-preview and reset handlers MUST be deleted; the decorator replaces them. Rate-limit and confirmation-text logic MUST remain.
- **FR-006**: `AdminAuth` in `apps/core/auth.py` MUST NOT be modified. `HomeOnlyAdminAuth` is a NEW class that subclasses `AdminAuth` without altering it. Home-mode permissiveness and passkey-mode `is_staff` enforcement in the base class are unchanged.
- **FR-007**: Admin-scope-expansion endpoints whose behavior differs by staff status without changing reachability (notably `GET /api/profiles/`) MUST be left unchanged.
- **FR-008**: If any helper function (e.g. an unused 403 error-message builder) becomes dead code after the inline guards are removed, it MUST be deleted, not retained.

**Backend public surface trim**

- **FR-009**: `GET /api/system/mode/` MUST NOT return a `version` key in its JSON response body. Other keys (`mode`, `registration_enabled`) are unchanged.

**Frontend hide-in-passkey**

- **FR-010**: The legacy Django template `apps/legacy/templates/legacy/settings.html` MUST render admin-only blocks only when the authenticated profile is admin AND the server is in home mode. Every `{% if is_admin %}` becomes `{% if is_admin and auth_mode == "home" %}`. The `auth_mode` context variable already exists via `apps/core/context_processors.py`.
- **FR-011**: Legacy navigation templates (e.g. `nav_header.html`) MUST apply the same combined check to any admin-only links.
- **FR-012**: The chosen legacy admin view policy MUST be: template-side hiding only; the `require_admin` decorator is NOT modified. In passkey mode an admin who navigates directly to an admin-only legacy URL lands on a mostly-empty settings page. This avoids surprising redirects and matches the SPA behavior.
- **FR-013**: The React SPA `frontend/src/screens/Settings.tsx` MUST hide admin-only sections when `mode !== 'home'`. Affected components include (at least): `APIKeySection`, `SettingsPrompts`, `PromptCard`, `SettingsSelectors`, `SettingsSources`, `SourceItem`, `SelectorItem`, `ConfirmResetStep`, `ResetPreviewStep`, `DangerZoneInfo`, `SettingsDanger`, `AIQuotaSection`, admin controls inside `UserProfileCard`, admin controls inside `SettingsUsers`.
- **FR-014**: The SPA MUST continue to render, in all modes, user-self-service sections: `SettingsGeneral`, `SettingsPasskeys`, `DeleteAccountSection`, `UserDeletionModal`, `AIUsageSection` (own usage), and the read-only portion of `AIStatusDisplay`.
- **FR-015**: Mode information MUST be read from the existing `useMode()` hook exported from `frontend/src/router.tsx` (the `ModeContext` already fetches `/api/system/mode/` at boot). No new HTTP call and no new context provider are introduced. Admin components that previously passed through `isAdmin` from `useAuth()` now also consult `useMode()`.
- **FR-016**: Hiding is sufficient; components need not be tree-shaken from the bundle. (The endpoints 404 so the only downside is bundle size, which is not the concern.)

**CLI parity — new `cookie_admin` subcommands**

- **FR-017**: `cookie_admin set-api-key [--key KEY | --stdin]` MUST persist `AppSettings.openrouter_api_key`. `--stdin` reads the key from standard input. The key value MUST NEVER be logged or echoed; the security log line MUST only record that the key changed.
- **FR-017a**: `cookie_admin set-api-key` MUST reject an empty key value (empty `--key ""` or empty stdin) with a clear error message and no DB write. Wiping an already-configured key is out of scope for this release.
- **FR-018**: `cookie_admin test-api-key [--key KEY | --stdin]` MUST validate a key against OpenRouter WITHOUT persisting it. Exit code reflects validity; `--json` output includes a boolean `valid` field.
- **FR-019**: `cookie_admin set-default-model <model_id>` MUST write `AppSettings.default_ai_model`.
- **FR-020**: `cookie_admin prompts list [--json]` MUST list all AI prompts with their type, model, and active state.
- **FR-021**: `cookie_admin prompts show <prompt_type> [--json]` MUST display a single prompt's full content.
- **FR-022**: `cookie_admin prompts set <prompt_type> [--system-file PATH] [--user-file PATH] [--model MODEL] [--active {true,false}]` MUST read system-prompt and user-template content from files. Omitted flags MUST leave the corresponding field unchanged. Missing or unreadable files MUST fail the command with a clear error and no DB write.
- **FR-023**: `cookie_admin sources list [--attention] [--json]` MUST list search sources. With `--attention`, only sources with `needs_attention=True` are shown.
- **FR-024**: `cookie_admin sources toggle <source_id>` MUST flip a single source's enabled state.
- **FR-025**: `cookie_admin sources toggle-all {--enable | --disable}` MUST set every source's enabled state to the same value.
- **FR-026**: `cookie_admin sources set-selector <source_id> --selector CSS` MUST overwrite the source's CSS selector.
- **FR-027**: `cookie_admin sources test [--id N | --all] [--json]` MUST run the same health-check logic as `POST /api/sources/{source_id}/test/` and `POST /api/sources/test-all/`. Either `--id` or `--all` is required.
- **FR-027a**: `cookie_admin sources test` MUST exit 0 whenever the command runs to completion, regardless of per-source pass/fail outcomes. `--json` MUST return a list of per-source objects shaped `{source_id, name, ok, status_code, message}`. Plain-text output prints one line per source plus a trailing `N ok / M failed` summary. A nonzero exit is reserved for command-level errors (invalid `--id`, DB unreachable).
- **FR-028**: `cookie_admin sources repair <source_id>` MUST run the same AI-assisted selector-regeneration flow as `POST /api/ai/repair-selector`. If the API key is not configured it MUST fail with a clear error and no DB write.
- **FR-029**: `cookie_admin quota show [--json]` MUST display every `AppSettings.daily_limit_*` field (remix, remix-suggestions, scale, tips, discover, timer).
- **FR-030**: `cookie_admin quota set {remix|remix-suggestions|scale|tips|discover|timer} <N>` MUST update one quota. `N` must be a non-negative integer; negative or non-integer input fails with a clear error and no DB write.
- **FR-031**: `cookie_admin rename <user_id_or_username> --name NEW` MUST, in passkey mode, rename the profile linked to the specified user (lookup accepts either the numeric user id or the username). In home mode, the positional argument is treated as `profile_id`.
- **FR-032**: Every mutating subcommand MUST emit a `security_logger.warning` line, even when `--json` is used. Read-only subcommands (`list`, `show`, `status`, `quota show`) MUST NOT emit security warnings.
- **FR-032a**: Every new `cookie_admin` subcommand (`set-api-key`, `test-api-key`, `set-default-model`, `prompts *`, `sources *`, `quota *`, `rename`) MUST be mode-agnostic: it behaves identically under `AUTH_MODE=home` and `AUTH_MODE=passkey`, operating on `AppSettings` / `AIPrompt` / `SearchSource` / `Profile` which exist identically in both modes. Tests MUST cover both modes for subcommands whose behavior differs per mode (e.g. `rename` — positional arg is `profile_id` in home, `user_id|username` in passkey per FR-031).
- **FR-032b**: The existing blanket passkey-mode check at the top of `cookie_admin.Command.handle` MUST be refactored so it applies only to the user-lifecycle subcommands that operate on the Django `User` model (`list-users`, `create-user`, `delete-user`, `promote`, `demote`, `activate`, `deactivate`, `set-unlimited`, `remove-unlimited`, `usage`, `create-session`). All other existing subcommands (`status`, `audit`, `reset`) and all new subcommands MUST be callable in either mode. Error messages for the remaining passkey-only subcommands remain unchanged.
- **FR-033**: `python manage.py cookie_admin --help` MUST list every new subcommand.
- **FR-034**: The existing `cookie_admin status [--json]` MUST be extended so its `--json` output includes a `cache` block matching the data that `GET /api/recipes/cache/health/` returns today.

**Observability & auditability**

- **FR-035**: In passkey mode, probes of any of the 18 gated endpoints MUST NOT produce auth-failure lines in `security_logger`. A 404 is a 404; no audit noise.
- **FR-036**: In home mode, existing security-log behavior on the 18 endpoints (e.g. audit lines on `POST /api/system/reset/`) MUST be unchanged.

**Versioning and release notes**

- **FR-037**: The deployed Cookie version MUST be bumped to `1.42.0` (minor: security hardening per repo convention) from the current `1.41.0`.
- **FR-038**: GitHub release notes under a "Security" heading MUST list: (1) 18 admin endpoints return 404 in passkey mode, (2) admin UI hidden in passkey mode, (3) version fingerprint removed from `/api/system/mode/`.

**Testing obligations**

- **FR-039**: Each of the 18 gated endpoints MUST have an integration test that asserts `404 Not Found` in passkey mode.
- **FR-040**: Each of the 18 gated endpoints MUST retain its existing home-mode tests; those tests MUST pass unchanged.
- **FR-041**: Each new `cookie_admin` subcommand MUST have at minimum: a happy-path test, an invalid-input test, and an assertion that a `security_logger.warning` line is emitted on mutation (read-only subcommands assert no warning).
- **FR-042**: A frontend test MUST verify that in passkey mode, the SPA Settings screen does not render admin-only components. The test is a Vitest component test using React Testing Library: mount `Settings` with a mocked `AuthContext` where `mode === 'passkey'` and assert that queries for each admin-only section's test-id resolve to `null`. No Playwright/E2E test is required for acceptance.

**Out of scope (explicit)**

- `AdminAuth` itself is not changed. Home-mode permissiveness is by design (constitution Principle III).
- The pentest target configuration (`pentest/targets/cookie.yaml` in the appserver repo) is not updated in this spec; a follow-up in that repo will re-run the authenticated pentest against the hardened surface.
- `SECURE_PROXY_SSL_HEADER` / HTTP-redirect proxy-chain issue is not addressed here (infra repo concern).
- Tunnel / Access / Cloudflare / Traefik configuration is not changed.

### Key Entities

- **Gated admin endpoint**: one of the 18 HTTP handlers enumerated in FR-003. Each has a method, path, handler file, and an `auth=AdminAuth()` declaration. The decorator wraps the handler above the `auth=` parameter so the 404 path is taken before any auth attempt.
- **AppSettings (existing)**: the singleton model holding `openrouter_api_key`, `default_ai_model`, and `daily_limit_*` fields. New CLI commands read and write this model.
- **AIPrompt (existing)**: one row per prompt type. New `prompts` CLI subcommands read and write rows in this table, reading multi-line content from files.
- **SearchSource (existing)**: one row per recipe source with CSS selector, enabled flag, and health metadata. New `sources` CLI subcommands read and write rows in this table.
- **Profile / User linkage (existing, passkey mode)**: `rename` CLI subcommand looks up the `User` by `user_id` or `username` and updates the linked `Profile.name`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In passkey mode, 100% of requests to any of the 18 gated endpoints return `404 Not Found`, with no `AdminAuth` invocation and no auth-failure security log line, regardless of caller identity (unauthenticated, non-admin, admin).
- **SC-002**: In home mode, 100% of existing backend tests for those 18 endpoints pass without modification; the full existing test suite is green.
- **SC-003**: In passkey mode, the rendered settings page in both frontends contains 0 admin-only sections; in home mode, the rendered settings page contains the same admin sections it does today.
- **SC-004**: `python manage.py cookie_admin --help` lists every new subcommand; the CLI has functional parity with the removed web admin surface (validated by completing every admin task previously performed via the web UI, end-to-end, using only the CLI).
- **SC-005**: `GET /api/system/mode/` response no longer includes a `version` key; manual inspection against a deployed passkey instance confirms no version fingerprint is returned to anonymous requests.
- **SC-006**: The deployed version advances to `1.42.0`; the corresponding GitHub release describes the three security changes under a "Security" heading.
- **SC-007**: Unauthenticated re-scan of the deployment using the same tooling that surfaced the original finding shows no admin endpoints in the path inventory.

## Assumptions

- The existing `auth_mode` template context variable provided by `apps/core/context_processors.py` is reliable and available in every relevant legacy template.
- The React SPA's `AuthContext` already exposes mode because it's the source of truth for the home/passkey layout split. No new HTTP call is introduced.
- Django Ninja's decorator stacking order is: decorators listed closer to the function are applied first. The `home_mode_only` decorator must appear *above* the `@router.*(..., auth=AdminAuth())` line so it executes before Ninja's auth resolution.
- Deleting dead helpers after the reset-handler 403 blocks are removed is bounded in scope — only helpers whose only caller was the deleted block are subject to removal.
- Frontend "hide" means conditional rendering guarded by `mode === 'home'`; it does not mean code-splitting or tree-shaking.
- The CLI follows the existing conventions in `apps/core/management/commands/cookie_admin.py`: plain-text default output, optional `--json`, `security_logger.warning` on mutations, non-zero exit on error.
- Release notes live in GitHub Releases (per `CLAUDE.md` "Releases & Versioning" section); there is no repo-level `CHANGELOG.md` to update.

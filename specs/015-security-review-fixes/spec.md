# Feature Specification: Security Review Fixes (Round 2)

**Feature Branch**: `015-security-review-fixes`
**Created**: 2026-04-18
**Status**: Draft
**Input**: User description: Close the verified findings from the post-v1.43.0 security review — secret persistence in cron, session hygiene on logout, production image pinning, CSRF coverage on the pre-session profile mutation endpoint, legacy `innerHTML` chokepoint violation, `cookie_admin create-session --confirm` parity, Dependabot configuration, and an enforced complexity gate — without breaking either frontend (modern React SPA, legacy ES5) in either auth mode (home, passkey).

## Clarifications

### Session 2026-04-18

- Q: Which scheduling mechanism does the production image adopt after the secrets-in-cron fix? → A: Replace Debian `cron` with **supercronic** — a single-process scheduler running as the app user, reading a static crontab (no secrets), inheriting env directly from its parent process. Rationale: no root daemon, no secrets on disk, no `/proc/1/environ` wrapper needed, smaller audited attack surface than `cron`.
- Q: Does the file-size gate cover `tests/` as well as `apps/`, given Constitution Principle V's "All code" scope? → A: **Yes.** The gate applies to every `*.py` file in `apps/` and `tests/` (migrations excluded). Pre-existing violations are grandfathered via an explicit allowlist in `tests/test_code_quality.py::EXEMPT_FILES` — an auditable list of concrete files with a follow-up spec (`016-code-quality-refactor`) committed to clearing them. New violations are blocked unconditionally. This respects Principle V's "no exceptions" rule (no thresholds raised, no suppression comments added) while keeping this spec bounded.
- Q: Should the gate ship with production-code refactors in the same spec, or defer them to a follow-up? → A: **Defer.** Landing the gate today with a full allowlist (covering the three oversized production files AND the ten oversized test files) blocks future drift. The refactors themselves are substantial (cookie_admin.py alone is 1172 lines) and each carries regression risk — bundling them into a security PR mixes unrelated concerns. Follow-up spec `016-code-quality-refactor` tracks every file in the allowlist and drops them as each is refactored below 500 lines. Allowlist size monotonically decreases.
- Q: Does User Story 5 (passkey display name) ship in this spec? → A: **No — scope-dropped.** Cookie's `WebAuthnCredential` model (`apps/core/models.py`) does not persist `display_name`, so the feature would only surface names in the platform's credential picker UI (Chrome/Apple Passwords). In Cookie's single-user-per-instance deployment model, multiple passkeys per user is uncommon and the picker pain rarely materializes. Shipping ceremony (schema field, sanitizer, SPA form, 6+ tests) without Cookie-side payoff is not worth it. Original review finding M4 is accepted as low-actual-impact UX quirk; revisit if a multi-user deployment pattern emerges.
- Q: Does the legacy ES5 frontend need a display-name input? → A: **Moot — resolved by dropping Story 5.** Also for the record: legacy devices lack WebAuthn support. The legacy `device_pair.html` is a device-code request UI only; it never calls `navigator.credentials.create()`. Passkey registration is a modern-frontend-only capability regardless.
- Q: Does User Story 4 (CSRF tests) need to cover all three pre-session profile endpoints? → A: **No.** Django's `CsrfViewMiddleware` is a global middleware (confirmed in `cookie/settings.py`); it applies identically to every `auth=None` endpoint. Writing three near-identical tests that assert framework behavior is redundant. Narrowed to one integration test covering `select_profile` (the one that mutates session state and was the actual vector of concern in the review). `list_profiles` is a GET (safe method — CSRF doesn't apply). `create_profile`'s CSRF surface is structurally identical to `select_profile`'s, so one test is sufficient regression coverage.
- Q: In passkey mode with multiple users, how does a user identify themselves to the admin for CLI operations like `set-unlimited`? → A: Surface their profile ID (already in `/api/auth/me`, no new storage) as a read-only caption in Settings, passkey mode only. Extend `cookie_admin set-unlimited` / `remove-unlimited` to accept `--profile-id N` as an alternative to the positional `pk_<uuid8>` username. Integer ID is harder to typo over the phone than a hex username; requires zero new PII (`profile.id` already exists). Added as User Story 7 after the question surfaced during /speckit.analyze remediation.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Operator knows secrets never persist on the production container filesystem (Priority: P1)

An operator runs Cookie in production using `docker-compose.prod.yml`. They need to trust that `SECRET_KEY` and `DATABASE_URL` live only in the container's process environment — never in files on disk that a secondary exploit or volume mis-mount could expose.

**Why this priority**: This is the sole HIGH-severity finding. A compromise of the image filesystem today leaks both Django's session-signing key and the database credentials in plaintext via `/etc/cron.d/cookie-cleanup`. Fixing it removes the highest-impact leak vector in the audit.

**Independent Test**: Start the production container. Exec in and `grep -rE "SECRET_KEY|DATABASE_URL" /etc/ /var/ /tmp/ /app/` — expect zero matches. Separately, wait for or trigger each of the three cron jobs (device-code cleanup, session cleanup, search-image cleanup) and confirm each one runs successfully.

**Acceptance Scenarios**:

1. **Given** the production container is running, **When** an operator scans `/etc/`, `/var/`, `/tmp/`, `/app/`, **Then** neither `SECRET_KEY` nor `DATABASE_URL` is present as a literal value.
2. **Given** the production container has been running for at least one hour, **When** the device-code cleanup job is scheduled to run, **Then** the job executes successfully and its output is visible in container logs.
3. **Given** the production container has been running past 03:15 UTC, **When** the session cleanup job fires, **Then** it runs successfully.
4. **Given** the production container has been running past 03:30 UTC, **When** the search-image cleanup job fires, **Then** it runs successfully.

---

### User Story 2 — A logged-out user's stolen session cookie is useless (Priority: P1)

A user in passkey mode logs out of Cookie. If their session cookie is later obtained by an attacker (network sniff, cross-device access, shared machine), that cookie MUST NOT permit any authenticated action.

**Why this priority**: Logout is a trust boundary — users expect their session to be fully invalidated. Today Django's `logout()` leaves `profile_id` in the session, and the passkey auth path has a documented fallback that re-authenticates from `session["profile_id"]` alone. This silently lets a replayed cookie regain access.

**Independent Test**: Log in via passkey. Capture the session cookie. POST to `/api/auth/logout/`. Replay the captured cookie against `/api/auth/me/` and any other authenticated endpoint (e.g., `/api/recipes/favorites/`). Every call must return 401 or 404, never 200.

**Acceptance Scenarios**:

1. **Given** a user logged in via passkey in passkey mode, **When** they POST to `/api/auth/logout/` and then a third party replays the same session cookie against `/api/auth/me/`, **Then** the response is 401 and includes no user or profile data.
2. **Given** a user logged in via passkey, **When** they log out and then the same cookie is replayed against a protected authenticated endpoint, **Then** the response is 401 or 404 (depending on endpoint auth class).
3. **Given** the existing logout test suite, **When** the fix is applied, **Then** all pre-existing logout tests continue to pass.

---

### User Story 3 — Production deployments are reproducible and rollback-safe (Priority: P1)

An operator running a production deployment pulls the published image by a concrete version tag. When a new release ships, pulling does not silently replace their image with a newer version until they update the pin.

**Why this priority**: A `:latest`-pinned production manifest has bitten many teams: a bad build tagged latest propagates to every `docker compose pull`, and rollback becomes "which digest was latest yesterday?" Pinning is a one-line change that makes deployments reproducible.

**Independent Test**: Inspect `docker-compose.prod.yml`. The image reference must be a concrete version tag, not `:latest`.

**Acceptance Scenarios**:

1. **Given** `docker-compose.prod.yml`, **When** a reader inspects the `image:` reference for the web service, **Then** they see a concrete version tag matching the current release, never `:latest`.
2. **Given** the release playbook, **When** an operator follows it to cut a new release, **Then** the playbook includes an explicit step to bump the compose image pin.

---

### User Story 4 — The pre-session profile mutation endpoint rejects forged cross-origin POSTs (Priority: P2)

A home-mode Cookie instance runs on a trusted LAN. Even without user accounts, `/api/profiles/{id}/select/` — which writes `profile_id` into the session — must not accept requests that originate from a third-party page a LAN user visits.

**Why this priority**: Home mode's threat model is trusted-network, but CSRF is still the difference between "my sibling's friend clicks a link and silently swaps my active profile" and "they can't." The existing `CsrfViewMiddleware` runs globally and should protect this endpoint; this story verifies that with an integration test so a future `@csrf_exempt` regression is caught.

**Independent Test**: POST to `/api/profiles/{id}/select/` without a CSRF token → 403. POST with a valid token → 200. (Narrowed from three endpoints to one — `list_profiles` is a GET so CSRF doesn't apply; `create_profile`'s CSRF surface is structurally identical to `select_profile`'s, so one regression test covers both.)

**Acceptance Scenarios**:

1. **Given** a home-mode deployment with at least one profile, **When** a POST to `/api/profiles/{id}/select/` arrives without a valid CSRF token, **Then** the response is 403.
2. **Given** a home-mode deployment, **When** the same request is made with a valid CSRF token, **Then** it proceeds and returns 200.
3. **Given** the test suite, **When** it runs, **Then** there is an integration test in `tests/test_csrf.py` asserting both outcomes above.

---

### User Story 5 — Every legacy JS file uses the audited `innerHTML` chokepoint (Priority: P3)

A developer auditing the legacy ES5 frontend for XSS follows the documented chokepoint rule: all HTML insertion routes through `Cookie.utils.setHtml` in `utils.js`. A grep for `.innerHTML =` or `.innerHTML +=` in `apps/legacy/static/legacy/js/` returns zero matches outside `utils.js`.

**Why this priority**: The current violation at `search.js:260` bypasses the audit surface with escape-safe content, so it's not an exploit today. But the whole point of the chokepoint pattern is that an auditor doesn't have to verify every call site individually. Any violation corrodes the pattern.

**Independent Test**: Run `grep -rnE "\.innerHTML\s*(=|\+=)" apps/legacy/static/legacy/js/ | grep -v utils.js`. Expected output: empty. Separately, exercise search pagination in the legacy UI against a fresh container and confirm the Load-More behavior still works.

**Acceptance Scenarios**:

1. **Given** the legacy JS tree, **When** a reviewer greps for `.innerHTML =` or `.innerHTML +=` outside `utils.js`, **Then** no matches are found.
2. **Given** the legacy search page with more than one page of results, **When** the user triggers pagination, **Then** additional results are appended and remain interactive (clickable, correctly styled).
3. **Given** CI, **When** it runs on a PR that reintroduces `.innerHTML = ` outside `utils.js`, **Then** CI fails with a clear error citing the offending file:line.

---

### User Story 6 — Non-interactive `create-session` requires explicit confirmation (Priority: P3)

An operator running `cookie_admin create-session` non-interactively (e.g., from a shell script) must pass `--confirm` for the command to proceed. Interactive use continues to prompt.

**Why this priority**: This is parity with `cookie_admin reset`, which already requires `--confirm` for `--json` mode. `create-session` is comparably sensitive (it manufactures a session cookie for an arbitrary user) but today proceeds silently in non-interactive mode. Aligning the CLI's safety posture is straightforward and prevents accidental use in automation.

**Independent Test**: Run `cookie_admin create-session alice --json` without `--confirm` — expect exit non-zero with a clear error. Run the same with `--confirm` — expect a session to be issued. Run `cookie_admin create-session alice` (no `--json`) — expect an interactive confirmation prompt.

**Acceptance Scenarios**:

1. **Given** a passkey-mode deployment with user `alice`, **When** the operator runs `cookie_admin create-session alice --json` without `--confirm`, **Then** the command exits non-zero with an error message instructing the operator to pass `--confirm`.
2. **Given** the same deployment, **When** the operator runs `cookie_admin create-session alice --json --confirm`, **Then** the command succeeds and a session is issued.
3. **Given** the same deployment, **When** the operator runs `cookie_admin create-session alice` interactively (no `--json`), **Then** the existing interactive confirmation prompt is shown and the command respects the operator's response.

---

### User Story 7 — In passkey mode, a user can read their account identifier from Settings so an admin can grant them unlimited AI via CLI (Priority: P3)

A passkey-mode deployment with multiple users (household, family, small group) needs a way for any user to identify themselves to the admin without ambiguity. The admin uses `cookie_admin set-unlimited` / `remove-unlimited` from the host shell; today those take a `pk_<uuid8>` username that the user never sees. Profile names are not unique ("Mum", "Dad") so the admin can't reliably match.

**Why this priority**: Cookie's design intent is "passkey users are peers; CLI is the admin surface" (Principle III + spec 014-remove-is-staff). That design breaks down in practice if no user can tell the admin who they are. P3 because it's operational UX, not a security fix — but it's what makes the spec-014 CLI-only admin model usable beyond a single-user install.

**Independent Test**: Register two passkey users. Each opens Settings in their respective frontend. Both see a read-only caption "Account ID: N" on their Settings page with distinct integers. One of them reads the integer to the admin; admin runs `cookie_admin set-unlimited --profile-id N` and `cookie_admin list-users --json` now shows that user's `unlimited_ai: true`. The other user's status is unchanged.

**Acceptance Scenarios**:

1. **Given** a passkey-mode deployment with a signed-in user, **When** the user opens Settings (either frontend), **Then** they see a small read-only caption displaying their profile ID (e.g., "Account ID: 17").
2. **Given** a home-mode deployment, **When** any user opens Settings, **Then** no account ID caption is shown (home mode has no admin concept; the integer would be meaningless).
3. **Given** the CLI `cookie_admin set-unlimited --profile-id 17`, **When** an operator runs it, **Then** profile id 17 has `unlimited_ai = True` and `cookie_admin list-users --json` reflects the change.
4. **Given** the existing `cookie_admin set-unlimited <username>` positional form, **When** invoked, **Then** it continues to work unchanged (parity — the new `--profile-id` is an alternative lookup, not a replacement).
5. **Given** an invalid `--profile-id 99999`, **When** run, **Then** the CLI exits non-zero with a clear error ("Profile with id 99999 not found").
6. **Given** `--profile-id` and the positional username both supplied, **When** run, **Then** the CLI exits non-zero with an error ("pass either --profile-id or username, not both").

---

### User Story 9 — The repo receives automated dependency-update PRs (Priority: P3)

A maintainer of Cookie receives weekly automated PRs that bump Python, npm, Docker, and GitHub Actions dependencies. Security-advisory updates arrive as separate PRs. Routine updates are grouped by ecosystem to keep PR noise manageable.

**Why this priority**: Today the project has strong passive scanning (pip-audit, Dependency Review action, Trivy, Gitleaks) but no proactive upgrade path. Maintainers only learn about upgrades from CVE pings or breakage. Dependabot closes that loop with low operational cost.

**Independent Test**: Confirm `.github/dependabot.yml` exists, lints via GitHub's dependabot config validator, and — after merge — triggers at least one PR within a week (or on manual trigger via the GitHub UI).

**Acceptance Scenarios**:

1. **Given** the repo, **When** GitHub's dependabot config validator runs on `.github/dependabot.yml`, **Then** validation passes.
2. **Given** the merged config, **When** the first weekly run fires, **Then** at least one ecosystem (pip, npm, docker, docker-compose, or actions) produces at least one PR if any update is available.
3. **Given** a known security advisory affects a direct dependency, **When** Dependabot runs, **Then** the advisory is surfaced as a security-labeled PR separately from routine updates.

---

### User Story 10 — CI rejects code that exceeds the constitution's complexity and file-size limits (Priority: P3)

A developer who introduces a function with cyclomatic complexity greater than 15, or a new `*.py` file longer than 500 lines anywhere under `apps/` or `tests/`, is blocked at CI rather than merged-then-reviewed. Pre-existing violations are carried in an explicit allowlist that can only shrink.

**Why this priority**: The project constitution sets these as immutable limits, and `CLAUDE.md`'s code-quality rule says they're enforced. Today radon prints them as reports but doesn't fail the build. Moving the gate to enforce mode closes the gap between stated and actual policy. This spec ships the gate infrastructure; the refactors themselves live in follow-up spec `016-code-quality-refactor`.

**Independent Test**: Current master passes both gates (because the allowlist grandfathers every current violation). A smoke-test PR adding a CC=16 function or a new 501-line file outside the allowlist fails CI at the appropriate step.

**Acceptance Scenarios**:

1. **Given** current master + the new gates + the EXEMPT_FILES allowlist covering all 13 current violators (3 `apps/` production files + 2 `apps/**/tests.py` + 8 `tests/` top-level files), **When** CI runs, **Then** both gates pass.
2. **Given** a PR that introduces a CC > 15 function anywhere in `apps/` or `tests/`, **When** CI runs, **Then** the ruff C901 check fails and names the offending function.
3. **Given** a PR that adds a new 501-line file under `apps/` or `tests/` (a file not in the EXEMPT_FILES allowlist), **When** CI runs, **Then** `tests/test_code_quality.py` fails and names the offending file.
4. **Given** a PR that both adds a new file-size violation AND extends the EXEMPT_FILES allowlist to hide it, **When** CI runs, **Then** `tests/test_code_quality.py` fails with a "no gaming the ratchet" message.

---

### Edge Cases

- **Scheduler env inheritance**: Supercronic inherits env directly from the entrypoint process. If the cleanup commands run without required variables (`DJANGO_SETTINGS_MODULE`, `SECRET_KEY`, `DATABASE_URL`), the failure MUST be surfaced in container logs loudly — not silently swallowed.
- **Supercronic binary integrity**: The binary is downloaded and verified against a pinned SHA256 at image-build time. Build fails if the checksum does not match, so a supply-chain swap cannot ship undetected.
- **Logout flush with no active session**: Calling `logout` + `flush` on a request that has no session yet must not 500.
- **CSRF + cookie-less first request**: Home-mode profile selection on a brand-new browser has no CSRF cookie yet. The fix must not create a chicken-and-egg where the user cannot bootstrap a session.
- **Legacy search with zero results**: The refactored pagination path must not throw when appending to an empty results grid.
- **`create-session --confirm` under programmatic callers**: Existing scripts (if any) that call `create-session --json` non-interactively will break. Mitigate by documenting the change in release notes; accept the break as intentional safety tightening.
- **Complexity gate on refactored files**: After follow-up spec `016-code-quality-refactor` refactors a file under 500 lines, its entry in `EXEMPT_FILES` must be removed in the same PR. Leaving a stale allowlist entry is inert but lies about the current state.

## Requirements *(mandatory)*

### Functional Requirements

**Secrets & cron (Finding 1 / User Story 1)**

- **FR-001**: The production container MUST NOT persist `SECRET_KEY`, `DATABASE_URL`, or any other sensitive environment value into any file on the container filesystem. Sensitive values are present only in the process environment of the entrypoint and its children.
- **FR-002**: The three existing scheduled cleanup jobs (device codes hourly, sessions daily 03:15, search images daily 03:30) MUST continue to run on their existing schedules with no change to their output or side effects.
- **FR-002a**: Scheduling MUST be performed by **supercronic v0.2.44** (a specific pinned version) rather than Debian `cron`. Supercronic is installed as a **SHA256-pinned** static binary in the production image; `Dockerfile.prod` MUST run `sha256sum -c` (or equivalent) against the downloaded binary and fail the build on mismatch. The SHA256 is computed locally during implementation and cross-verified at least once against the upstream-published SHA1 so the pin represents a known-good artifact. Supercronic reads a static crontab file (schedule + command only — no environment values) and inherits its environment directly from the entrypoint process.
- **FR-002b**: The Debian `cron` package and `/etc/cron.d/*` invocation path MUST be removed from the production image. `cron` MUST NOT be installed or started.
- **FR-003**: The scheduled jobs (the supercronic daemon and the Django management commands it invokes) MUST run as the `app` user (not root), consistent with the rest of the production process model.
- **FR-004**: If a scheduled job fails because it cannot find required environment variables, the failure MUST be surfaced in container logs with enough detail for an operator to diagnose (job name + missing variable name). Supercronic's default behavior (logging each job's stdout/stderr to its own stdout) satisfies this when combined with Django's existing error output.

**Session hygiene (Finding 2 / User Story 2)**

- **FR-005**: The `/api/auth/logout/` endpoint MUST flush every key from the session (not just the Django auth keys). After a successful logout, no authenticated endpoint accessible through the replayed session cookie may return a success status.
- **FR-006**: The passkey authentication path that re-authenticates from `session["profile_id"]` alone (i.e., without a Django auth token) MUST NOT permit a session cookie that has been explicitly logged out to re-authenticate. This is a consequence of FR-005 and MUST be covered by an integration test.
- **FR-007**: Existing logout tests MUST continue to pass without modification.

**Image pinning (Finding 3 / User Story 3)**

- **FR-008**: `docker-compose.prod.yml` MUST reference the web service image by a concrete version tag matching a published release (e.g., `ghcr.io/matthewdeaves/cookie:v1.44.0`). The `:latest` tag MUST NOT appear in any compose file committed to the repo.
- **FR-009**: `CLAUDE.md` (or the authoritative release documentation) MUST include an explicit step in the release playbook for bumping the compose image pin when a new version is tagged.

**CSRF coverage (Finding 4 / User Story 4)**

- **FR-010**: `tests/test_csrf.py` (or an equivalent integration test module) MUST include an integration test covering `select_profile` (POST `/api/profiles/{id}/select/`) in home mode: a POST without a valid CSRF token returns 403; the same POST with a valid token returns 200.
- **FR-011**: If the endpoint unexpectedly accepts a forged cross-origin mutation, it MUST be changed to enforce CSRF explicitly. The test MUST be written first; the fix only if the test shows the gap.

**Legacy innerHTML chokepoint (Finding 5 / User Story 5)**

- **FR-012**: `apps/legacy/static/legacy/js/pages/search.js` MUST be updated so that the pagination appender does not use `.innerHTML =` or `.innerHTML +=`. It MUST route through `Cookie.utils.setHtml` or build a DOM fragment and use `appendChild`.
- **FR-013**: A repo-wide regression guard (pytest-driven static test) MUST fail if `.innerHTML\s*(=|\+=)` appears in `apps/legacy/static/legacy/js/` outside `utils.js`. The guard's failure message MUST cite the offending file:line.
- **FR-014**: Legacy search pagination MUST remain functionally unchanged from the user's perspective — clicking Load More still appends additional result cards that remain clickable and correctly styled.

**CLI parity (Finding 6 / User Story 6)**

- **FR-015**: `cookie_admin create-session` invoked with `--json` and without `--confirm` MUST error with a non-zero exit status and a message directing the operator to pass `--confirm`. The error message MUST mention both `--confirm` and the target username for clarity.
- **FR-016**: `cookie_admin create-session` invoked interactively (no `--json`) MUST continue to prompt for confirmation and respect the operator's response. The existing prompt text does not need to change.
- **FR-017**: `cookie_admin create-session` invoked with `--json --confirm` MUST succeed and produce the same session-creation JSON output as today.

**Passkey user identifier in Settings (User Story 7)**

- **FR-018**: In passkey mode, the modern SPA Settings page MUST display the signed-in user's profile ID as a small read-only caption (e.g., "Account ID: 17" or "Your account: #17"). Placement should be in the Preferences / About area — visible without scrolling, not a call-to-action.
- **FR-019**: In passkey mode, the legacy Settings page MUST display the same profile ID via template rendering (the data is already available server-side as `current_profile_id`).
- **FR-020**: In home mode, NO account-ID caption is rendered in either frontend (home mode has no admin concept — the integer would be misleading).
- **FR-021**: `cookie_admin set-unlimited` MUST accept `--profile-id N` as an alternative to the positional username argument. `cookie_admin remove-unlimited` MUST do the same. When both are supplied, the CLI exits non-zero with "pass either --profile-id or username, not both". When neither is supplied, the CLI's existing behavior (error requesting a username) is unchanged.
- **FR-022**: `--profile-id N` MUST look up the profile by primary key in the `profiles_profile` table, find its associated user, and toggle `profile.unlimited_ai` exactly as the existing username path does. JSON output shape is unchanged. If the profile is not found, exit non-zero with "Profile with id N not found".
- **FR-023**: Existing `cookie_admin set-unlimited <username>` and `cookie_admin remove-unlimited <username>` positional-form invocations MUST continue to work unchanged (backwards-compatibility for any existing scripts).

**Dependabot (Finding 7 / User Story 9)**

- **FR-024**: `.github/dependabot.yml` MUST be present and valid per GitHub's dependabot schema.
- **FR-025**: The config MUST cover all five active dependency ecosystems in the repo: `pip` (root `requirements.txt` / `requirements.lock`), `npm` (`frontend/package.json`), `docker` (both Dockerfiles), `docker-compose` (`docker-compose.yml` and `docker-compose.prod.yml`), and `github-actions` (`.github/workflows/`). (Note: `docker` and `docker-compose` are separate Dependabot ecosystems as of GA Feb 2025.)
- **FR-026**: Routine updates MUST be grouped per ecosystem to minimize PR noise. Security-advisory updates MUST be surfaced as separate PRs (dependabot's default split-out of `security` updates suffices).
- **FR-027**: PRs MUST auto-assign to the repo owner (`matthewdeaves`) and carry a consistent label (e.g., `dependencies`).

**Complexity & file-size gate (Finding 8 / User Story 10)**

- **FR-028**: CI MUST fail a PR if any function in `apps/` or `tests/` has cyclomatic complexity greater than 15. The failure message MUST name the offending function and its file. Enforcement rides on ruff's `C901` (mccabe) rule configured at `max-complexity = 15`, so it runs inside the already-required `backend-lint` CI job.
- **FR-029**: CI MUST fail a PR if any `*.py` file in `apps/` or `tests/` has more than 500 lines, excluding `*/migrations/*.py` (auto-generated). The failure message MUST name the offending file and its line count. Enforcement is a pytest static test under `tests/test_code_quality.py` that runs inside the already-required `backend-test` CI job.
- **FR-030**: Pre-existing file-size violations are grandfathered via an explicit allowlist `tests/test_code_quality.py::EXEMPT_FILES` — a concrete enumeration of every currently-violating file with its current line count. The allowlist includes all 13 current violators (3 production, 2 apps/-side test files, 8 top-level tests/ files). Adding a file to the allowlist requires a commit message referencing a follow-up spec id. Once a file is refactored under 500 lines, it MUST be removed from the allowlist. The allowlist's total size MUST monotonically decrease; `tests/test_code_quality.py` MUST fail if a PR both adds a new file-size violation AND adds a new allowlist entry (no gaming the ratchet).
- **FR-031**: Follow-up spec `016-code-quality-refactor` MUST be opened at merge time of this spec, scheduling the cleanup of every file in the allowlist. This spec does NOT refactor any file — it ships only the gates and the grandfather list so production-code refactoring risk is isolated from this security PR.
- **FR-032**: Silent raising of thresholds, `# noqa` suppression, or `# ruff: noqa: C901` file-level disables are not permitted per Constitution Principle V. The allowlist mechanism is the only sanctioned way to carry current violations forward.

**Cross-cutting**

- **FR-033**: Both frontends MUST remain fully functional in both auth modes (home, passkey) after all changes. The existing frontend and backend test suites MUST pass unchanged (except where tests have been added or updated explicitly to cover the new requirements).
- **FR-034**: No new runtime dependency MUST be introduced in the backend to satisfy any of these fixes. (CI config files and crontab file do not count.)
- **FR-035**: The project version MUST be bumped to the next semver minor (v1.43.0 → v1.44.0) as part of shipping this work, consistent with the release-versioning rules in `CLAUDE.md`.

### Key Entities

- **Cron job definitions**: The three scheduled Django management commands — `cleanup_device_codes`, `cleanup_sessions`, `cleanup_search_images` — with their schedules, invoked via supercronic which inherits env from the entrypoint instead of persisting it to a config file.
- **Logout session state**: The mapping between a session cookie and the set of keys it holds on the server side. After logout, the server-side record MUST be empty (flushed), not just have its auth-specific keys cleared.
- **Production image pin**: A concrete published tag (`ghcr.io/matthewdeaves/cookie:vX.Y.Z`) referenced by `docker-compose.prod.yml`. Updated in lockstep with releases.
- **`EXEMPT_FILES` allowlist**: A `frozenset[str]` constant in `tests/test_code_quality.py` enumerating every file currently above the 500-line limit, with a comment pointing at `016-code-quality-refactor`. Entries are removed as files are refactored; new entries require a spec reference.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero instances of `SECRET_KEY` or `DATABASE_URL` appear as literal values in `/etc/`, `/var/`, `/tmp/`, or `/app/` on the production container after 24 hours of runtime, verified by a recursive `grep -rE "SECRET_KEY|DATABASE_URL" /etc/ /var/ /tmp/ /app/` scan returning zero matches.
- **SC-002**: 100% of the three scheduled cleanup jobs (device codes, sessions, search images) run successfully on their first scheduled fire after the fix ships, with their output visible in container logs.
- **SC-003**: After `POST /api/auth/logout/`, 100% of subsequent requests replaying the same session cookie to any authenticated endpoint return 401 (or 404 for routes guarded by mode-dependent auth). No endpoint returns 200.
- **SC-004**: `grep :latest docker-compose.prod.yml` produces zero output lines referencing the Cookie web image.
- **SC-005**: The CSRF integration test for `select_profile` passes: POST without CSRF token → 403, POST with CSRF token → 200.
- **SC-006**: `grep -rnE "\.innerHTML\s*(=|\+=)" apps/legacy/static/legacy/js/` returns only lines inside `utils.js`. A planted violation in a test PR causes CI to fail.
- **SC-007**: `cookie_admin create-session alice --json` without `--confirm` exits with a non-zero status and a clear error message. `cookie_admin create-session alice --json --confirm` succeeds.
- **SC-008**: In passkey mode, a signed-in user opening Settings in either frontend sees a read-only caption displaying their profile ID (e.g., "Account ID: 17"). In home mode, no such caption appears. The admin runs `cookie_admin set-unlimited --profile-id 17` and `cookie_admin list-users --json` reflects `unlimited_ai: true` for that profile only. The existing positional-username form of the command continues to work.
- **SC-009**: `.github/dependabot.yml` is present, passes GitHub's config validator, and produces at least one automated PR within 8 days of merging (or on manual trigger via the GitHub UI).
- **SC-010**: CI's CC gate (ruff C901 at `max-complexity = 15`) fails a smoke-test PR that introduces a function with CC ≥ 16 anywhere in `apps/` or `tests/`. CI's file-size gate (`tests/test_code_quality.py`) fails a smoke-test PR that adds a 501-line file outside the `EXEMPT_FILES` allowlist. On current master with the allowlist populated, both gates pass.
- **SC-011**: Both frontends pass their existing test suites (516 frontend tests, 1300+ backend tests) and render the primary flows in both auth modes after the changes ship.
- **SC-012**: Release `v1.44.0` is tagged with all of the above changes merged, and `docker-compose.prod.yml` pins to `ghcr.io/matthewdeaves/cookie:v1.44.0`.

## Assumptions

- The production container replaces Debian `cron` with **supercronic** (chosen in Clarifications). Supercronic's upstream release channel (`github.com/aptible/supercronic`) is used; the binary is pinned by SHA256 in the Dockerfile. This gives the scheduler non-root, static-env-inheriting behavior without any secrets-on-disk.
- The project's Recipe model is a shared-between-profiles entity by design (confirmed). No IDOR findings related to per-user recipe ownership are in scope for this spec.
- The file-size and CC gates ship with a full grandfather allowlist; zero refactors are performed in this spec. Refactors are tracked in follow-up spec `016-code-quality-refactor`, opened at merge time.
- Dependabot's default grouping behavior (one ecosystem = one weekly grouped PR, with security updates split out) is acceptable. No custom grouping strategies beyond the defaults are required.
- The next release version is `v1.44.0`. No higher version has been cut since `v1.43.0`; this is the next available minor.
- Passkey display-name UX (original review finding M4) is deferred as low-impact for Cookie's deployment model. `WebAuthnCredential` does not store a display name; credential-picker UX is a nice-to-have that doesn't justify the implementation cost right now. Revisit if/when a multi-user deployment pattern emerges.

## Dependencies

- Completion of 014-remove-is-staff (shipped as `v1.43.0`): session-auth classes, `HomeOnlyAuth` naming, and the CLI-only admin surface are prerequisites for the logout/session-flush fix and for the `create-session --confirm` change.
- Existing CSRF middleware configuration in `cookie/settings.py`: the CSRF test relies on `CsrfViewMiddleware` already running on all requests (which it does). No middleware reordering is required.
- Existing GitHub Actions CI configuration (`.github/workflows/ci.yml`): the new gates ride on the already-required `backend-lint` (ruff) and `backend-test` (pytest) jobs — no new workflow is required.
- Existing `cookie_admin` CLI framework: the `--confirm` flag parity change follows the exact same pattern already used by `cookie_admin reset`.
- Follow-up spec `016-code-quality-refactor`: must be filed as a stub (even if just a title + brief description) before this spec merges, so the EXEMPT_FILES allowlist's "referenced spec id" promise is real.

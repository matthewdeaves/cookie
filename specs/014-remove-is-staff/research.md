# Phase 0 Research: Remove is_staff

All four clarifications from `/speckit.clarify` are resolved in the spec. Phase 0 crystallizes them into implementation-level decisions and documents the supporting audit evidence.

## R1 — Auth class design

**Decision**: Rename `HomeOnlyAdminAuth` → `HomeOnlyAuth`. Change its parent from `AdminAuth` to `SessionAuth` (drop the admin check). Its `__call__` keeps the `if settings.AUTH_MODE != "home": raise HttpError(404, "Not found")` gate. Delete `AdminAuth` entirely.

**Rationale**:
- Audit confirmed `AdminAuth` has **0 direct call sites** in `apps/`; only `HomeOnlyAdminAuth` (its subclass) is used (18 endpoints). Deleting `AdminAuth` is purely mechanical once the subclass stops inheriting from it.
- Post-refactor, the "admin" concept does not exist in the auth layer. Every auth-gated endpoint is either (a) home-mode + profile-session (the 25 home-only endpoints), (b) any-mode + profile-session (ordinary endpoints via `SessionAuth`), or (c) public. Collapsing into two classes (`SessionAuth`, `HomeOnlyAuth`) matches this conceptual reality.
- Keeps the v1.42.0 security property: the mode check runs BEFORE any auth / cookie logic, so passkey-mode probes on home-only endpoints are indistinguishable from 404s on never-existed routes (no auth-failure log line is emitted).

**Alternatives considered**:
- *Keep `HomeOnlyAdminAuth` name*: bad — name lies about what it does post-refactor.
- *Two classes (`HomeOnly` for public endpoints + `HomeOnlyAuth` for authenticated)*: unnecessary; only 2 unauthenticated endpoints need gating (see R2).
- *Django middleware*: broader blast radius; harder to unit-test; couples URL patterns to security.

## R2 — Unauthenticated profile endpoint gating

**Decision**: For the **3** profile endpoints that are (or must remain) unauthenticated — `list_profiles`, `create_profile`, `select_profile` — add an inline mode check as the first statement of each handler:

```python
if settings.AUTH_MODE != "home":
    raise HttpError(404, "Not found")
```

**Why 3, not 2**: initial analysis assumed only `create_profile` and `select_profile` were unauthenticated. On reading `apps/profiles/api.py:128` directly, `list_profiles` has conditional auth: `auth=[SessionAuth()] if settings.AUTH_MODE == "passkey" else None`. That means it's publicly accessible in home mode (the profile-selection screen runs before any session exists). Applying `HomeOnlyAuth()` to `list_profiles` would require a session in home mode and BREAK the profile-selection flow. So `list_profiles` joins `create_profile` and `select_profile` in the "inline check" bucket.

Current state of each handler (before refactor):

- `list_profiles` (line 130): `auth=[SessionAuth()] if AUTH_MODE == "passkey" else None`; passkey branch at lines 147–152 filters by `is_staff`. After: `auth=None`, inline `raise HttpError(404)` in non-home, the entire passkey branch deleted.
- `create_profile` (line 181): `auth=None`; existing inline check returns `Status(404, {"error":"not_found","message":"Not found"})`. After: `auth=None`, convert existing return to `raise HttpError(404, "Not found")` for body uniformity.
- `select_profile` (line 327): `auth=None`; existing inline check returns `Status(404, {"detail":"Not found"})`. After: `auth=None`, convert to `raise HttpError(404, "Not found")`.

**Body uniformity**: all 27 gated endpoints produce exactly `{"detail": "Not found"}` on 404, indistinguishable from a nonexistent route. This is the security property v1.42.0 established for the admin endpoints and is now extended to the profile namespace.

**Rationale**:
- Creating an auth class that does "mode check only, no session" just for 3 endpoints is overengineering.
- For `auth=None` endpoints, Ninja does not resolve any auth object, so inline `raise HttpError` fires as the first line of logic — no log-line differential versus an auth-class-based gate.
- Keeps handler bodies self-contained and readable.

**Alternatives considered**:
- *Single `HomeOnly` class with no session requirement*: works; adds a class for 3 consumers; inline check is tighter.
- *Apply `HomeOnlyAuth` to list_profiles*: BREAKS home-mode profile-selection (chicken-and-egg). Rejected.
- *Leave endpoints accessible in passkey mode*: breaks FR-009. Non-starter.

## R3 — Pytest static test (regression guard)

**Decision**: Add `tests/test_no_is_staff_reads.py`. It walks `apps/`, reads each `.py` file, and asserts the string `is_staff` appears only in allowlisted locations.

**Allowlist** (tuples of file-substring + line-pattern):
1. `apps/core/management/commands/cookie_admin.py` — line matching `is_staff=False` on user creation (one occurrence expected post-refactor).
2. `apps/core/passkey_api.py` — line matching `is_staff=False` on passkey user creation (one occurrence expected).
3. `apps/core/migrations/*` — any Django migration files (none expected to reference is_staff, but prefix-allow just in case).

**Failure message shape**:
```
is_staff read found in apps/foo/bar.py:42
  line: `if user.is_staff: ...`
  remediation: `is_staff` is no longer a privilege signal. Use `Profile.unlimited_ai`
  for quota bypass, or delete this check. See specs/014-remove-is-staff/spec.md.
```

**Rationale**:
- Chosen via spec clarification Q2.
- Runs in every CI test run; no startup overhead; no new infra.
- Allowlist is explicit and auditable — adding a new allowed location requires a test edit, which is visible in code review.

**Alternatives considered**:
- *Django system check*: designed for config validation, awkward for "grep the source tree" semantics.
- *Ruff custom rule*: requires plugin infrastructure; overkill for a single-token deny-list.
- *Pre-commit hook*: opt-in; doesn't run in CI unless explicitly invoked.

## R4 — CLI informational output shapes

**Decision**: strip every admin/is_staff field from `status`, `audit`, and `list-users` output.

**Concrete diffs** (captured in `contracts/cli-output-shapes.md`):

- `status --json`: drop top-level keys `admins`, `active_admins`. Retain all other keys (users total, active, api_key_configured, cache block, etc.).
- `audit --json`: in each per-user event dict, drop `is_admin` key. No other audit-event fields change.
- `list-users --json`: in each user object, drop `is_admin` key; also drop the summary footer `admins: N`.
- `list-users` (text): drop the `ADMIN` column from the header and each row; drop the `Admins: N` summary line at bottom.
- `list-users --admins-only`: flag is DELETED (the concept no longer exists).

**Rationale**:
- Chosen via spec clarification Q4.
- Leaving degraded fields (e.g. "admins: 0") would lie about the model. Post-refactor there is no admin concept; the output must reflect that.

## R5 — TypeScript type update for /auth/me

**Decision**: Grep `frontend/src/` for `is_admin`. If a type alias or interface contains `is_admin: boolean` on the `/auth/me` response, delete the field. If no consumer references the field, deletion is safe (backward compat is a non-goal in dev mode).

**Audit result** (from earlier exploration): frontend has zero `is_staff` / `is_admin` consumer references. The `/auth/me` TypeScript type may or may not include the field; verify during implementation and delete if present.

**Rationale**: prevents future devs from relying on a field that doesn't exist in the response. Forces TS compile errors if someone reintroduces a read.

## R6 — Test rewrite strategy

**Decision**: triage the 45 `is_staff` test matches into three buckets.

**Bucket A — DELETE** (the test's entire purpose is is_staff-driven privilege):
- `test_cookie_admin.py`: `test_promote_*`, `test_demote_*`, `test_demote_last_admin_refused`, `test_list_users_admins_only`, `test_create_user_admin_flag`.
- `test_auth_api.py`: any assertion on `response["user"]["is_admin"]`.
- `test_permissions.py`: test cases that assert `is_staff=True` grants admin access to endpoints (those endpoints are now home-only; admin concept is gone).

**Bucket B — REWRITE** (test asserts quota-bypass behavior via `is_staff=True`):
- `test_ai_quota.py`: the ~7 matches that set up `is_staff=True` to verify unlimited AI — rewrite to set `profile.unlimited_ai = True` and assert same outcome. Add NEW case asserting that `is_staff=True` with `unlimited_ai=False` hits quota (FR-001 coverage).

**Bucket C — FIXTURE UPDATE** (test creates an admin user as scaffolding but doesn't assert on the flag):
- `test_system_api.py`, `test_ai_api.py`, `test_profiles_api.py`, `test_legacy_auth.py`, `test_gated_endpoints_passkey.py`, `test_passkey_api.py`: strip `is_staff=True` from `create_user()` calls. The tests exercise endpoints now gated by mode (not privilege), so the fixture no longer needs the flag.

**Rationale**: preserves test coverage where semantically relevant; eliminates no-longer-applicable tests; adds explicit coverage of the new "is_staff doesn't bypass quota" invariant.

**Alternatives considered**:
- *Mass delete all is_staff-touching tests*: loses coverage of quota-bypass semantics (still needed, just via a different flag).
- *Keep tests; flip assertions*: perpetuates the is_staff concept in test code even though it's been removed from prod code.

## R7 — Constitution amendment wording

**Decision**: rewrite Principle III's passkey-mode paragraph. Specifically the line currently reading:

> Site-wide settings (API keys, AI prompts, search sources, database reset) are restricted to administrators. Admin promotion is done exclusively via CLI.

replace with:

> All passkey users are peers — there is no in-app admin privilege. Site-wide settings (API keys, AI prompts, search sources, database reset, profile management) are reached exclusively via the `cookie_admin` CLI and are unreachable from the web UI. There is no `promote`/`demote` operation; `is_staff` on the User model is inert and always `False` for application-created users.

**Version bump**: constitution 1.3.0 → 1.4.0 (MINOR — principle materially expanded/redefined per existing governance rules). Add amendment-history row dated 2026-04-18.

**Sync impact report** (to insert at top of constitution.md):

```
Version: 1.3.0 → 1.4.0
Changed principles: III — passkey-mode admin concept retired; all users peers; CLI is the admin surface
Follow-up TODOs: none
```

## R8 — Release version

**Decision**: v1.43.0.

**Rationale**:
- v1.42.0 shipped admin-lockdown (013-admin-home-only).
- This feature is MINOR per the project's semver rules: security hardening + breaking CLI surface change (promote/demote removed). No API data model changes, no auth flow changes for end users.
- Not PATCH because it breaks the CLI contract.
- Not MAJOR because the web API surface and user-facing behavior are preserved for home mode, and passkey-mode users retain their login capability and profiles.

**Release notes headline**: "Remove is_staff privilege signal; consolidate quota bypass on Profile.unlimited_ai. Lock /api/profiles/* to home mode only. Remove promote/demote from cookie_admin CLI."

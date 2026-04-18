# Phase 0 Research — 013-admin-home-only

## R1 — Where does the mode check run, relative to `AdminAuth`?

**Question**: If I stack `@home_mode_only` above `@router.post("/path", auth=AdminAuth())`, does `home_mode_only` run *before* Ninja attempts authentication?

**Arc**:
- A `@wraps` decorator attached to a Ninja view runs *inside* Ninja's view wrapper: at request time the sequence is `route match → Ninja view wrapper → auth=AdminAuth() resolution → inner decorator (home_mode_only) → original function`. So the decorator runs AFTER `AdminAuth.authenticate`, which in passkey mode emits a `security_logger.warning` auth-failure line before our 404 can fire.
- That violates FR-002 and FR-035.

**Alternatives considered**:
- **Django middleware keyed on URL patterns**: moves the decision away from the code site; URL-pattern drift risk; rejected.
- **Conditional route registration** — wrap each `@router.*` in `if settings.AUTH_MODE == "home": @router.post(...)`. Clean, but breaks the test story: Django tests use `@override_settings(AUTH_MODE="passkey")` after module load, so route registration at import time can't respond. Rejected.
- **`HomeOnlyAdminAuth(AdminAuth)` subclass** that overrides `__call__` to raise `HttpError(404)` before `super().__call__(request)`. The mode check executes inside the auth phase, before the cookie is read and before the base-class `authenticate()` is reached. No auth-failure log line. Passes FR-002 and FR-035. Single-site swap per endpoint (`auth=AdminAuth()` → `auth=HomeOnlyAdminAuth()`). **Selected**.

**Decision (final)**:

```python
# apps/core/auth.py
from django.conf import settings
from ninja.errors import HttpError

class HomeOnlyAdminAuth(AdminAuth):
    """AdminAuth that first checks AUTH_MODE == 'home'; raises 404 otherwise.

    Runs the mode check before any cookie extraction or authenticate() call so
    passkey-mode probes produce no auth-failure log line.
    """
    def __call__(self, request):
        if settings.AUTH_MODE != "home":
            raise HttpError(404, "Not found")
        return super().__call__(request)
```

Usage on each gated endpoint: change `auth=AdminAuth()` to `auth=HomeOnlyAdminAuth()`.

The spec-level name `home_mode_only` is kept in the Clarifications section as shorthand for "the mode gate"; the runtime realisation is the subclass above. `AdminAuth` itself is not modified (FR-006 honored).

**Test gate for the "no auth-failure log line" property (FR-002/FR-035)**: integration test captures `security_logger` output while probing each endpoint in passkey mode; asserts the captured stream gains 0 new lines from the gated endpoints. If that test ever fails (e.g. base-class change moves log lines into `__call__`), the fix is localised to `HomeOnlyAdminAuth.__call__`.

## R2 — 404 body shape in Ninja

**Decision**: `raise HttpError(404, "Not found")` produces `{"detail":"Not found"}` with HTTP 404, identical to Ninja's response for an unknown API path.

**Verification source**: `django-ninja` source, `ninja/errors.py` — `HttpError` is caught by Ninja's global exception handler which JSON-encodes `{"detail": message}` with the provided status.

## R3 — SPA mode context

**Decision**: Reuse `useMode()` exported from `frontend/src/router.tsx`. Do NOT add `mode` to `AuthContext`. Admin components import `useMode` alongside `useAuth`.

**Rationale**: The mode provider already exists in `router.tsx`. Adding it to `AuthContext` would either duplicate the fetch or create a circular dependency. The import cost is one extra line per component.

## R4 — Writing `AppSettings.openrouter_api_key` from CLI

**Decision**: `obj = AppSettings.get(); obj.openrouter_api_key = new_value; obj.save()`.

**Rationale**: The model has a `@property` with a setter that encrypts `value` if not already encrypted. The `save()` override enforces `pk=1` (singleton). The CLI path must never touch the private `_openrouter_api_key` field directly.

## R5 — CLI passkey-mode guard refactor

**Decision**: Add a class-level attribute `PASSKEY_ONLY_SUBCOMMANDS: set[str]` containing the existing user-lifecycle subcommands. Replace the top-level `if settings.AUTH_MODE != "passkey"` check in `handle()` with: "if `subcommand in PASSKEY_ONLY_SUBCOMMANDS` and `settings.AUTH_MODE != "passkey"`, error." Existing error text is preserved for the restricted subcommands.

**Rationale**: Minimizes blast radius. Existing passkey-only tests keep passing. New subcommands work in both modes without special casing.

## R6 — `--stdin` UX for secrets

**Decision**: `sys.stdin.read().strip()`. Reject empty string with clear error and non-zero exit. Do NOT echo the value. Do NOT log the value.

**Rationale**: `strip()` tolerates a trailing newline from `echo`/`cat`. Rejecting empty input prevents accidental key wipe.

## R7 — File-based prompt content input

**Decision**: Open each file with `encoding="utf-8"`, read the full contents as-is (no stripping — prompt formatting matters). Missing or unreadable files raise `CommandError` before any DB write. `--active` is parsed as `true`/`false` (case-insensitive).

**Rationale**: Avoids shell-escaping pain for multi-line prompts containing `{}` placeholders. Preserves exact whitespace, which matters for some prompts.

## R8 — Handling the `GET /api/recipes/cache/health/` response shape inside `status --json`

**Decision**: `status --json` adds a `"cache"` key whose value is the same dict the HTTP endpoint returns. Implementation factors out the cache-health query into a small helper (`get_cache_health() -> dict`) used by both the HTTP handler and the CLI — avoids code duplication.

**Rationale**: Don't call the HTTP handler from the CLI. Share the data source instead.

## R9 — Versioning

**Decision**: Bump `COOKIE_VERSION` default (in `cookie/settings.py`) from `"dev"` to `"1.42.0"`. The GitHub release workflow sets this environment variable at deploy time. Tag `v1.42.0`; publish a release with a "Security" section listing the three changes per FR-038.

**Rationale**: The previous release is `v1.41.0` (verified via `gh release list --limit 1`). This is a security-hardening MINOR per the repo's semver convention.

## R10 — SPA test strategy

**Decision**: Add one Vitest test file `Settings.passkey-hide.test.tsx`. Mount `Settings` with a wrapped provider that forces `useMode()` to return `'passkey'`. Use a stable `data-testid` attribute on each admin section's root element and assert `screen.queryByTestId(id)` is `null`. Add `data-testid` attributes where they don't already exist (they're test-only, don't change visual output).

**Rationale**: Component-level assertion is fast, hermetic, and directly enforces the requirement. No E2E framework needed.

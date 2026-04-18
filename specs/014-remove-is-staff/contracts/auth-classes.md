# Contract: Auth Classes (post-refactor)

## Classes in `apps/core/auth.py` after this refactor

```
__all__ = ["SessionAuth", "HomeOnlyAuth"]
```

Two classes. No `AdminAuth`. No `HomeOnlyAdminAuth`.

### `SessionAuth(APIKeyCookie)` — unchanged

Mode-aware profile-session authenticator. Behavior and implementation unchanged from pre-refactor:

- Home mode: reads `session["profile_id"]` → Profile.
- Passkey mode: reads authenticated `request.user.profile` (with session-fallback).

### `HomeOnlyAuth(SessionAuth)` — new (renamed + simplified)

Renamed from `HomeOnlyAdminAuth`. Parent changed from `AdminAuth` (deleted) to `SessionAuth` (retained). The admin check is gone; only the mode check remains.

**Contract**:

```python
class HomeOnlyAuth(SessionAuth):
    """SessionAuth gated by AUTH_MODE=home.

    Raises 404 before any cookie extraction or session lookup when
    AUTH_MODE != "home". Probes from passkey deployments are indistinguishable
    from hits on a never-existed path: same status, same body, no
    security-log auth-failure line.
    """

    def __call__(self, request: HttpRequest) -> Any:
        if settings.AUTH_MODE != "home":
            raise HttpError(404, "Not found")
        return super().__call__(request)
```

**Usage**:

```python
from apps.core.auth import HomeOnlyAuth

@router.post("/admin-endpoint/", auth=HomeOnlyAuth())
def admin_endpoint(request): ...
```

### Deleted: `AdminAuth`

Had 0 direct call sites. Was parent of `HomeOnlyAdminAuth`. Deletion is safe.

If any out-of-tree fork depends on it, migration path: if the site wants "admin only in passkey mode", that concept no longer exists — review whether the endpoint should be (a) home-only (use `HomeOnlyAuth`) or (b) accessible to any authenticated user (use `SessionAuth`). Do not reintroduce a privilege tier.

### Renamed: `HomeOnlyAdminAuth` → `HomeOnlyAuth`

All 18 existing call sites updated mechanically (import + constructor rename). Behavior is unchanged:

| Before | After |
|---|---|
| `auth=HomeOnlyAdminAuth()` | `auth=HomeOnlyAuth()` |
| `from apps.core.auth import HomeOnlyAdminAuth` | `from apps.core.auth import HomeOnlyAuth` |

## Endpoint inline mode check

For the three unauthenticated profile endpoints (`list_profiles`, `create_profile`, `select_profile`), the first statement of the handler becomes:

```python
if settings.AUTH_MODE != "home":
    raise HttpError(404, "Not found")
```

This is equivalent in security posture to using an auth class (no auth log line, 404 before any work). `HomeOnlyAuth` is NOT applied to these three because it inherits from `SessionAuth` and thus requires a profile-session cookie — home-mode profile selection must work without a session (chicken-and-egg). See `gated-endpoints.md` for the per-endpoint rationale.

## Test surface

- Unit tests for `HomeOnlyAuth` live in `apps/core/tests.py` (existing location for auth tests). Rename/update existing `HomeOnlyAdminAuth` tests to cover `HomeOnlyAuth`. Drop tests that asserted admin-specific behavior (those assertions no longer apply).
- Integration tests live in `tests/test_gated_endpoints_passkey.py`. Existing 18 endpoint cases are updated to use the renamed class. 9 new cases added for the profile endpoints.

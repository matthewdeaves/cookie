# Contract — Auth Logout

## Endpoint

`POST /api/auth/logout/` — passkey-mode only (404 in home mode).

Response shape is unchanged. The contract change is a **post-condition strengthening**: after a successful logout, the session is fully flushed, and no replay of the same cookie can authenticate against any endpoint.

## Request / Response

Unchanged. Authenticated POST (SessionAuth), no body, returns `200 {"message": "Logged out successfully"}`.

## Post-condition (new)

Before: `logout(request)` cleared Django auth keys (`_auth_user_id`, `_auth_user_backend`, `_auth_user_hash`). The session record remained on the server with any other keys (notably `profile_id`) intact.

**After**: `request.session.flush()` is called immediately after `logout(request)`. The server-side session record is deleted and a new (empty) session key is rotated in. The client's old cookie now resolves to a nonexistent session → every authenticated endpoint returns 401 (or 404 for mode-dependent routes).

## Threat model

- **Before fix**: stolen cookie + `session.get("profile_id")` fallback in `apps/core/auth.py` re-authenticates the attacker as the previous holder. Logout was a soft boundary.
- **After fix**: stolen cookie points at a deleted session; `profile_id` read returns `None`; fallback cannot re-authenticate. Logout is a hard boundary.

## Tests

- `tests/test_passkey_logout_replay.py::test_logged_out_cookie_cannot_hit_auth_me`
  - Log in (passkey flow), capture `sessionid` cookie, call `/api/auth/logout/`, replay cookie against `GET /api/auth/me/`, assert 401.
- `tests/test_passkey_logout_replay.py::test_logged_out_cookie_cannot_hit_recipes_favorites`
  - Same but replay against `GET /api/recipes/favorites/`, assert 401.
- Existing `tests/test_auth_api.py::test_logout_*` tests MUST continue to pass without modification.

## Notes on the fallback

`apps/core/auth.py:52-81`'s passkey-fallback code is left in place intentionally — it still serves its documented purpose of bridging the login/middleware handoff. This spec does not refactor the fallback because the session flush de-fangs the only attack path it enabled.

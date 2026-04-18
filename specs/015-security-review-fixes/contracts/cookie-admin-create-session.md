# Contract — `cookie_admin create-session` (CLI)

## Command

```
docker compose exec web python manage.py cookie_admin create-session <username-or-profile> [--json] [--confirm] [--ttl SECONDS]
```

Passkey-mode only (same as today).

## Flag behavior truth table

| `--json` | `--confirm` | Exit | Behavior |
|:--------:|:-----------:|:----:|----------|
| No | any | 0 (after prompt yes) / non-zero (after prompt no) | Interactive confirmation prompt; proceeds on "y" |
| Yes | No | **non-zero** (NEW) | Prints JSON error `{"error": "--confirm flag required for non-interactive create-session"}` to stderr; no session created |
| Yes | Yes | 0 | Session created; JSON emitted to stdout |

## JSON error shape (new)

When `--json` without `--confirm`, output to stderr:

```json
{
  "error": "confirm_required",
  "message": "--confirm flag required for non-interactive create-session. Re-run with --json --confirm <username>.",
  "target": "<username-or-profile-id>"
}
```

Exit code 1.

## JSON success shape (unchanged)

With `--json --confirm`, stdout:

```json
{
  "session_id": "<session-key>",
  "user_id": 42,
  "username": "alice",
  "profile_id": 17,
  "expires_at": "2026-04-19T12:34:56Z",
  "cookie": {
    "name": "sessionid",
    "value": "<session-key>",
    "httponly": true,
    "secure": true,
    "samesite": "Lax"
  }
}
```

Unchanged from today.

## Interactive prompt (unchanged)

```
WARNING: This will create a valid session cookie for user 'alice'.
Anyone with this session key can log in as that user until it expires.
Continue? [y/N]
```

Typing `y` proceeds; anything else aborts.

## Rationale

Parity with `cookie_admin reset`, which already enforces `--confirm` when `--json` is used. The risk surface is comparable: manufacturing a session cookie for an arbitrary user is as sensitive as wiping the database.

## Tests

- `tests/test_cookie_admin.py::test_create_session_json_without_confirm_errors`
- `tests/test_cookie_admin.py::test_create_session_json_with_confirm_succeeds`
- `tests/test_cookie_admin.py::test_create_session_interactive_y_succeeds`
- `tests/test_cookie_admin.py::test_create_session_interactive_n_aborts`
- Existing tests for interactive mode MUST continue to pass.

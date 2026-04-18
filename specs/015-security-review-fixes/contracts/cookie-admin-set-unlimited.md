# Contract — `cookie_admin set-unlimited` / `remove-unlimited` (CLI)

## Commands

```
docker compose exec web python manage.py cookie_admin set-unlimited [<username>] [--profile-id N] [--json]
docker compose exec web python manage.py cookie_admin remove-unlimited [<username>] [--profile-id N] [--json]
```

Passkey mode only (same as today).

## Why this contract changes

Today the CLI accepts only a positional `<username>` (`pk_<uuid8>`). Users can't see their own username — Settings in neither frontend displays it. For a multi-user passkey deployment (household, family, small group) the admin has no reliable way to identify who to grant unlimited to. Adding `--profile-id N` closes that gap without storing new PII: `profile.id` is an integer already exposed to its owner via `/api/auth/me`.

## Argparse shape

| Argument | Required | Type | Notes |
|----------|:--------:|------|-------|
| `username` | no (positional) | str | Existing path. `pk_<uuid8>` in passkey mode. |
| `--profile-id` | no | int | New path. Looks up `Profile.objects.get(id=N)`. |
| `--json` | no | bool | Existing. |

Exactly one of `username` and `--profile-id` must be present.

## Invocation truth table

| `username` | `--profile-id` | Behavior |
|:----------:|:--------------:|---------|
| `alice` | absent | Existing: look up by `User.objects.get(username="alice")` |
| absent | `17` | NEW: look up by `Profile.objects.get(id=17)`, derive `user = profile.user` |
| `alice` | `17` | **Exit non-zero**: `{"error": "ambiguous_target", "message": "pass either username or --profile-id, not both"}` |
| absent | absent | **Exit non-zero**: existing "must pass username" error |
| absent | `99999` | **Exit non-zero**: `{"error": "profile_not_found", "message": "Profile with id 99999 not found", "profile_id": 99999}` |

Both code paths converge on the existing `profile.unlimited_ai = True` update logic at `cookie_admin.py:587` (set) / `:598` (remove). JSON output shape is unchanged.

## JSON success output (unchanged)

```json
{
  "username": "pk_a3f91c2e",
  "user_id": 42,
  "unlimited_ai": true,
  "action": "set-unlimited"
}
```

Same for `remove-unlimited` with `"unlimited_ai": false` and `"action": "remove-unlimited"`.

## Back-compat guarantees

- Existing `cookie_admin set-unlimited <username>` scripts continue to work unchanged.
- JSON output shape is unchanged (same keys, same types).
- Interactive mode (no `--json`) continues to print the same human-readable message.

## Tests

- `tests/test_cookie_admin.py::test_set_unlimited_by_username_succeeds` (existing pattern, may already exist)
- `tests/test_cookie_admin.py::test_set_unlimited_by_profile_id_succeeds`
- `tests/test_cookie_admin.py::test_set_unlimited_both_args_errors`
- `tests/test_cookie_admin.py::test_set_unlimited_profile_id_not_found_errors`
- Mirror tests for `remove-unlimited`

## Security notes

- `profile.id` is not a secret. It's returned to every authenticated user via `/auth/me`. Surfacing it in Settings and accepting it on the CLI introduces zero new authz surface.
- The CLI already requires shell access to the container (implicit admin authn). Adding `--profile-id` doesn't change who can run the command.

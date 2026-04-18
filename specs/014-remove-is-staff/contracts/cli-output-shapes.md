# Contract: CLI Output Shapes (post-refactor)

Every admin/is_staff reference is stripped from informational CLI output. Diffs below are illustrative and show the exact field-level changes.

## `cookie_admin status --json`

### Before (current)

```json
{
  "auth_mode": "passkey",
  "users": {
    "total": 3,
    "active": 3,
    "admins": 1,
    "active_admins": 1
  },
  "api_key_configured": true,
  "default_model": "anthropic/claude-haiku-4.5",
  "cache": { /* existing block */ }
}
```

### After

```json
{
  "auth_mode": "passkey",
  "users": {
    "total": 3,
    "active": 3
  },
  "api_key_configured": true,
  "default_model": "anthropic/claude-haiku-4.5",
  "cache": { /* existing block */ }
}
```

**Delta**: `users.admins` and `users.active_admins` removed. Text output of `status` loses its "Admins: N active" line.

## `cookie_admin audit --json`

### Before (per-user event dict)

```json
{
  "user_id": 42,
  "username": "alice",
  "is_admin": false,
  "is_active": true,
  "date_joined": "2026-03-01T12:00:00Z",
  "last_login": "2026-04-17T09:30:00Z"
}
```

### After

```json
{
  "user_id": 42,
  "username": "alice",
  "is_active": true,
  "date_joined": "2026-03-01T12:00:00Z",
  "last_login": "2026-04-17T09:30:00Z"
}
```

**Delta**: `is_admin` field removed from every per-user event in the audit output.

## `cookie_admin list-users --json`

### Before (per-user record)

```json
{
  "user_id": 42,
  "username": "alice",
  "is_admin": false,
  "is_active": true,
  "unlimited_ai": false,
  "date_joined": "2026-03-01T12:00:00Z",
  "last_login": "2026-04-17T09:30:00Z"
}
```

### After

```json
{
  "user_id": 42,
  "username": "alice",
  "is_active": true,
  "unlimited_ai": false,
  "date_joined": "2026-03-01T12:00:00Z",
  "last_login": "2026-04-17T09:30:00Z"
}
```

**Delta**: `is_admin` field removed. JSON envelope no longer contains `admins: N` summary.

### Flag deletions

- `--admins-only` flag: DELETED. The concept no longer exists.

## `cookie_admin list-users` (text)

### Before

```
USERNAME   ADMIN   ACTIVE  UNLIMITED  LAST LOGIN           JOINED
alice      no      yes     no         2026-04-17 09:30:00  2026-03-01
bob        yes     yes     yes        2026-04-18 10:15:00  2026-03-15

Users: 2   Active: 2   Admins: 1
```

### After

```
USERNAME   ACTIVE  UNLIMITED  LAST LOGIN           JOINED
alice      yes     no         2026-04-17 09:30:00  2026-03-01
bob        yes     yes        2026-04-18 10:15:00  2026-03-15

Users: 2   Active: 2
```

**Delta**: `ADMIN` column removed from header and all rows. `Admins: N` removed from summary footer.

## `cookie_admin create-user`

### Before

```
usage: cookie_admin create-user [--admin] [--json] <username>
```

### After

```
usage: cookie_admin create-user [--json] <username>
```

**Delta**: `--admin` flag DELETED. All created users have `is_staff=False`.

## `cookie_admin promote` — DELETED

Subcommand removed entirely. `cookie_admin promote --help` returns argparse error "unknown subcommand".

## `cookie_admin demote` — DELETED

Subcommand removed entirely. Same as above.

## `cookie_admin --help`

### Before (subcommand list excerpt)

```
  list-users        List users (with --admins-only, --admin column shown)
  create-user       Create passkey user (--admin to grant admin)
  delete-user       Delete passkey user
  promote           Grant admin privilege to a user
  demote            Revoke admin privilege (floor: 1 admin)
  activate          Activate passkey user
  deactivate        Deactivate passkey user
  set-unlimited     Grant unlimited AI to a user
  remove-unlimited  Revoke unlimited AI
  rename            Rename a profile
  ...
```

### After

```
  list-users        List users (table or --json)
  create-user       Create passkey user
  delete-user       Delete passkey user
  activate          Activate passkey user
  deactivate        Deactivate passkey user
  set-unlimited     Grant unlimited AI to a user
  remove-unlimited  Revoke unlimited AI
  rename            Rename a profile
  ...
```

**Delta**: `promote` and `demote` lines gone. Descriptive help for `list-users` and `create-user` updated to drop admin references.

## `/auth/me` response body

### Before (passkey mode)

```json
{
  "user": {
    "id": 42,
    "is_admin": false
  },
  "profile": { /* ... */ }
}
```

### After

```json
{
  "user": {
    "id": 42
  },
  "profile": { /* ... */ }
}
```

**Delta**: `user.is_admin` field removed. No frontend consumer reads this field today; TypeScript types are updated to remove it.

## `CLAUDE.md` updates

The "Admin CLI" section must be updated to:

- Remove `promote` and `demote` example commands.
- Remove `--admin` flag from the `create-user` example.
- Remove `--admins-only` flag from the `list-users` example.
- Add a note: "Admin privilege no longer exists in passkey mode — all passkey users are peers. All app config is via CLI."

# API Contract: Admin CLI Tool

Django management command: `python manage.py cookie_admin <subcommand>`

Invoked via Docker: `docker compose exec web python manage.py cookie_admin <subcommand>`
Remote: `ssh user@server docker compose exec web python manage.py cookie_admin <subcommand>`

Only functional in public mode. In home mode, prints error and exits.

---

## Subcommands

### list-users

List all registered users.

```
$ cookie_admin list-users

USERNAME     ADMIN  ACTIVE  JOINED
──────────   ─────  ──────  ──────────
matt         yes    yes     2026-03-24
alice        no     yes     2026-03-25
bob          no     no      2026-03-26  (unverified)

Total: 3 users (2 active, 1 admin)
```

**Options**:
- `--active-only` — Show only active (verified) users
- `--admins-only` — Show only admin users
- `--json` — Output as JSON array

---

### promote \<username\>

Grant admin privileges to a user.

```
$ cookie_admin promote alice
✓ alice is now an admin.
```

**Errors**:
```
$ cookie_admin promote nonexistent
Error: User 'nonexistent' not found.

$ cookie_admin promote matt
User 'matt' is already an admin.
```

---

### demote \<username\>

Revoke admin privileges from a user.

```
$ cookie_admin demote alice
✓ alice is no longer an admin.
```

**Errors**:
```
$ cookie_admin demote matt
Error: Cannot demote the last remaining admin. Promote another user first.
```

**Safety**: Cannot demote the last admin — always ensures at least one admin exists.

---

### reset-password \<username\>

Reset a user's password. Prompts for new password (interactive) or accepts `--password` flag.

```
$ cookie_admin reset-password alice
New password: ********
Confirm password: ********
✓ Password for 'alice' has been reset.
```

**Options**:
- `--password <value>` — Set password non-interactively (for scripting)
- `--generate` — Generate a random password and print it

```
$ cookie_admin reset-password alice --generate
✓ Password for 'alice' has been reset.
  New password: xK9m2pQr7vB4
  (Share this with the user securely)
```

---

### deactivate \<username\>

Deactivate a user account (prevents login).

```
$ cookie_admin deactivate bob
✓ bob has been deactivated. They can no longer log in.
```

**Notes**: Does not delete data. User's profile and recipes remain intact.

---

### activate \<username\>

Reactivate a deactivated user account.

```
$ cookie_admin activate bob
✓ bob has been reactivated. They can now log in.
```

---

### cleanup-unverified

Delete inactive accounts older than the verification window.

```
$ cookie_admin cleanup-unverified
Found 3 unverified accounts older than 24 hours.
Deleting... ✓ Removed 3 accounts and their associated profiles.
```

**Options**:
- `--older-than <hours>` — Age threshold (default: 24)
- `--dry-run` — Show what would be deleted without deleting

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (user not found, validation failure, etc.) |
| 2 | Wrong mode (running in home mode) |

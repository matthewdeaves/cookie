# Data Model

No schema changes in this refactor. This document records the post-refactor semantic state of the entities involved and how they are touched during the migration.

## Entities

### User (Django `AbstractUser`)

**Location**: `django.contrib.auth.models.User` (default Django user). The project does NOT set `AUTH_USER_MODEL`; we use the stock model.

**Fields and their post-refactor status**:

| Field | Status | Notes |
|-------|--------|-------|
| `username` | ACTIVE | Used as the account identifier in passkey mode; not used in home mode (no users exist). |
| `password` | INACTIVE (set to unusable) | `set_unusable_password()` called on every passkey user — passkey mode has no passwords. |
| `email` | ALWAYS EMPTY `""` | Constitution Principle II bars storage. |
| `is_active` | ACTIVE | Used by auth flow (`activate`/`deactivate` CLI subcommands, login gate). |
| **`is_staff`** | **INERT** | **Column remains (Django requirement) but contains `False` for every application-created user. No application code reads it.** |
| `is_superuser` | INERT | Never written; Django `createsuperuser` is not used (no `manage.py createsuperuser` is part of the deploy flow). |
| `date_joined` | ACTIVE | Reported in `list-users` and `audit` CLI output. |
| `last_login` | ACTIVE | Reported in `audit`. |
| `first_name`, `last_name` | UNUSED | Never written or read. |
| `groups`, `user_permissions` | UNUSED | No permission framework in use; no `has_perm()` / `.groups` reads. |

**Migration posture**: none. The `is_staff` column is part of `auth.User` and cannot be dropped without switching to a custom `AUTH_USER_MODEL` (explicitly out of scope). For greenfield dev databases, no migration is needed because all app-created users already get `is_staff=False` post-refactor. Operators upgrading an old dev DB with existing `is_staff=True` rows should `reset` or manually set to False — no automated migration is provided (dev-mode posture).

### Profile

**Location**: `apps/profiles/models.py`. No schema changes.

**Fields relevant to this refactor**:

| Field | Status | Notes |
|-------|--------|-------|
| `id` | ACTIVE | Surrogate primary key. |
| `user` (FK) | Mode-dependent | `None` in home mode; `User` FK in passkey mode. |
| `name` | ACTIVE | Display name. |
| `unlimited_ai` | **PROMOTED TO SOLE PRIVILEGE FLAG** | Was previously one of two signals for quota bypass (alongside `User.is_staff`). Post-refactor, the ONLY signal. Granted via `cookie_admin set-unlimited <username>`; revoked via `cookie_admin remove-unlimited <username>`. |
| *(other fields)* | Unchanged | Recipe scope, preferences, etc. |

## Relationships

```
User  1 ─── 1  Profile   (passkey mode only; home mode has Profiles without Users)
```

No relationship changes.

## State transitions

### User.is_staff lifecycle (before → after)

**Before this refactor**:

```
create-user --admin  ─►  is_staff=True  ─►  promote         ─►  is_staff=True (no-op)
create-user          ─►  is_staff=False ─►  promote         ─►  is_staff=True
is_staff=True        ─►  demote         ─►  is_staff=False
is_staff=True        ─►  (last admin)   ─►  demote blocked by one-admin-floor
```

**After this refactor**:

```
create-user          ─►  is_staff=False        (terminal state; no transitions)
```

### Profile.unlimited_ai lifecycle (unchanged — documented here for context)

```
Profile created        ─►  unlimited_ai=False
cookie_admin set-unlimited <username>    ─►  unlimited_ai=True
cookie_admin remove-unlimited <username> ─►  unlimited_ai=False
```

## Validation rules

None introduced or changed. `unlimited_ai` is a plain boolean; `is_staff` becomes a DB column with no application semantics.

## Test-fixture implications

Three categories of existing test fixtures touch `is_staff`:

1. **Admin-privilege assertion fixtures** (in e.g. `test_cookie_admin.py`): DELETE. The tests they support are gone.
2. **Quota-bypass fixtures** (in `test_ai_quota.py`): REWRITE. Replace `User.objects.create_user(..., is_staff=True)` calls with a Profile setup that sets `profile.unlimited_ai = True; profile.save()`.
3. **Scaffold fixtures that happen to pass `is_staff=True`** (in `test_system_api.py`, `test_legacy_auth.py`, etc.): SIMPLIFY. Drop the `is_staff=True` kwarg from the `create_user` call — the test doesn't depend on it; the flag was just boilerplate.

The pytest static test (`test_no_is_staff_reads.py`) enforces that after this cleanup, no `is_staff` token survives in test files except in an allowlisted location (the static test itself, which references the token by necessity).

## Seed data

No seed data changes. Fresh installs already create the first passkey user (via WebAuthn registration) with `is_staff=False` — that continues unchanged.

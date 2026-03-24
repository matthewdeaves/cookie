# Data Model: Dual-Mode Authentication

## Entity Relationship Overview

```
┌─────────────────┐       ┌──────────────────┐
│   Django User    │ 1───1 │     Profile      │
│  (public mode)   │       │   (both modes)   │
└─────────────────┘       └──────────────────┘
                                   │
                     ┌─────────────┼─────────────┐
                     │             │             │
               ┌─────┴─────┐ ┌────┴────┐ ┌─────┴──────┐
               │  Recipe    │ │Favorite │ │ Collection │
               │(per-prof)  │ │(per-prof)│ │ (per-prof) │
               └───────────┘ └─────────┘ └────────────┘
```

## New Entity: User (Django auth.User)

Only exists/used in public mode. Standard Django User model — no custom fields needed.

| Field | Type | Notes |
|-------|------|-------|
| `id` | AutoField | Primary key |
| `username` | CharField(150) | Unique, case-insensitive. Validated: 3-30 chars, alphanumeric + underscores |
| `password` | CharField(128) | Django's PBKDF2-SHA256 hash (never plaintext) |
| `is_active` | BooleanField | False until email verified, True after |
| `is_staff` | BooleanField | True = admin. First user auto-promoted |
| `is_superuser` | BooleanField | Always False (not used, Django admin not enabled) |
| `date_joined` | DateTimeField | Auto-set on creation |
| `email` | CharField(254) | **ALWAYS EMPTY STRING**. Field exists on Django User model but is never populated. Email is only held transiently in memory. |
| `first_name` | CharField(150) | **ALWAYS EMPTY STRING**. Not used. |
| `last_name` | CharField(150) | **ALWAYS EMPTY STRING**. Not used. |

**Important**: Django's User model has `email`, `first_name`, `last_name` fields by default. We do NOT populate them. They remain empty strings (Django's default). We do not create a custom User model to remove them — that would add migration complexity for no security benefit (empty string stores nothing).

### Validation Rules
- Username: 3-30 characters, `^[a-zA-Z0-9_]+$`, unique (case-insensitive via `__iexact` lookup)
- Password: Minimum 8 characters, not entirely numeric, not in Django's common password list
- Email (transient only): Valid email format, used only to send verification, immediately discarded

### State Transitions
```
REGISTERED (is_active=False)
    │
    ├── Verification link clicked (within 2 hours)
    │   └── ACTIVE (is_active=True)
    │
    ├── Verification expired (after 2 hours)
    │   └── Must register again
    │       (inactive user can be overwritten or cleaned up)
    │
    └── Admin deactivates via CLI
        └── DEACTIVATED (is_active=False)
            └── Admin reactivates via CLI
                └── ACTIVE (is_active=True)
```

## Modified Entity: Profile

| Field | Type | Change | Notes |
|-------|------|--------|-------|
| `id` | AutoField | Unchanged | |
| `name` | CharField(100) | Unchanged | |
| `avatar_color` | CharField(7) | Unchanged | Hex color |
| `theme` | CharField(10) | Unchanged | light/dark |
| `unit_preference` | CharField(10) | Unchanged | metric/imperial |
| `created_at` | DateTimeField | Unchanged | |
| `updated_at` | DateTimeField | Unchanged | |
| `user` | OneToOneField(User) | **NEW** | Nullable. Set in public mode, null in home mode. `on_delete=CASCADE` (deleting User deletes Profile) |

### Behavior by Mode
- **Home mode**: `user` is always null. Profile works exactly as today.
- **Public mode**: `user` links to the Django User. Profile is auto-created at registration. Deleting User cascades to Profile and all profile-scoped data.

## Transient: Verification Token

Not stored in database. Generated using `django.core.signing.TimestampSigner`.

| Component | Description |
|-----------|-------------|
| Payload | User's primary key (integer) |
| Signature | HMAC-SHA256 using SECRET_KEY |
| Timestamp | Embedded in signed value, checked on verification |
| Expiry | 2 hours from creation |
| Single-use | Enforced by checking `user.is_active` — if already True, token was consumed |

**Token URL format**: `/api/auth/verify-email/?token=<signed_value>`

## Stale Registration Cleanup

Inactive users (registered but never verified) accumulate over time. A periodic cleanup is needed:

| Strategy | Implementation |
|----------|---------------|
| Management command | `python manage.py cleanup_unverified --older-than 24h` |
| Trigger | Cron job or called in entrypoint on restart |
| Behavior | Deletes User + Profile where `is_active=False` and `date_joined` > 24 hours ago |

## Existing Entities (Unchanged)

These entities are profile-scoped and require no changes:

- **Recipe**: `profile` FK (includes remixes with `remix_profile`)
- **RecipeFavorite**: `profile` FK
- **RecipeCollection**: `profile` FK
- **RecipeViewHistory**: `profile` FK
- **ServingAdjustment**: `profile` FK
- **AIDiscoverySuggestion**: `profile` FK
- **AppSettings**: Singleton (pk=1), not profile-scoped — admin-only in public mode
- **SearchSource**: Global, not profile-scoped — admin-only in public mode
- **AIPrompt**: Global, not profile-scoped — admin-only in public mode

## Migration Strategy

Single migration adds:
1. `django.contrib.auth` tables (User, Group, Permission) — Django handles this
2. `Profile.user` OneToOneField (nullable) — our migration

Both migrations are safe to run in either mode. In home mode, auth tables exist but are empty and unused.

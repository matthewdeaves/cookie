# API Contract: Permission Map

Defines the auth level for every API endpoint in both modes.

## Legend

| Level | Home Mode | Public Mode |
|-------|-----------|-------------|
| **Public** | No auth needed | No auth needed |
| **Profile** | SessionAuth (profile_id in session) | Authenticated user (profile resolved from User→Profile) |
| **Admin** | Same as Profile (no admin distinction) | Authenticated user with `is_staff=True` |

---

## System Endpoints (`/api/system/`)

| Endpoint | Method | Home | Public | Notes |
|----------|--------|------|--------|-------|
| `/system/health/` | GET | Public | Public | Liveness probe |
| `/system/ready/` | GET | Public | Public | Readiness probe |
| `/system/mode/` | GET | Public | Public | **NEW** — Returns operating mode |
| `/system/reset-preview/` | GET | Profile | Admin | Shows data counts |
| `/system/reset/` | POST | Profile | Admin | Destructive — deletes all data |

## Auth Endpoints (`/api/auth/`) — Public Mode Only

| Endpoint | Method | Home | Public | Notes |
|----------|--------|------|--------|-------|
| `/auth/register/` | POST | N/A (404) | Public | Rate limited: 5/h per IP |
| `/auth/login/` | POST | N/A (404) | Public | Rate limited: 10/h per IP |
| `/auth/logout/` | POST | N/A (404) | Profile | Requires active session |
| `/auth/verify-email/` | GET | N/A (404) | Public | Token in query string |
| `/auth/me/` | GET | N/A (404) | Profile | Returns current user+profile |
| `/auth/change-password/` | POST | N/A (404) | Profile | Rate limited: 5/h per user |

## Profile Endpoints (`/api/profiles/`)

| Endpoint | Method | Home | Public | Notes |
|----------|--------|------|--------|-------|
| `/profiles/` | GET | Public | Profile* | *Public mode: returns only own profile (admin sees all) |
| `/profiles/` | POST | Public | N/A (404) | Public mode: profiles created via /auth/register only |
| `/profiles/{id}/` | GET | Public | Profile | Own profile only (admin: any) |
| `/profiles/{id}/` | PUT | Profile | Profile | Own profile only |
| `/profiles/{id}/` | DELETE | Profile | Profile | Own profile only (cascade deletes User too) |
| `/profiles/{id}/deletion-preview/` | GET | Public | Profile | Own profile only |
| `/profiles/{id}/select/` | POST | Public | N/A (404) | Public mode: no profile switching |

## Recipe Endpoints (`/api/recipes/`)

| Endpoint | Method | Home | Public | Notes |
|----------|--------|------|--------|-------|
| `/recipes/` | GET | Public | Profile | Profile-scoped |
| `/recipes/scrape/` | POST | Profile | Profile | Profile-scoped |
| `/recipes/search/` | GET | Public | Public | Search doesn't require auth |
| `/recipes/cache/health/` | GET | Public | Admin | Monitoring endpoint |
| `/recipes/{id}/` | GET | Public | Profile | Profile-scoped (404 if not owned) |
| `/recipes/{id}/` | DELETE | Profile | Profile | Profile-scoped |

## Favorites (`/api/favorites/`)

| Endpoint | Method | Home | Public | Notes |
|----------|--------|------|--------|-------|
| `/favorites/` | GET | Public | Profile | Profile-scoped |
| `/favorites/` | POST | Profile | Profile | Profile-scoped |
| `/favorites/{id}/` | DELETE | Profile | Profile | Profile-scoped |

## Collections (`/api/collections/`)

| Endpoint | Method | Home | Public | Notes |
|----------|--------|------|--------|-------|
| `/collections/` | GET | Public | Profile | Profile-scoped |
| `/collections/` | POST | Profile | Profile | Profile-scoped |
| `/collections/{id}/` | GET | Public | Profile | Profile-scoped |
| `/collections/{id}/` | PUT | Profile | Profile | Profile-scoped |
| `/collections/{id}/` | DELETE | Profile | Profile | Profile-scoped |
| `/collections/{id}/recipes/` | POST | Profile | Profile | Profile-scoped |
| `/collections/{id}/recipes/{rid}/` | DELETE | Profile | Profile | Profile-scoped |

## History (`/api/history/`)

| Endpoint | Method | Home | Public | Notes |
|----------|--------|------|--------|-------|
| `/history/` | GET | Public | Profile | Profile-scoped |
| `/history/` | POST | Profile | Profile | Profile-scoped |
| `/history/` | DELETE | Profile | Profile | Profile-scoped |

## AI Endpoints (`/api/ai/`)

| Endpoint | Method | Home | Public | Notes |
|----------|--------|------|--------|-------|
| `/ai/status` | GET | Public | Public | API key status indicator |
| `/ai/test-api-key` | POST | Profile | Admin | Tests OpenRouter key validity |
| `/ai/save-api-key` | POST | Profile | Admin | Saves to global AppSettings |
| `/ai/prompts` | GET | Public | Public | Lists all prompts |
| `/ai/prompts/{type}` | GET | Public | Public | Gets single prompt |
| `/ai/prompts/{type}` | PUT | Profile | Admin | Edits prompt template |
| `/ai/models` | GET | Public | Public | Lists available models |
| `/ai/tips` | POST | Profile | Profile | Profile-scoped |
| `/ai/timer-name` | POST | Profile | Profile | Profile-scoped |
| `/ai/repair-selector` | POST | Profile | Admin | Maintenance operation |
| `/ai/sources-needing-attention` | GET | Public | Admin | Monitoring |
| `/ai/remix-suggestions` | POST | Profile | Profile | Profile-scoped |
| `/ai/remix` | POST | Profile | Profile | Profile-scoped |
| `/ai/scale` | POST | Profile | Profile | Profile-scoped |
| `/ai/discover/{id}/` | GET | Public | Profile | Profile-scoped (own only) |

## Sources (`/api/sources/`)

| Endpoint | Method | Home | Public | Notes |
|----------|--------|------|--------|-------|
| `/sources/` | GET | Public | Public | Needed by search |
| `/sources/enabled-count/` | GET | Public | Public | |
| `/sources/{id}/` | GET | Public | Public | |
| `/sources/{id}/toggle/` | POST | Profile | Admin | Global setting |
| `/sources/bulk-toggle/` | POST | Profile | Admin | Global setting |
| `/sources/{id}/selector/` | PUT | Profile | Admin | Global setting |
| `/sources/{id}/test/` | POST | Profile | Admin | Resource-intensive |
| `/sources/test-all/` | POST | Profile | Admin | Resource-intensive |

## Static Pages

| Path | Auth | Notes |
|------|------|-------|
| `/privacy/` | Public | Privacy policy — always accessible |

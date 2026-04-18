# Contract: Gated Endpoints (post-refactor)

27 endpoints return `404 {"detail": "Not found"}` in passkey mode. In home mode they behave identically to pre-refactor. No auth-failure log line is emitted on the 404 path.

## Admin endpoints (18) — behavior unchanged, auth class renamed

| # | Method | Path | Handler | Auth (after) |
|---|--------|------|---------|--------------|
| 1 | GET | `/api/system/reset-preview/` | `core.api.get_reset_preview` | `HomeOnlyAuth()` |
| 2 | POST | `/api/system/reset/` | `core.api.reset` | `HomeOnlyAuth()` |
| 3 | PUT | `/api/ai/quotas` | `ai.api_quotas.update_quotas` | `HomeOnlyAuth()` |
| 4 | POST | `/api/ai/test-api-key` | `ai.api.test_api_key` | `HomeOnlyAuth()` |
| 5 | POST | `/api/ai/save-api-key` | `ai.api.save_api_key` | `HomeOnlyAuth()` |
| 6 | GET | `/api/ai/prompts` | `ai.api.list_prompts` | `HomeOnlyAuth()` |
| 7 | GET | `/api/ai/prompts/{prompt_type}` | `ai.api.get_prompt` | `HomeOnlyAuth()` |
| 8 | PUT | `/api/ai/prompts/{prompt_type}` | `ai.api.update_prompt` | `HomeOnlyAuth()` |
| 9 | POST | `/api/ai/settings/` | `ai.api.save_settings` | `HomeOnlyAuth()` |
| 10 | GET | `/api/ai/sources-needing-attention` | `ai.api.get_sources_needing_attention` | `HomeOnlyAuth()` |
| 11 | POST | `/api/sources/bulk-toggle/` | `recipes.sources_api.bulk_toggle` | `HomeOnlyAuth()` |
| 12 | POST | `/api/sources/test-all/` | `recipes.sources_api.test_all` | `HomeOnlyAuth()` |
| 13 | POST | `/api/sources/{source_id}/toggle/` | `recipes.sources_api.toggle_source` | `HomeOnlyAuth()` |
| 14 | PUT | `/api/sources/{source_id}/selector/` | `recipes.sources_api.update_selector` | `HomeOnlyAuth()` |
| 15 | POST | `/api/sources/{source_id}/test/` | `recipes.sources_api.test_source` | `HomeOnlyAuth()` |
| 16 | GET | `/api/recipes/cache/health/` | `recipes.api.get_cache_health` | `HomeOnlyAuth()` |
| 17 | POST | `/api/profiles/{profile_id}/set-unlimited/` | `profiles.api.set_unlimited` | `HomeOnlyAuth()` |
| 18 | PATCH | `/api/profiles/{profile_id}/rename/` | `profiles.api.rename_profile` | `HomeOnlyAuth()` |

## Profile endpoints (9) — newly gated

| # | Method | Path | Handler | Auth (after) | Notes |
|---|--------|------|---------|--------------|-------|
| 19 | GET | `/api/profiles/` | `profiles.api.list_profiles` | `auth=None` + inline `raise HttpError(404)` in non-home | Was conditional auth; inline gate chosen because home-mode profile-selection runs pre-session |
| 20 | POST | `/api/profiles/` | `profiles.api.create_profile` | `auth=None` + inline `raise HttpError(404)` in non-home | Was `auth=None` + inline `Status(404, …)`; body unified to `{"detail":"Not found"}` |
| 21 | GET | `/api/profiles/{profile_id}/` | `profiles.api.get_profile` | `HomeOnlyAuth()` | Was `SessionAuth()`; ownership check simplified (no is_staff bypass) |
| 22 | PUT | `/api/profiles/{profile_id}/` | `profiles.api.update_profile` | `HomeOnlyAuth()` | Was `SessionAuth()` |
| 23 | GET | `/api/profiles/{profile_id}/deletion-preview/` | `profiles.api.get_deletion_preview` | `HomeOnlyAuth()` | Was `SessionAuth()` |
| 24 | DELETE | `/api/profiles/{profile_id}/` | `profiles.api.delete_profile` | `HomeOnlyAuth()` | Was `SessionAuth()` |
| 25 | POST | `/api/profiles/{profile_id}/select/` | `profiles.api.select_profile` | `auth=None` + inline `raise HttpError(404)` in non-home | Was `auth=None` + inline `Status(404, …)`; body unified |

(Endpoints 17 and 18 were already gated via `HomeOnlyAdminAuth` → renamed; listed in the admin section.)

**Why the split between `HomeOnlyAuth` and inline check**: `HomeOnlyAuth` inherits from `SessionAuth`, which requires a profile-session cookie. In home mode, three of the profile endpoints (list, create, select) must be reachable WITHOUT a session because they are the profile-selection flow that precedes session establishment. For those three, an inline `raise HttpError(404, "Not found")` at the top of the handler provides the same security posture (404 before any logic runs, no auth-failure log line) without demanding a session. The remaining four profile endpoints (get, update, deletion-preview, delete) operate on an existing profile and are always hit post-selection, so `HomeOnlyAuth` (requires session) is the correct gate.

## Behavior matrix

For every endpoint in the table above:

| Caller / Mode | Home mode | Passkey mode |
|---|---|---|
| Unauthenticated request | Existing behavior (most require profile session → 401/redirect; create/select allow anonymous create) | **404 `{"detail": "Not found"}`** |
| Authenticated profile session | Existing behavior (200/204/etc.) | **404 `{"detail": "Not found"}`** |
| `is_staff=True` user | Existing behavior | **404 `{"detail": "Not found"}`** — `is_staff` no longer grants any privilege |
| `unlimited_ai=True` profile | Existing behavior | **404 `{"detail": "Not found"}`** — `unlimited_ai` is for quota bypass, not endpoint access |

The 404 is structurally indistinguishable from a non-existent route. No `security_logger.warning` line is emitted on the 404 path.

## Endpoints intentionally NOT gated

For clarity, the following profile-adjacent endpoints keep `SessionAuth` and work in both modes:

- None. All `/api/profiles/*` endpoints are home-only per FR-009.

Auth endpoints (`/auth/me`, `/auth/logout`, `/passkey/*`, `/device-code/*`) keep their existing auth and work in their intended modes — they are out of scope for this refactor (FR-023).

## Test coverage contract

`tests/test_gated_endpoints_passkey.py` asserts, for every row 1–25 above:

1. In passkey mode with an authenticated passkey session, the endpoint returns exactly `404` with body `{"detail": "Not found"}`.
2. No log line containing `"Auth failure"` or `"Admin auth failure"` is emitted for the request.
3. In home mode with a valid profile session, the endpoint returns its documented success code.

The test suite additionally adds:

- `test_home_mode_only_decorator.py` (rewrite existing): unit-level tests of `HomeOnlyAuth.__call__` behavior — home pass-through, passkey 404, preserves request object, etc.

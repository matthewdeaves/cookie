# Contract: Gated admin endpoints (home-only in passkey mode)

Every row below is a gated endpoint. In home mode behavior is unchanged (the "Home mode response" column summarizes the existing contract). In passkey mode every row, regardless of caller identity, returns `404 {"detail": "Not found"}` with no `security_logger` auth-failure line.

## Mode behavior matrix

For every row below, under `AUTH_MODE=passkey`:

| Caller identity | Expected response | Security log |
|------------------|-------------------|--------------|
| Anonymous        | `404 {"detail":"Not found"}` | no new line |
| Authenticated non-admin | `404 {"detail":"Not found"}` | no new line |
| Authenticated admin | `404 {"detail":"Not found"}` | no new line |

Home mode responses (column 4 below) are captured as references to existing tests; this change MUST NOT alter them.

## Endpoint inventory

| # | Method + Path | Handler file | Home mode response (unchanged) | Auth (before → after) |
|---|---------------|--------------|-------------------------------|------------------------|
| 1 | `POST /api/ai/save-api-key` | `apps/ai/api.py` | existing `SaveApiKeyOut` / 400 / 429 | `AdminAuth()` → `HomeOnlyAdminAuth()` |
| 2 | `POST /api/ai/test-api-key` | `apps/ai/api.py` | existing `TestApiKeyOut` / 400 / 429 | `AdminAuth()` → `HomeOnlyAdminAuth()` |
| 3 | `GET /api/ai/prompts` | `apps/ai/api.py` | `List[PromptOut]` | `AdminAuth()` → `HomeOnlyAdminAuth()` |
| 4 | `GET /api/ai/prompts/{prompt_type}` | `apps/ai/api.py` | `PromptOut` / 404 | `AdminAuth()` → `HomeOnlyAdminAuth()` |
| 5 | `PUT /api/ai/prompts/{prompt_type}` | `apps/ai/api.py` | `PromptOut` / 404 / 422 | `AdminAuth()` → `HomeOnlyAdminAuth()` |
| 6 | `POST /api/ai/repair-selector` | `apps/ai/api.py` | `SelectorRepairOut` / 400 / 404 / 429 / 503 | `AdminAuth()` → `HomeOnlyAdminAuth()` |
| 7 | `GET /api/ai/sources-needing-attention` | `apps/ai/api.py` | `List[SourceNeedingAttentionOut]` | `AdminAuth()` → `HomeOnlyAdminAuth()` |
| 8 | `PUT /api/ai/quotas` | `apps/ai/api_quotas.py` | `QuotaResponse` / 404 | `AdminAuth()` → `HomeOnlyAdminAuth()` |
| 9 | `GET /api/system/reset-preview/` | `apps/core/api.py` | `ResetPreviewSchema` / 403 | `AdminAuth()` → `HomeOnlyAdminAuth()`. Delete the inline `if AUTH_MODE == "passkey": return 403` block. |
| 10 | `POST /api/system/reset/` | `apps/core/api.py` | `ResetSuccessSchema` / 400 / 403 / 429 | `AdminAuth()` → `HomeOnlyAdminAuth()`. Delete the inline `if AUTH_MODE == "passkey": return 403` block. Keep the rate-limit block and the `confirmation_text != "RESET"` check. |
| 11 | `POST /api/sources/{source_id}/toggle/` | `apps/recipes/sources_api.py` | `SourceToggleOut` / 404 | `AdminAuth()` → `HomeOnlyAdminAuth()` |
| 12 | `POST /api/sources/bulk-toggle/` | `apps/recipes/sources_api.py` | `BulkToggleOut` | `AdminAuth()` → `HomeOnlyAdminAuth()` |
| 13 | `PUT /api/sources/{source_id}/selector/` | `apps/recipes/sources_api.py` | `SourceUpdateOut` / 404 | `AdminAuth()` → `HomeOnlyAdminAuth()` |
| 14 | `POST /api/sources/{source_id}/test/` | `apps/recipes/sources_api.py` | `SourceTestOut` / 404 / 500 | `AdminAuth()` → `HomeOnlyAdminAuth()` |
| 15 | `POST /api/sources/test-all/` | `apps/recipes/sources_api.py` | `{200: dict}` | `AdminAuth()` → `HomeOnlyAdminAuth()` |
| 16 | `GET /api/recipes/cache/health/` | `apps/recipes/api.py` | `{200: dict}` | `AdminAuth()` → `HomeOnlyAdminAuth()` |
| 17 | `POST /api/profiles/{profile_id}/set-unlimited/` | `apps/profiles/api.py` | `{200: dict, 404: ErrorSchema}` | `AdminAuth()` → `HomeOnlyAdminAuth()` |
| 18 | `PATCH /api/profiles/{profile_id}/rename/` | `apps/profiles/api.py` | `{200: dict, 400: ErrorSchema, 404: ErrorSchema}` | `AdminAuth()` → `HomeOnlyAdminAuth()` |

## NOT gated (intentional)

- `GET /api/profiles/` — `is_staff` controls scope (all profiles vs own), not reachability. Left unchanged per FR-007.
- `GET /api/system/mode/` — public by design. Remove the `version` key from the JSON body per FR-009.
- `GET /api/ai/status`, `GET /api/ai/models`, `POST /api/ai/timer-name`, recipe CRUD, search, etc. — non-admin endpoints, not affected.

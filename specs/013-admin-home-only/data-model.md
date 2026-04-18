# Phase 1 Data Model — 013-admin-home-only

No new entities. No schema migrations. The CLI expansion reads and writes existing tables.

## Entities touched

### AppSettings (apps/core/models.py, singleton pk=1)

Fields used by new CLI subcommands:

| Field | Read by | Written by | Notes |
|-------|---------|------------|-------|
| `openrouter_api_key` (property → `_openrouter_api_key`, encrypted) | `test-api-key` | `set-api-key` | Write via the property setter, not the private field. Empty/blank writes rejected (FR-017a). |
| `default_ai_model` | (existing uses) | `set-default-model` | `max_length=100`. |
| `daily_limit_remix` | `quota show` | `quota set remix` | `PositiveIntegerField`. |
| `daily_limit_remix_suggestions` | `quota show` | `quota set remix-suggestions` | `PositiveIntegerField`. |
| `daily_limit_scale` | `quota show` | `quota set scale` | `PositiveIntegerField`. |
| `daily_limit_tips` | `quota show` | `quota set tips` | `PositiveIntegerField`. |
| `daily_limit_discover` | `quota show` | `quota set discover` | `PositiveIntegerField`. |
| `daily_limit_timer` | `quota show` | `quota set timer` | `PositiveIntegerField`. |

### AIPrompt (apps/ai/models.py)

| Field | Read by | Written by | Notes |
|-------|---------|------------|-------|
| `prompt_type` (choices) | `prompts list`, `prompts show`, `prompts set` | — | Lookup key. |
| `name` | `prompts list`, `prompts show` | — | Display only. |
| `description` | `prompts show` | — | Display only. |
| `system_prompt` | `prompts show` | `prompts set --system-file` | Read file UTF-8 verbatim. |
| `user_prompt_template` | `prompts show` | `prompts set --user-file` | Read file UTF-8 verbatim. |
| `model` (choices) | `prompts list`, `prompts show` | `prompts set --model` | Validated against `AIPrompt.AVAILABLE_MODELS`. |
| `is_active` | `prompts list`, `prompts show` | `prompts set --active` | Bool. |

### SearchSource (apps/recipes/models.py)

| Field | Read by | Written by | Notes |
|-------|---------|------------|-------|
| `id`, `name`, `url` | `sources list`, `sources test` | — | Display only. |
| `enabled` | `sources list` | `sources toggle`, `sources toggle-all` | Bool flip. |
| `selector` | `sources list` (optional), `sources test` | `sources set-selector`, `sources repair` (AI) | CSS string. |
| `needs_attention` | `sources list --attention` | — (repaired by `sources repair` path) | Read-only here. |

### Profile (apps/profiles/models.py)

| Field | Read by | Written by | Notes |
|-------|---------|------------|-------|
| `id`, `name`, `user_id` | `rename` | `rename` (updates `name`) | In home mode the CLI positional arg is `profile_id`; in passkey mode it is `user_id` or `username` resolved via the Django `User` model. |

### User (django.contrib.auth.models.User) — passkey mode only

Used for `rename` lookup by `user.username` or `user.pk`. No fields written.

## Validation rules (new)

- `set-api-key`: `value` MUST be a non-empty string after `strip()`. Empty → `CommandError` with exit 2.
- `set-default-model`: `model_id` SHOULD match an entry in `AIPrompt.AVAILABLE_MODELS`; reject unknown with a clear error listing available options.
- `prompts set --system-file PATH` / `--user-file PATH`: the file MUST be readable UTF-8; missing/unreadable → `CommandError` with exit 2 and no DB write.
- `prompts set --active`: accepts `true` or `false` (case-insensitive); other values → `CommandError`.
- `prompts set <prompt_type>`: `prompt_type` MUST be in `AIPrompt.PROMPT_TYPES`; unknown → `CommandError` with exit 2.
- `sources set-selector`: `selector` is a non-empty string. No structural CSS validation here (the `sources test` subcommand exercises it).
- `sources test`: either `--id N` or `--all` is required; supplying both is an error.
- `sources repair`: requires `AppSettings.openrouter_api_key` to be set; empty → `CommandError` with exit 2 and no DB write.
- `quota set`: `N` is `int >= 0` (matches `PositiveIntegerField`); negative / non-numeric → `CommandError` with exit 2.
- `rename`: `--name` is a non-empty string; over-long input is truncated to the model's `max_length` after a warning, OR rejected (choose "rejected" — safer).

## State transitions

None new. All CLI writes are simple field updates on existing rows — no state machines change.

## Audit log hygiene (cross-entity)

For every new mutating subcommand the handler MUST call:

```python
security_logger.warning("cookie_admin %s: %s", subcommand_name, structured_summary)
```

`structured_summary` MUST NOT contain the API key value; for prompts it MAY include the `prompt_type` but MUST NOT include the full prompt body; for `rename` it MUST include the old and new names.

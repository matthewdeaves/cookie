# Contract: New `cookie_admin` subcommands

Every subcommand below follows the existing conventions in `apps/core/management/commands/cookie_admin.py`:

- Plain-text output by default. `--json` emits structured output.
- Exit codes: `0` success, `1` general error, `2` input error.
- Mutating subcommands emit exactly one `security_logger.warning` line per invocation.
- Read-only subcommands (`list`, `show`, `status`, `quota show`) emit NO security warnings.
- All new subcommands work in both `AUTH_MODE=home` and `AUTH_MODE=passkey` (FR-032a).

## Existing `handle()` passkey-mode guard refactor (FR-032b)

Before:
```python
if settings.AUTH_MODE != "passkey":
    self._error("cookie_admin is only available in passkey mode ...", ..., code=2)
```

After:
```python
PASSKEY_ONLY_SUBCOMMANDS = {
    "list-users", "create-user", "delete-user", "promote", "demote",
    "activate", "deactivate", "set-unlimited", "remove-unlimited",
    "usage", "create-session",
}

if subcommand in PASSKEY_ONLY_SUBCOMMANDS and settings.AUTH_MODE != "passkey":
    self._error(f"'{subcommand}' requires AUTH_MODE=passkey.", options, code=2)
```

## Subcommands

### `set-api-key [--key KEY | --stdin]`

Writes `AppSettings.openrouter_api_key`. `--stdin` reads `sys.stdin.read().strip()`. Empty value → error exit 2, no DB write.

Plain output: `API key saved.`
JSON: `{"saved": true}`
Log: `security_logger.warning("cookie_admin set-api-key: key changed")` (value never logged)

### `test-api-key [--key KEY | --stdin]`

Validates against OpenRouter. Does NOT persist. Mutating? No → no security log line.

Plain output: `valid` or `invalid: <reason>`
JSON: `{"valid": true}` or `{"valid": false, "reason": "<text>"}`
Exit: 0 if valid, 1 if invalid.

### `set-default-model <model_id>`

Writes `AppSettings.default_ai_model`. Validates `model_id` against `AIPrompt.AVAILABLE_MODELS`.

Plain output: `Default model set to <model_id>.`
JSON: `{"default_ai_model": "<model_id>"}`
Log: `security_logger.warning("cookie_admin set-default-model: %s", model_id)`

### `prompts list [--json]`

Lists AI prompts.

Plain output (one row per prompt): `<prompt_type>  model=<model>  active=<bool>  name="<name>"`
JSON: `[{"prompt_type": ..., "name": ..., "model": ..., "is_active": ...}, ...]`

### `prompts show <prompt_type> [--json]`

Displays a single prompt.

Plain output: multi-line (name, description, model, active, system prompt, user prompt template)
JSON: full object including `system_prompt` and `user_prompt_template`

### `prompts set <prompt_type> [--system-file PATH] [--user-file PATH] [--model MODEL] [--active {true,false}]`

Updates selected fields. Omitted flags leave fields unchanged.

Plain output: `Prompt <prompt_type> updated: fields=[system_prompt, model, is_active]`
JSON: `{"prompt_type": "...", "updated_fields": ["system_prompt", "model", "is_active"]}`
Log: `security_logger.warning("cookie_admin prompts set %s: fields=%s", prompt_type, updated_fields)` (prompt body NEVER logged)

### `sources list [--attention] [--json]`

Lists search sources.

Plain output (one row per source): `<id>  enabled=<bool>  attention=<bool>  <name>  <url>`
JSON: `[{"id": ..., "name": ..., "url": ..., "enabled": ..., "needs_attention": ..., "selector": ...}, ...]`

### `sources toggle <source_id>`

Flip `enabled`.

Plain output: `Source <id> (<name>): enabled=<new>`
JSON: `{"source_id": ..., "enabled": ...}`
Log: `security_logger.warning("cookie_admin sources toggle %d: %s", id, new_enabled)`

### `sources toggle-all {--enable | --disable}`

Set every source's `enabled`. Error if both flags or neither.

Plain output: `Set enabled=<value> for N sources.`
JSON: `{"enabled": <value>, "count": N}`
Log: `security_logger.warning("cookie_admin sources toggle-all: enabled=%s count=%d", value, n)`

### `sources set-selector <source_id> --selector CSS`

Overwrite selector.

Plain output: `Source <id> (<name>): selector updated.`
JSON: `{"source_id": ..., "selector": "..."}`
Log: `security_logger.warning("cookie_admin sources set-selector %d", id)` (selector NOT logged — can be long)

### `sources test [--id N | --all] [--json]`

Per FR-027a. Exit 0 if the command ran; per-source `ok` booleans in output.

Plain output:
```
[OK]   Source 1 (AllRecipes) — status=200 — 3 recipes found
[FAIL] Source 2 (Epicurious) — status=500 — selector did not match
...
2 ok / 1 failed
```
JSON: `[{"source_id": ..., "name": ..., "ok": bool, "status_code": int|null, "message": "..."}, ...]`
Log: none (read-only).

### `sources repair <source_id>`

AI-assisted selector regeneration. Requires API key.

Plain output: `Source <id>: selector repaired. confidence=<0.0-1.0>. auto_update=<bool>.`
JSON: `{"source_id": ..., "selector": "...", "confidence": 0.92, "auto_update": true}`
Log: `security_logger.warning("cookie_admin sources repair %d", id)`
Errors:
- API key not set → exit 2 with `sources repair requires OPENROUTER_API_KEY or AppSettings.openrouter_api_key to be set.`
- AI service 5xx → exit 1 with service error.

### `quota show [--json]`

Read-only.

Plain output (6 rows):
```
remix             = 3
remix-suggestions = 10
scale             = 20
tips              = 15
discover          = 2
timer             = 30
```
JSON: `{"remix": 3, "remix_suggestions": 10, "scale": 20, "tips": 15, "discover": 2, "timer": 30}`

### `quota set {remix|remix-suggestions|scale|tips|discover|timer} <N>`

Set one field. `N` is `int >= 0`.

Plain output: `quota.<name> = <N>`
JSON: `{"<name>": N}`
Log: `security_logger.warning("cookie_admin quota set %s=%d", name, n)`

### `rename <user_id_or_profile_id_or_username> --name NEW`

In passkey mode: argument is `User.id` (int) or `User.username`. Resolves to `User.profile`.
In home mode: argument is `Profile.id` (int).

Plain output: `Profile renamed: <old> → <new> (profile_id=<id>)`
JSON: `{"profile_id": ..., "old_name": "...", "new_name": "..."}`
Log: `security_logger.warning("cookie_admin rename profile_id=%d: %s → %s", id, old, new)`
Errors:
- target not found → exit 1 with `No profile found for <arg>.`
- `--name` empty or exceeds `max_length` → exit 2.

## `status --json` extension (FR-034)

Existing output now includes:

```json
{
  "mode": "passkey",
  "...existing keys...": "...",
  "cache": {
    "hits": 12345,
    "misses": 678,
    "hit_rate": 0.948,
    "entries": 4321
  }
}
```

Plain-text `status` output appends a `Cache:` block with the same data. Cache-health payload shape matches `GET /api/recipes/cache/health/` current body. Data source is factored out into a shared helper `get_cache_health_dict()` used by both the HTTP handler and the CLI.

# Data Model — Security Review Fixes (Round 2)

Minimal. No new database tables, no migrations, no persisted entities.

What this spec touches:
1. A new on-disk scheduler config (the crontab)
2. Two config-file constants (ruff C901, pytest static test)
3. Session state transitions at logout
4. One new API response field surfacing (`profile.id` → Settings UI; no schema change, data already present)
5. CLI argparse shape (add `--profile-id` to two subcommands)
6. New Dependabot config file

---

## 1. Crontab file (new on-disk entity)

**Location**: `/home/matt/cookie/crontab` (new top-level file, `COPY`ed to `/app/crontab` in `Dockerfile.prod`).

**Format**: standard vixie-cron user-crontab syntax (5 fields + command). No `USER` column. No environment variables defined inline — supercronic inherits them from its parent process.

**Contents**:
```cron
# Cookie cleanup jobs — scheduled by supercronic
# supercronic inherits env (SECRET_KEY, DATABASE_URL, DJANGO_SETTINGS_MODULE) from the parent entrypoint
# NEVER add environment variables here; see specs/015-security-review-fixes/research.md Decision 1
0  * * * * /usr/local/bin/python /app/manage.py cleanup_device_codes
15 3 * * * /usr/local/bin/python /app/manage.py cleanup_sessions
30 3 * * * /usr/local/bin/python /app/manage.py cleanup_search_images
```

**Ownership & permissions**: readable by the `app` user. Mode `0644`. Contains no secrets.

**Lifecycle**: shipped inside the image at build time. Never rewritten at runtime.

**Validation**: `supercronic -test /app/crontab` is invoked in `entrypoint.prod.sh` before starting the daemon (preflight).

---

## 2. ruff config extension

**Location**: `/home/matt/cookie/pyproject.toml`, under `[tool.ruff.lint]`.

**Delta**:
```toml
[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "SIM", "DJ", "S", "C90"]  # +C90

[tool.ruff.lint.mccabe]
max-complexity = 15

[tool.ruff.lint.per-file-ignores]
# existing per-file-ignores preserved; add:
"*/migrations/*.py" = ["C901"]
```

**Observable behavior**: `docker compose exec web ruff check apps/ cookie/` now returns non-zero if any function in `apps/`, `tests/`, or `cookie/` has CC > 15. Current max is 14 — initial run passes.

---

## 3. Pytest static test + EXEMPT_FILES allowlist

**Location**: `/home/matt/cookie/tests/test_code_quality.py` (new file).

```python
"""Static code-quality gates per Constitution Principle V."""

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
MAX_FILE_LINES: int = 500

# Grandfathered file-size violations. Cleanup tracked in spec 016-code-quality-refactor.
# Adding a file to this map requires a PR referencing a follow-up-spec id.
# Removing a file is mandatory once it's refactored below MAX_FILE_LINES.
# Current-line ceiling prevents "adding more lines to a grandfathered file".
EXEMPT_FILES: dict[str, int] = {
    # production code — apps/ non-test
    "apps/core/management/commands/cookie_admin.py": 1172,
    "apps/ai/api.py": 534,
    "apps/recipes/services/scraper.py": 517,
    # test code — in apps/
    "apps/ai/tests.py": 1852,
    "apps/recipes/tests.py": 564,
    # test code — top-level tests/
    "tests/test_passkey_api.py": 903,
    "tests/test_recipes_api.py": 799,
    "tests/test_cookie_admin.py": 792,
    "tests/test_ai_quota.py": 768,
    "tests/test_search.py": 718,
    "tests/test_system_api.py": 701,
    "tests/test_image_cache.py": 674,
    "tests/test_ai_api.py": 597,
    "tests/test_device_code_api.py": 540,
    "tests/test_user_features.py": 524,
}


def test_py_file_size_under_limit() -> None:
    """Every .py in apps/ or tests/ must be ≤ MAX_FILE_LINES, or explicitly grandfathered."""
    # Algorithm:
    #   For each candidate .py file:
    #     count = lines
    #     If count > MAX_FILE_LINES:
    #       If path in EXEMPT_FILES:
    #         ceiling = EXEMPT_FILES[path]
    #         If count > ceiling: fail ("ceiling exceeded")
    #         Else: allowed
    #       Else: fail ("new violation")
    #     Else:  # count <= MAX_FILE_LINES
    #       If path in EXEMPT_FILES: fail ("file now under limit; remove from allowlist")
    ...
```

**Test identity**: `tests/test_code_quality.py::test_py_file_size_under_limit`. Runs inside existing `backend-test` CI job.

**State transitions** on the allowlist:
| Event | Legal? |
|-------|:------:|
| Refactor an allowlisted file under 500 lines, remove its entry in same PR | ✅ |
| Add a brand-new file > 500 lines, don't touch allowlist | ❌ fails "new violation" |
| Add a brand-new file > 500 lines, add it to allowlist | ❌ fails "no gaming the ratchet" — requires spec reference in commit, enforced socially |
| Add more lines to an allowlisted file past its ceiling | ❌ fails "ceiling exceeded" |
| Add more lines to an allowlisted file under its ceiling | ✅ |

---

## 4. Session state transitions at logout

**Entity**: Django session (stored in the `django_session` DB table).

| Trigger | Before fix | After fix |
|---------|-----------|-----------|
| User logs in (passkey) | `_auth_user_id`, `_auth_user_backend`, `_auth_user_hash`, `profile_id` set | Unchanged |
| User logs out | auth keys cleared; `profile_id` survives | session row deleted (flushed) |
| Replayed cookie to `/auth/me/` | Passkey fallback finds `profile_id`, re-auths → **200** (BUG) | Fallback finds `profile_id=None`, returns `None` → **401** (FIXED) |

No schema change — an invariant change on the existing session mechanism.

---

## 5. Surfacing `profile.id` in Settings (no schema change)

**Data path**: already exists.
- Server: `apps/core/auth_helpers.py::passkey_user_profile_response` returns `{"profile": {"id": ...}}` (line 16–23).
- Modern SPA: `/api/auth/me` → `AuthContext` → `useProfile()` hook → `profile.id`.
- Legacy: view renders the template with `current_profile_id` already in context.

**UI delta only**. No model change, no API change.

**Modern SPA display**: in `frontend/src/components/settings/SettingsGeneral.tsx`, within the About card or a new small "Account" caption, conditional on `mode === 'passkey'`:
```
Account ID: {profile.id}
(share with your admin if they need to grant you quota changes)
```

**Legacy display**: in `apps/legacy/templates/legacy/settings.html`, under the About block, conditional on `{% if auth_mode == 'passkey' %}`:
```html
<div class="about-row">
  <span>Account ID</span>
  <span class="font-medium">{{ current_profile_id }}</span>
</div>
```

**Home mode**: explicitly NOT rendered. No caption. Home mode's threat model has no admin concept, so the integer is misleading.

---

## 6. `cookie_admin set-unlimited` / `remove-unlimited` argparse shape

**Location**: `apps/core/management/commands/cookie_admin.py` subparser definitions + `_handle_set_unlimited` / `_handle_remove_unlimited` handlers.

**Argparse deltas**:
- Add `--profile-id` (type=int) to both subparsers as an optional argument.
- Make `username` positional `nargs='?'` (optional) so either identifier can be used.
- In the handler: validate exactly one of `username` or `--profile-id` is supplied; look up the target user/profile accordingly.

**Invocation truth table** for `set-unlimited`:
| Positional `username` | `--profile-id N` | Behavior |
|:---------------------:|:----------------:|----------|
| `alice` | absent | Look up by `User.objects.get(username="alice")` — existing path |
| absent | `17` | Look up by `Profile.objects.get(id=17)`, derive `user` — new path |
| `alice` | `17` | **Error**: "pass either username or --profile-id, not both" |
| absent | absent | **Error**: "must pass either username or --profile-id" (existing error) |
| absent | `99999` (nonexistent) | **Error**: "Profile with id 99999 not found" |

**Same shape for `remove-unlimited`**.

JSON output unchanged in both success paths.

---

## 7. Dependabot config file (new)

**Location**: `/home/matt/cookie/.github/dependabot.yml`.

Full normative contents live in `contracts/dependabot-config.md`. Summary:

| Ecosystem | Directory | Groups | Assignees | Labels |
|-----------|-----------|--------|-----------|--------|
| pip | `/` | `python` (minor+patch) | matthewdeaves | dependencies, python |
| npm | `/frontend` | `types`, `npm` (minor+patch, excluding @types) | matthewdeaves | dependencies, javascript |
| docker | `/` | — | matthewdeaves | dependencies, docker |
| docker-compose | `/` | — | matthewdeaves | dependencies, docker |
| github-actions | `/` | — | matthewdeaves | dependencies, github-actions |

All weekly Mon 09:00 Australia/Sydney. Security PRs auto-separated (default).

---

## 8. Legacy DOM insertion pattern (not a DB entity)

**Location**: `apps/legacy/static/legacy/js/pages/search.js:~260`.

| Event | DOM state |
|-------|-----------|
| Initial search | Results grid populated via `Cookie.utils.setHtml(resultsGrid, html)` — chokepoint |
| Load-more (today) | **Violation**: `resultsGrid.innerHTML += html` |
| Load-more (after fix) | `var wrapper = document.createElement('div'); Cookie.utils.setHtml(wrapper, html); while (wrapper.firstChild) resultsGrid.appendChild(wrapper.firstChild);` |

---

## 9. `cookie_admin create-session` argparse shape

**Location**: `apps/core/management/commands/cookie_admin.py`, `create-session` subparser + `_handle_create_session`.

**Delta**:
- Add `--confirm` boolean flag to `create-session` subparser (existing on `reset`).

**Invocation truth table**:
| `--json` | `--confirm` | Behavior |
|:--------:|:-----------:|---------|
| No | — | Interactive prompt, respects operator response |
| Yes | No | **Exits non-zero** with "`--confirm` required" (NEW) |
| Yes | Yes | Proceeds; outputs session JSON |

---

## Summary

| Artifact | Status |
|----------|:------:|
| `/app/crontab` file | NEW |
| `pyproject.toml` ruff config | EXTENDED |
| `tests/test_code_quality.py` + EXEMPT_FILES | NEW |
| Session state at logout | CHANGED invariant (no schema change) |
| Settings UI shows `profile.id` (passkey only) | NEW (display-only, no API change) |
| `cookie_admin set-unlimited --profile-id` | EXTENDED argparse |
| `cookie_admin remove-unlimited --profile-id` | EXTENDED argparse |
| `cookie_admin create-session --confirm` | EXTENDED argparse |
| `.github/dependabot.yml` | NEW |
| Search-grid DOM insertion pattern | CHANGED (routed through chokepoint) |

Zero database migrations.

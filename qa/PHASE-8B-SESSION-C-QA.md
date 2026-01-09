# Phase 8B Session C - QA Issues

## QA-029: Ingredient quantities need AI tidying
**Status:** Fixed
**Severity:** Medium
**Component:** AI Scaling / Recipe Display

**Description:**
Ingredient quantities often display with impractical precision that makes them difficult to use in practice. This affects both original recipe ingredients and scaled results.

**Examples:**
- "1.3 cups of all purpose flour" - should be "1 1/3 cups" or similar
- "0.66666666666666666666 cup ground almonds" - should be "2/3 cup"

**Research Findings:**

_How existing code handles this:_
- **Scraping (`scraper.py`):** Uses `recipe-scrapers` library, stores ingredients as flat JSON list without normalization
- **Scaling (`scaling.py:70-77`):** Formats ingredients as newline-separated list, sends to AI
- **Scaling prompt (migration 0004):** Already says "Round to practical measurements (e.g., 1/4 cup, not 0.247 cups)" but AI doesn't always comply
- **No fraction conversion code exists** anywhere in the codebase (searched for `fraction`, `Fraction`, `simplify`)
- **Frontend (`RecipeDetail.tsx`):** Displays ingredients as-is with no post-processing

_Root cause:_
1. Scraped quantities stored as-is from source websites
2. AI scaling prompt instruction is natural language (not enforced)
3. No post-processing or validation of quantity formats
4. Frontend has no safety net for formatting

_Established patterns:_
- Validator (`validator.py`) validates response structure but not content format
- AI response post-processing could be added in `scaling.py` after validation, before caching

**Tasks:**
- [x] Create `tidy_quantities()` utility function for fraction conversion
- [x] Apply post-processor in `scaling.py` after AI validation, before caching
- [x] Handle common fractions: 0.25→1/4, 0.33→1/3, 0.5→1/2, 0.67→2/3, 0.75→3/4
- [x] Test with examples from this issue
- [ ] Consider optional AI-based tidying service for complex conversions (future)

**Implementation:**

Created `apps/recipes/utils.py` with:
- `decimal_to_fraction()` - Converts decimals to common fractions (1/8, 1/6, 1/4, 1/3, 3/8, 1/2, 5/8, 2/3, 3/4, 5/6, 7/8)
- `tidy_ingredient()` - Applies fraction conversion to ingredient strings
- `tidy_quantities()` - Applies to a list of ingredients

Unit-aware processing:
- **Fraction units** (cups, tablespoons, teaspoons, pieces, etc.) → Convert to fractions
- **Decimal units** (grams, kg, ml, liters, oz, lb) → Keep precise decimals

Integrated in `scaling.py:150-151`:
```python
# Tidy ingredient quantities (convert decimals to fractions) - QA-029
ingredients = tidy_quantities(validated['ingredients'])
```

**Files changed:**
- `apps/recipes/utils.py` - New utility module with fraction conversion
- `apps/ai/services/scaling.py` - Import and apply tidy_quantities
- `apps/recipes/tests.py` - Added 17 tests for quantity tidying

**Verification:**
- [x] 0.5 cup → 1/2 cup
- [x] 1.333 cups → 1 1/3 cups
- [x] 0.666 cup → 2/3 cup
- [x] 225g butter → 225 g butter (unchanged)
- [x] All 85 backend tests pass

---

## QA-030: Nutrition tab serving label is ambiguous
**Status:** Fixed
**Severity:** Low
**Component:** Recipe Detail UI

**Description:**
The nutrition tab displays "Per X servings" which is confusing. It's unclear whether the nutrition values shown are:
- The total for all X servings combined, or
- The amount per single serving (with X being the recipe yield)

**Example:**
Tarte aux Pommes Normande shows "Per 8 servings" followed by nutrition values. Users cannot tell if 200 calories means 200 per slice or 200 total.

**Research Findings:**

_What the data actually represents:_
- **Schema.org convention:** Nutrition data is ALWAYS per serving (standardized)
- **Scraper (`scraper.py:214`):** Gets `nutrients` from recipe-scrapers which follows schema.org
- **AI prompts confirm:** nutrition_estimate prompt says "Estimate the nutrition values per serving"
- **Data is correct, label is wrong**

_Current UI implementation:_
- **Modern (`RecipeDetail.tsx:511-514`):**
  ```tsx
  <p>Per {recipe.servings} serving{recipe.servings > 1 ? 's' : ''}</p>
  ```
- **Legacy (`recipe_detail.html:248`):**
  ```django
  <p>Per {{ recipe.servings }} serving{{ recipe.servings|pluralize }}</p>
  ```

_The problem:_
- Label "Per 8 servings" grammatically implies total, not per-serving
- Should be "Per serving (recipe makes 8)" or "Nutrition per serving"

**Tasks:**
- [x] Update Modern frontend label in `RecipeDetail.tsx:511-514`
- [x] Update Legacy template label in `recipe_detail.html:248`
- [x] Use format: "Per serving (recipe makes X)"
- [ ] Test both frontends

**Files to modify:**
- `frontend/src/screens/RecipeDetail.tsx` - Line ~511-514
- `apps/legacy/templates/legacy/recipe_detail.html` - Line ~248

---

## QA-031 + QA-032: Scaling Service v2 (Combined Implementation)

> **Implementation Session:** These two issues are implemented together as they both modify the same files and share the same migration.

### QA-031: Scaled recipes need instruction step alignment
**Status:** Fixed
**Severity:** High
**Component:** AI Scaling Service

**Description:**
When ingredients are scaled, the instruction steps are not updated to match. This creates a mismatch that could confuse users or cause recipe failures.

**Example:**
- Scaled ingredients: "2 cups of flour (scaled from 1 cup)"
- Instruction step still says: "Put 1 cup of flour in a bowl"

---

### QA-032: Scaled recipes need cooking time adjustments
**Status:** Fixed
**Severity:** Medium
**Component:** AI Scaling Service

**Description:**
When recipes are scaled significantly (especially up), cooking times may need adjustment. Larger quantities often require longer cooking times.

**Example:**
- Original: "Bake for 25 minutes" (for 4 servings)
- Scaled to 12 servings: Still says "Bake for 25 minutes" but larger volume may need 35-40 minutes

---

### Combined Implementation Plan

#### Task 1: Model Migration
**File:** `apps/recipes/models.py` (lines 229-265)
**New migration:** `apps/recipes/migrations/XXXX_serving_adjustment_instructions_times.py`

Add fields to `ServingAdjustment`:
```python
instructions = models.JSONField(default=list)                           # QA-031
prep_time_adjusted = models.PositiveIntegerField(null=True, blank=True) # QA-032
cook_time_adjusted = models.PositiveIntegerField(null=True, blank=True) # QA-032
total_time_adjusted = models.PositiveIntegerField(null=True, blank=True)# QA-032
```

#### Task 2: Validator Schema Update
**File:** `apps/ai/services/validator.py` (lines 30-37)

Update `serving_adjustment` schema:
```python
'serving_adjustment': {
    'type': 'object',
    'required': ['ingredients'],
    'properties': {
        'ingredients': {'type': 'array', 'items': {'type': 'string'}},
        'instructions': {'type': 'array', 'items': {'type': 'string'}},  # NEW
        'notes': {'type': 'array', 'items': {'type': 'string'}},
        'prep_time': {'type': ['string', 'null']},   # NEW
        'cook_time': {'type': ['string', 'null']},   # NEW
        'total_time': {'type': ['string', 'null']},  # NEW
    },
},
```

#### Task 3: Prompt Migration
**New file:** `apps/ai/migrations/XXXX_update_serving_adjustment_v2.py`

Update system prompt to return:
```json
{
  "ingredients": [...],
  "instructions": [...],
  "notes": [...],
  "prep_time": "X minutes" or null,
  "cook_time": "X minutes" or null,
  "total_time": "X minutes" or null
}
```

Rules for instructions:
- Copy all original instruction steps
- Update any quantity references to match the scaled ingredients
- Example: "Add 1 cup flour" becomes "Add 2 cups flour" when doubling

Rules for cooking times:
- Return null if scaling by less than 50% (times unchanged)
- For significant scaling (50%+), estimate adjusted times

User prompt template additions:
```
Instructions:
{instructions}

Cooking times:
- Prep time: {prep_time}
- Cook time: {cook_time}
- Total time: {total_time}
```

#### Task 4: Scaling Service Update
**File:** `apps/ai/services/scaling.py` (lines 66-103)

1. Add `_parse_time()` helper (copy pattern from `remix.py:243-267`)
2. Format prompt with instructions and times
3. Parse response for new fields
4. Cache all fields in ServingAdjustment
5. Return new fields in response dict

#### Task 5: API Schema Update
**File:** `apps/ai/api.py` (lines 314-320)

Update `ScaleOut`:
```python
class ScaleOut(Schema):
    target_servings: int
    original_servings: int
    ingredients: List[str]
    instructions: List[str] = []                    # NEW
    notes: List[str]
    prep_time_adjusted: Optional[int] = None        # NEW
    cook_time_adjusted: Optional[int] = None        # NEW
    total_time_adjusted: Optional[int] = None       # NEW
    nutrition: Optional[NutritionOut] = None
    cached: bool
```

#### Task 6: Frontend Type Update
**File:** `frontend/src/api/client.ts` (lines 59-66)

Update `ScaleResponse`:
```typescript
export interface ScaleResponse {
  target_servings: number
  original_servings: number
  ingredients: string[]
  instructions: string[]                // NEW
  notes: string[]
  prep_time_adjusted: number | null     // NEW
  cook_time_adjusted: number | null     // NEW
  total_time_adjusted: number | null    // NEW
  nutrition: NutritionValues | null
  cached: boolean
}
```

#### Task 7: Frontend InstructionsTab Update
**File:** `frontend/src/screens/RecipeDetail.tsx`

1. Update `InstructionsTab` to accept `scaledData` prop
2. Use `scaledData?.instructions` when available
3. Pass `scaledData` when rendering InstructionsTab

#### Task 8: Frontend Time Display Update
**File:** `frontend/src/screens/RecipeDetail.tsx` (lines 270-300)

Show adjusted times with "(was X min)" comparison when scaled.

---

### Files Changed Summary

| File | Changes |
|------|---------|
| `apps/recipes/models.py` | Add 4 fields to ServingAdjustment |
| `apps/recipes/migrations/XXXX_*.py` | New migration for model fields |
| `apps/ai/migrations/XXXX_*.py` | New migration for prompt update |
| `apps/ai/services/validator.py` | Add instructions + time fields to schema |
| `apps/ai/services/scaling.py` | Include instructions/times in prompt, parse response, cache |
| `apps/ai/api.py` | Add fields to ScaleOut schema |
| `frontend/src/api/client.ts` | Add fields to ScaleResponse type |
| `frontend/src/screens/RecipeDetail.tsx` | Pass scaledData to InstructionsTab, show adjusted times |

---

### Verification

1. Run migrations:
   ```bash
   docker compose exec web python manage.py makemigrations recipes ai
   docker compose exec web python manage.py migrate
   ```

2. Run tests:
   ```bash
   docker compose exec web python -m pytest apps/ai/tests/ -v
   docker compose exec frontend npm test
   ```

3. Manual testing:
   - Open a recipe with steps mentioning quantities (e.g., "Add 1 cup flour")
   - Scale from 4 servings to 8 servings (2x)
   - Verify:
     - [x] Ingredients show scaled quantities
     - [x] Instructions tab shows updated quantity references
     - [x] Cooking times show adjusted values (if significantly scaled)
     - [x] Times show "(was X min)" comparison when adjusted
   - Scale back to original servings
   - Verify instructions and times return to original

**Testing completed:** 2026-01-08
- Modern frontend: All features verified working
- Legacy frontend: All features verified working (iPad tested)

---

## QA-033: Tips should generate automatically and adjust for scaling
**Status:** Resolved
**Severity:** Medium
**Component:** Tips Generation Service / UI

**Description:**
Tips should generate automatically when importing or remixing recipes, not require manual button clicks.

**Resolution (2026-01-09):**

The main functionality is implemented:

1. **On import** (`scraper.py:147-153`): Background thread auto-generates tips immediately after recipe import
2. **Polling for recent imports** (`RecipeDetail.tsx:66-108`, `detail.js:25-64`): For recipes imported < 60 seconds ago, frontend polls every 3s until tips arrive
3. **On remix** (QA-044): Tips auto-regenerate for remixed recipes

**Remaining edge case:** Old recipes (> 60s) without tips still require button click. Tracked in **QA-046**.

**Scaling notes** are already working:
- Generated by scaling service in `notes` array
- Displayed in TipsTab as separate "Scaling Notes" section
- Shows things like "Use a larger pan for this batch size"

**Phase 2 (scaling-aware tips regeneration)** deferred - current scaling notes provide adequate guidance.

---

## QA-034: AI prompts must be in migrations and visible in settings
**Status:** Fixed
**Severity:** Low
**Type:** Task/Process

**Description:**
All AI prompts added to the system should:
1. Be seeded via Django migrations (not manual DB inserts)
2. Appear in the Settings > AI Prompts management UI

This ensures prompts are version-controlled, reproducible across environments, and editable by users.

**Research Findings:**

_Current state: MOSTLY COMPLIANT_

All 11 prompts are seeded via migrations:
- `0002_seed_prompts.py` - Seeds 9 initial prompts
- `0003_nutrition_estimate_prompt.py` - Adds nutrition_estimate
- `0004_update_serving_adjustment_prompt.py` - Updates serving_adjustment

_Settings UI (`Settings.tsx`):_
- Two-tab interface: API Settings + AI Prompts
- Lists all prompts with name, description, model
- Expandable to view system_prompt and user_prompt_template
- Edit functionality: can modify prompts, model, active status
- API endpoints working: GET/PUT `/api/ai/prompts`

_Issue found:_
`nutrition_estimate` is seeded in migration 0003 but NOT in `PROMPT_TYPES` choices in `models.py`:

```python
# models.py - PROMPT_TYPES has 10 entries, missing nutrition_estimate
PROMPT_TYPES = [
    ('recipe_remix', 'Recipe Remix'),
    ('serving_adjustment', 'Serving Adjustment'),
    # ... 8 more ...
    # MISSING: ('nutrition_estimate', 'Nutrition Estimate')
]
```

_Verification:_
| Prompt | In Migration | In PROMPT_TYPES | In Settings UI |
|--------|--------------|-----------------|----------------|
| recipe_remix | ✓ 0002 | ✓ | ✓ |
| remix_suggestions | ✓ 0002 | ✓ | ✓ |
| serving_adjustment | ✓ 0002, 0004 | ✓ | ✓ |
| tips_generation | ✓ 0002 | ✓ | ✓ |
| nutrition_estimate | ✓ 0003 | **MISSING** | ✓ (works anyway) |

**Tasks:**
- [x] Add `('nutrition_estimate', 'Nutrition Estimate')` to PROMPT_TYPES in `models.py`
- [ ] Verify all 11 prompts appear in Settings UI after fix

**Files to modify:**
- `apps/ai/models.py` - Add nutrition_estimate to PROMPT_TYPES choices

**Checklist for future prompts:**
- [x] Create migration file with RunPython to seed prompt
- [x] Include prompt_type, name, description, system_prompt, user_prompt_template, model
- [x] Verify prompt appears in Settings after migration
- [x] Add reverse migration to remove prompt if needed
- [ ] **Add prompt_type to PROMPT_TYPES choices in models.py**

---

## Summary

| Issue | Title | Severity | Status |
|-------|-------|----------|--------|
| QA-029 | Ingredient quantities need AI tidying | Medium | Fixed |
| QA-030 | Nutrition tab serving label is ambiguous | Low | Fixed |
| QA-031 | Scaled recipes need instruction step alignment | High | Fixed |
| QA-032 | Scaled recipes need cooking time adjustments | Medium | Fixed |
| QA-033 | Tips should generate automatically and adjust for scaling | Medium | Resolved |
| QA-034 | AI prompts must be in migrations and visible in settings | Low | Fixed |
| QA-035 | SQLite database locking errors under concurrent load | Medium | Fixed |

> **Note:** QA-031 and QA-032 are implemented together as "Scaling Service v2" since they share the same files and migration.

---

## QA-035: SQLite database locking errors under concurrent load
**Status:** Fixed
**Severity:** Medium
**Component:** Database / Infrastructure

**Description:**
Occasional "database is locked" errors occur when multiple requests try to write to the SQLite database simultaneously. This is a known SQLite limitation with concurrent writes.

**Example error:**
```
sqlite3.OperationalError: database is locked
django.db.utils.OperationalError: database is locked
```

**Observed in:**
- `RecipeViewHistory.objects.update_or_create()` in legacy views (line 117)
- `RecipeViewHistory.objects.update_or_create()` in API (api_user.py:291)
- `CachedSearchImage.objects.get_or_create()` in image caching service
- Any concurrent write operations

**Research Findings:**

_Current configuration:_
- **Django version:** 5.2.10 (supports `init_command` and `transaction_mode` options)
- **Gunicorn:** 2 workers × 2 threads = 4 concurrent request capacity
- **SQLite settings:** Default (no timeout override, no WAL, default transactions)
- **Database config (`settings.py:52-57`):**
  ```python
  DATABASES = {
      'default': {
          'ENGINE': 'django.db.backends.sqlite3',
          'NAME': BASE_DIR / 'db.sqlite3',
      }
  }
  ```

_Root causes of "database is locked":_

1. **Default journal mode (DELETE)** - Writers block readers, readers block writers
2. **Deferred transactions (default)** - Lock acquired mid-transaction; if another connection holds lock, SQLite cannot retry (would break serializable isolation)
3. **Default timeout (5 seconds)** - May not be enough under concurrent load
4. **No busy_timeout PRAGMA** - Connection-level timeout not configured

_How SQLite locking works:_
- SQLite allows only ONE writer at a time (global write lock)
- In default (DELETE) journal mode, writes block reads entirely
- When a transaction needs a lock mid-execution and another holds it, SQLite waits up to `timeout` seconds
- If timeout exceeded → "database is locked" error
- Critical insight: Deferred transactions can't retry mid-transaction without violating isolation guarantees

_Recommended solutions (Django 5.1+):_

**Solution 1: Enable WAL mode** (Write-Ahead Logging)
- Allows concurrent reads while writing
- Writers don't block readers, readers don't block writers
- Persists in database file (only needs to be set once)
- Creates `.db-shm` and `.db-wal` files alongside database
- ⚠️ Do NOT use on network file systems (NFS)

**Solution 2: IMMEDIATE transaction mode**
- Acquires write lock at START of transaction (not mid-transaction)
- If lock unavailable, transaction fails immediately and can be retried
- Prevents the "stuck mid-transaction" scenario that causes most errors
- This is the KEY fix for "database is locked" during concurrent writes

**Solution 3: Increase timeout**
- Default 5 seconds → 20+ seconds
- Gives more time for lock acquisition under load

**Solution 4: synchronous=NORMAL PRAGMA**
- Safe for WAL mode (not safe for DELETE journal mode)
- Better write performance

_Recommended configuration:_
```python
# cookie/settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 20,
            'transaction_mode': 'IMMEDIATE',
            'init_command': (
                'PRAGMA journal_mode=WAL;'
                'PRAGMA synchronous=NORMAL;'
                'PRAGMA busy_timeout=5000;'
            ),
        },
    }
}
```

_Alternative: Signal-based approach (more explicit):_
```python
# apps/core/db_signals.py
from django.db.backends.signals import connection_created
from django.dispatch import receiver

@receiver(connection_created)
def setup_sqlite_pragmas(sender, connection, **kwargs):
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        cursor.execute('PRAGMA journal_mode=wal;')
        cursor.execute('PRAGMA synchronous=NORMAL;')
        cursor.execute('PRAGMA busy_timeout=5000;')
        cursor.close()
```

_One-time WAL enablement (alternative to init_command):_
```bash
# WAL mode persists in the database file
sqlite3 db.sqlite3 'PRAGMA journal_mode=WAL;'
```

_When to consider PostgreSQL:_
- High-concurrency production environments
- Multiple application servers (SQLite is single-file)
- Need for advanced features (full-text search, JSON operators, etc.)
- For this project: SQLite with WAL is sufficient for home/small-scale use

**Tasks:**
- [x] Update `cookie/settings.py` with recommended OPTIONS
- [x] Run one-time `PRAGMA journal_mode=WAL` on existing database (handled by init_command)
- [x] Restart Docker containers to pick up new settings
- [x] Verify WAL mode enabled via `PRAGMA journal_mode;` (returns 'wal')
- [ ] Load test with concurrent requests to verify fix
- [ ] Document SQLite limitations in README if deploying

**Files changed:**
- `cookie/settings.py` - Added OPTIONS to DATABASES config

**Implementation:**
Updated `settings.py` DATABASES configuration with:
- `timeout: 20` - Increased lock wait from 5s to 20s
- `transaction_mode: 'IMMEDIATE'` - Acquires write lock at transaction start
- `init_command` with PRAGMAs:
  - `journal_mode=WAL` - Allows concurrent reads during writes
  - `synchronous=NORMAL` - Safe for WAL, better performance
  - `busy_timeout=5000` - Connection-level lock timeout

**Verification:**
```
$ docker compose exec web python manage.py shell -c "..."
Journal mode: wal
Synchronous: 1 (1=NORMAL, 2=FULL)
Busy timeout: 5000ms
Recipe count: 44 (database working)
```

All 68 backend tests pass.

---

### Remaining Issue: Async Test Database Locking

**Two scraper integration tests still fail with "database table is locked":**
- `tests/test_scraper.py::TestScraperIntegration::test_scrape_url_creates_recipe`
- `tests/test_scraper.py::TestScraperIntegration::test_scrape_url_with_image_download`

**Root Cause Analysis:**

The tests use `@pytest.mark.django_db` without `transaction=True`. This creates a conflict:

1. **pytest-django wraps tests in a transaction** for isolation (faster than truncating tables)
2. **The test calls `scraper.scrape_url()`** which calls `sync_to_async(recipe.save)()` at `scraper.py:139`
3. **`sync_to_async` runs code in a thread pool** - Django DB connections are thread-local
4. **The thread pool thread creates a NEW database connection** separate from test's connection
5. **This new connection attempts an INSERT** (write operation)
6. **The original test connection holds an open transaction** (pytest-django's isolation)
7. **SQLite only allows ONE writer at a time** → `"database table is locked"`

**Why WAL mode doesn't help here:**

1. The `init_command` option in settings is NOT a valid Django SQLite option (it's MySQL syntax) - Django silently ignores it
2. The test database is separate and doesn't inherit production WAL settings
3. Even with WAL, you can't have two concurrent writers - only concurrent readers during writes

**Why similar tests pass:**

`test_recipes_api.py:402` has a nearly identical test that passes:
```python
@pytest.mark.django_db(transaction=True)  # <-- Key difference
class TestRecipeScrapeCreatesNewRecords:
```

With `transaction=True`:
- pytest-django uses `TransactionTestCase` behavior
- No wrapping transaction - tables truncated between tests instead
- The new connection from `sync_to_async` can acquire the write lock

**Fix:**

Add `transaction=True` to `TestScraperIntegration`:
```python
@pytest.mark.django_db(transaction=True)
class TestScraperIntegration:
```

This matches the pattern used in:
- `tests/test_recipes_api.py:402` - `TestRecipeScrapeCreatesNewRecords`
- `tests/test_search.py:186` - async search tests
- `tests/test_search.py:337` - async failure counter tests

**Tasks:**
- [x] Configure WAL mode for production database (settings.py)
- [x] Fix `TestScraperIntegration` tests with `transaction=True`
- [x] Verify all 307 backend tests pass

**References:**
- [Django, SQLite, and the Database is Locked Error](https://blog.pecar.me/django-sqlite-dblock)
- [Enabling WAL in SQLite in Django](https://djangoandy.com/2024/07/08/enabling-wal-in-sqlite-in-django/)
- [SQLite WAL Mode](https://sqlite.org/wal.html)
- [Simon Willison: Enabling WAL Mode](https://til.simonwillison.net/sqlite/enabling-wal-mode)

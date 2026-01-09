# Phase 8B Session C - QA Issues

## QA-029: Ingredient quantities need AI tidying
**Status:** Open (Researched)
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
- [ ] Create `tidy_quantities()` utility function for fraction conversion
- [ ] Apply post-processor in `scaling.py` after AI validation, before caching
- [ ] Handle common fractions: 0.25→1/4, 0.33→1/3, 0.5→1/2, 0.67→2/3, 0.75→3/4
- [ ] Consider optional AI-based tidying service for complex conversions
- [ ] Test with examples from this issue

**Additional insight (from QA testing):**
- **Discrete/practical units** (onions, eggs, cups, tablespoons) should round to halves (1, 1½, 2)
- **Continuous/weight units** (grams, kg, ounces, ml) can scale precisely (225g, 340g)
- Update AI prompt to be smarter about unit-appropriate rounding

**Files to modify:**
- `apps/ai/services/scaling.py` - Add post-processing
- `apps/recipes/utils.py` (new) - Create tidy_quantities utility

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
**Status:** Open (Researched)
**Severity:** Medium
**Component:** Tips Generation Service / UI

**Description:**
Currently users must manually click "Generate Tips" button to get cooking tips. This is not intuitive - tips should be generated automatically when viewing the Tips tab or recipe detail.

Additionally, when a recipe is scaled, the tips should be regenerated or adjusted to reflect the scaled quantities (e.g., "use a larger pan" when doubling a recipe).

**Research Findings:**

_Current tips flow (`tips.py`):_
1. `generate_tips(recipe_id)` - no scaling context accepted
2. Checks `recipe.ai_tips` cache (single global cache per recipe)
3. If not cached, calls AI with recipe title, ingredients, instructions
4. Caches result in `Recipe.ai_tips` field
5. Returns `{tips: [], cached: bool}`

_Frontend flow (`RecipeDetail.tsx`):_
- Tips loaded from `recipe.ai_tips` on initial load
- `handleGenerateTips()` only called on button click
- TipsTab shows "Generate Tips" button if `tips.length === 0`
- No auto-trigger on tab view

_Caching comparison:_
| Feature | Tips | Scaling |
|---------|------|---------|
| Model | Recipe.ai_tips (single field) | ServingAdjustment (separate table) |
| Per-profile | No | Yes |
| Per-servings | No | Yes |
| Scaling-aware | No | N/A |

_Scaling notes (already working):_
- Generated by scaling service in `notes` array
- Displayed in TipsTab as separate "Scaling Notes" section
- Shows things like "Use a larger pan for this batch size"

**Tasks:**

Phase 1 - Auto-generation:
- [ ] Add useEffect to auto-trigger `handleGenerateTips()` when Tips tab becomes active
- [ ] Only trigger if `tips.length === 0 && aiAvailable && !tipsLoading`
- [ ] Show loading spinner during generation

Phase 2 - Scaling-aware tips:
- [ ] Extend `generate_tips()` to accept optional `target_servings` parameter
- [ ] Update tips_generation prompt to include scaling context if provided
- [ ] Create RecipeTips model for per-profile, per-serving caching (like ServingAdjustment)
- [ ] Add "Regenerate for current serving" button when scaled
- [ ] Update API endpoint to accept optional target_servings

**Files to modify:**

Phase 1:
- `frontend/src/screens/RecipeDetail.tsx` - Add useEffect for auto-generation

Phase 2:
- `apps/recipes/models.py` - Add RecipeTips model
- `apps/ai/services/tips.py` - Accept target_servings parameter
- `apps/ai/api.py` - Update TipsIn schema and endpoint
- `apps/ai/migrations/` - Migration for new model + prompt update
- `frontend/src/screens/RecipeDetail.tsx` - Add regenerate button

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
| QA-029 | Ingredient quantities need AI tidying | Medium | Researched |
| QA-030 | Nutrition tab serving label is ambiguous | Low | Fixed |
| QA-031 | Scaled recipes need instruction step alignment | High | Fixed |
| QA-032 | Scaled recipes need cooking time adjustments | Medium | Fixed |
| QA-033 | Tips should generate automatically and adjust for scaling | Medium | Researched |
| QA-034 | AI prompts must be in migrations and visible in settings | Low | Fixed |
| QA-035 | SQLite database locking errors under concurrent load | Medium | Researched |

> **Note:** QA-031 and QA-032 are implemented together as "Scaling Service v2" since they share the same files and migration.

---

## QA-035: SQLite database locking errors under concurrent load
**Status:** Researched
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
- [ ] Update `cookie/settings.py` with recommended OPTIONS
- [ ] Run one-time `PRAGMA journal_mode=WAL` on existing database
- [ ] Restart Docker containers to pick up new settings
- [ ] Verify `.db-wal` and `.db-shm` files created
- [ ] Load test with concurrent requests to verify fix
- [ ] Document SQLite limitations in README if deploying

**Files to modify:**
- `cookie/settings.py` - Add OPTIONS to DATABASES config

**References:**
- [Django, SQLite, and the Database is Locked Error](https://blog.pecar.me/django-sqlite-dblock)
- [Enabling WAL in SQLite in Django](https://djangoandy.com/2024/07/08/enabling-wal-in-sqlite-in-django/)
- [SQLite WAL Mode](https://sqlite.org/wal.html)
- [Simon Willison: Enabling WAL Mode](https://til.simonwillison.net/sqlite/enabling-wal-mode)

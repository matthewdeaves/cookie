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

**Files to modify:**
- `apps/ai/services/scaling.py` - Add post-processing
- `apps/recipes/utils.py` (new) - Create tidy_quantities utility

---

## QA-030: Nutrition tab serving label is ambiguous
**Status:** Open (Researched)
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
- [ ] Update Modern frontend label in `RecipeDetail.tsx:511-514`
- [ ] Update Legacy template label in `recipe_detail.html:248`
- [ ] Use format: "Per serving (recipe makes X)" or "Nutrition per serving"
- [ ] Test both frontends

**Files to modify:**
- `frontend/src/screens/RecipeDetail.tsx` - Line ~511-514
- `apps/legacy/templates/legacy/recipe_detail.html` - Line ~248

---

## QA-031: Scaled recipes need instruction step alignment
**Status:** Open (Researched)
**Severity:** High
**Component:** AI Scaling Service

**Description:**
When ingredients are scaled, the instruction steps are not updated to match. This creates a mismatch that could confuse users or cause recipe failures.

**Example:**
- Scaled ingredients: "2 cups of flour (scaled from 1 cup)"
- Instruction step still says: "Put 1 cup of flour in a bowl"

**Research Findings:**

_Current scaling service flow (`scaling.py`):_
1. Get recipe, check cache (ServingAdjustment model)
2. Format only `{ingredients}`, `{original_servings}`, `{new_servings}` for AI
3. **Instructions are NOT included in the prompt**
4. Validate response expects only `ingredients` and `notes` arrays
5. Cache in ServingAdjustment (no instructions field)
6. Return to frontend

_Frontend display (`RecipeDetail.tsx`):_
- `IngredientsTab` uses `scaledData?.ingredients || recipe.ingredients`
- `InstructionsTab` ALWAYS uses `recipe.instructions` (never scaled)
- No `scaledData` parameter passed to InstructionsTab

_Database model (`models.py`):_
```python
class ServingAdjustment(models.Model):
    ingredients = models.JSONField(default=list)
    notes = models.JSONField(default=list)
    # NO instructions field
```

_Validator schema (`validator.py:30-37`):_
```python
'serving_adjustment': {
    'required': ['ingredients'],
    'properties': {
        'ingredients': {...},
        'notes': {...},
        # NO instructions property
    },
}
```

**Tasks:**
- [ ] Add `instructions` field to ServingAdjustment model (migration)
- [ ] Update serving_adjustment prompt to include `{instructions}` placeholder
- [ ] Update prompt rules: "Update quantity references in steps to match scaled ingredients"
- [ ] Update validator schema to include optional `instructions` array
- [ ] Update `scaling.py` to pass instructions to AI and cache response
- [ ] Update API schema (`ScaleOut`) to include instructions
- [ ] Update frontend `ScaleResponse` type
- [ ] Update `InstructionsTab` to accept and use `scaledData`
- [ ] Test: "Add 1 cup flour" → "Add 2 cups flour" when doubled

**Files to modify:**
- `apps/recipes/models.py` - Add instructions field to ServingAdjustment
- `apps/ai/migrations/` - New migration for prompt update
- `apps/ai/services/validator.py` - Add instructions to schema
- `apps/ai/services/scaling.py` - Include instructions in prompt and response
- `apps/ai/api.py` - Update ScaleOut schema
- `frontend/src/api/client.ts` - Update ScaleResponse type
- `frontend/src/screens/RecipeDetail.tsx` - Pass scaledData to InstructionsTab

---

## QA-032: Scaled recipes need cooking time adjustments
**Status:** Open (Researched)
**Severity:** Medium
**Component:** AI Scaling Service

**Description:**
When recipes are scaled significantly (especially up), cooking times may need adjustment. Larger quantities often require longer cooking times, different temperatures, or technique modifications.

**Example:**
- Original: "Bake for 25 minutes" (for 4 servings)
- Scaled to 12 servings: Still says "Bake for 25 minutes" but larger volume may need 35-40 minutes

**Research Findings:**

_Current time storage (`models.py`):_
```python
class Recipe(models.Model):
    prep_time = models.PositiveIntegerField(null=True)   # minutes
    cook_time = models.PositiveIntegerField(null=True)   # minutes
    total_time = models.PositiveIntegerField(null=True)  # minutes
```

_Current scaling prompt (migration 0004):_
- Mentions "Add notes about cooking time adjustments if scaling significantly"
- But does NOT receive actual cooking times as context
- Notes returned as strings, not structured time values

_Existing time parsing (`remix.py`):_
```python
def _parse_time(time_str: str | None) -> int | None:
    """Parse a time string like '30 minutes' into minutes."""
    # Already implemented and working for remix service
```

_ServingAdjustment model:_
- No fields for adjusted times
- Only stores `ingredients` and `notes`

_Notes infrastructure:_
- Working: notes cached in ServingAdjustment.notes
- Displayed in TipsTab as "Scaling Notes" section
- First note shown as toast notification

**Tasks:**
- [ ] Add time fields to ServingAdjustment: `prep_time_adjusted`, `cook_time_adjusted`, `total_time_adjusted`
- [ ] Update scaling prompt to include original times as context
- [ ] Update prompt to return adjusted times (or null if unchanged)
- [ ] Update validator schema for optional time fields
- [ ] Reuse `_parse_time()` helper from remix.py (or extract to shared utils)
- [ ] Update API response schema with adjusted times
- [ ] Update frontend to display adjusted times with comparison to original
- [ ] Test with significant scaling (2x, 3x) on baked goods

**Files to modify:**
- `apps/recipes/models.py` - Add time fields to ServingAdjustment
- `apps/ai/migrations/` - Migration for model + prompt update
- `apps/ai/services/validator.py` - Add time fields to schema
- `apps/ai/services/scaling.py` - Pass times to AI, parse response
- `apps/ai/api.py` - Update ScaleOut schema
- `frontend/src/api/client.ts` - Update ScaleResponse type
- `frontend/src/screens/RecipeDetail.tsx` - Display adjusted times

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
**Status:** Open (Researched) - Mostly Compliant
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
- [ ] Add `('nutrition_estimate', 'Nutrition Estimate')` to PROMPT_TYPES in `models.py`
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
| QA-030 | Nutrition tab serving label is ambiguous | Low | Researched |
| QA-031 | Scaled recipes need instruction step alignment | High | Researched |
| QA-032 | Scaled recipes need cooking time adjustments | Medium | Researched |
| QA-033 | Tips should generate automatically and adjust for scaling | Medium | Researched |
| QA-034 | AI prompts must be in migrations and visible in settings | Low | Researched |

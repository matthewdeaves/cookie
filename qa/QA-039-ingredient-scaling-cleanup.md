# QA-039: AI Ingredient Scaling Produces Impractical Results

## Issue

When scaling recipes, the AI produces mathematically correct but practically nonsensical ingredient quantities.

### Example
- **Original:** `1 unbaked pizza crusts` (recipe for 1 serving)
- **Scaled to 2 servings:** `1 1/8 unbaked pizza crusts (scaled from 1)`

### Problems
1. You cannot have 1/8 of a pizza crust - it's an indivisible item
2. The scaling should recognize countable/indivisible items and round sensibly
3. Similar issues likely affect: eggs, bread slices, tortillas, etc.

## Current Implementation

### Existing Tidying Logic
Location: `apps/recipes/utils.py:114-181`

The `tidy_ingredient()` function handles:
- Converting decimals to fractions (0.666 → 2/3)
- Keeping precise units as-is (grams, ml)

**What it doesn't handle:**
- Recognizing indivisible items (eggs, crusts, slices)
- Rounding to practical quantities
- Contextual awareness of what makes sense

### Scaling Service
Location: `apps/ai/services/scaling.py`

The scaling service calls the AI and uses `tidy_quantities()` to clean up results, but the AI itself is producing impractical outputs.

## Proposed Solutions

### Option A: Improve AI Prompt (Recommended)
Update the `serving_adjustment` prompt in `AIPrompt` model to include:
- Instructions to identify indivisible items
- Round indivisible items to nearest whole number
- Add notes when scaling creates impractical quantities
- Example: "Recipe calls for 1 egg but 1.5 would be needed - suggest using 2 eggs"

### Option B: Post-Processing Cleanup
Add a cleanup step after AI response:
- Maintain list of indivisible item patterns (egg, crust, slice, tortilla, etc.)
- Detect fractions of indivisible items
- Round to nearest whole number
- Add note explaining adjustment

### Option C: New AI Feature - Ingredient Tidying
Create dedicated `ingredient_tidy` prompt that:
- Reviews scaled ingredients for practicality
- Adjusts impractical quantities
- Provides cooking notes for significant adjustments

## Related Files

| File | Purpose |
|------|---------|
| `apps/ai/services/scaling.py` | Main scaling logic |
| `apps/recipes/utils.py` | `tidy_ingredient()` function |
| `apps/ai/models.py` | `AIPrompt` model with `serving_adjustment` prompt |

## Acceptance Criteria

- [ ] Indivisible items (eggs, crusts, slices, etc.) scale to whole numbers
- [ ] Notes explain when rounding was applied
- [ ] Common countable items are handled gracefully
- [ ] Existing decimal-to-fraction tidying still works

## Priority

Low - UX improvement, not blocking core functionality

## Phase

Future - To be addressed in polish/QA phase

---

## Research Findings

### Current Data Flow

```
Recipe with ingredients
    ↓
scale_recipe() calls AI (apps/ai/services/scaling.py:137-144)
    ↓
AI returns: "1.125 unbaked pizza crusts (scaled from 1)"
    ↓
tidy_quantities() processes it (line 151)
    ↓
tidy_ingredient() converts decimal to fraction
    ↓
Result: "1 1/8 unbaked pizza crusts" (mathematically correct, practically wrong)
```

### AI Prompt Analysis

**Current prompt:** `apps/ai/migrations/0005_update_serving_adjustment_v2.py:12-69`

The system prompt includes:
```
Rules for ingredients:
- Round to practical measurements (e.g., 1/4 cup, not 0.247 cups)
```

**Problem:** No guidance on handling indivisible items. The AI treats pizza crusts the same as cups of flour.

### Solution Analysis

#### Option A: Improve AI Prompt (RECOMMENDED)

**Why this is best:**
- Fixes at the source - AI generates correct output
- No fragile pattern matching code needed
- Single migration update
- All future scalings benefit automatically
- AI can provide intelligent notes about rounding

**Implementation:** Create new migration to update `serving_adjustment` prompt:

```python
# Add to system_prompt after existing "Rules for ingredients:"

Rules for indivisible items:
- Identify items that cannot be fractionally used: eggs, pizza crusts,
  bread slices, tortillas, steaks, chicken breasts, loaves, etc.
- Round quantities of indivisible items to the nearest whole number
- Round UP when insufficient quantity affects the dish
  (e.g., 1.4 eggs → 2 eggs, 0.6 crusts → 1 crust)
- In notes, explain if rounding was applied: "Rounded eggs from 1.5 to 2"
```

#### Option B: Post-Processing Cleanup (NOT RECOMMENDED)

**Problems:**
- Requires maintaining pattern list (eggs, crusts, etc.)
- Pattern matching is fragile ("duck eggs"? "tortilla chips"?)
- Happens AFTER AI, so cleaning up bad data
- More complex regex/parsing code

#### Option C: New AI Feature (NOT RECOMMENDED)

**Problems:**
- Doubles API calls (scale → then tidy)
- Increased latency and cost
- Overkill for what should be in initial prompt

### Files Reference

| File | Lines | Purpose |
|------|-------|---------|
| `apps/ai/services/scaling.py` | 56-186 | Main `scale_recipe()` function |
| `apps/ai/services/scaling.py` | 137-144 | AI call |
| `apps/ai/services/scaling.py` | 151 | `tidy_quantities()` call |
| `apps/recipes/utils.py` | 114-169 | `tidy_ingredient()` function |
| `apps/ai/migrations/0005_update_serving_adjustment_v2.py` | 12-69 | Current AI prompt |
| `apps/ai/services/validator.py` | 30-41 | Response validation schema |

### Implementation Plan

1. Create new migration `0007_update_serving_adjustment_indivisible.py`
2. Add indivisible item rules to system prompt
3. Test with sample recipes containing eggs, crusts, slices
4. Verify existing decimal-to-fraction tidying still works

### Notes

This could be combined with QA-029 (ingredient quantity tidying) which already addresses some formatting issues. The scaling prompt may need enhancement to produce more practical outputs from the start rather than relying on post-processing.

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

## Notes

This could be combined with QA-029 (ingredient quantity tidying) which already addresses some formatting issues. The scaling prompt may need enhancement to produce more practical outputs from the start rather than relying on post-processing.

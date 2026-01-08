# Phase 8B Session C - QA Issues

## QA-029: Ingredient quantities need AI tidying
**Status:** Open
**Severity:** Medium
**Component:** AI Scaling / Recipe Display

**Description:**
Ingredient quantities often display with impractical precision that makes them difficult to use in practice. This affects both original recipe ingredients and scaled results.

**Examples:**
- "1.3 cups of all purpose flour" - should be "1 1/3 cups" or similar
- "0.66666666666666666666 cup ground almonds" - should be "2/3 cup"

**Root Cause:**
Either mathematical calculations are producing raw float values, or scraped recipes contain these values and aren't being normalized.

**Proposed Solution:**
Create an AI prompt/service to "tidy" ingredient quantities:
- Convert decimal values to practical fractions (1/4, 1/3, 1/2, 2/3, 3/4)
- Round to sensible precision
- Use appropriate units for the quantity (e.g., switch from cups to tablespoons for small amounts)

---

## QA-030: Nutrition tab serving label is ambiguous
**Status:** Open
**Severity:** Low
**Component:** Recipe Detail UI

**Description:**
The nutrition tab displays "Per X servings" which is confusing. It's unclear whether the nutrition values shown are:
- The total for all X servings combined, or
- The amount per single serving (with X being the recipe yield)

**Example:**
Tarte aux Pommes Normande shows "Per 8 servings" followed by nutrition values. Users cannot tell if 200 calories means 200 per slice or 200 total.

**Proposed Solution:**
Change label to be explicit:
- "Nutrition per serving (recipe makes 8)" or
- "Per 1 serving" with serving count shown separately

---

## QA-031: Scaled recipes need instruction step alignment
**Status:** Open
**Severity:** High
**Component:** AI Scaling Service

**Description:**
When ingredients are scaled, the instruction steps are not updated to match. This creates a mismatch that could confuse users or cause recipe failures.

**Example:**
- Scaled ingredients: "2 cups of flour (scaled from 1 cup)"
- Instruction step still says: "Put 1 cup of flour in a bowl"

**Proposed Solution:**
Extend the scaling service to:
1. Include instruction steps in the AI prompt
2. Have AI update any quantity references in steps to match scaled ingredients
3. Return updated instructions alongside scaled ingredients

---

## QA-032: Scaled recipes need cooking time adjustments
**Status:** Open
**Severity:** Medium
**Component:** AI Scaling Service

**Description:**
When recipes are scaled significantly (especially up), cooking times may need adjustment. Larger quantities often require longer cooking times, different temperatures, or technique modifications.

**Example:**
- Original: "Bake for 25 minutes" (for 4 servings)
- Scaled to 12 servings: Still says "Bake for 25 minutes" but larger volume may need 35-40 minutes

**Proposed Solution:**
Extend the scaling service to:
1. Include cooking times in the AI prompt context
2. Have AI assess if time adjustments are needed based on scale factor
3. Return adjusted times and update relevant instruction steps
4. Add scaling notes about time changes (already have notes infrastructure)

---

## QA-033: Tips should generate automatically and adjust for scaling
**Status:** Open
**Severity:** Medium
**Component:** Tips Generation Service / UI

**Description:**
Currently users must manually click "Generate Tips" button to get cooking tips. This is not intuitive - tips should be generated automatically when viewing the Tips tab or recipe detail.

Additionally, when a recipe is scaled, the tips should be regenerated or adjusted to reflect the scaled quantities (e.g., "use a larger pan" when doubling a recipe).

**Proposed Solution:**
1. Auto-generate tips when user views Tips tab (if not already cached)
2. When recipe is scaled, either:
   - Regenerate tips with scaling context, or
   - Append scaling-specific tips to existing tips
3. Show loading state while tips are being generated

---

## QA-034: AI prompts must be in migrations and visible in settings
**Status:** Open
**Severity:** Low
**Type:** Task/Process

**Description:**
All AI prompts added to the system should:
1. Be seeded via Django migrations (not manual DB inserts)
2. Appear in the Settings > AI Prompts management UI

This ensures prompts are version-controlled, reproducible across environments, and editable by users.

**Checklist for new prompts:**
- [ ] Create migration file with RunPython to seed prompt
- [ ] Include prompt_type, name, description, system_prompt, user_prompt_template, model
- [ ] Verify prompt appears in Settings after migration
- [ ] Add reverse migration to remove prompt if needed

**Current prompts to verify:**
- recipe_remix
- remix_suggestions
- serving_adjustment
- tips_generation
- nutrition_estimate

---

## Summary

| Issue | Title | Severity | Status |
|-------|-------|----------|--------|
| QA-029 | Ingredient quantities need AI tidying | Medium | Open |
| QA-030 | Nutrition tab serving label is ambiguous | Low | Open |
| QA-031 | Scaled recipes need instruction step alignment | High | Open |
| QA-032 | Scaled recipes need cooking time adjustments | Medium | Open |
| QA-033 | Tips should generate automatically and adjust for scaling | Medium | Open |
| QA-034 | AI prompts must be in migrations and visible in settings | Low | Open |

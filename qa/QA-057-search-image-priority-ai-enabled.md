# QA-057: Search Results Image Priority Not Working When AI Enabled

## Status
**RESOLVED** - Fixed via stronger prompt engineering

## Phase
Phase 9 Session B (Polish - Loading/Error handling)

## Issue

When searching for "goat" with AI enabled, search results display a mixture of results with and without images. Results with images should consistently appear before results without images on the first page of results.

### Current Behavior (Before Fix)
- Search for "goat" returns mixed results (with/without images interspersed)
- First page shows results without images mixed among results with images
- "traditional grandma recipe" showed no-image results at positions 11-16

### Expected Behavior
- Results with images should appear first
- Results without images should appear at the end
- This should work both with AI enabled AND when AI is disabled
- Subsequent pages (40+) reportedly work correctly (sorted by images first)

## Related Issues

- **QA-043**: Original implementation of image priority ranking
- **QA-052**: Fix for fallback paths when AI unavailable (marked VERIFIED)

## Research Findings

### Root Cause Identified

**Two issues were discovered:**

1. **Prompt Regression**: Migration 0007 was applied, but the database prompt had been **reverted** to the old version (likely via Settings UI edit). The DB showed:
   ```
   Has RANKING PRIORITIES: False
   Has SIGNIFICANTLY: False
   ```

2. **Weak Prompt Instructions**: Even the migration 0007 prompt wasn't strong enough. The AI model (claude-3.5-haiku) wasn't consistently following the image-priority instructions.

### Code Analysis

**File:** `apps/ai/services/ranking.py`

The fallback paths (no API key, AI failure) correctly use `_sort_by_image()`:

```python
# Line 33-40: Image-first sorting helper
def _sort_by_image(results: list[dict]) -> list[dict]:
    valid_results = _filter_valid(results)
    return sorted(valid_results, key=lambda r: (0 if r.get('image_url') else 1))

# Line 71-73: Fallback when no API key
if not is_ranking_available():
    return _sort_by_image(results)

# Lines 126-131: Fallback when AI fails
except (AIUnavailableError, AIResponseError, ValidationError) as e:
    return _sort_by_image(results)
```

**The AI ranking path (lines 99-124):**
- AI receives results with `[has image]` tag for items with images
- AI prompt (migration 0007) explicitly states images are "most important factor"
- AI returns ranking indices which are applied via `_apply_ranking()`
- Results 41+ are sorted with images first (lines 116-121)

### Test Results

**Before Fix** ("traditional grandma recipe"):
```
11. [---] Recipes
12. [---] Budget Recipes
13. [---] Stories
14. [---] Programmes
15. [---] Your Favourites
16. [---] Find us here
17. [IMG] Ultimate traditional Victoria sponge
```
No-image results mixed in at positions 11-16.

**After Fix** ("traditional grandma recipe"):
```
27. [IMG] Mushroom stroganoff
28. [---] Recipes
29. [---] Budget Recipes
30. [---] Stories
```
No-image results correctly appear at positions 28-30 (end of results).

## Resolution

### Fix Applied

Updated the search_ranking prompt to use stronger, more explicit language:

**Old prompt (ineffective):**
```
RANKING PRIORITIES (in order of importance):
1. Results WITH images should rank SIGNIFICANTLY higher than those without...
```

**New prompt (working):**
```
CRITICAL RULE: ALL results with [has image] MUST appear BEFORE any results without images. This is NON-NEGOTIABLE.

Within each group (with images vs without images), rank by:
1. Relevance to the search query
2. Recipe completeness (ratings, reviews)
3. Source reliability
```

### Files Modified

1. **`apps/ai/migrations/0007_update_search_ranking_prompt.py`** - Updated with stronger prompt
2. **Database AIPrompt record** - Updated via Django shell

### Key Learnings

1. LLMs don't always follow "soft" instructions like "SIGNIFICANTLY higher"
2. Using "CRITICAL", "MUST", and "NON-NEGOTIABLE" improves compliance
3. Separating the hard constraint from the ranking criteria makes it clearer
4. Settings UI can override migration-applied prompts - consider adding version tracking

## Verification

- [x] Search "goat" - all first page results have images
- [x] Search "traditional grandma" - no-image results at end (pos 28-30)
- [x] Migration file updated with new prompt
- [x] Database prompt updated

## Affected Components

- `apps/ai/services/ranking.py` - Main ranking logic (unchanged)
- `apps/ai/migrations/0007_update_search_ranking_prompt.py` - Prompt updated
- `apps/ai/models.py` - AIPrompt for search_ranking (data updated)

## Priority

Medium - Visual/UX issue affecting search result quality

## Testing Notes

- Test with query "goat"
- Test with query "traditional grandma recipe"
- Verify first page results order (images should come first)
- No-image results should appear at positions 25+ (end of first page)

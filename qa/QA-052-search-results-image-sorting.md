# QA-052: Search Results Not Sorted With Images First

## Status
**VERIFIED** - Confirmed working on Legacy frontend

## Issue

Search results on Legacy frontend are not being sorted to show recipes with images first. When searching for "beef" on iPad, results without images appear mixed with results that have images.

### Current Behavior
- Search results appear in arbitrary order
- Recipes without images are interspersed with recipes that have images

### Expected Behavior
- Recipes with images should appear first in search results
- Recipes without images should appear at the end

## Root Cause

The QA-043 fix added image-priority sorting, but **only when AI ranking succeeds**. When AI ranking is unavailable (no API key) or fails, the fallback returns results in original order **without any image sorting**.

**File:** `apps/ai/services/ranking.py`

```python
# Line 49-51: When AI unavailable, returns original order (NO image sorting)
if not is_ranking_available():
    logger.debug('AI ranking skipped: No API key configured')
    return results  # <-- BUG: should sort by image first

# Lines 104-109: When AI fails, returns original order (NO image sorting)
except (AIUnavailableError, AIResponseError, ValidationError) as e:
    logger.warning(f'AI ranking failed for query "{query}": {e}')
    return results  # <-- BUG: should sort by image first
```

The image sorting (lines 94-99) only happens for "remaining" results AFTER AI ranks the first 40. If AI is skipped entirely, no sorting happens.

## Fix

Add image-first sorting to all fallback paths in `ranking.py`:

```python
def _sort_by_image(results: list[dict]) -> list[dict]:
    """Sort results to prioritize those with images."""
    return sorted(results, key=lambda r: (0 if r.get('image_url') else 1))

# In rank_results():
if not is_ranking_available():
    logger.debug('AI ranking skipped: No API key configured')
    return _sort_by_image(results)  # Sort by image as fallback

# And in exception handlers:
except (AIUnavailableError, AIResponseError, ValidationError) as e:
    logger.warning(f'AI ranking failed for query "{query}": {e}')
    return _sort_by_image(results)  # Sort by image as fallback
```

## Affected Components

- `apps/ai/services/ranking.py` - Add image sorting to fallback paths

## Priority

Medium - Affects user experience when AI ranking is unavailable

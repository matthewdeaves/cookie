# QA-053: Search Results Should Filter Out Recipes Without Titles

## Status
**VERIFIED** - URL filtering working on iOS 9

## Issue

Search results include recipes that have no title, which causes import errors when users try to import them. Users should never see results that will fail to import.

### Current Behavior
- Search results can include recipes without titles
- Results without images are shown (this is OK, just lower priority)
- When user tries to import a titleless recipe, they get an error
- Searched for "prawn", loaded several pages, tried to import a recipe → error "recipe has no title"

### Expected Behavior
1. **Filter out titleless results** - Results without a title should be excluded entirely
2. **Keep image-first sorting** - Results WITH images should still appear before results WITHOUT images
3. **Allow imageless results** - Results without images are fine, just sorted lower

### Sorting Priority (both AI and non-AI)
1. Results with image AND title (highest)
2. Results without image but WITH title (lower)
3. Results without title → **EXCLUDED** (never shown)

## Root Cause

### Issue 1: Title can become empty after rating extraction

**File:** `apps/recipes/services/search.py:276-290`

```python
if not title:
    return None  # Check happens BEFORE rating extraction

# Rating extraction can make title empty
rating_match = re.search(r'([\d,]+)\s*[Rr]atings?\s*$', title)
if rating_match:
    title = title[:rating_match.start()].strip()  # Could become empty!
    # NO CHECK HERE if title is now empty

return SearchResult(
    url=url,
    title=title[:200],  # Could be empty string
    ...
)
```

If the extracted "title" was only "1,392 Ratings", after stripping the rating, the title becomes empty but this isn't caught.

### Issue 2: No defensive filtering in ranking

**File:** `apps/ai/services/ranking.py:24-30`

```python
def _sort_by_image(results: list[dict]) -> list[dict]:
    # Only sorts - no filtering of titleless results
    return sorted(results, key=lambda r: (0 if r.get('image_url') else 1))
```

The sorting function doesn't filter out results with empty/missing titles.

## Fix Plan

### 1. Add title check after rating extraction (`search.py`)

```python
# After rating extraction:
if not title:
    return None  # Title became empty after stripping rating
```

### 2. Add defensive filtering in `_sort_by_image()` (`ranking.py`)

```python
def _sort_by_image(results: list[dict]) -> list[dict]:
    # Filter out results without titles, then sort by image
    valid_results = [r for r in results if r.get('title')]
    return sorted(valid_results, key=lambda r: (0 if r.get('image_url') else 1))
```

### 3. Add filtering before AI ranking (`ranking.py`)

```python
def rank_results(query: str, results: list[dict]) -> list[dict]:
    # Filter out titleless results first
    results = [r for r in results if r.get('title')]

    if not results or len(results) <= 1:
        return results
    # ... rest of function
```

## Research Findings

**Verified:** Code review confirms both root causes are accurate.

1. **search.py:276-290** - Title check at line 276-277 happens BEFORE rating extraction. Rating extraction at line 288 can leave title empty with no subsequent check.

2. **ranking.py:24-30** - `_sort_by_image()` only sorts by image presence, doesn't filter.

3. **ranking.py:33-55** - `rank_results()` passes results directly to AI ranking without filtering titleless entries.

4. **ranking.py:103-108** - When sorting remaining results (beyond first 40), also no title filter.

**Fix approach:** Defense in depth - filter at source (search.py) AND at ranking stage (ranking.py) to catch any edge cases.

## Affected Components

- `apps/recipes/services/search.py` - `_extract_result_from_element()`
- `apps/ai/services/ranking.py` - `_sort_by_image()`, `rank_results()`

## Affects
- Modern frontend
- Legacy frontend

## Priority

High - Users encountering errors when trying to import search results

## Implementation

### Files Changed

**`apps/recipes/services/search.py`**
- Added title check after rating extraction (line 292-294)
- If title becomes empty after stripping rating text, result is filtered out
- Added extensive URL exclusion patterns to `_looks_like_recipe_url()`:
  - Article/blog: `/article/`, `/blog/`, `/story/`, `/news/`, `/feature/`, `/guide/`, `/review/`, `/roundup/`
  - Video/media: `/video/`, `/watch/`, `/episode/`, `/series/`, `/show/`, `/gallery/`, `/slideshow/`
  - Index pages: `/seasons`, `/collections`, `/cuisines`, `/ingredients`, `/occasions`, `/courses`, `/diets/`, `/menus/`

**`apps/ai/services/ranking.py`**
- Added `_filter_valid()` helper to filter results without titles
- Updated `_sort_by_image()` to filter before sorting
- Added filtering at start of `rank_results()` for defense in depth

### Verification Checklist
- [ ] Search for "prawn" and load several pages - no titleless results appear
- [ ] All displayed results can be imported successfully
- [ ] Results still sorted with images first

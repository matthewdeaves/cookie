# QA-053: Search Results Should Filter Out Recipes Without Titles

## Status
**OPEN** - Root cause identified

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

## Affected Components

- `apps/recipes/services/search.py` - `_extract_result_from_element()`
- `apps/ai/services/ranking.py` - `_sort_by_image()`, `rank_results()`

## Affects
- Modern frontend
- Legacy frontend

## Priority

High - Users encountering errors when trying to import search results

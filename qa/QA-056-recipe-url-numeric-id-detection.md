# QA-056: Test Failure - Recipe URL Numeric ID Detection

## Status
**VERIFIED** - Test URL updated to avoid exclude pattern, all 228 tests pass

## Issue

Unit test `test_looks_like_recipe_url_numeric_id` fails because the test URL contains `/article/` which is explicitly excluded.

### Test Details
- **File:** `tests/test_search.py:33`
- **Test:** `TestSearchHelpers::test_looks_like_recipe_url_numeric_id`

### Current Behavior
```python
result = search._looks_like_recipe_url(
    'https://example.com/article/12345/yummy-cookies',
    'example.com'
)
# Returns: False
# Expected: True
```

### Expected Behavior
The test expects URLs with numeric IDs to be detected as recipe URLs.

## Root Cause Analysis

**File:** `apps/recipes/services/search.py`

The `_looks_like_recipe_url()` method logic:
1. First checks **exclude_patterns** (lines 456-458)
2. Then checks **recipe_patterns** (lines 460-463)

The test URL `https://example.com/article/12345/yummy-cookies` fails because:
1. `/article/` is in exclude_patterns (line 406, added in QA-053)
2. Exclude check happens BEFORE recipe pattern check
3. The URL is correctly rejected as an article page

**This is correct behavior** - article pages should be excluded even if they have numeric IDs. The test expectation is wrong.

## Resolution

**Update the test** to use a URL that properly tests numeric ID detection without hitting exclude patterns.

## Implementation Plan

### Task 1: Update test URL

**File:** `tests/test_search.py`

**Current code (lines 31-36):**
```python
def test_looks_like_recipe_url_numeric_id(self):
    """Test URL with numeric ID in path is detected."""
    assert self.search._looks_like_recipe_url(
        'https://example.com/article/12345/yummy-cookies',
        'example.com'
    ) is True
```

**Change to:**
```python
def test_looks_like_recipe_url_numeric_id(self):
    """Test URL with numeric ID in path is detected."""
    assert self.search._looks_like_recipe_url(
        'https://example.com/12345/yummy-cookies',
        'example.com'
    ) is True
```

The new URL `/12345/yummy-cookies`:
- Contains numeric ID pattern `/\d+/` which matches `r'/\d+/'` in recipe_patterns
- Does NOT contain any exclude patterns
- Represents a real recipe URL pattern (e.g., `allrecipes.com/12345/chocolate-cake`)

### Task 2: Run tests to verify

```bash
pytest tests/test_search.py::TestSearchHelpers -v
```

## Alternative Considered

Could reorder the pattern checks so recipe patterns take precedence, but this would cause false positives (article pages with numeric IDs would be incorrectly detected as recipes). The current behavior is correct.

## Files to Change

- `tests/test_search.py` - Update `test_looks_like_recipe_url_numeric_id` test URL

## Verification

1. `pytest tests/test_search.py::TestSearchHelpers -v` passes
2. All search tests pass: `pytest tests/test_search.py -v`
3. Manual verification that `/article/` URLs are still correctly excluded

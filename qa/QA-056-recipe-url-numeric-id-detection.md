# QA-056: Test Failure - Recipe URL Numeric ID Detection

## Status
**OPEN** - Test failure discovered during Session G testing

## Issue

Unit test `test_looks_like_recipe_url_numeric_id` fails because the `_looks_like_recipe_url()` method doesn't detect URLs with numeric IDs in the path.

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

URLs with patterns like `/article/12345/slug` are not being recognized as potential recipe URLs.

### Expected Behavior
URLs containing numeric IDs in the path (e.g., `/article/12345/`) should be detected as likely recipe URLs, as many recipe sites use this pattern.

## Root Cause

**File:** `apps/recipes/services/search.py`

The `_looks_like_recipe_url()` method's pattern matching doesn't include a check for numeric IDs in URL paths.

## Analysis Needed

1. Review the current `_looks_like_recipe_url()` implementation
2. Determine if the test expectation is correct (should numeric ID paths be recipe URLs?)
3. Either update the method to detect numeric IDs, or update/remove the test if the expectation is wrong

## Common Recipe URL Patterns with Numeric IDs

- `example.com/recipes/12345/recipe-name`
- `example.com/article/12345/recipe-name`
- `example.com/r/12345`
- `example.com/recipe-12345`

## Files to Investigate

- `apps/recipes/services/search.py` - `_looks_like_recipe_url()` method
- `tests/test_search.py` - Test expectations

## Recommendation

Investigate whether this is a missing feature in the URL detection logic or an incorrect test expectation. If the pattern is common among recipe sites, add detection for numeric ID paths.

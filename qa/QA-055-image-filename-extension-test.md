# QA-055: Test Failure - PNG Image Filename Extension

## Status
**OPEN** - Test failure discovered during Session G testing

## Issue

Unit test `test_generate_image_filename_png` fails because the scraper always generates `.jpg` extensions regardless of source image format.

### Test Details
- **File:** `tests/test_scraper.py:91`
- **Test:** `TestScraperHelpers::test_generate_image_filename_png`

### Current Behavior
```python
filename = scraper._generate_image_filename(
    'https://example.com/recipe/123',
    'https://example.com/images/photo.png'
)
# Returns: 'recipe_84452edcaf83.jpg'
# Expected: 'recipe_84452edcaf83.png'
```

The `_generate_image_filename()` method always returns `.jpg` extension.

### Expected Behavior
The test expects PNG URLs to generate `.png` filenames.

## Root Cause

**File:** `apps/recipes/services/scraper.py`

The `_generate_image_filename()` method was intentionally changed in QA-054 to always use `.jpg` extension because all images are now converted to JPEG format for iOS 9 compatibility.

## Resolution Options

1. **Update the test** - The test is outdated and should be updated to expect `.jpg` since all images are converted to JPEG per QA-054
2. **Remove the test** - The test is no longer valid given the WebP conversion behavior

## Recommendation

Update the test to expect `.jpg` extension, as this is the intended behavior after the QA-054 fix.

## Files to Change

- `tests/test_scraper.py` - Update `test_generate_image_filename_png` to expect `.jpg`

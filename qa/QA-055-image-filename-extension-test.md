# QA-055: Test Failure - PNG Image Filename Extension

## Status
**VERIFIED** - Test updated to expect .jpg, all 228 tests pass

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
# Expected by test: 'recipe_84452edcaf83.png'
```

The `_generate_image_filename()` method always returns `.jpg` extension.

### Expected Behavior
The test expects PNG URLs to generate `.png` filenames, but this is outdated.

## Root Cause

**File:** `apps/recipes/services/scraper.py`

The `_generate_image_filename()` method was intentionally changed in QA-054 to always use `.jpg` extension because all images are now converted to JPEG format for iOS 9 compatibility via `_convert_webp_to_jpeg()`.

This is correct behavior - the test expectation is wrong.

## Resolution

**Update the test** to expect `.jpg` since all images are converted to JPEG per QA-054.

## Implementation Plan

### Task 1: Update test to expect `.jpg`

**File:** `tests/test_scraper.py`

**Current code (lines 86-91):**
```python
def test_generate_image_filename_png(self):
    filename = self.scraper._generate_image_filename(
        'https://example.com/recipe/123',
        'https://example.com/images/photo.png'
    )
    assert filename.endswith('.png')
```

**Change to:**
```python
def test_generate_image_filename_png(self):
    """PNG source images still get .jpg extension (converted to JPEG for iOS 9)."""
    filename = self.scraper._generate_image_filename(
        'https://example.com/recipe/123',
        'https://example.com/images/photo.png'
    )
    assert filename.endswith('.jpg')  # All images converted to JPEG (QA-054)
```

### Task 2: Run tests to verify

```bash
pytest tests/test_scraper.py::TestScraperHelpers -v
```

## Files to Change

- `tests/test_scraper.py` - Update `test_generate_image_filename_png` assertion

## Verification

1. `pytest tests/test_scraper.py::TestScraperHelpers -v` passes
2. All scraper tests pass: `pytest tests/test_scraper.py -v`

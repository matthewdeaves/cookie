# QA-054: WebP Images Not Displaying on iOS 9

## Status
**FIXED** - Pending verification

## Issue

Recipe images from some sources (e.g., epicurious.com) are served as WebP format even when the URL ends in `.jpg`. iOS 9 does not support WebP images, causing images to not display on iPad 3 / legacy browsers.

### Current Behavior
- Scraper downloads image from URL ending in `.jpg`
- CDN serves WebP content regardless of URL extension
- Image is saved as `.jpg` but contains WebP data
- iOS 9 cannot display the image

### Expected Behavior
- All cached images should be converted to JPEG format
- Images should be resized to reasonable dimensions (max 1200px)
- iOS 9 should display all cached recipe images

## Root Cause

**File:** `apps/recipes/services/scraper.py`

The `_download_image()` method saved image content as-is without checking the actual format. The `_generate_image_filename()` method determined extension from URL path, not actual content.

Modern CDNs like epicurious.com serve WebP images regardless of the URL extension for bandwidth savings.

## Fix

1. Added `_convert_webp_to_jpeg()` method that:
   - Detects WebP images using Pillow
   - Converts to JPEG format
   - Resizes large images (>1200px) to reduce file size
   - Handles RGBA/P modes by converting to RGB

2. Updated `_download_image()` to call conversion on all downloaded images

3. Updated `_generate_image_filename()` to always use `.jpg` extension

## Files Changed

- `apps/recipes/services/scraper.py`
  - Added PIL Image import
  - Added `_convert_webp_to_jpeg()` method
  - Updated `_download_image()` to convert images
  - Simplified `_generate_image_filename()` to always use `.jpg`

## Verification Checklist
- [ ] Re-import a recipe from epicurious.com
- [ ] Verify cached image is JPEG format (`file media/recipe_images/...`)
- [ ] Verify image displays on iOS 9 / iPad 3
- [ ] Verify file size is reasonable (<500KB)

## Notes

Existing WebP images saved as `.jpg` will need to be re-imported or manually converted. The fix only applies to newly imported recipes.

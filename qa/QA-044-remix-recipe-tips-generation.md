# QA-044: Remix Recipe Tips Generation Fails/Times Out

## Status
**RESOLVED** (2026-01-09) - Verified on Modern and Legacy frontends

## Issue

Cooking tips generation for remix recipes appears to fail or time out. The UI shows inconsistent states across page refreshes.

## Steps to Reproduce

1. Create or view a remix recipe (e.g., recipe ID 62)
2. Navigate to the Tips tab
3. Observe "tips are being generated" message
4. Wait - generation appears to time out
5. Refresh page - same behavior repeats
6. Refresh again - now shows "no cooking tips yet" with option to generate manually

## Current Behavior

- Tips tab shows "generating" state
- Generation seems to time out without completing
- State is inconsistent across refreshes
- Eventually falls back to "no tips" state

## Expected Behavior

- Tips should generate successfully for remix recipes
- If generation fails, should show error state immediately
- State should be consistent across refreshes

## Affected Components

- **Legacy**: Tips tab in recipe detail
- Tips generation service
- Remix recipe handling

## Test Recipe

- Recipe ID: 62 (remix recipe)

## Priority

Medium - Feature not working for remix recipes

## Phase

TBD

---

## Research Findings

### Root Cause

**Remix recipes do NOT auto-generate tips.** Unlike imported recipes, remix creation does not spawn a background thread to generate tips. This is a gap in the implementation.

### Code Path Comparison

| Aspect | Imported Recipes | Remix Recipes |
|--------|------------------|---------------|
| Tips trigger | Automatic (background thread) | **None** |
| Code location | `scraper.py:147-153` | `remix.py:63-174` |
| Background thread | Yes, spawns after creation | No |
| User experience | Tips appear automatically | Must manually generate |

### Why the UI Shows "Generating" Then Fails

**Frontend polling logic** (`detail.js:46-64`):

```javascript
// Check if we should poll for tips (recently imported recipe with no tips)
var scrapedAt = pageEl.getAttribute('data-scraped-at');
var hasTips = pageEl.getAttribute('data-has-tips') === 'true';

if (scrapedAt && !hasTips) {
    var recipeAge = Date.now() - scrapedDate.getTime();
    if (recipeAge < TIPS_RECENT_THRESHOLD) {  // 60 seconds
        startTipsPolling();
    }
}
```

**Problem for remix recipes:**
- Remix recipes have `scraped_at = NULL` (they weren't scraped)
- Polling condition `scrapedAt && !hasTips` fails on first check
- But the template may still show loading state initially
- After timeout/refresh, shows empty state with "Generate Tips" button

### Polling Timeout Behavior

**Constants** (`detail.js:30-32`):
- `TIPS_POLL_INTERVAL = 3000` (every 3 seconds)
- `TIPS_MAX_POLL_DURATION = 30000` (max 30 seconds)
- `TIPS_RECENT_THRESHOLD = 60000` (only poll if < 60 seconds old)

After 30 seconds of polling with no tips found, frontend silently gives up and shows empty state.

### Imported Recipe Flow (Working)

```
scraper.py creates recipe
    ↓
Background thread spawns (line 147-153)
    ↓
Thread calls generate_tips(recipe_id)
    ↓
Tips saved to recipe.ai_tips
    ↓
Frontend polling detects tips, renders them
```

### Remix Recipe Flow (Broken)

```
remix.py creates recipe with is_remix=True
    ↓
NO background thread spawned
    ↓
Recipe has ai_tips = [] (empty)
    ↓
Frontend may briefly show loading (race condition)
    ↓
No polling starts (scraped_at is NULL)
    ↓
Shows empty state after refresh
```

### Files Reference

| Component | File | Lines |
|-----------|------|-------|
| Tips service | `apps/ai/services/tips.py` | 14-85 |
| Scraper (auto-gen) | `apps/recipes/services/scraper.py` | 147-178 |
| Remix service | `apps/ai/services/remix.py` | 63-174 |
| Frontend polling | `apps/legacy/static/legacy/js/pages/detail.js` | 46-64, 1057-1104 |
| Template | `apps/legacy/templates/legacy/recipe_detail.html` | 263-313 |

### Proposed Fix

**Option A: Add background tips generation to remix creation (Recommended)**

In `apps/ai/services/remix.py`, after recipe creation (around line 170), add:

```python
# Fire-and-forget: Generate AI tips in background thread
from apps.ai.services.tips import generate_tips
import threading

thread = threading.Thread(
    target=generate_tips,
    args=(recipe.id,),
    daemon=True
)
thread.start()
```

**Option B: Set a "created_at" flag for polling**

Add `created_at` timestamp to remix recipes and update frontend to poll for both `scraped_at` OR recently created remixes.

### Acceptance Criteria

- [x] Remix recipes auto-generate tips like imported recipes
- [x] Tips appear within ~10-15 seconds of remix creation
- [x] If generation fails, user can manually trigger via button
- [x] No silent failures - appropriate error states shown

### Fix Applied

Added background thread tips generation to `apps/ai/services/remix.py`:
- Added `threading` import
- Added `_generate_tips_background()` helper function (lines 289-310)
- Spawned background thread after remix creation (lines 175-181)

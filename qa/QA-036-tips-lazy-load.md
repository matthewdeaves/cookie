# QA-036: Tips Tab Should Lazy Load After Import

## Issue
When a recipe is imported, AI tips are generated in a background thread (fire-and-forget). This takes ~5-10 seconds. If the user navigates to the Tips tab before generation completes, they see "No cooking tips yet" even though tips are being generated.

## Current Behavior
1. User imports recipe
2. Recipe detail page loads immediately
3. Tips generation runs in background (~5-10 seconds)
4. User clicks Tips tab - sees empty state
5. User must manually refresh to see tips

## Expected Behavior
1. User imports recipe
2. Recipe detail page loads immediately
3. Tips tab shows loading state OR polls for tips
4. When tips are ready, they appear automatically (no refresh needed)

## Affected Components
- **React**: `RecipeDetail.tsx` - TipsTab component
- **Legacy**: `recipe_detail.html` + `detail.js`

## Priority
Medium - UX improvement, not blocking functionality

## Phase
8B - AI Features (Session D follow-up)

---

## Research Findings

### Background Tips Generation Flow
Location: `apps/recipes/services/scraper.py:147-153`

```python
# Fire-and-forget: Generate AI tips in background thread (non-blocking)
thread = threading.Thread(
    target=self._generate_tips_background,
    args=(recipe.id,),
    daemon=True
)
thread.start()
```

The `_generate_tips_background()` method (lines 157-178) calls `generate_tips(recipe_id)` which takes ~5-10 seconds.

### Existing Polling Pattern
The codebase already has a polling pattern in `apps/legacy/static/legacy/js/pages/search.js` for progressive image caching:

```javascript
// State tracking
imagePollingState = {
    isPolling: false,
    pendingUrls: {},
    pollInterval: null,
    pollStartTime: null
}

// Polling constants
var MAX_POLL_DURATION = 20000;  // 20 seconds
var POLL_INTERVAL = 4000;       // 4 seconds
```

### Key Data Points
- `scraped_at` field on Recipe model indicates when recipe was imported
- Already returned in API response (`RecipeOut` schema)
- Can determine "recently imported" by checking if `scraped_at` < 60 seconds ago

---

## Implementation Plan

### Chosen Approach: Polling (Option A)
Matches existing codebase patterns and is simpler than WebSockets/SSE.

### Configuration
- **Poll interval**: 3 seconds
- **Max duration**: 30 seconds (tips generation typically takes ~10s)
- **Recent threshold**: 60 seconds (only poll for recipes imported within last minute)

### React Implementation (`RecipeDetail.tsx`)

Add polling effect when recipe is recent and has no tips:

```typescript
// Poll for tips if recipe is recent and tips are empty
useEffect(() => {
  const recipeAge = Date.now() - new Date(recipe.scraped_at).getTime();
  const isRecent = recipeAge < 60000; // 60 seconds

  if (!isRecent || tips.length > 0) return;

  setTipsPolling(true);
  const startTime = Date.now();

  const interval = setInterval(async () => {
    if (Date.now() - startTime > 30000) {
      clearInterval(interval);
      setTipsPolling(false);
      return;
    }

    try {
      const updated = await api.recipes.detail(recipe.id);
      if (updated.ai_tips?.length > 0) {
        setTips(updated.ai_tips);
        clearInterval(interval);
        setTipsPolling(false);
      }
    } catch (e) {
      // Ignore polling errors
    }
  }, 3000);

  return () => {
    clearInterval(interval);
    setTipsPolling(false);
  };
}, [recipe.id, recipe.scraped_at]);
```

### Legacy Implementation (`detail.js`)

Add similar polling logic using existing patterns:

```javascript
var tipsPollingState = {
    isPolling: false,
    pollInterval: null,
    pollStartTime: null
};

function startTipsPolling(recipeId, scrapedAt) {
    var MAX_POLL_DURATION = 30000;  // 30 seconds
    var POLL_INTERVAL = 3000;       // 3 seconds

    var recipeAge = Date.now() - new Date(scrapedAt).getTime();
    if (recipeAge > 60000) return; // Not recent

    tipsPollingState.isPolling = true;
    tipsPollingState.pollStartTime = Date.now();

    // Show loading indicator
    showTipsPollingIndicator();

    tipsPollingState.pollInterval = setInterval(function() {
        var elapsed = Date.now() - tipsPollingState.pollStartTime;

        if (elapsed > MAX_POLL_DURATION) {
            stopTipsPolling();
            return;
        }

        Cookie.ajax.get('/api/recipes/' + recipeId + '/', function(error, data) {
            if (!error && data && data.ai_tips && data.ai_tips.length > 0) {
                renderTips(data.ai_tips);
                stopTipsPolling();
            }
        });
    }, POLL_INTERVAL);
}
```

### UI Changes

**Tips Tab Badge (while polling):**
- Show subtle pulsing/loading indicator
- Text: "Generating..." or animated dots

**Tips Content (while polling):**
- Show loading state with message: "Generating cooking tips..."
- Use existing loading spinner pattern

---

## Files to Modify

| File | Changes |
|------|---------|
| `frontend/src/screens/RecipeDetail.tsx` | Add `tipsPolling` state, polling useEffect, update TipsTab |
| `apps/legacy/static/legacy/js/pages/detail.js` | Add tips polling functions |
| `apps/legacy/templates/legacy/recipe_detail.html` | No changes needed (uses existing loading markup) |

## Testing

1. Import a new recipe
2. Immediately navigate to Tips tab
3. Verify loading state is shown
4. Wait for tips to appear automatically (~10 seconds)
5. Verify polling stops after tips arrive
6. Test timeout (disable AI, verify polling stops after 30s)

---

## Implementation Status

### Completed

**React Frontend (`frontend/src/screens/RecipeDetail.tsx`):**
- Added `tipsPolling` state variable
- Added `useEffect` that polls for tips when:
  - Recipe is recent (`scraped_at` < 60 seconds ago)
  - Tips array is empty
- Polls every 3 seconds for up to 30 seconds
- Updated `TipsTab` component to show polling state with message "Tips are being generated in the background"

**Legacy Frontend:**
- `apps/legacy/static/legacy/js/pages/detail.js`:
  - Added `tipsPollingState` object and polling constants
  - Added `startTipsPolling()` and `stopTipsPolling()` functions
  - Updated `init()` to check recipe age and start polling if needed
- `apps/legacy/templates/legacy/recipe_detail.html`:
  - Added `data-scraped-at` and `data-has-tips` attributes to page element
  - Added subtext element for polling message
- `apps/legacy/static/legacy/css/recipe-detail.css`:
  - Added `.tips-loading-subtext` styles

---

## Bug Report: Legacy Frontend Polling Not Working

### Issue Discovered
Testing confirmed that tips lazy loading is NOT working on the legacy frontend. The polling never starts.

### Root Cause Analysis

**Location:** `apps/legacy/static/legacy/js/pages/detail.js:51-53`

```javascript
// Current (broken) code:
var scrapedDate = new Date(scrapedAt.replace('T', ' ').replace(/\+.*$/, '').replace('Z', ''));
```

**Problem:** Safari (especially iOS 9) date parsing is very strict. The current implementation has multiple issues:

1. **Microseconds not removed:** Django's `date:'c'` filter outputs microseconds (e.g., `2026-01-09T09:18:29.135626+00:00`). Safari cannot parse dates with 6-digit fractional seconds.

2. **Dash format not supported:** Safari doesn't support `YYYY-MM-DD HH:mm:ss` format. After the current transformations, the result is `2026-01-09 09:18:29.135626` which Safari returns as `Invalid Date` (NaN).

3. **Negative timezone offsets not handled:** The regex `/\+.*$/` only removes positive timezone offsets like `+00:00`. Negative offsets like `-05:00` are not removed.

**Parsing Flow (Current - Broken):**
```
Input:  "2026-01-09T09:18:29.135626+00:00"
Step 1: "2026-01-09 09:18:29.135626+00:00"  (replace T)
Step 2: "2026-01-09 09:18:29.135626"        (remove +00:00)
Step 3: "2026-01-09 09:18:29.135626"        (no Z to remove)
Result: new Date(...) = NaN on Safari      ❌
```

**Why Polling Never Starts:**
```javascript
if (!isNaN(recipeAge) && recipeAge < TIPS_RECENT_THRESHOLD) {
    startTipsPolling();  // Never reached because recipeAge is NaN
}
```

### Research Sources

- [Safari JavaScript Date issues](https://chrispennington.blog/blog/safari-does-not-show-new-date-from-javascript/) - Safari doesn't support `YYYY-MM-DD` format
- [MDN browser-compat-data Issue #15401](https://github.com/mdn/browser-compat-data/issues/15401) - iOS Safari ISO 8601 incompatibility
- [Fix: Invalid date on Safari & IE](https://www.linkedin.com/pulse/fix-invalid-date-safari-ie-hatem-ahmad) - Use slashes instead of dashes

**Safari-Compatible Date Formats:**
- `'07/06/2021 10:05:00'` (mm/dd/yyyy hh:mm:ss) ✓
- `2021, 07, 06, 10, 05, 00` (numeric arguments) ✓
- `1625600237781` (milliseconds timestamp) ✓
- `'2021-07-06 10:05:00'` (YYYY-MM-DD) ✗

### Fix Required

**Location:** `apps/legacy/static/legacy/js/pages/detail.js:51-53`

Replace:
```javascript
var scrapedDate = new Date(scrapedAt.replace('T', ' ').replace(/\+.*$/, '').replace('Z', ''));
```

With:
```javascript
// iOS 9 Safari compatible date parsing
// Convert "2026-01-09T09:18:29.135626+00:00" to Safari-parseable format
var scrapedDate = new Date(scrapedAt
    .replace('T', ' ')              // Replace T with space
    .replace(/\.\d+/, '')           // Remove microseconds (.135626)
    .replace(/[+\-]\d{2}:\d{2}$/, '') // Remove timezone (+00:00 or -05:00)
    .replace('Z', '')               // Remove Z suffix if present
    .replace(/-/g, '/'));           // Convert dashes to slashes for Safari
```

**Parsing Flow (Fixed):**
```
Input:  "2026-01-09T09:18:29.135626+00:00"
Step 1: "2026-01-09 09:18:29.135626+00:00"  (replace T)
Step 2: "2026-01-09 09:18:29+00:00"         (remove microseconds)
Step 3: "2026-01-09 09:18:29"               (remove timezone)
Step 4: "2026-01-09 09:18:29"               (no Z)
Step 5: "2026/01/09 09:18:29"               (slashes for Safari)
Result: new Date(...) = valid Date object  ✓
```

### Comparison with Working Code

The **search.js** image polling works because it doesn't rely on date parsing - it tracks state using URL maps and doesn't need to determine "recipe age". The tips polling needs date parsing to determine if a recipe is recently imported.

### Testing Plan

After fix:
1. Import a new recipe via legacy search
2. Navigate to recipe detail page
3. Click Tips tab immediately
4. Should see "Generating cooking tips..." loading state
5. After ~10 seconds, tips should appear automatically
6. Verify on Safari (especially iOS) if possible

---

## Fix Applied

**Date:** 2026-01-09

**Change:** Updated `apps/legacy/static/legacy/js/pages/detail.js:50-58`

The Safari-compatible date parsing fix was applied:
- Added microseconds removal (`/\.\d+/`)
- Fixed timezone regex to handle negative offsets (`/[+-]\d{2}:\d{2}$/`)
- Added dash-to-slash conversion for Safari compatibility

**Additional infrastructure fixes:**
- Created `entrypoint.sh` to run `collectstatic` on container boot
- Added cache-control headers to `nginx/nginx.conf`
- Logged QA-038 for legacy QA workflow improvements

## Status
**RESOLVED** (2026-01-09) - Verified on Modern and Legacy frontends

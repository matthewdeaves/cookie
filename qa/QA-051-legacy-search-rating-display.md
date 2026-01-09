# QA-051: Legacy Search Results Don't Display Rating Count

## Status
**VERIFIED** - Confirmed working on Legacy frontend

## Issue

Legacy frontend search result cards don't display the rating count, even though the API returns the `rating_count` field.

### Current Behavior
- Modern frontend: Shows "host · 1,392 Ratings" correctly
- Legacy frontend: Shows only "host" without rating count

### Expected Behavior
Legacy search results should display rating count matching modern frontend format.

## Root Cause

The Legacy frontend renders search results via **JavaScript**, not Django templates. The `renderSearchResultCard()` function in `search.js:303-327` builds HTML directly and does not include `rating_count`.

The Django template `search_result_card.html` that was edited in QA-048 is **not used** for search results - it may only be used for server-rendered contexts.

**File:** `apps/legacy/static/legacy/js/pages/search.js:303-327`

```javascript
function renderSearchResultCard(result) {
    // ... builds HTML without rating_count
    return '...' +
        '<p class="search-result-host">' + escapeHtml(result.host) + '</p>' +
        // Missing: rating_count display
        '...';
}
```

## Fix

Update `renderSearchResultCard()` to include rating count:

```javascript
// Build host line with optional rating count
var hostHtml = escapeHtml(result.host);
if (result.rating_count) {
    hostHtml += ' · ' + formatNumber(result.rating_count) + ' Ratings';
}

// In the return statement:
'<p class="search-result-host">' + hostHtml + '</p>'
```

Note: Need to add `formatNumber()` helper for comma formatting (ES5 compatible).

## Affected Components

- `apps/legacy/static/legacy/js/pages/search.js` - `renderSearchResultCard()` function

## Priority

Low - Cosmetic issue, Modern frontend works correctly

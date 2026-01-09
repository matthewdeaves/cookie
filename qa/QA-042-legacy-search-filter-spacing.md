# QA-042: Legacy Search Results - Source Filters Need More Spacing

## Problem

On the legacy frontend search results page, the source filter buttons/chips are too close together. They appear cramped with insufficient spacing between them.

## Affects

- Legacy frontend only
- Search results page (`/legacy/search/`)

## Current Behavior

Source filter buttons are displayed with minimal or no gap between them, making them:
- Harder to tap accurately on touch devices (iPad)
- Visually cramped and harder to scan

## Expected Behavior

Source filters should have adequate spacing (e.g., 8-12px gap) between each filter chip for:
- Better touch targets on mobile/tablet
- Improved visual hierarchy and readability

## Files to Check

- `apps/legacy/static/legacy/css/components.css` - Filter/chip styling
- `apps/legacy/templates/legacy/search.html` - Search results template

## Priority

Low - Visual polish / UX improvement

## Status

**FIXED** (2026-01-09)

## Root Cause

The original `.source-filters` CSS used `gap: 0.5rem` for spacing. However, the CSS `gap` property for flexbox wasn't supported until Safari 14.1 (2021). iOS 9 Safari doesn't support flex gap at all, so filter chips had zero spacing between them on the legacy iPad.

## Solution

Replaced the `gap` property with a margin-based approach that works universally:

1. Each chip gets `margin: 0.375rem` (6px on all sides = 12px between chips)
2. Container uses negative margins to compensate for outer chip margins
3. Total effective gap: 12px (0.75rem) - at the high end of the 8-12px recommendation

## Changes Made

**File:** `apps/legacy/static/legacy/css/components.css`

```css
/* Source Filters - uses margin for iOS 9 compatibility (no flex gap support) */
.source-filters {
    display: -webkit-flex;
    display: flex;
    -webkit-flex-wrap: wrap;
    flex-wrap: wrap;
    /* Negative margin compensates for chip margins */
    margin: 0 -0.375rem 0.625rem -0.375rem;
}

.source-filters > .chip {
    margin: 0.375rem;
}
```

## Verification

1. Search for any recipe on the legacy frontend
2. Verify source filter chips have visible spacing between them
3. Test on iPad to ensure touch targets are easier to tap

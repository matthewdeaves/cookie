# QA-040: Discover Tab Shows "Configure API Key" When AI Is Available

## Problem

When the user has an API key configured for OpenRouter, the Discover tab still shows:
> "Configure an API key in settings to enable personalized recipe suggestions"

This message is misleading because the API key IS configured - the issue is that no suggestions were returned (either because the API call failed or returned empty results).

## Affects

- Modern frontend (React)
- Legacy frontend (after discover implementation)

## Root Cause

The frontend shows the same empty state for two different scenarios:
1. AI unavailable (no API key configured) - "Configure an API key" is correct
2. AI available but no suggestions returned - "Configure an API key" is incorrect

In React `Home.tsx`, the logic is:
```tsx
discoverSuggestions.length > 0 ? (
  // show suggestions
) : (
  /* Empty state - AI unavailable */
  // Shows "Configure an API key" message
)
```

When `api.ai.discover()` returns an empty array or fails, it's treated the same as "no API key".

## Expected Behavior

Should differentiate between:
1. **No API key** → "Configure an API key in settings..."
2. **API error** → "Unable to load suggestions. Please try again."
3. **No suggestions available** → "No suggestions available yet. Add some favorites to get personalized recommendations."

## Proposed Fix

1. Track whether AI is available from app settings (already have this via `settings.ai_available`)
2. Track error state separately from empty state
3. Show appropriate message based on state:
   - `!settings.ai_available` → "Configure an API key"
   - `error` → "Unable to load suggestions"
   - `suggestions.length === 0` → "No suggestions available"

## Files to Update

- `frontend/src/screens/Home.tsx` - React discover logic
- `apps/legacy/templates/legacy/home.html` - Legacy discover template (if implementing)
- `apps/legacy/static/legacy/js/pages/home.js` - Legacy discover JS (if implementing)

## Priority

Low - UX improvement, not blocking functionality

## Status
**RESOLVED** (2026-01-09) - Verified on Modern and Legacy frontends

## Implementation

### React Frontend (`frontend/src/`)
- Added `aiAvailable` prop to Home component (`screens/Home.tsx`)
- Added `discoverError` state to track API errors
- App.tsx now loads settings and passes `aiAvailable` to Home
- Three distinct empty states:
  1. `!aiAvailable` → "Configure an API key in settings..."
  2. `discoverError` → "Unable to Load Suggestions" with retry button
  3. Default (empty suggestions) → "No Suggestions Yet" with View Favorites button

### Legacy Frontend (`apps/legacy/`)
- Template (`templates/legacy/home.html`): Added three separate empty state divs:
  - `#discover-empty-no-api` - No API key configured
  - `#discover-empty-error` - API error with retry button
  - `#discover-empty-none` - No suggestions, add favorites
- JavaScript (`static/legacy/js/pages/home.js`):
  - Added `hideAllEmptyStates()` helper
  - Differentiate between error response and empty data
  - Added event listeners for retry and view favorites buttons

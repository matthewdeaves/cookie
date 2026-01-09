# QA-050: Tips Tab Should Be Hidden Without Valid API Key

## Status
**VERIFIED** - Confirmed working on iPad

## Issue

The Tips tab is always visible in recipe detail, even when:
1. No OpenRouter API key is configured
2. The API key is invalid/expired

### Current Behavior

**Modern frontend:**
- Tips tab always shows in the tab bar
- Inside the tab, if no API key: shows "Configure an API key in settings"
- If API key exists but is invalid: attempts to generate tips, then fails with error

**Legacy frontend:**
- Tips tab always shows in the tab bar (line 82: `{% if ai_available %}`)
- Same issue with invalid keys

### Expected Behavior

- Tips tab should be completely hidden if AI is not available
- AI should be considered "unavailable" if:
  - No API key is configured, OR
  - The API key is invalid/expired

## Root Cause Analysis

### 1. `ai_available` Only Checks Key Existence

**File:** `apps/core/api.py:25`
```python
'ai_available': bool(settings.openrouter_api_key),
```

**File:** `apps/ai/api.py:83`
```python
'available': bool(settings.openrouter_api_key),
```

This only checks if a key exists, not if it's valid.

### 2. Modern Frontend Always Shows Tips Tab

**File:** `frontend/src/screens/RecipeDetail.tsx:448`
```tsx
{ key: 'tips', label: 'Tips' },
```

The tab is unconditionally rendered. Should be:
```tsx
settings?.ai_available && { key: 'tips', label: 'Tips' },
```

### 3. Legacy Frontend Conditionally Shows Tab (Partially)

**File:** `apps/legacy/templates/legacy/recipe_detail.html:82`
```html
{% if ai_available %}
```

Legacy already hides the Tips tab if `ai_available` is false, but the issue is that `ai_available` is true even with an invalid key.

## Proposed Fix

### Option A: Validate Key on Settings Load (Recommended)

1. Update `/api/settings/` to validate the API key on each request
2. Cache the validation result briefly (5 minutes) to avoid rate limiting
3. Return `ai_available: false` if key is missing or invalid

**Pros:** Single source of truth, works for both frontends
**Cons:** Adds latency to settings endpoint, potential rate limiting

### Option B: Validate Key Once on Save

1. When saving API key, test it immediately
2. Store `api_key_valid: boolean` alongside the key
3. Use this flag for `ai_available`

**Pros:** No latency on settings load
**Cons:** Key could become invalid later (revoked, expired)

### Option C: Frontend Hides Tab, Backend Returns Errors

1. Modern frontend: Only show Tips tab if `ai_available`
2. Keep current behavior where invalid key causes error on use

**Pros:** Simple, minimal changes
**Cons:** Doesn't address invalid key scenario

## Implementation Plan (Option C - Minimal Fix)

### 1. Modern Frontend - Hide Tips Tab

**File:** `frontend/src/screens/RecipeDetail.tsx`

Update tab rendering to conditionally include Tips:
```tsx
const tabs = [
  { key: 'ingredients', label: 'Ingredients' },
  { key: 'instructions', label: 'Instructions' },
  { key: 'nutrition', label: 'Nutrition' },
  ...(settings?.ai_available ? [{ key: 'tips', label: 'Tips' }] : []),
] as const
```

### 2. Legacy Frontend - Already Correct

Legacy already hides the tab with `{% if ai_available %}`, so no changes needed.

## Affected Components

- `frontend/src/screens/RecipeDetail.tsx` - Tab rendering
- `apps/core/api.py` - Settings endpoint (if validating key)
- `apps/ai/api.py` - AI status endpoint (if validating key)

## Priority

Low - The current behavior shows a helpful message when AI is unavailable. This is a UX polish issue.

## Implementation

Per PHASE-8B-AI-FEATURES.md 8B.11 requirement: "Remove API key - ALL AI features hidden (no buttons visible)"

### Modern Frontend

**`frontend/src/screens/RecipeDetail.tsx`** - Conditionally render Tips tab:
```tsx
// Only show Tips tab when AI is available (8B.11 graceful degradation)
...(settings?.ai_available ? [{ key: 'tips' as const, label: 'Tips' }] : []),
```

**`frontend/src/screens/Home.tsx`** - Conditionally render Discover tab toggle:
```tsx
{/* Tab toggle - only show if AI is available (8B.11 graceful degradation) */}
{aiAvailable && (
  <div className="tab-toggle">...</div>
)}
```

Also updated favorites-only rendering when AI unavailable:
```tsx
activeTab === 'favorites' || !aiAvailable ? (
```

### Legacy Frontend

**`apps/legacy/templates/legacy/recipe_detail.html`** - Conditionally render Tips tab:
```html
{% if ai_available %}
<button type="button" class="tab" data-tab="tips">Tips</button>
{% endif %}
```

**`apps/legacy/templates/legacy/home.html`** - Conditionally render Discover tab toggle:
```html
{% if ai_available %}
<div class="tab-toggle">...</div>
{% endif %}
```

Also hid the "Discover Recipes" button in empty favorites state.

### Files Changed
- `frontend/src/screens/RecipeDetail.tsx` - Tips tab conditional
- `frontend/src/screens/Home.tsx` - Discover tab toggle conditional
- `apps/legacy/templates/legacy/recipe_detail.html` - Tips tab conditional
- `apps/legacy/templates/legacy/home.html` - Discover tab toggle conditional

## Related

- QA-027: Invalid AI model selection breaks features silently (Verified)

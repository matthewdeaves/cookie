# QA-046: Auto-Generate Tips When Viewing Tips Tab (Edge Case)

## Status
**RESOLVED** (2026-01-09) - Implemented for both Modern and Legacy frontends

## Issue

For recipes imported more than 60 seconds ago that have no tips (e.g., AI was unavailable at import time, or tips generation failed), users must manually click the "Generate Tips" button. Tips should auto-generate when the user views the Tips tab.

### Scenario

1. Recipe imported while AI service was down (no tips generated)
2. User views recipe later (> 60 seconds, so no polling)
3. User clicks Tips tab
4. Current: Shows "No cooking tips yet" with button
5. Expected: Auto-generates tips immediately

### Why This Happens

- **Recent recipes** (< 60s): Polling mechanism fetches tips as they're generated
- **Old recipes without tips**: No polling, no auto-generation - requires button click

## Affected Components

- **React**: `frontend/src/screens/RecipeDetail.tsx`
- **Legacy**: `apps/legacy/static/legacy/js/pages/detail.js`

## Priority

Low - Edge case, main flows (import, remix) already auto-generate tips

## Implementation Plan

### React Frontend

Add useEffect that triggers when Tips tab becomes active:

```typescript
// Auto-generate tips when viewing Tips tab for recipes without tips
useEffect(() => {
  if (
    activeTab === 'tips' &&
    tips.length === 0 &&
    settings?.ai_available &&
    !tipsLoading &&
    !tipsPolling
  ) {
    handleGenerateTips(false)
  }
}, [activeTab, tips.length, settings?.ai_available, tipsLoading, tipsPolling])
```

### Legacy Frontend

Add click handler for Tips tab that triggers generation:

```javascript
// In setupEventListeners() or tab click handler
function handleTipsTabClick() {
  var hasTips = document.querySelectorAll('.tip-item').length > 0;
  var aiAvailable = window.Cookie && Cookie.settings && Cookie.settings.ai_available;

  if (!hasTips && aiAvailable && !isGeneratingTips && !tipsPollingState.isPolling) {
    generateTips();
  }
}
```

## Files to Modify

| File | Change |
|------|--------|
| `frontend/src/screens/RecipeDetail.tsx` | Add useEffect for auto-generation on tab view |
| `apps/legacy/static/legacy/js/pages/detail.js` | Add auto-generation on Tips tab click |

## Acceptance Criteria

- [x] React: Tips auto-generate when clicking Tips tab (if no tips exist)
- [x] React: Loading spinner shown during generation
- [x] React: No duplicate API calls if already loading/polling
- [x] Legacy: Tips auto-generate when clicking Tips tab (if no tips exist)
- [x] Legacy: Loading state shown during generation
- [x] Legacy: No duplicate calls if already generating/polling

---

## Implementation (2026-01-09)

### React Frontend (`frontend/src/screens/RecipeDetail.tsx:110-122`)

Added useEffect that triggers on tab change:

```typescript
// Auto-generate tips when viewing Tips tab for old recipes without tips (QA-046)
useEffect(() => {
  if (
    activeTab === 'tips' &&
    tips.length === 0 &&
    settings?.ai_available &&
    !tipsLoading &&
    !tipsPolling &&
    recipe
  ) {
    handleGenerateTips(false)
  }
}, [activeTab]) // Only trigger on tab change
```

### Legacy Frontend

**Template** (`apps/legacy/templates/legacy/recipe_detail.html:11`):
- Added `data-ai-available` attribute to page element

**JavaScript** (`apps/legacy/static/legacy/js/pages/detail.js:286-295`):

Added auto-generation logic in `handleTabClick()`:

```javascript
// QA-046: Auto-generate tips when viewing Tips tab for old recipes without tips
if (tabName === 'tips') {
    var pageEl = document.querySelector('[data-page="recipe-detail"]');
    var aiAvailable = pageEl && pageEl.getAttribute('data-ai-available') === 'true';
    var hasTips = document.querySelectorAll('.tips-list .tip-item').length > 0;

    if (aiAvailable && !hasTips && !isGeneratingTips && !tipsPollingState.isPolling) {
        handleGenerateTips(false);
    }
}
```

### Files Changed

| File | Change |
|------|--------|
| `frontend/src/screens/RecipeDetail.tsx` | Added useEffect for auto-generation on tab view |
| `apps/legacy/templates/legacy/recipe_detail.html` | Added `data-ai-available` attribute |
| `apps/legacy/static/legacy/js/pages/detail.js` | Added auto-generation in `handleTabClick()` |

# QA-045: Recipe Scaling Shows "(was X min)" for Unchanged Times

## Status
**RESOLVED** - Implemented frontend comparison

## Issue

When scaling recipes, the "(was X min)" label appears next to prep_time, cook_time, and total_time even when those times haven't changed. The label should only appear next to times that actually changed.

### Example
- **Original recipe:** Prep 15 min, Cook 30 min, Total 45 min
- **Scaled (small adjustment):** Times unchanged
- **Current display:** "15 min (was 15 min)" - redundant and confusing
- **Expected display:** "15 min" - no change label needed

### Desired Behavior
Show/hide the "(was X min)" label on an individual basis per time field:
- If prep stayed same but cook changed: only show "(was X min)" next to cook time
- If all times changed: show "(was X min)" next to all three
- If no times changed: show no "(was X min)" labels at all

## Current Implementation

### Data Flow
```
User adjusts servings
    ↓
Frontend calls /api/ai/scale
    ↓
AI returns: prep_time_adjusted, cook_time_adjusted, total_time_adjusted
    ↓
Frontend checks if adjusted values EXIST (not if they DIFFER)
    ↓
Shows "(was X min)" whenever adjusted value is present
```

### Modern Frontend (React)
**File:** `frontend/src/screens/RecipeDetail.tsx:313-371`

```typescript
// Current logic - checks existence only
{scaledData?.prep_time_adjusted ? (
  <>
    {formatTime(scaledData.prep_time_adjusted)}
    <span className="ml-1 text-muted-foreground">
      (was {formatTime(recipe.prep_time)})
    </span>
  </>
) : (
  formatTime(recipe.prep_time)
)}
```

### Legacy Frontend (Vanilla JS)
**File:** `apps/legacy/static/legacy/js/pages/detail.js:673-696`

```javascript
// Current logic - always shows "(was X)" when adjusted data exists
function renderAdjustedTimes() {
    if (!adjustedTimes) return;

    var timeTypes = ['prep', 'cook', 'total'];
    for (var i = 0; i < timeTypes.length; i++) {
        var type = timeTypes[i];
        var adjusted = adjustedTimes[type];
        if (!adjusted) continue;

        var el = document.querySelector('[data-time-type="' + type + '"]');
        if (el) {
            var valueEl = el.querySelector('.time-value');
            if (valueEl) {
                if (!valueEl.getAttribute('data-original')) {
                    valueEl.setAttribute('data-original', valueEl.textContent);
                }
                var original = valueEl.getAttribute('data-original');
                // Always shows "(was X)" - doesn't compare values
                valueEl.innerHTML = formatTime(adjusted) + ' <span class="time-was">(was ' + original + ')</span>';
            }
        }
    }
}
```

## Proposed Solution

### Option A: Frontend Comparison (Recommended)

Compare adjusted time with original time before showing the label.

**Modern Frontend Fix:**
```typescript
{scaledData?.prep_time_adjusted && scaledData.prep_time_adjusted !== recipe.prep_time ? (
  <>
    {formatTime(scaledData.prep_time_adjusted)}
    <span className="ml-1 text-muted-foreground">
      (was {formatTime(recipe.prep_time)})
    </span>
  </>
) : (
  formatTime(scaledData?.prep_time_adjusted ?? recipe.prep_time)
)}
```

**Legacy Frontend Fix:**
```javascript
var adjustedMinutes = adjusted; // already in minutes
var originalMinutes = parseTimeToMinutes(original); // need to parse

if (adjustedMinutes !== originalMinutes) {
    valueEl.innerHTML = formatTime(adjusted) + ' <span class="time-was">(was ' + original + ')</span>';
    valueEl.classList.add('time-adjusted');
} else {
    // Time unchanged - just show the value, no "(was X)"
    valueEl.textContent = formatTime(adjusted);
    valueEl.classList.remove('time-adjusted');
}
```

### Option B: Backend Null for Unchanged

Have the backend return `null` for times that didn't change, only returning values when they differ.

**Pros:** Frontend logic stays simple
**Cons:** Requires backend changes, loses information about what was calculated

## Files to Modify

| File | Change |
|------|--------|
| `frontend/src/screens/RecipeDetail.tsx` | Add comparison before showing "(was X)" |
| `apps/legacy/static/legacy/js/pages/detail.js` | Add comparison in `renderAdjustedTimes()` |

## Acceptance Criteria

### Modern Frontend (React)
- [x] "(was X min)" only shows when adjusted time differs from original
- [x] Each time field (prep, cook, total) evaluated independently
- [x] If all times unchanged, no "(was X)" labels appear anywhere
- [x] If only some times changed, only those show the label

### Legacy Frontend (Django/JS)
- [x] "(was X min)" only shows when adjusted time differs from original
- [x] Each time field (prep, cook, total) evaluated independently
- [x] If all times unchanged, no "(was X)" labels appear anywhere
- [x] If only some times changed, only those show the label

## Priority

Low - UX polish, not blocking core functionality

## Research Findings

### Key Files Reference

| Component | File | Lines |
|-----------|------|-------|
| Modern Frontend Display | `frontend/src/screens/RecipeDetail.tsx` | 313-371 |
| Modern Time Formatting | Same file | 130-136 |
| Legacy Template | `apps/legacy/templates/legacy/recipe_detail.html` | 125-156 |
| Legacy JS Rendering | `apps/legacy/static/legacy/js/pages/detail.js` | 673-714 |
| Legacy CSS Styling | `apps/legacy/static/legacy/css/recipe-detail.css` | 952-960 |
| Backend Parsing | `apps/ai/services/scaling.py` | 155-172 |
| API Schema (Backend) | `apps/ai/api.py` | 315-326 |
| API Schema (Frontend) | `frontend/src/api/client.ts` | 59-70 |

### Time Data Types

- **Backend:** Returns times as `Optional[int]` (minutes)
- **Frontend API types:** `number | null`
- **Recipe object:** `prep_time`, `cook_time`, `total_time` as integers (minutes)
- **Comparison:** Direct integer comparison possible

### Implementation Notes

1. **Modern frontend** has direct access to `recipe.prep_time` etc. for comparison
2. **Legacy frontend** stores original in `data-original` attribute as formatted string - will need to either:
   - Parse it back to minutes for comparison, OR
   - Store original minutes in a separate data attribute, OR
   - Compare formatted strings (simpler but slightly less robust)
3. The `formatTime()` functions are identical in both frontends - comparing formatted output would work

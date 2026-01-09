# QA-049: Recipe Import Fails on Both Modern and Legacy Frontends

## Status
**FIXED** - Awaiting verification

## Issue

When attempting to import a recipe from search results, the import fails on both frontends.

### Current Behavior

**Modern frontend:**
- User searches for recipes
- User clicks to import a recipe from search results
- Error displayed: "Failed to import recipe. Please check the URL."

**Legacy frontend (iPad):**
- User searches for recipes
- User clicks to import a recipe from search results
- Error displayed: Internal server error

### Expected Behavior
- Recipe should be scraped and imported successfully

## Root Cause Analysis

### Primary Issue: No Profile in Session

The scrape endpoint now requires a profile (per QA-047):

```python
# apps/recipes/api.py:171-173
profile = get_current_profile_or_none(request)
if not profile:
    return 403, {'detail': 'Profile required to scrape recipes'}
```

If no profile is selected, the API returns `403` with a JSON error message.

### Secondary Issue: Modern Frontend Error Handling

The modern frontend's API client doesn't properly parse JSON error responses:

```typescript
// frontend/src/api/client.ts:233-234
if (!response.ok) {
  const error = await response.text()  // ← Gets raw JSON string, not parsed
  throw new Error(error || `Request failed with status ${response.status}`)
}
```

When the API returns `403 {"detail": "Profile required to scrape recipes"}`, the code:
1. Gets the raw JSON string via `response.text()`
2. Throws an error with the raw JSON as the message
3. `App.tsx` catches this and shows generic: "Failed to import recipe. Please check the URL."

**User never sees the real problem: no profile selected.**

### Legacy Frontend Error Handling

The legacy frontend (`apps/legacy/static/legacy/js/ajax.js:37-46`) actually handles this correctly:
```javascript
var errorData = JSON.parse(xhr.responseText);
errorMsg = errorData.detail || errorData.message || errorMsg;
```

So legacy should show "Profile required to scrape recipes" - if it shows "Internal server error" there may be a different issue (possibly the profile not being set in session at all).

## Fix Required

### Fix 1: Modern Frontend Error Handling (Critical)

Update `frontend/src/api/client.ts` to parse JSON error responses:

```typescript
if (!response.ok) {
  let error: string
  try {
    const errorData = await response.json()
    error = errorData.detail || errorData.message || `Request failed with status ${response.status}`
  } catch {
    error = await response.text() || `Request failed with status ${response.status}`
  }
  throw new Error(error)
}
```

### Fix 2: Ensure Profile Context

Verify that:
1. Profile selection is working (`/api/profiles/{id}/select/`)
2. Session is properly storing `profile_id`
3. Both frontends select a profile before allowing recipe import

## Affected Components

- `frontend/src/api/client.ts` - Error handling broken
- `/api/recipes/scrape/` endpoint - Working correctly (returns 403)
- Session/profile context - May not be set

## Priority

High - Core functionality broken on all platforms

## Implementation

### Fix Applied

Updated `frontend/src/api/client.ts` to parse JSON error responses:

```typescript
if (!response.ok) {
  let errorMessage: string
  try {
    const errorData = await response.json()
    errorMessage = errorData.detail || errorData.message || `Request failed with status ${response.status}`
  } catch {
    // Response wasn't JSON, try text
    const errorText = await response.text()
    errorMessage = errorText || `Request failed with status ${response.status}`
  }
  throw new Error(errorMessage)
}
```

Updated `frontend/src/App.tsx` to show actual error message:

```typescript
} catch (error) {
  console.error('Failed to import recipe:', error)
  const message = error instanceof Error ? error.message : 'Failed to import recipe'
  toast.error(message)
  throw error
}
```

**Files Changed:**
- `frontend/src/api/client.ts:232-243` - Parse JSON error responses
- `frontend/src/App.tsx:138-143` - Show actual error message in toast

**Result:** Users now see "Profile required to scrape recipes" instead of generic "Failed to import recipe. Please check the URL."

## Related

- QA-047: Recipe profile isolation (introduced the profile requirement)

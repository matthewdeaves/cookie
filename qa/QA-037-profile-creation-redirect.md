# QA-037: Auto-Navigate to Home After Profile Creation

## Status
**RESOLVED** (2026-01-09) - Verified on Modern and Legacy frontends

## Issue
After creating a new profile, the user stays on the profile selector screen. They should automatically be taken to the home/search page.

## Current Behavior
1. User opens app
2. User clicks "Create Profile"
3. User enters name and creates profile
4. User stays on profile selector screen
5. User must manually select the new profile to proceed

## Expected Behavior
1. User opens app
2. User clicks "Create Profile"
3. User enters name and creates profile
4. User is automatically logged in as the new profile and taken to home/search page

## Affected Components
- **React**: `ProfileSelector.tsx` - profile creation flow
- **Legacy**: Profile creation in legacy templates/JS

## Priority
Low - UX improvement, minor friction

## Phase
TBD

---

## Research Findings

### Root Cause

The `onProfileSelect(profile)` callback is never called after profile creation. The profile is created and added to the list, but the user is not automatically logged in.

### React Implementation

**File:** `frontend/src/screens/ProfileSelector.tsx`

**Current flow (lines 50-74):**
```typescript
const handleCreateProfile = async (e: React.FormEvent) => {
  // ... validation ...
  const profile = await api.profiles.create(data)  // Line 62
  setProfiles([...profiles, profile])               // Line 63
  setShowCreateForm(false)                          // Line 64
  toast.success(`Welcome, ${profile.name}!`)        // Line 67
  // MISSING: onProfileSelect(profile) to auto-login and navigate
}
```

**Fix:** Add `onProfileSelect(profile)` after line 63 (after `setProfiles()`).

The `onProfileSelect` callback (defined in `App.tsx:85-93`) handles:
1. Calling `api.profiles.select(profile.id)`
2. Setting `currentProfile` state
3. Navigating to home via `setCurrentScreen('home')`

### Legacy Implementation

**File:** `apps/legacy/static/legacy/js/pages/profile-selector.js`

**Current flow (lines 160-192):**
```javascript
function handleCreateProfile(e) {
  // ... validation ...
  Cookie.ajax.post('/profiles/', data, function(err, profile) {
    Cookie.toast.success('Welcome, ' + profile.name + '!')
    addProfileToGrid(profile)      // Line 188
    hideCreateForm()               // Line 191
    // MISSING: selectProfile(profile.id) to auto-login and navigate
  })
}
```

**Fix:** Add `selectProfile(profile.id)` after line 188 (after `addProfileToGrid()`).

The `selectProfile()` function (lines 113-126) handles:
1. POST to `/profiles/{id}/select/`
2. Storing in `Cookie.state`
3. Navigating to `/legacy/home/`

### Implementation Summary

| Platform | File | Location | Change |
|----------|------|----------|--------|
| React | `frontend/src/screens/ProfileSelector.tsx` | After line 63 | Add `onProfileSelect(profile)` |
| Legacy | `apps/legacy/static/legacy/js/pages/profile-selector.js` | After line 188 | Add `selectProfile(profile.id)` |

### Effort Estimate

Very small - 1 line addition per platform.

---

## Fix Implementation

### React (`frontend/src/screens/ProfileSelector.tsx`)
Added `onProfileSelect(profile)` after `setProfiles()` in `handleCreateProfile()`:
```typescript
const profile = await api.profiles.create(data)
setProfiles([...profiles, profile])
onProfileSelect(profile)  // NEW: Auto-select and navigate
```

### Legacy (`apps/legacy/static/legacy/js/pages/profile-selector.js`)
Added `selectProfile(profile.id)` after `addProfileToGrid()` in `handleCreateProfile()`:
```javascript
addProfileToGrid(profile);
selectProfile(profile.id);  // NEW: Auto-select and navigate
```

Note: Removed `hideCreateForm()` call in Legacy since `selectProfile()` navigates away from the page.

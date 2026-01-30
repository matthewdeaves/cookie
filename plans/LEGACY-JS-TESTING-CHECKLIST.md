# Legacy JavaScript Manual Testing Checklist

> **Purpose:** Verify legacy ES5 JavaScript functionality during Phase 6 refactoring
> **Last Updated:** 2026-01-30
> **Run Before/After:** Each significant refactoring change

---

## Test Environment Setup

```bash
# Start the development server
docker compose up -d

# Open legacy frontend at
http://localhost:8000/legacy/
```

---

## Critical User Flows

### 1. Profile Selection (`profile-selector.js`)

| Step | Action | Expected Result | Pass |
|------|--------|-----------------|------|
| 1.1 | Load `/legacy/` without active profile | Profile selector page displays | [ ] |
| 1.2 | Click "Create Profile" | Name input and color picker appear | [ ] |
| 1.3 | Enter name, select color, submit | Profile created, redirects to home | [ ] |
| 1.4 | Return to `/legacy/` | Profile selector shows existing profile | [ ] |
| 1.5 | Click existing profile | Redirects to home page | [ ] |

### 2. Home Page (`home.js`)

| Step | Action | Expected Result | Pass |
|------|--------|-----------------|------|
| 2.1 | Load home page | Recent recipes display (if any) | [ ] |
| 2.2 | Click "Favorites" tab | Favorites tab content shows | [ ] |
| 2.3 | Click "Discover" tab (if AI enabled) | Loading state, then suggestions | [ ] |
| 2.4 | Click refresh on discover | New suggestions load | [ ] |
| 2.5 | Click favorite heart on recipe card | Heart fills, toast shows "Added to favorites" | [ ] |
| 2.6 | Click filled heart again | Heart empties, toast shows "Removed" | [ ] |
| 2.7 | Submit search form with query | Redirects to search results | [ ] |
| 2.8 | Click discover suggestion card | Redirects to search with query | [ ] |

### 3. Search Results (`search.js`)

| Step | Action | Expected Result | Pass |
|------|--------|-----------------|------|
| 3.1 | Search for "pasta" | Results grid displays | [ ] |
| 3.2 | Observe images | Images load progressively (polling) | [ ] |
| 3.3 | Click source filter chip | Results filter to that source | [ ] |
| 3.4 | Click "All Sources" chip | All results show again | [ ] |
| 3.5 | Click "Load More" (if available) | More results append | [ ] |
| 3.6 | Click "Import" on result | Button shows "Importing...", then redirects | [ ] |
| 3.7 | Search for URL directly | URL import card appears | [ ] |

### 4. Recipe Detail (`detail.js`)

| Step | Action | Expected Result | Pass |
|------|--------|-----------------|------|
| 4.1 | View imported recipe | Recipe details display | [ ] |
| 4.2 | Click back button | Returns to previous page | [ ] |
| 4.3 | Click meta section toggle | Meta section expands/collapses | [ ] |
| 4.4 | Click "Ingredients" tab | Ingredients list shows | [ ] |
| 4.5 | Click "Instructions" tab | Instructions list shows | [ ] |
| 4.6 | Click "Tips" tab | Tips show (or generate button) | [ ] |
| 4.7 | Click favorite button | Favorite toggles, toast shows | [ ] |
| 4.8 | Click serving + button | Servings increase, AI scales ingredients | [ ] |
| 4.9 | Click serving - button | Servings decrease (min 1) | [ ] |
| 4.10 | Click "Collections" button | Collection modal opens | [ ] |
| 4.11 | Select collection in modal | Recipe added, toast shows | [ ] |
| 4.12 | Click "Create Collection" in modal | Create modal opens | [ ] |
| 4.13 | Create new collection with name | Collection created, recipe added | [ ] |
| 4.14 | Click "Remix" button (if AI enabled) | Remix modal opens, suggestions load | [ ] |
| 4.15 | Click remix suggestion chip | Chip becomes active | [ ] |
| 4.16 | Enter custom remix text | Chips deselect, text used | [ ] |
| 4.17 | Click "Create Remix" | Remix creates, redirects to new recipe | [ ] |
| 4.18 | Click "Generate Tips" (if no tips) | Tips generate and display | [ ] |
| 4.19 | Click "Regenerate Tips" | New tips generate | [ ] |
| 4.20 | Click "Cook" button | Play mode page loads | [ ] |

### 5. Play Mode (`play.js`, `timer.js`)

| Step | Action | Expected Result | Pass |
|------|--------|-----------------|------|
| 5.1 | Enter play mode from recipe | First instruction displays | [ ] |
| 5.2 | Click next step button | Next instruction shows | [ ] |
| 5.3 | Click previous step button | Previous instruction shows | [ ] |
| 5.4 | Click step dot indicator | Jumps to that step | [ ] |
| 5.5 | Use keyboard arrows | Steps navigate | [ ] |
| 5.6 | Click quick timer (1m, 5m, etc.) | Timer adds to panel | [ ] |
| 5.7 | Click detected time in instruction | Timer adds with AI name (if enabled) | [ ] |
| 5.8 | Observe timer counting | Timer counts down | [ ] |
| 5.9 | Click pause on timer | Timer pauses | [ ] |
| 5.10 | Click resume on timer | Timer resumes | [ ] |
| 5.11 | Click reset on timer | Timer resets to original | [ ] |
| 5.12 | Let timer complete | Toast notification, audio plays | [ ] |
| 5.13 | Click delete on timer | Timer removes from list | [ ] |
| 5.14 | Toggle timer panel collapse | Panel collapses/expands | [ ] |
| 5.15 | Click exit button | Returns to recipe detail | [ ] |

### 6. Settings Page (`settings.js`)

#### 6A. General Tab
| Step | Action | Expected Result | Pass |
|------|--------|-----------------|------|
| 6.1 | Load settings page | General tab active by default | [ ] |
| 6.2 | Enter API key in input | Test/Save buttons enable | [ ] |
| 6.3 | Click "Test Key" | Shows "Testing...", then result toast | [ ] |
| 6.4 | Click "Save Key" | Shows "Saving...", reloads page on success | [ ] |

#### 6B. Prompts Tab
| Step | Action | Expected Result | Pass |
|------|--------|-----------------|------|
| 6.5 | Click "Prompts" tab | Prompts tab displays | [ ] |
| 6.6 | Click expand on prompt card | Prompt content reveals | [ ] |
| 6.7 | Click "Edit" on prompt | Edit form shows | [ ] |
| 6.8 | Toggle status button | Status changes Active/Disabled | [ ] |
| 6.9 | Edit prompt text, click "Save" | Saves, toast confirms | [ ] |
| 6.10 | Click "Cancel" edit | Edit form closes | [ ] |

#### 6C. Sources Tab
| Step | Action | Expected Result | Pass |
|------|--------|-----------------|------|
| 6.11 | Click "Sources" tab | Sources list displays with counter | [ ] |
| 6.12 | Click toggle on source | Source enables/disables | [ ] |
| 6.13 | Click "Enable All" | All sources enable | [ ] |
| 6.14 | Click "Disable All" | All sources disable | [ ] |

#### 6D. Selectors Tab
| Step | Action | Expected Result | Pass |
|------|--------|-----------------|------|
| 6.15 | Click "Selectors" tab | Selectors list with status icons | [ ] |
| 6.16 | Click "Test" on selector | Test runs, result toast shows | [ ] |
| 6.17 | Click "Test All Sources" | Batch test runs, summary toast | [ ] |
| 6.18 | Click "Edit" on selector | Edit input appears | [ ] |
| 6.19 | Edit selector, click "Save" | Selector updates | [ ] |
| 6.20 | Click "Cancel" selector edit | Edit closes | [ ] |

#### 6E. Users Tab
| Step | Action | Expected Result | Pass |
|------|--------|-----------------|------|
| 6.21 | Click "Users" tab | Profile list loads | [ ] |
| 6.22 | Observe current profile | Shows "Current" badge | [ ] |
| 6.23 | Click delete on non-current profile | Deletion preview modal opens | [ ] |
| 6.24 | Modal shows data to delete | Profile info and data summary | [ ] |
| 6.25 | Click "Delete Profile" in modal | Profile deletes, modal closes | [ ] |
| 6.26 | Click delete on current profile | Button is disabled | [ ] |

#### 6F. Danger Zone Tab
| Step | Action | Expected Result | Pass |
|------|--------|-----------------|------|
| 6.27 | Click "Danger Zone" tab | Reset database section shows | [ ] |
| 6.28 | Click "Reset Database" | Step 1 modal shows data preview | [ ] |
| 6.29 | Click "Continue" | Step 2 shows confirmation input | [ ] |
| 6.30 | Type "RESET" in input | Confirm button enables | [ ] |
| 6.31 | Click "Cancel" | Modal closes | [ ] |
| 6.32 | (Optional) Click "Reset Database" | Database resets, redirects to profile selector | [ ] |

### 7. Collections Pages (`collections.js`, `collection-detail.js`)

| Step | Action | Expected Result | Pass |
|------|--------|-----------------|------|
| 7.1 | Navigate to collections list | Collections display | [ ] |
| 7.2 | Click collection | Collection detail page loads | [ ] |
| 7.3 | View recipes in collection | Recipe cards display | [ ] |
| 7.4 | Remove recipe from collection | Recipe removes | [ ] |

### 8. Favorites Page (`favorites.js`)

| Step | Action | Expected Result | Pass |
|------|--------|-----------------|------|
| 8.1 | Navigate to favorites | Favorite recipes display | [ ] |
| 8.2 | Click unfavorite on card | Recipe removes from list | [ ] |

---

## Console Error Check

After each major change, open browser DevTools (F12) and verify:

| Check | Expected | Pass |
|-------|----------|------|
| No JavaScript errors in console | Console clean | [ ] |
| No 404 errors for JS files | All scripts load | [ ] |
| No undefined function errors | All functions defined | [ ] |

---

## Cross-Browser Testing (iOS 9 Compatibility)

If available, test on:

| Browser | Status |
|---------|--------|
| Safari (iOS 9/10) | [ ] |
| Chrome (Latest) | [ ] |
| Firefox (Latest) | [ ] |
| Safari (macOS) | [ ] |

---

## Regression Testing After Refactoring

After each Phase 6 task completion:

1. [ ] Run through critical flows (sections 1-6 above)
2. [ ] Check console for errors
3. [ ] Verify all toasts display correctly
4. [ ] Test on mobile viewport size

---

## Quick Smoke Test (5 minutes)

For rapid verification after small changes:

1. [ ] Profile selection works
2. [ ] Search returns results
3. [ ] Recipe imports successfully
4. [ ] Favorite toggle works
5. [ ] Settings tabs switch
6. [ ] Play mode timer works

---

## Notes

- **Toast messages** are the primary user feedback mechanism
- **AI features** may not work without API key configured
- **Progressive image loading** requires search results with external images
- **Timer audio** requires user interaction to unlock on iOS

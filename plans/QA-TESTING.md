# QA Testing Issues

> **Purpose:** Track issues found during manual testing and fix them in focused sessions
> **Workflow:** Test & Log → Research → Fix → Verify

---

## Issue Log

| ID | Summary | Affects | Status | Session |
|----|---------|---------|--------|---------|
| QA-001 | Navigation bar missing menu links | Legacy | Verified | QA-A |
| QA-002 | No way to view all imported recipes | Legacy + Modern | Verified | QA-B |
| QA-003 | Numbered list styling inconsistent | Legacy + Modern | Verified | QA-C |
| QA-004 | Back button returns to Play Mode after closing it | Legacy | Verified | QA-D |
| QA-005 | No "View All Recipes" link on home page | Legacy + Modern | Verified | QA-E |
| QA-006 | Insufficient spacing between list number and text | Legacy | New | QA-F |

### Status Key
- **New** - Logged, not yet fixed
- **Fixed** - Code changed, awaiting verification
- **Verified** - Confirmed working on device
- **Won't Fix** - Intentional or out of scope

---

## How to Run QA Sessions

QA sessions follow the same pattern as implementation phases. Use `/clear` between sessions.

### Starting a Research Session

Research the issue before defining tasks. This prevents fixes that violate existing patterns.

```
/clear
"Read plans/QA-TESTING.md and research QA-B. Investigate how the existing codebase handles imported recipes. Check the Modern frontend pattern and Figma design intent. Update the Research Findings section."
```

### Starting a Fix Session

After research is complete and tasks are defined:

```
/clear
"Read plans/QA-TESTING.md and implement QA-B. Follow the tasks defined in the session plan. The research findings show the patterns to follow."
```

### After Each Session

1. Confirm fix is deployed (dev server restarted, no build errors)
2. Clear caches (hard refresh, Cmd+Shift+R / Ctrl+Shift+R)
3. Verify new code is running (check a changed element or behavior)
4. Test fix on target device (iPad 3 / iOS 9 or modern browser)
5. Update issue status (Fixed/Verified/Won't Fix)
6. Run `/clear`
7. Start next session or log new issues discovered

---

## Fix Plan

### Session Scope

| Session | Issue | Focus |
|---------|-------|-------|
| QA-A | QA-001 | Legacy navigation bar |
| QA-B | QA-002 | Imported recipes visibility |
| QA-C | QA-003 | List styling consistency |
| QA-D | QA-004 | Play mode history navigation |
| QA-E | QA-005 | View All Recipes link |
| QA-F | QA-006 | List number/text spacing |

---

### QA-A: Legacy Navigation Bar

**Issue:** QA-001 - Navigation bar missing menu links
**Affects:** Legacy
**Status:** Verified

**Problem:**
The legacy header only shows the profile icon (top right). No navigation links to Favorites, Collections, or Search. Users cannot navigate between sections without using browser back or typing URLs.

**Screenshots:** `ipadscreenshots/IMG_0012.PNG`, `ipadscreenshots/IMG_0017.PNG`

**Research Findings:** _(Retrospective - research phase added after this fix)_
- _Existing pattern:_ Modern frontend uses header icons; Legacy should match
- _Design intent:_ Figma shows header navigation, not bottom nav
- _Lesson:_ Initial fix considered bottom nav; research would have shown header icons are the established pattern

**Tasks:**
- [x] Check Figma design for legacy navigation intent
- [x] Compare with modern frontend navigation pattern
- [x] Implement navigation (header links or bottom nav)
- [x] Ensure touch targets meet 44px minimum for iOS
- [x] Test ES5/CSS compatibility

**Implementation:**
- Added header navigation icons (Favorites heart, Collections book) to home page header
- Icons placed between "Cookie" title and profile avatar
- CSS uses -webkit prefixes for iOS 9 flexbox compatibility
- Touch targets are 44x44px (meets iOS minimum)
- Uses pure HTML/CSS anchor tags (no JavaScript required)

**Files Changed:**
- `apps/legacy/static/legacy/css/layout.css` - Added `.header-nav` and `.header-nav-link` styles
- `apps/legacy/templates/legacy/home.html` - Added nav icons to header

**Verification:**
- [x] Navigation icons visible in home page header (heart + book icons)
- [x] Can navigate to Favorites from home
- [x] Can navigate to Collections from home
- [x] Icons are tappable on iPad 3 / iOS 9
- [ ] No JavaScript errors in console

---

### QA-B: Imported Recipes Visibility

**Issue:** QA-002 - No way to view all imported recipes
**Affects:** Legacy + Modern
**Status:** Verified

**Problem:**
After importing a recipe, user is redirected to home but the recipe doesn't appear in "Recently Viewed" (only viewed recipes appear there). No "My Recipes" or "All Recipes" section exists. Users must search again to find recipes they just imported.

**Screenshots:** `ipadscreenshots/IMG_0016.PNG`, `ipadscreenshots/IMG_0017.PNG`

**Research Findings:**

_How existing code handles this:_
- **Legacy (`search.js:321-350`):** After import success, shows toast "Recipe imported!" and redirects to `/legacy/home/` after 1 second. Does NOT record the recipe in view history.
- **Modern (`App.tsx:112-127`):** After import success, shows toast, records recipe in history via `api.history.record()`, then navigates to recipe detail page. The recipe immediately appears in "Recently Viewed" because it was recorded in history.
- **API:** The scrape endpoint returns the full recipe object including `id`, which Modern uses to navigate and record history.

_Design intent (Figma):_
- Figma prototype uses "Simulate Import" button that goes to home (for prototyping simplicity)
- Home page has "Recently Viewed" section with "View All" link to an "all-recipes" screen
- Design intent: users should access imported recipes through Recently Viewed
- The Modern frontend correctly implements this by recording imports in history

_Established patterns to follow:_
- **Modern frontend is the reference implementation** - it correctly handles post-import flow
- Pattern: Import → Record in history → Navigate to recipe detail
- This ensures: (1) User sees the recipe immediately, (2) Recipe appears in Recently Viewed

_Root cause:_
- Legacy redirects to home without recording history or navigating to the recipe
- Modern correctly navigates to recipe detail AND records in history

**Recommended Fix:** Update Legacy to match Modern behavior:
1. After successful import, redirect to recipe detail page (not home)
2. The recipe detail page already records views, so no additional history call needed

**Tasks:**
- [x] Update Legacy `search.js` to redirect to recipe detail after import
- [x] Pass recipe ID from scrape API response to build redirect URL
- [x] Test import → redirect → recipe visible in Recently Viewed
- [x] Verify on iPad 3 / iOS 9

**Implementation:**
- Updated `search.js:346-347` to redirect to `/legacy/recipe/{id}/` instead of `/legacy/home/`
- The recipe detail view (`views.py:108-113`) already records view history
- After import, user sees the recipe immediately and it appears in Recently Viewed

**Files Changed:**
- `apps/legacy/static/legacy/js/pages/search.js` - Changed import redirect URL

**Verification:**
- [x] After importing a recipe, user can immediately find it
- [x] Works on Legacy (iPad 3 / iOS 9)
- [x] Works on Modern (desktop browser) - already worked correctly
- [x] Clear path from import -> viewing the recipe

---

### QA-C: List Styling Consistency

**Issue:** QA-003 - Numbered list styling inconsistent
**Affects:** Legacy + Modern
**Status:** Verified

**Problem:**
Numbered lists for ingredients and instructions have different styling between legacy and modern frontends.

**Screenshots:** _Need comparison screenshots from both frontends_

**Research Findings:**

_How existing code handles this:_
- **Legacy (`recipe-detail.css:384-461`):**
  - Ingredients: 24px circle, `--muted` background, `--muted-foreground` text
  - Instructions: 28px circle, `--primary` background, `--primary-foreground` text
- **Modern (`RecipeDetail.tsx:355, 401`):**
  - Ingredients: `h-6 w-6` (24px), `bg-muted`, `text-muted-foreground`
  - Instructions: `h-7 w-7` (28px), `bg-primary`, `text-primary-foreground`
- Both frontends are **consistent with each other** but differ from Figma

_Design intent (Figma - `App.tsx:1559, 1572`):_
- **Both ingredients AND instructions use identical styling:**
  - `w-7 h-7` (28px) circle
  - `bg-primary text-primary-foreground` (green background, white text)
  - `text-sm font-medium`

_Discrepancy:_
| List | Current (Both) | Figma Design |
|------|----------------|--------------|
| Ingredients | 24px gray badge | 28px green badge |
| Instructions | 28px green badge | 28px green badge |

_Root cause:_
Implementation intentionally differentiated ingredients (gray) from instructions (green) for visual hierarchy, but Figma shows them identical.

**Decision:** Match Figma exactly - both ingredients and instructions use green (primary) badges.

**Tasks:**
- [x] Decide: Match Figma (both green) or keep current differentiation
- [x] Update Legacy `recipe-detail.css` ingredient styles
- [x] Update Modern `RecipeDetail.tsx` IngredientsTab component
- [x] Ensure iOS 9 CSS compatibility for legacy

**Implementation:**
- Updated `recipe-detail.css:399-415` - Changed `.ingredient-number` from muted to primary colors, size from 1.5rem to 1.75rem
- Updated `RecipeDetail.tsx:355,372` - Changed ingredient badges from `h-6 w-6 bg-muted text-muted-foreground` to `h-7 w-7 bg-primary text-primary-foreground`

**Files Changed:**
- `apps/legacy/static/legacy/css/recipe-detail.css`
- `frontend/src/screens/RecipeDetail.tsx`

**Verification:**
- [x] Ingredients list uses green badges (matches Figma)
- [x] Instructions list unchanged (already correct)
- [x] Consistent between Legacy and Modern
- [x] Works on iPad 3 / iOS 9 (legacy)

**Note:** Related issue QA-006 logged for spacing between number badge and text.

---

### QA-D: Play Mode History Navigation

**Issue:** QA-004 - Back button returns to Play Mode after closing it
**Affects:** Legacy
**Status:** Verified

**Problem:**
When a user navigates from Home → Recipe Detail → Play Mode, then closes Play Mode to return to Recipe Detail, pressing the browser back button incorrectly navigates back to Play Mode instead of returning to Home. Play Mode is being added to the browser history stack, causing unexpected back button behavior.

**Expected behavior:** Back button from Recipe Detail should return to the previous logical page (Home, Search, etc.), not to Play Mode which was just closed.

**Current flow (broken):**
1. User on Home page
2. User taps recipe → Recipe Detail page
3. User taps "Play" → Play Mode
4. User completes/closes Play Mode → Recipe Detail page
5. User taps Back → **Goes to Play Mode** (wrong!)

**Expected flow:**
1-4. Same as above
5. User taps Back → **Goes to Home** (correct)

**Note:** This issue does not affect the Modern frontend, which handles Play Mode navigation correctly.

**Research Findings:**

_How Modern frontend handles this:_
- Modern `PlayMode.tsx` is a React component that receives an `onExit` callback prop
- It never uses browser navigation - exit just calls `onExit()` which changes app state
- Browser history is never touched, so no back button issue exists

_How Legacy currently handles this:_
- Cook button in `detail.js:373`: `window.location.href = '/legacy/recipe/' + recipeId + '/play/'` - pushes to history
- Exit button in `play_mode.html:29`: `<a href="{% url 'legacy:recipe_detail' recipe.id %}">` - also pushes to history
- This creates history: `[Home, Recipe, Play, Recipe]` where Back from last Recipe goes to Play

_Root cause:_
- Legacy uses full page navigation for Play Mode entry AND exit
- Both push new entries onto history stack instead of replacing

_Browser history API solution:_
- `location.replace(url)` - navigates to URL but replaces current history entry (ES5 compatible)
- When exiting Play Mode, replace Play with Recipe in history: `[Home, Recipe, Play]` → `[Home, Recipe]`

**Tasks:**
- [x] Research how Modern frontend handles Play Mode navigation
- [x] Investigate browser history API options (`replaceState` vs `pushState`)
- [x] Determine best approach for Legacy (ES5 compatible)
- [x] Implement fix without affecting Modern frontend
- [x] Test back button behavior through full flow

**Implementation:**
- Added click handler for exit button in `play.js:116-134`
- Handler calls `e.preventDefault()` to stop the `<a>` link navigation
- Uses `window.history.back()` to go back to Recipe Detail (initial attempt with `location.replace()` had issues on iOS 9)
- This navigates back rather than forward, so Play Mode doesn't affect back button behavior
- Keyboard Escape key still works (triggers button click which fires our handler)
- Fallback to href navigation if no history (direct URL access edge case)

**Files Changed:**
- `apps/legacy/static/legacy/js/pages/play.js` - Added `handleExit()` function and event listener

**Verification:**
- [x] Play Mode → Close → Back returns to page before Recipe Detail
- [x] Normal Recipe Detail → Back still works correctly
- [x] Works on iPad 3 / iOS 9
- [x] Modern frontend behavior unchanged

---

### QA-E: View All Recipes Link

**Issue:** QA-005 - No "View All Recipes" link on home page
**Affects:** Legacy + Modern
**Status:** Verified

**Problem:**
The home page has limits on how many recipes are displayed:
- Recently Viewed: 6 recipes (Legacy), 6 recipes (Modern)
- Favorites section: Limited display

Users who import many recipes over time will eventually have older recipes fall off the visible list with no way to access them. The Figma design shows a "View All" link but it's not implemented.

**Research Findings:**

_How existing code handles this:_
- Legacy `views.py:45`: History limited to 6 items with `[:6]`
- Modern `Home.tsx:51`: History fetched with `api.history.list(6)`
- Both frontends show only the first 6 recently viewed recipes
- API supports variable limit parameter for history endpoint

_Design intent (Figma):_
- `App.tsx:987-994`: Section header with "Recently Viewed" and "View All ({count})" button
- `App.tsx:1903-1949`: Full "All Recipes" screen showing all viewed recipes in grid
- Empty state with "No recipes viewed yet" message and "Browse Recipes" button
- Pattern matches existing Favorites screen structure

_Established patterns to follow:_
- Favorites screen already exists with same structure (header, back button, recipe grid)
- URL pattern: `/legacy/favorites/` → `/legacy/all-recipes/`
- Modern screen pattern: Favorites.tsx → AllRecipes.tsx

**Tasks:**
- [x] Add "View All" link to Recently Viewed section (Legacy)
- [x] Add "View All" link to Recently Viewed section (Modern)
- [x] Create All Recipes page/screen for both frontends
- [x] Pass total history count to home pages for display

**Implementation:**

_Legacy:_
- Added `all_recipes` view in `views.py:187-217` (fetches all history, no limit)
- Added URL pattern `/legacy/all-recipes/` in `urls.py:13`
- Created `all_recipes.html` template (matches favorites.html structure)
- Updated `home.html:64-66` with section-header containing View All link
- Added `.section-header` and `.section-link` CSS in `layout.css:320-351`
- Updated home view to pass `history_count` for total recipe count

_Modern:_
- Created `AllRecipes.tsx` screen (matches Favorites.tsx structure)
- Added `'all-recipes'` screen type in `App.tsx:21`
- Added handlers `handleAllRecipesClick/Back` in `App.tsx:187-193`
- Added `onAllRecipesClick` prop to Home component
- Updated Home to fetch full history, display 6, show total count
- Added View All button in Recently Viewed section header

**Files Changed:**
- `apps/legacy/views.py` - Added `all_recipes` view, updated `home` view
- `apps/legacy/urls.py` - Added all-recipes URL
- `apps/legacy/templates/legacy/all_recipes.html` - New template
- `apps/legacy/templates/legacy/home.html` - Added View All link
- `apps/legacy/static/legacy/css/layout.css` - Added section-header styles
- `frontend/src/screens/AllRecipes.tsx` - New screen
- `frontend/src/screens/Home.tsx` - Added View All link and prop
- `frontend/src/App.tsx` - Added screen type, handlers, routing

**Verification:**
- [x] "View All" link visible on home page when recipes exist
- [x] Clicking link shows all imported recipes
- [x] Works on Legacy (iPad 3 / iOS 9)
- [x] Works on Modern (desktop browser)

---

### QA-F: List Number/Text Spacing

**Issue:** QA-006 - Insufficient spacing between list number and text
**Affects:** Legacy
**Status:** New

**Problem:**
In Legacy recipe detail ingredient and instruction lists, there is insufficient spacing (gap) between the numbered circle badge and the text content to the right of it. The text appears too close to the number, making it harder to read. Modern frontend spacing is acceptable.

**Research Findings:**
- _Current gap values:_ [TBD - check Legacy CSS gap values]
- _Design intent (Figma):_ [TBD - check Figma for intended spacing]
- _Modern frontend gap (reference):_ [TBD - check what Modern uses]

**Tasks:** _(Define after research is complete)_
- [ ] Check current gap values in Legacy CSS
- [ ] Check Modern gap values for reference
- [ ] Check Figma design for intended spacing
- [ ] Update Legacy `recipe-detail.css` gap values
- [ ] Verify spacing looks good on iPad

**Verification:**
- [ ] Adequate spacing between number badge and text
- [ ] Works on iPad 3 / iOS 9

---

## Issue Details

### QA-001: Navigation bar missing menu links

**Found:** 2025-01-07 (iPad 3 / iOS 9)
**Reporter:** Matt

The legacy header only shows "Cookie" branding on the left and a profile icon (colored circle) on the right. The modern frontend has navigation options accessible from the header/nav area. Legacy users have no way to navigate to Favorites, Collections, or Search without manually entering URLs or using browser history.

---

### QA-002: No way to view all imported recipes

**Found:** 2025-01-07 (iPad 3 / iOS 9)
**Reporter:** Matt

Current flow:
1. User searches for "chicken"
2. User clicks "Import" on a recipe
3. Toast shows "Recipe imported!"
4. User redirected to home page
5. Imported recipe is NOT in "Recently Viewed" (because user hasn't viewed it yet)
6. User has no way to find the recipe they just imported

The "Recently Viewed" section only shows recipes the user has actually opened/viewed, not all imported recipes. With a future limit on Recently Viewed, older imports could become unfindable.

---

### QA-003: Numbered list styling inconsistent

**Found:** 2025-01-07 (iPad 3 / iOS 9)
**Reporter:** Matt

The ingredient list styling differs from Figma design in both frontends:
- **Current:** Ingredients use gray (muted) numbered badges, Instructions use green (primary) badges
- **Figma:** Both ingredients AND instructions use green (primary) numbered badges

Both Legacy and Modern frontends are consistent with each other, but both deviate from the Figma design. The current implementation appears intentional (visual differentiation between list types) but doesn't match the design spec.

---

### QA-004: Back button returns to Play Mode after closing it

**Found:** 2026-01-07 (iPad 3 / iOS 9)
**Reporter:** Matt

Navigation flow issue with browser history in Legacy frontend:

1. Navigate: Home → Recipe Detail → Play Mode
2. Close Play Mode (returns to Recipe Detail)
3. Press browser Back button
4. **Actual:** Returns to Play Mode
5. **Expected:** Returns to Home (or wherever user was before Recipe Detail)

The issue occurs because entering Play Mode pushes a new entry onto the browser history stack. When the user closes Play Mode, they return to Recipe Detail but the Play Mode history entry remains. The back button then navigates to that stale history entry.

The Modern frontend does not have this issue, likely using `history.replaceState()` or a modal/overlay pattern that doesn't affect browser history.

---

### QA-005: No "View All Recipes" link on home page

**Found:** 2026-01-07
**Reporter:** Matt

Both Legacy and Modern frontends have display limits on recipe sections:
- Recently Viewed: Limited to 6 (Legacy) or 9 (Modern) recipes
- No way to see all imported recipes beyond these limits

As users import more recipes over time, older recipes become inaccessible. The Figma design includes a "View All" link that navigates to an "all-recipes" screen, but this is not implemented in either frontend.

Related to QA-002 (imported recipes visibility) - while QA-002's fix ensures newly imported recipes are immediately viewable, QA-005 addresses long-term discoverability of all imported recipes.

---

### QA-006: Insufficient spacing between list number and text

**Found:** 2026-01-07 (iPad 3 / iOS 9)
**Reporter:** Matt

In Legacy recipe detail, the ingredient and instruction lists have insufficient gap between the numbered circle badge and the text content. The text appears cramped against the number badge. Modern frontend has adequate spacing.

Related to QA-003 (list styling) - discovered during verification of the badge color fix.

---

## Testing Rounds

### Round 1 - 2025-01-07

**Device:** iPad 3 / iOS 9
**Tester:** Matt
**Areas Tested:** Profile selector, Home, Search, Import flow

**Results:**
- Profile selector: Working
- Home page: Working (but missing nav - QA-001)
- Search: Working
- Import flow: Working (but can't find imported recipe - QA-002)
- Recipe cards: Displaying with images
- Toast notifications: Working

**Issues Found:** QA-001, QA-002, QA-003

---

## Pending Tests

Areas not yet tested on iOS 9:
- [ ] Recipe detail page (all tabs)
- [x] Play mode navigation (QA-004 logged)
- [ ] Timer functionality (CRITICAL)
- [ ] Multiple simultaneous timers
- [ ] Favorites add/remove
- [ ] Collections CRUD
- [ ] Serving adjustment UI

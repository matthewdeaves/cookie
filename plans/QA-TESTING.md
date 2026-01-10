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
| QA-006 | Recipe detail layout/spacing issues (iOS 9 gap) | Legacy | Verified | QA-F |
| QA-007 | Button icons off-center (Safari flexbox bug) | Legacy | Verified | QA-G |
| QA-008 | Search input text unreadable in dark mode | Modern | Verified | QA-H |
| QA-009 | Search results missing/broken images | Legacy + Modern | Verified | QA-I |
| QA-010 | Multiple timers have no spacing in Play Mode | Legacy | Verified | QA-J |
| QA-011 | Timers don't auto-start when added in Play Mode | Modern | Verified | QA-K |
| QA-012 | Timer completion sound doesn't play | Modern | Verified | QA-L |
| QA-013 | Timer completion sound doesn't play | Legacy | Verified | QA-M |
| QA-014 | Screen locks during Play Mode | Legacy | Verified | QA-N |
| QA-015 | No "View All" link for Favorites section | Legacy + Modern | Verified | QA-O |
| QA-016 | Back button after import goes to home instead of search results | Modern | Verified | QA-P |
| QA-017 | Frontend build fails - test files missing cached_image_url | Modern | Verified | QA-Q |
| QA-018 | Frontend build - tsconfig permission denied errors | Modern | Won't Fix | QA-R |
| QA-019 | Screen locks during Play Mode (Modern) | Modern | Verified | QA-S |
| QA-020 | Profile icon should navigate to profile chooser | Modern | Verified | QA-T |
| QA-021 | Remixed recipes have no image | Modern + Legacy | Verified | - |
| QA-022 | Instructions tab crashes on remixed recipes | Modern | Verified | - |
| QA-023 | Remix button does nothing on Legacy | Legacy | Verified | - |
| QA-024 | Legacy instructions tab shows curly braces on remixes | Legacy | Verified | - |
| QA-025 | Legacy Play Mode shows [object Object] for remix steps | Legacy | Verified | - |
| QA-026 | Remixed recipes have no nutrition information | Modern + Legacy | Verified | - |
| QA-027 | Invalid AI model selection breaks features silently | Modern + Legacy | Verified | - |
| QA-028 | Old browsers show white page instead of redirecting to Legacy | Legacy | Verified | - |
| QA-029 | Ingredient quantities need AI tidying | Backend | Verified | 8B-C |
| QA-030 | Nutrition tab serving label is ambiguous | Modern + Legacy | Verified | 8B-C |
| QA-031 | Scaled recipes need instruction step alignment | Backend | Verified | 8B-C |
| QA-032 | Scaled recipes need cooking time adjustments | Backend | Verified | 8B-C |
| QA-033 | Tips should generate automatically and adjust for scaling | Backend | Verified | 8B-C |
| QA-034 | AI prompts must be in migrations and visible in settings | Backend | Verified | 8B-C |
| QA-035 | SQLite database locking errors under concurrent load | Backend | Verified | 8B-C |
| QA-036 | Tips lazy loading and progressive enhancement | Modern + Legacy | Verified | - |
| QA-037 | Profile creation redirect issues | Modern + Legacy | Verified | - |
| QA-038 | Legacy QA workflow improvements | Legacy | Verified | - |
| QA-039 | Ingredient scaling cleanup for indivisible items | Backend | Verified | - |
| QA-040 | Discover tab shows wrong empty state message | Modern | Verified | - |
| QA-041 | Discover search terms don't match suggestion titles | Modern | Verified | - |
| QA-042 | Legacy search filter spacing issues | Legacy | Verified | - |
| QA-043 | Search ranking should prioritize results with images | Backend | Verified | - |
| QA-044 | Remix recipe tips generation fails/times out | Backend | Verified | - |
| QA-045 | Scaling shows "(was X min)" for unchanged times | Modern + Legacy | Verified | - |
| QA-046 | Auto-generate tips when viewing Tips tab | Modern + Legacy | Verified | - |
| QA-047 | Recipes should be linked to users (profile isolation) | All | Verified | - |
| QA-048 | Search results missing space before "Ratings" | Modern + Legacy | Verified | - |
| QA-051 | Legacy search results don't display rating count | Legacy | Verified | - |
| QA-052 | Search results not sorted with images first | Legacy | Verified | - |
| QA-053 | Search results should filter out recipes without titles | Modern + Legacy | Verified | - |
| QA-054 | WebP images not displaying on iOS 9 | Legacy | Verified | - |
| QA-055 | Test expects .png but code returns .jpg (correct behavior) | Tests | Verified | - |
| QA-056 | Test URL uses /article/ which is correctly excluded | Tests | Verified | - |
| QA-049 | Recipe import fails (403 error not shown to user) | Modern | Verified | - |
| QA-050 | Tips tab should be hidden without valid API key | Modern + Legacy | Verified | - |
| QA-057 | Discover tab shows "no suggestions" for new users without history | Modern + Legacy | Verified | - |
| QA-058 | AllRecipes article pages cause "Recipe has no title" on import | Modern + Legacy | Verified | - |
| QA-059 | Phase 10 CI/CD code review items (6 minor issues) | All | New | - |
| QA-060 | GitHub Pages root landing page returns 404 | Infrastructure | Fixed | - |
| QA-061 | CI/CD code quality tooling gaps and improvements | Infrastructure | Fixed | Phase 1-5 complete |
| QA-063 | Flaky test: test_scrape_url_with_image_download database flush error | Tests | New | - |

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
| QA-F | QA-006 | Recipe detail layout/spacing (iOS 9) |
| QA-G | QA-007 | Button icons off-center (Safari) |
| QA-H | QA-008 | Search input dark mode styling |
| QA-I | QA-009 | Search results image loading |
| QA-J | QA-010 | Play Mode timer spacing |
| QA-K | QA-011 | Timer auto-start behavior (Modern) |
| QA-L | QA-012 | Timer completion sound (Modern) |
| QA-M | QA-013 | Timer completion sound (Legacy) |
| QA-N | QA-014 | Screen wake lock (Legacy) |
| QA-O | QA-015 | View All link for Favorites |
| QA-P | QA-016 | Modern back button after import |
| QA-Q | QA-017 | Fix frontend test file type errors |
| QA-R | QA-018 | Fix tsconfig permission errors |
| QA-S | QA-019 | Screen wake lock (Modern) |
| QA-T | QA-020 | Profile icon navigation (Modern) |

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

### QA-F: Recipe Detail Layout/Spacing Issues

**Issue:** QA-006 - Multiple spacing/layout issues on recipe detail page
**Affects:** Legacy
**Status:** Verified

**Problem:**
Multiple spacing and layout issues on the Legacy recipe detail page, all stemming from CSS `gap` property not being supported on iOS 9 Safari:
1. Insufficient spacing between numbered badges and text in ingredient/instruction lists
2. Meta items (Prep/Cook/Total/Servings) running together with no spacing
3. Nutrition labels showing raw field names instead of human-readable text

**Screenshots:** `ipadtestingshots/IMG_0018.PNG`, `IMG_0019.PNG`, `IMG_0020.PNG`

**Research Findings:**

_Root Cause: iOS 9 Safari does not support CSS `gap` for flexbox_
- Flexbox `gap` support was added in Safari 14.1 (iOS 14.5)
- Legacy CSS uses `gap:` property 13+ times in `recipe-detail.css` without proper fallbacks
- The `> * + *` "owl selector" pattern should provide margin-based fallbacks, but most are missing or broken

_Current vs Figma vs Modern comparison:_

| Element | Legacy CSS | Modern (Tailwind) | Figma Design |
|---------|------------|-------------------|--------------|
| Ingredient item gap | `gap: 0.75rem` (12px) | `gap-3` (12px) | `gap-4` (16px) |
| Instruction item gap | `gap: 1rem` (16px) | `gap-4` (16px) | `gap-4` (16px) |
| Meta items gap | `gap: 1rem` (16px) | `gap-4` (16px) | `gap-4` (16px) |
| Ingredient text padding-top | none | none | `pt-0.5` (2px) |
| Instruction text padding-top | `0.125rem` (2px) | `pt-0.5` (2px) | `pt-0.5` (2px) |

_Specific issues found:_

1. **`.meta-items`** (line 243-248): Has `gap: 1rem` but fallback is `margin-left: 0` (should be `1rem`)
2. **`.ingredient-item`** (line 390-397): Has `gap: 0.75rem` with NO fallback
3. **`.instruction-item`** (line 429-436): Has `gap: 1rem` with NO fallback
4. **`.meta-item`** (line 250-257): Has `gap: 0.5rem` with NO fallback
5. **`.hero-rating`** (line 107-114): Has `gap: 0.25rem` with NO fallback

_Nutrition labels issue (separate from gap):_
- Legacy template outputs `{{ key }}` raw, showing "CarbohydrateContent", "CholesterolContent"
- Modern uses `{key.replace(/_/g, ' ')}` with CSS `capitalize` class
- Need Django template filter to humanize/format nutrition keys

_Files to modify:_
- `apps/legacy/static/legacy/css/recipe-detail.css` - Add margin fallbacks for all `gap:` usages
- `apps/legacy/templatetags/legacy_tags.py` - Add `format_nutrition_key` filter
- `apps/legacy/templates/legacy/recipe_detail.html` - Use new filter for nutrition labels

**Tasks:**
- [x] Add `> * + *` margin fallbacks for all flexbox `gap:` properties in recipe-detail.css
- [x] Fix `.meta-items` fallback from `margin-left: 0` to `margin-left: 1rem`
- [x] Add `padding-top` to `.ingredient-text` for vertical alignment with badge
- [x] Create `format_nutrition_key` template filter to humanize nutrition labels
- [x] Apply filter in recipe_detail.html nutrition section
- [x] Increased ingredient gap from 12px to 16px to match Figma
- [x] Verify all spacing works on iPad 3 / iOS 9

**Implementation:**
- Added `> * + *` margin fallbacks for 11 elements in `recipe-detail.css`:
  - `.hero-rating`, `.cook-btn`, `.meta-items`, `.meta-item`, `.serving-adjuster`
  - `.serving-controls`, `.ingredient-item`, `.instruction-item`, `.tip-item`, `.collection-list`
- For `.nutrition-grid` (wrapped layout), used negative margin on container + margin on items
- Fixed `.meta-items` fallback from `margin-left: 0` to `margin-left: 1rem`
- Added `padding-top: 0.125rem` to `.ingredient-text` for vertical alignment
- Increased `.ingredient-item` gap from `0.75rem` to `1rem` to match Figma design
- Created `format_nutrition_key` filter that converts:
  - "CarbohydrateContent" → "Carbohydrate"
  - "SaturatedFatContent" → "Saturated fat"
  - "saturated_fat" → "Saturated Fat"

**Files Changed:**
- `apps/legacy/static/legacy/css/recipe-detail.css` - Added margin fallbacks for iOS 9
- `apps/legacy/templatetags/legacy_tags.py` - Added `format_nutrition_key` filter
- `apps/legacy/templates/legacy/recipe_detail.html` - Applied filter to nutrition labels

**Verification:**
- [x] Meta items have visible spacing between them
- [x] Adequate spacing between number badge and text in all lists
- [x] Nutrition labels show human-readable text (e.g., "Carbohydrate" not "CarbohydrateContent")
- [x] Text vertically aligned with badge centers
- [x] Works on iPad 3 / iOS 9

---

### QA-G: Button Icons Off-Center (Safari Flexbox Bug)

**Issue:** QA-007 - Button icons appear slightly left-of-center
**Affects:** Legacy
**Status:** Verified

**Problem:**
On iPad 3 / iOS 9, circular icon buttons (back button, favorite, collection, servings +/-) display the SVG icon slightly to the left of center within the circle. The icons are still inside the circle, but visibly offset.

**Screenshots:** `ipadtestingshots/IMG_0018.PNG`, `IMG_0019.PNG`, `IMG_0020.PNG`

**Affected Elements:**
- `.hero-back` - Back button (chevron icon)
- `.hero-action-btn` - Favorite (heart) and Collection (+) buttons
- `.serving-btn` - Servings decrease (-) and increase (+) buttons

**Research Findings:**

_Root Cause: Safari bug with button elements as flex containers_

This is a **documented Safari bug** in the [flexbugs repository](https://github.com/philipwalton/flexbugs/issues/236):

> Safari ignores `align-items` and `justify-content` when the flex container is a `<button>` element.

Current CSS applies flexbox centering directly to button elements:
```css
.hero-back {
    display: -webkit-flex;
    display: flex;
    -webkit-align-items: center;
    align-items: center;
    -webkit-justify-content: center;
    justify-content: center;
}
```

While this works in modern browsers, Safari (especially older versions like iOS 9) ignores these properties on `<button>` elements due to how the browser's default button rendering conflicts with `display: flex`.

_Workaround from flexbugs:_

Wrap the button contents in a `<span>` or `<div>` and apply the flexbox centering to that wrapper instead:

```html
<!-- Before -->
<button class="hero-back">
    <svg>...</svg>
</button>

<!-- After -->
<button class="hero-back">
    <span class="btn-icon-wrapper">
        <svg>...</svg>
    </span>
</button>
```

```css
.btn-icon-wrapper {
    display: -webkit-flex;
    display: flex;
    -webkit-align-items: center;
    align-items: center;
    -webkit-justify-content: center;
    justify-content: center;
}
```

_Alternative: CSS text-align fallback_

Since SVGs are inline by default, `text-align: center` on the button may help as a simpler fallback, though this only handles horizontal centering.

**Tasks:**
- [x] Add `.btn-icon-wrapper` CSS class with flexbox centering
- [x] Wrap SVG icons in hero buttons (back, favorite, collection) with wrapper spans
- [x] Wrap SVG icons in serving buttons (+/-) with wrapper spans
- [ ] Verify icons are centered on iPad 3 / iOS 9

**Implementation:**
- Added `.btn-icon-wrapper` class to `recipe-detail.css:72-82` with full flexbox centering and `-webkit-` prefixes
- Wrapper spans fill the button (`width: 100%; height: 100%`) so flex centering works properly
- Updated `recipe_detail.html`: back button, favorite button, collection button
- Updated `serving_adjuster.html`: decrease button, increase button

**Files Changed:**
- `apps/legacy/static/legacy/css/components.css` - Added `.btn-icon-wrapper` class (global)
- `apps/legacy/static/legacy/css/recipe-detail.css` - Added `.btn-icon-wrapper` class (duplicate for recipe page)
- `apps/legacy/templates/legacy/recipe_detail.html` - Wrapped 5 buttons (back, favorite, collection, 2 modal close)
- `apps/legacy/templates/legacy/partials/serving_adjuster.html` - Wrapped 2 buttons (decrease, increase)
- `apps/legacy/templates/legacy/partials/recipe_card.html` - Wrapped favorite button
- `apps/legacy/templates/legacy/collection_detail.html` - Wrapped 2 buttons (remove, modal close)
- `apps/legacy/templates/legacy/collections.html` - Wrapped modal close button
- `apps/legacy/templates/legacy/profile_selector.html` - Wrapped add profile button
- `apps/legacy/templates/legacy/home.html` - Wrapped profile avatar letter

**Verification:**
- [x] Back button icon centered
- [x] Favorite button icon centered
- [x] Collection button icon centered
- [x] Servings decrease (-) button icon centered
- [x] Servings increase (+) button icon centered
- [x] Recipe card favorite buttons centered
- [x] Collection remove (X) buttons centered
- [x] Modal close buttons centered
- [x] Profile avatar letter centered
- [x] Add profile (+) button centered
- [x] Works on iPad 3 / iOS 9

---

### QA-H: Search Input Dark Mode Styling

**Issue:** QA-008 - Search input text unreadable in dark mode
**Affects:** Modern
**Status:** Verified

**Problem:**
On the Modern frontend, when dark mode is enabled, the text typed into the search input field is not readable - appears to be white text on a white or light background.

**Research Findings:**

_Root cause:_
- Search input in `Home.tsx:160` uses `bg-input-background` and `text-foreground` classes
- Light mode: `--input-background: #f4ede6;` (beige) defined correctly
- Dark mode: `--input-background` was **missing** from CSS variables
- Result: Dark mode fell back to light mode's beige background
- Text color: `--foreground: #f5ebe0;` (light beige)
- Background: `#f4ede6` (also light beige from light mode fallback)
- Outcome: Light text on light background = unreadable

_Solution:_
- Added `--input-background: #3d3531;` to dark mode CSS variables in `theme.css:64`
- Color matches dark mode `--secondary` for consistency
- Now dark mode has: light text (`#f5ebe0`) on dark background (`#3d3531`) = readable

**Tasks:**
- [x] Research search input styling in Modern frontend
- [x] Identify cause of color mismatch in dark mode (missing CSS variable)
- [x] Fix input text/background colors to use proper theme variables
- [x] Verify fix works in both light and dark modes

**Implementation:**
- Added `--input-background: #3d3531;` to `.dark` section in `theme.css`
- Used color consistent with dark mode secondary color
- No changes needed to `Home.tsx` - already using correct classes

**Files Changed:**
- `frontend/src/styles/theme.css:64` - Added `--input-background` for dark mode

**Verification:**
- [x] Search input readable in light mode
- [x] Search input readable in dark mode
- [x] Placeholder text visible in both modes
- [x] Focus ring visible in both modes

---

### QA-I: Search Results Image Loading

**Issue:** QA-009 - Search results missing/broken images
**Affects:** Legacy + Modern
**Status:** Verified

**Problem:**
When searching for recipes (e.g. "chicken"), some recipe cards display broken/missing images:

1. **Legacy (iPad/iOS 9):** Some recipes show white/blank boxes where images should be. These same recipes have working images on Modern frontend. Other recipes correctly show "No image" placeholder.

2. **Modern:** Some recipes have working images, others show "No Image" placeholder. The "No Image" cases appear consistent between frontends.

**Screenshots:** `shots/ipad.PNG`, `shots/firefox.png`

**Observed behavior:**
- "Chicken Makhani" - Image works on Modern, white box on Legacy
- "Chicken Arroz Caldo" - Image works on Modern, white box on Legacy
- "Garlic Chicken Fried" - Image works on Modern, white box on Legacy
- "Recipes" (bbc.co.uk) - "No image" on both frontends
- "In Season" (bbc.co.uk) - "No image" on both frontends
- "Occasions" (bbc.co.uk) - "No image" on both frontends

**Research Findings:**

_Root cause:_
- iOS 9 Safari cannot load external image URLs from third-party recipe sites due to CORS and security restrictions
- External URLs work reliably on Modern browsers (Chrome, Firefox) but fail silently on Legacy
- Failed images render as white/blank boxes (not broken image icons)
- When source sites provide no image URL, both frontends correctly show "No image" placeholder

_Solution approach:_
- **Two-tier storage strategy:** Cache search result images to the server immediately (fire-and-forget)
- Search API returns local `cached_image_url` when available, external `image_url` as fallback
- When user imports a recipe, scraper reuses cached image (avoids re-download)
- Cleanup removes unused cache entries after 30 days (keeps actively used images)
- Recipe images stored permanently in `media/recipe_images/`, separate from cache

_Why this fixes the issue:_
- Legacy gets images from local server storage (no CORS/security issues)
- Modern continues to use external URLs (faster, no server storage overhead)
- Both frontends gracefully fall back to external URLs during initial cache period
- Actively used images persist indefinitely (updated `last_accessed_at` prevents cleanup)

_Files to modify:_
- Model: `apps/recipes/models.py` - Add CachedSearchImage
- Service: `apps/recipes/services/image_cache.py` (new) - Image caching logic
- API: `apps/recipes/api.py` - Return cached_image_url in search results
- Scraper: `apps/recipes/services/scraper.py` - Reuse cached images on import
- Frontend: Legacy + Modern search result cards - Prefer cached images

_Implementation plan:_
See `plans/QA-009.md` for 4-session implementation breakdown with code snippets, test scenarios, and rollback strategy.

**Tasks:**
Follow the 10-session implementation plan in `plans/QA-009.md`:
- [x] Session 1: Create CachedSearchImage model + image_cache.py service
- [x] Session 2: Integrate caching in API + scraper
- [x] Session 3: Update Legacy + Modern frontend templates/components
- [x] Session 4: Create cleanup command + update documentation
- [x] Session 5: Performance fix (threading-based background caching)
- [x] Session 6: Image quality improvement (JPEG quality 92)
- [x] Session 7: Production configuration (Gunicorn, monitoring)
- [x] Session 8: Progressive image loading with spinners
- [x] Session 9: Fix "Load More" polling (multi-page tracking)
- [x] Session 10: Performance optimizations (DOM queries, early shutdown)

**Implementation Complete:**
All sessions completed successfully. See `plans/QA-009.md` for detailed implementation notes, critical bug fixes, and verification results.

**Verification Confirmed:**
- ✅ iOS 9 Legacy: Images load progressively with spinners
- ✅ iOS 9 Legacy: "Load More" pagination works correctly
- ✅ Modern browsers: High-quality cached images
- ✅ Performance: Optimized DOM queries, immediate polling shutdown

---

### QA-J: Play Mode Timer Spacing

**Issue:** QA-010 - Multiple timers have no spacing in Play Mode
**Affects:** Legacy
**Status:** Verified

**Problem:**
When a recipe has more than one timer in Play Mode, the timers are stacked vertically with no space between them. They appear to be sitting directly on top of each other, making them difficult to distinguish and interact with.

**Screenshots:** _To be added during testing_

**Research Findings:**

_Root cause: iOS 9 Safari does not support CSS `gap` for flexbox_

Same as QA-006, the play mode CSS uses `gap:` property without proper fallbacks for iOS 9 Safari. Flexbox `gap` support was added in Safari 14.1 (iOS 14.5).

_Current vs Modern comparison:_

| Element | Legacy CSS | Modern (Tailwind) | Purpose |
|---------|------------|-------------------|---------|
| `.timer-list` | `gap: 0.5rem` (8px) | `space-y-2` (8px) | Timer widgets stacking |
| `.nav-btn` | `gap: 0.5rem` | `gap-2` | Prev/Next button icons |
| `.step-indicators` | `gap: 0.375rem` | `gap-1.5` | Step dots |
| `.timer-panel-title` | `gap: 0.5rem` | `gap-2` | Timer header icons/text |
| `.quick-timers` | `gap: 0.5rem` | `gap-2` | Quick timer buttons wrap |
| `.quick-timer-btn` | `gap: 0.25rem` | `gap-1` | Button icon/text |
| `.detected-times-btns` | `gap: 0.5rem` | `gap-2` | Detected time buttons wrap |
| `.detected-time-btn` | `gap: 0.25rem` | `gap-1` | Button icon/text |
| `.timer-actions` | `gap: 0.5rem` | `gap-2` | Timer control buttons |

Modern frontend uses Tailwind's `space-y-*` utility which adds `margin-top` to children (not `gap`), so it works correctly on all browsers including iOS 9.

_Specific issues found in `play-mode.css`:_

1. **`.timer-list`** (line 377-387): Has `gap: 0.5rem` with NO fallback - **THIS IS THE REPORTED ISSUE**
2. **`.nav-btn`** (line 164-179): Has `gap: 0.5rem` with NO fallback
3. **`.step-indicators`** (line 206-218): Has `gap: 0.375rem` with NO fallback
4. **`.timer-panel-title`** (line 271-283): Has `gap: 0.5rem` with NO fallback
5. **`.quick-timers`** (line 305-312): Has `gap: 0.5rem` with NO fallback
6. **`.quick-timer-btn`** (line 314-334): Has `gap: 0.25rem` with NO fallback
7. **`.detected-times-btns`** (line 347-353): Has `gap: 0.5rem` with NO fallback
8. **`.detected-time-btn`** (line 355-375): Has `gap: 0.25rem` with NO fallback
9. **`.timer-actions`** (line 465-469): Has `gap: 0.5rem` with NO fallback

_Solution (same as QA-006):_
- Add `> * + *` margin fallbacks for all elements using `gap:` in play-mode.css
- For flex-row: Use `margin-left` on subsequent children
- For flex-column: Use `margin-top` on subsequent children
- For flex-wrap: May need negative margin on container + margin on all items

**Tasks:**
- [x] Add `> * + *` margin fallbacks for all 9 elements using `gap:` in play-mode.css
- [x] For `.timer-list` (flex-column): Add `> * + * { margin-top: 0.5rem; }`
- [x] For flex-row elements: Add `> * + * { margin-left: [gap-value]; }`
- [x] For flex-wrap elements (`.quick-timers`, `.detected-times-btns`): Use negative margin pattern
- [ ] Test timer spacing on iPad 3 / iOS 9
- [ ] Verify all play mode UI elements have proper spacing

**Implementation:**

Added iOS 9 margin fallbacks for all 9 elements using CSS `gap:` property in play-mode.css:

1. **`.nav-btn`** (line 181-184): Flex-row → `margin-left: 0.5rem` on subsequent children
2. **`.step-indicators`** (line 218-221): Flex-row → `margin-left: 0.375rem` on subsequent children
3. **`.timer-panel-title`** (line 291-294): Flex-row → `margin-left: 0.5rem` on subsequent children
4. **`.quick-timers`** (line 327-333): Flex-wrap → Negative margin `-0.25rem` on container, `margin: 0.25rem` on all children
5. **`.quick-timer-btn`** (line 354-357): Flex-row → `margin-left: 0.25rem` on subsequent children
6. **`.detected-times-btns`** (line 380-387): Flex-wrap → Negative margin `-0.25rem` on container, `margin: 0.25rem` on all children
7. **`.detected-time-btn`** (line 407-410): Flex-row → `margin-left: 0.25rem` on subsequent children
8. **`.timer-list`** (line 428-431): Flex-column → `margin-top: 0.5rem` on subsequent children - **MAIN FIX**
9. **`.timer-actions`** (line 515-518): Flex-row → `margin-left: 0.5rem` on subsequent children

**Pattern used:**
- **Flex-row:** Used `> * + *` selector with `margin-left` (owl selector targets all siblings after the first)
- **Flex-column:** Used `> * + *` selector with `margin-top`
- **Flex-wrap:** Used negative margin on container plus positive margin on all children to simulate gap behavior

**Additional fixes applied after initial testing:**

After testing on iPad 3, discovered that timer buttons were extending beyond the timer box. Root cause: iOS 9 flexbox sizing issues. Applied the following fixes:

1. **`.timer-widget`**: Added `overflow: hidden`, `flex-shrink: 0` for proper containment
2. **`.timer-actions`**: Added `width: 100%`, `align-items: stretch` for proper flex layout
3. **`.btn-timer`**: Added explicit `flex-shrink: 1`, `box-sizing: border-box`, `max-width: 100%`
4. **`.btn-timer-secondary`**: Same sizing fixes as btn-timer
5. **`.btn-timer-danger`**: Added `flex-shrink: 0`, `box-sizing: border-box`

These ensure iOS 9 Safari correctly calculates flexbox dimensions and prevents button overflow.

**Files Changed:**
- `apps/legacy/static/legacy/css/play-mode.css` - Added 9 iOS 9 margin fallbacks for flexbox gap properties + timer button sizing fixes

**Verification:**
- [x] Multiple timers have visible spacing between them
- [x] Timer buttons stay within timer box borders
- [x] Touch targets remain accessible (44px minimum)
- [x] Works on iPad 3 / iOS 9
- [x] Modern frontend behavior unchanged (if applicable)

---

### QA-K: Timer Auto-Start Behavior

**Issue:** QA-011 - Timers don't auto-start when added in Play Mode
**Affects:** Modern
**Status:** New

**Problem:**
On the Modern frontend in Play Mode, when a user adds a timer, it does not automatically start counting down. The user must manually start the timer after adding it. Expected behavior is for timers to start automatically when added.

**Screenshots:** _To be added during testing_

**Research Findings:**

_How existing code handles this:_
- **useTimers.ts:40-52:** `addTimer()` creates timers with `isRunning: false` hardcoded
- **TimerPanel.tsx:37-43:** Calls `addTimer()` but never calls `startTimer()` afterward
- **TimerWidget.tsx:55-80:** Renders Play/Pause button based on `isRunning` state
- Timer only starts when user manually clicks Play button, which calls `toggleTimer()` → `startTimer()`

_Current flow (broken):_
1. User clicks "Add Timer" (Quick Timer or Detected Time button)
2. `addTimer(label, duration)` creates timer with `isRunning: false`
3. Timer appears in list with Play button visible
4. User must manually tap Play to start countdown

_Root cause:_
- `useTimers.ts:49` hardcodes `isRunning: false` for all new timers
- No automatic call to `startTimer()` after timer creation
- Two-step process (add, then start) creates unnecessary friction

_Design consideration:_
- `setTimers()` is asynchronous, so `startTimer()` can't be called immediately after `addTimer()`
- Need to either: (a) return timer ID and use effect/callback, or (b) start interval inline during creation

_Recommended fix approach:_
- Modify `addTimer()` to return the timer ID
- Use `useEffect` to auto-start newly added timers, OR
- Modify `addTimer()` to optionally start the timer inline during creation

**Tasks:**
- [x] Modify `useTimers.ts` to return timer ID from `addTimer()`
- [x] Add auto-start logic (inline in addTimer with optional parameter)
- [x] TimerPanel.tsx already uses addTimer - auto-start is now default behavior
- [x] Update `timers.test.ts` to expect auto-started timers
- [ ] Verify on Modern frontend (desktop browser)

**Implementation:**
- Modified `addTimer()` function signature to accept optional `autoStart` parameter (default: `true`)
- When `autoStart` is true, the interval is created immediately before `setTimers()` is called
- The timer is created with `isRunning: autoStart` so it starts counting down immediately
- `addTimer()` now returns the timer ID for potential future use cases
- No changes needed to `TimerPanel.tsx` - it already calls `addTimer()` which now auto-starts by default
- Tests updated: 3 new tests added for auto-start behavior, existing tests use `autoStart: false` where explicit start/pause/toggle testing is needed

**Files Changed:**
- `frontend/src/hooks/useTimers.ts` - Modified `addTimer()` to auto-start and return timer ID
- `frontend/src/test/timers.test.ts` - Updated tests for auto-start behavior

**Verification:**
- [x] Timers automatically start counting down when added
- [x] Quick timers (+5 min, +10 min, +15 min) auto-start
- [x] Detected time buttons auto-start timers
- [x] Pause/resume still works correctly (toggle button works)
- [x] Works on Modern frontend (desktop browser)
- [x] Legacy frontend behavior unchanged (Legacy uses separate JS implementation)

---

### QA-L: Timer Completion Sound

**Issue:** QA-012 - Timer completion sound doesn't play
**Affects:** Modern
**Status:** Verified

**Problem:**
On the Modern frontend in Play Mode, when a timer completes (reaches 0:00), no sound is played to alert the user. This is a critical issue for cooking, as users may be away from the device or focused on other tasks when the timer completes.

**Screenshots:** _N/A (audio issue)_

**Research Findings:**

_Root cause:_
- **Modern frontend has NO audio implementation** - `handleTimerComplete` in `PlayMode.tsx:27-49` only shows toast and browser notification
- Timer completion is correctly detected in `useTimers.ts:74` and callback fires
- The Browser Notification API may or may not play a system sound (depends on OS/browser settings)
- No audio playback code exists anywhere in the Modern frontend

_How Legacy handles this (comparison):_
- Legacy `timer.js:196-203` has audio code: `new Audio('/static/legacy/audio/timer.mp3').play()`
- But the audio file doesn't exist, so it fails silently (related to QA-013)

_Design intent (PLANNING.md:1568):_
- "Audio alert: Default browser notification sound (no custom audio files)"
- Suggests using programmatic sound (Web Audio API) rather than audio file assets

_Implementation options:_
1. **Web Audio API** - Generate beep/tone programmatically (no file dependency, works across browsers)
2. **Base64-encoded audio** - Embed short alert sound as data URL in code
3. **HTML5 Audio with file** - Requires creating/hosting audio asset

_iOS Safari consideration:_
- iOS requires user interaction before audio playback
- Workaround: "unlock" audio context on first user tap in Play Mode
- Alternative: Use vibration API (haptic feedback) as fallback

_Files to modify:_
- `frontend/src/screens/PlayMode.tsx` - Add audio playback to `handleTimerComplete`
- Consider creating `frontend/src/utils/audio.ts` utility for reusable sound functions

**Recommended approach:** Use Web Audio API to generate a pleasant beep tone when timer completes. This matches the design intent (no custom audio files) and works reliably across browsers. Pre-unlock audio context when user enters Play Mode to handle iOS restrictions.

**Tasks:**
- [x] Create audio utility with Web Audio API beep function
- [x] Unlock audio context on Play Mode mount (iOS compatibility)
- [x] Call audio alert in `handleTimerComplete` callback
- [ ] Test on desktop browsers (Chrome, Firefox, Safari)
- [ ] Test audio restrictions on mobile (may need user interaction)

**Implementation:**
- Created `frontend/src/lib/audio.ts` with Web Audio API utility:
  - `getAudioContext()` - Singleton AudioContext with webkitAudioContext fallback
  - `unlockAudio()` - Plays silent buffer to unlock iOS audio restrictions
  - `playTimerAlert()` - Plays pleasant three-tone beep (A5-A5-E5 pattern)
  - `playTone()` - Low-level tone generator with smooth gain envelope
- Updated `PlayMode.tsx` to:
  - Import audio utilities
  - Call `unlockAudio()` on component mount (useEffect)
  - Call `playTimerAlert()` in `handleTimerComplete` callback

**Files Changed:**
- `frontend/src/lib/audio.ts` - New file with Web Audio API utilities
- `frontend/src/screens/PlayMode.tsx` - Added audio import and calls

**Verification:**
- [ ] Sound plays when timer reaches 0:00
- [ ] Sound is audible and distinct
- [ ] Works on Modern frontend (desktop browser)
- [ ] Audio unlocking works on mobile Safari

---

### QA-M: Timer Completion Sound (Legacy)

**Issue:** QA-013 - Timer completion sound doesn't play
**Affects:** Legacy
**Status:** Verified

**Problem:**
On the Legacy frontend (iPad 3 / iOS 9) in Play Mode, when a timer completes (reaches 0:00), no sound is played to alert the user. This is a critical issue for cooking, as users may be away from the device or focused on other tasks when the timer completes.

**Screenshots:** _N/A (audio issue)_

**Research Findings:**

_Root cause:_
- Initial HTML5 Audio attempts failed due to iOS 9 audio restrictions
- iOS 9 requires user interaction before audio playback ("unlock")
- Found working implementation in `/home/matt/Desktop/cookie1_old` using Web Audio API

_Solution (from working old codebase):_
- Use Web Audio API with `webkitAudioContext` fallback for iOS 9 Safari
- Initialize AudioContext on first user gesture (touchstart/click on document)
- Generate beep tones programmatically using oscillator (880 Hz, square wave)
- No audio files needed - pure programmatic sound generation

**Tasks:**
- [x] Rewrite timer.js to use Web Audio API with `webkitAudioContext`
- [x] Add global touchstart/click handlers in play.js to initialize audio
- [x] Play 3 beeps at 880 Hz on timer completion
- [x] Remove alert() - just play sound and show toast
- [x] Remove unused HTML5 audio element from play_mode.html
- [x] Test on iPad 3 / iOS 9

**Implementation:**
- Rewrote `timer.js` with Web Audio API:
  - `initAudio()` creates AudioContext with `webkitAudioContext` fallback
  - `playAlarmSound()` generates 3 beeps at 880 Hz using square wave oscillator
  - Handles suspended context state (iOS autoplay policy)
- Updated `play.js`:
  - Added global `touchstart` and `click` listeners to call `unlockAudio()`
  - Added `onComplete` callback to show toast when timer finishes
- Removed base64 audio element from `play_mode.html` (not needed)

**Files Changed:**
- `apps/legacy/static/legacy/js/timer.js` - Complete rewrite with Web Audio API
- `apps/legacy/static/legacy/js/pages/play.js` - Global audio init + toast callback
- `apps/legacy/templates/legacy/play_mode.html` - Removed unused audio element

**Verification:**
- [x] Sound plays when timer reaches 0:00
- [x] Sound is audible and distinct (3 beeps at 880 Hz)
- [x] Works on iPad 3 / iOS 9
- [x] ES5/iOS 9 audio API compatibility (webkitAudioContext)

**Related:** QA-012 (same issue on Modern frontend) - Fixed with similar Web Audio API approach

---

### QA-N: Screen Wake Lock

**Issue:** QA-014 - Screen locks during Play Mode
**Affects:** Legacy
**Status:** Verified

**Problem:**
On the Legacy frontend (iPad 3 / iOS 9) in Play Mode, the iPad screen locks after the device's auto-lock timeout (typically 2-5 minutes). When cooking, users are often away from the device or not actively touching the screen, and the screen locking interrupts their workflow - they must unlock the device to check timers or view instructions.

**Screenshots:** _N/A (behavioral issue)_

**Research Findings:**

_Available APIs for iOS 9:_
- **Screen Wake Lock API:** NOT supported on iOS 9 (requires iOS 16.4+)
- **NoSleep.js pattern (silent video loop):** Proven to work on iOS 9 Safari
- **Canvas animation:** Less reliable than video loop, not recommended

_Why silent video loop is the best approach:_
- Battle-tested pattern used in production apps
- ES5 compatible (no modern API dependencies)
- Can be toggled on/off without page reload
- Minimal bandwidth (silent video is very small)
- Follows existing codebase patterns (similar to timer.js audio handling)

_How it works:_
1. Create a hidden `<video>` element with base64-encoded silent MP4
2. Set `loop` and `muted` attributes
3. Call `play()` when entering Play Mode
4. Call `pause()` when exiting Play Mode
5. Video plays silently in background, preventing device sleep

_Entry/exit points identified:_
- **Entry:** `play.js:23` in `init()` function - Enable wake lock
- **Exit:** `play.js:122` in `handleExit()` function - Disable wake lock

_Pattern to follow:_
- `timer.js` module demonstrates identical singleton IIFE pattern
- `unlockAudio()` in timer.js shows iOS workaround approach
- ES5 syntax throughout

**Tasks:**
- [x] Create `apps/legacy/static/legacy/js/wake-lock.js` module with video loop
- [x] Embed base64-encoded silent MP4 video in module
- [x] Add `WakeLock.enable()` call in `play.js` `init()` function
- [x] Add `WakeLock.disable()` call in `play.js` `handleExit()` function
- [x] Add script include in `play_mode.html` template
- [ ] Test on iPad 3 / iOS 9

**Implementation:**
- Created `wake-lock.js` module using IIFE singleton pattern (matches timer.js)
- **iOS version detection:** Parses user agent to detect iOS < 10
- **iOS 9 technique (verified working):** Page refresh every 15 seconds
  - Uses `window.location.href = url; window.setTimeout(window.stop, 0);`
  - Creates activity to prevent screen sleep without actual reload
- **iOS 10+ technique:** Silent video loop (base64 MP4, ~1KB)
- `Cookie.WakeLock.enable()` called in `play.js` init()
- `Cookie.WakeLock.unlock()` called on first user touch (for video technique)
- `Cookie.WakeLock.disable()` called in `play.js` handleExit()

**Files Changed:**
- `apps/legacy/static/legacy/js/wake-lock.js` - New module with dual technique
- `apps/legacy/static/legacy/js/pages/play.js` - Added enable/unlock/disable calls
- `apps/legacy/templates/legacy/play_mode.html` - Added script include

**Verification:**
- [x] Screen stays awake while in Play Mode (tested 5+ minutes on iPad 3)
- [x] Works on iPad 3 / iOS 9 using page refresh technique
- [ ] Screen returns to normal auto-lock behavior when exiting Play Mode
- [ ] Timer alerts still work while wake lock active
- [ ] Exit via back button also disables wake lock
- [x] Modern frontend logged as separate issue (QA-019)

---

### QA-O: View All Link for Favorites

**Issue:** QA-015 - No "View All" link for Favorites section
**Affects:** Legacy + Modern
**Status:** New

**Problem:**
On the home page, the "Recently Viewed" section has a "View All" link that navigates to a dedicated page showing all recipes. However, the "Favorites" section (displayed below Recently Viewed) does not have a similar "View All" link. This creates an inconsistent UX pattern and makes it unclear to users that they can view all their favorites.

**Screenshots:** _To be added during testing_

**Research Findings:**

_How QA-005 implemented "View All" for Recently Viewed:_

**Legacy backend (`views.py`):**
```python
history_qs = RecipeViewHistory.objects.filter(profile=profile)
history_count = history_qs.count()  # Total count passed to template
history = history_qs[:6]            # Limited preview
```

**Legacy template (`home.html:64-66`):**
```html
<div class="section-header">
    <h2 class="section-title">Recently Viewed</h2>
    <a href="{% url 'legacy:all_recipes' %}" class="section-link">View All ({{ history_count }})</a>
</div>
```

**Modern frontend (`Home.tsx`):**
- `historyCount` state stores total count
- View All button with `onClick={onAllRecipesClick}` handler
- Shows count: `View All ({historyCount})`

_Current Favorites section (missing pattern):_
- Legacy `home.html:79-80`: Just `<h2>` title, no section-header wrapper
- Modern `Home.tsx:226-230`: Just `<h2>` title, no View All button
- No `favorites_count` variable passed to Legacy template

_Existing Favorites pages (no new pages needed):_
- Legacy: `/legacy/favorites/` URL already exists with full list
- Modern: `Favorites.tsx` screen already exists
- Navigation handlers already wired up in `App.tsx`

**Tasks:**
- [x] Add `favorites_count` to home view context in `views.py`
- [x] Wrap Favorites title in `section-header` div in `home.html`
- [x] Add View All link to Favorites section in `home.html`
- [x] Add View All button to Favorites section in `Home.tsx` (uses `favorites.length` directly)
- [x] Test on Legacy (iPad 3 / iOS 9)
- [x] Test on Modern (desktop browser)

**Implementation:**

_Legacy:_
- Updated `views.py:37-42` to use `favorites_qs` queryset pattern (like `history_qs`)
- Added `favorites_count = favorites_qs.count()` and `favorites = favorites_qs[:12]`
- Added `favorites_count` to template context (line 61)
- Updated `home.html:79-85` to wrap title in `.section-header` div
- Added View All link with count: `View All ({{ favorites_count }})`
- Link only shown when favorites exist (matches empty state pattern)

_Modern:_
- Updated `Home.tsx:227-240` Favorites section header
- Added flex container with `justify-between` to match Recently Viewed pattern
- Added View All button that calls existing `onFavoritesClick` handler
- Uses `favorites.length` directly (no separate state needed - full list already fetched)
- Button only shown when `favorites.length > 0`

**Files Changed:**
- `apps/legacy/views.py` - Added `favorites_count` to home view context
- `apps/legacy/templates/legacy/home.html` - Added section-header with View All link
- `frontend/src/screens/Home.tsx` - Added View All button to Favorites section

**Verification:**
- [x] "View All" link appears in Favorites section header on home page
- [x] Link shows favorite count (e.g., "View All (12)")
- [x] Clicking link navigates to existing Favorites page
- [x] Works on Legacy (iPad 3 / iOS 9)
- [x] Works on Modern (desktop browser)

---

### QA-P: Modern Back Button After Import

**Issue:** QA-016 - Back button after import goes to home instead of search results
**Affects:** Modern
**Status:** Verified

**Problem:**
On the modern frontend, after importing a search result:
1. User searches for recipes (e.g., "chicken")
2. User clicks "Import" on a search result
3. User is taken to the recipe view page (correct)
4. User clicks the in-page back button
5. User is taken to home/search page instead of back to search results with their query (incorrect)

**Expected behavior:** Back button should return user to the search results page with their previous search query intact.

**Note:** This issue does NOT occur on Legacy frontend - back button correctly returns to search results.

**Screenshots:** _To be added during testing_

**Research Findings:**

**Root Cause:** In `App.tsx`, the `handleImport()` function clears the search query (`setSearchQuery('')`) immediately after successful import. When `handleRecipeDetailBack()` is called, it evaluates `searchQuery ? 'search' : 'home'` - but since the query is now empty, it returns `'home'`.

Key code in `App.tsx`:
```typescript
// handleImport() - line 123
setSearchQuery('')  // <- BUG: Clears search query on import

// handleRecipeDetailBack() - line 148
setCurrentScreen(searchQuery ? 'search' : 'home')  // searchQuery is empty!
```

**Why Legacy Works:** Legacy uses browser history API (`window.history.back()`) which naturally preserves the page stack. Modern is a SPA that manages navigation internally via React state.

**Solution:** Don't clear `searchQuery` on import. Also ensure `previousScreen` is set to `'search'` so back navigation knows where to return.

**Tasks:**
- [x] Remove `setSearchQuery('')` from `handleImport()` in `App.tsx`
- [x] Add `setPreviousScreen('search')` before navigating to recipe-detail in `handleImport()`
- [x] Update `handleRecipeDetailBack()` to explicitly check for `previousScreen === 'search'`
- [x] Search query is already cleared in `handleSearchBack()` when user explicitly leaves search

**Implementation:**
- Modified `handleImport()` (App.tsx:114-129):
  - Removed `setSearchQuery('')` call that was clearing the search context
  - Added `setPreviousScreen('search')` to explicitly track where user came from
- Modified `handleRecipeDetailBack()` (App.tsx:142-150):
  - Added `'search'` to the explicit previousScreen check
  - Simplified fallback to just `'home'` since we now explicitly handle search

**Files Changed:**
- `frontend/src/App.tsx` - Modified `handleImport()` and `handleRecipeDetailBack()`

**Verification:**
- [x] Import recipe from search results
- [x] Click in-page back button on recipe view
- [x] Returns to search results page
- [x] Search query is preserved (same results displayed)
- [x] Works on Modern (desktop browser)
- [x] Legacy frontend still works correctly (no regression)

---

### QA-Q: Fix Frontend Test File Type Errors

**Issue:** QA-017 - Frontend build fails - test files missing cached_image_url
**Affects:** Modern
**Status:** New

**Problem:**
The frontend TypeScript build fails with type errors in test files. The `SearchResult` type was updated in QA-009 to include `cached_image_url`, but the test file mock data was not updated to match.

**Build Error:**
```
src/test/components.test.tsx(164,9): error TS2741: Property 'cached_image_url' is missing in type '{ url: string; title: string; host: string; image_url: string; description: string; }' but required in type 'SearchResult'.
```

**Root Cause:**
When QA-009 added image caching, the `SearchResult` interface in `api/client.ts` was updated to include `cached_image_url`. The test files in `src/test/components.test.tsx` have mock `SearchResult` objects that are now missing this required property.

**Tasks:**
- [ ] Update mock SearchResult objects in `components.test.tsx` to include `cached_image_url`
- [ ] Verify `npm run build` completes without errors
- [ ] Verify `npm run test` passes

**Implementation:**
- Added `cached_image_url: null` to all 5 mock SearchResult objects in `components.test.tsx`
- Lines 164, 165, 183, 247, 263

**Files Changed:**
- `frontend/src/test/components.test.tsx` - Added `cached_image_url: null` to mock data

**Verification:**
- [x] No TypeScript type errors (TS2741 resolved)
- [x] `npm run build` succeeds (in Docker)
- [x] `npm run test` passes (65 tests in Docker)

---

### QA-R: Fix tsconfig Permission Errors

**Issue:** QA-018 - Frontend build - tsconfig permission denied errors
**Affects:** Modern
**Status:** New

**Problem:**
The frontend build fails with permission errors when TypeScript tries to write build info files:
```
error TS5033: Could not write file '.../node_modules/.tmp/tsconfig.app.tsbuildinfo': EACCES
error TS5033: Could not write file '.../node_modules/.tmp/tsconfig.node.tsbuildinfo': EACCES
```

**Root Cause:**
Docker containers run as root, creating files owned by root in mounted volumes. When running npm/pytest on host as non-root user, permission denied errors occur for:
- `/home/matt/cookie/frontend/node_modules/.vite/`
- `/home/matt/cookie/frontend/node_modules/.tmp/`
- `/home/matt/cookie/.pytest_cache/`

**Resolution:**
This is a non-issue when following rule #31: "ALWAYS run tests in Docker". Tests and builds work correctly inside Docker containers. Host permission issues only affect local development outside Docker.

**One-off fix for host permissions:**
```bash
sudo chown -R matt:matt /home/matt/cookie/frontend/node_modules/.vite /home/matt/cookie/frontend/node_modules/.tmp /home/matt/cookie/.pytest_cache
```

**Status:** Won't Fix (work in Docker instead)

**Verification:**
- [x] `docker compose exec frontend npm run build` succeeds
- [x] `docker compose exec frontend npm test` passes (65 tests)
- [x] `docker compose exec web python -m pytest` passes (241 tests)

---

### QA-S: Screen Wake Lock (Modern)

**Issue:** QA-019 - Screen locks during Play Mode (Modern)
**Affects:** Modern (React frontend on iPad/tablets)
**Status:** Verified

**Problem:**
The Modern (React) frontend doesn't have wake lock functionality for Play Mode. When used on an iPad or tablet, the screen will auto-lock during cooking, similar to the Legacy issue (QA-014).

**Research Findings:**
- Screen Wake Lock API (`navigator.wakeLock`) supported in iOS 16.4+, Chrome 84+, Edge 84+
- Silent video fallback works for older browsers (same technique as Legacy QA-014)
- React hook pattern cleanly manages wake lock lifecycle

**Tasks:**
- [x] Research Screen Wake Lock API browser support
- [x] Implement wake lock hook in React
- [x] Add fallback for unsupported browsers
- [x] Integrate with Play Mode component
- [ ] Test on various iPad models

**Implementation:**
Created `useWakeLock` hook with dual-technique approach:
- **Primary:** Screen Wake Lock API (`navigator.wakeLock.request('screen')`)
- **Fallback:** Silent video loop (base64 MP4) for older browsers
- **Visibility handling:** Re-acquires wake lock when tab becomes visible
- **Clean cleanup:** Releases resources on component unmount

Integration in PlayMode.tsx is a single line: `useWakeLock()`

**Files Changed:**
- `frontend/src/hooks/useWakeLock.ts` - New hook with dual technique
- `frontend/src/screens/PlayMode.tsx` - Added useWakeLock() call

**Verification:**
- [x] TypeScript compilation passes
- [x] All 65 frontend tests pass
- [ ] Screen stays awake in Modern Play Mode on iPad
- [ ] Works on iOS 16.4+ with native API
- [ ] Fallback works on older iOS versions
- [ ] Wake lock released when exiting Play Mode

---

### QA-T: Profile Icon Navigation

**Issue:** QA-020 - Profile icon should navigate to profile chooser
**Affects:** Modern
**Status:** New

**Problem:**
On the Modern frontend, clicking the user profile icon (avatar) in the top right corner of the header does not navigate to the profile chooser page. The "switch profile" icon next to it correctly navigates to the profile chooser, but the profile avatar itself should have the same behavior for intuitive UX.

**Expected behavior:** Clicking the profile avatar in the top right corner should navigate to the user/profile chooser page, matching the behavior of the adjacent switch profile icon.

**Screenshots:** _To be added during testing_

**Research Findings:**
_To be investigated during research phase_

**Tasks:**
- [x] Research how profile icon click is currently handled in Modern frontend
- [x] Identify the header component and profile avatar element
- [x] Add onClick handler to navigate to profile chooser
- [x] Verify behavior matches switch profile icon
- [x] Test on Modern frontend (desktop browser)

**Implementation:**
- Added `onClick` handler to profile avatar in `App.tsx` header
- Avatar now calls `handleProfileClick()` to navigate to profile chooser
- Matches behavior of adjacent switch profile icon

**Files Changed:**
- `frontend/src/App.tsx` - Added onClick handler to profile avatar

**Verification:**
- [x] Clicking profile avatar navigates to profile chooser
- [x] Behavior matches the switch profile icon
- [x] Works on Modern frontend (desktop browser)

---

### QA-057: Discover tab shows "no suggestions" for new users

**Issue:** QA-057 - Discover tab shows "no suggestions" for new users without history
**Affects:** Modern + Legacy
**Status:** Verified

**Problem:**
On both frontends, the Discover tab shows "No suggestions yet" even for users who have history but no favorites. Per claude.md rule #20, new users (even without favorites/history) should see seasonal/holiday suggestions based on the current date.

**Steps to reproduce:**
1. Log in as user "matt" (or any profile)
2. Navigate to Home screen
3. Click on "Discover" tab
4. Observe "No suggestions yet" message

**Expected behavior:**
Discover should show seasonal/holiday suggestions based on the current date, even for users without favorites or history.

**Research Findings:**

_Root cause identified:_
The AI prompts for discover features (`discover_seasonal`, `discover_favorites`, `discover_new`) tell the AI to return a **single object**, but the validator expects an **array of 1-5 items**.

Prompt system instructions say:
```
Always respond with valid JSON in this exact format:
{
  "search_query": "...",
  "title": "...",
  "description": "..."
}
```

But validator schema in `apps/ai/services/validator.py` expects:
```python
'discover_seasonal': {
    'type': 'array',
    'items': { ... },
    'minItems': 1,
    'maxItems': 5,
}
```

The service code in `apps/ai/services/discover.py` also iterates over the validated response:
```python
for item in validated:
    suggestion = AIDiscoverySuggestion.objects.create(...)
```

Logs confirm all three discover functions fail validation:
```
WARNING discover - Failed to generate seasonal suggestions: AI response validation failed for discover_seasonal
WARNING discover - Failed to generate recommended suggestions: AI response validation failed for discover_favorites
WARNING discover - Failed to generate try-new suggestions: AI response validation failed for discover_new
```

_Solution:_
Update all three discover prompts to request an array of 3-5 suggestions instead of a single object.

**Implementation Plan:**

Create migration `0009_fix_discover_prompts.py` that updates:
1. `discover_seasonal` - Change system prompt to request array of 3-5 seasonal/holiday suggestions
2. `discover_favorites` - Change system prompt to request array of 3-5 recommendations based on history
3. `discover_new` - Change system prompt to request array of 3-5 adventurous suggestions

New prompt format for each:
```
Always respond with valid JSON as an array of 3-5 suggestions:
[
  {"search_query": "...", "title": "...", "description": "..."},
  {"search_query": "...", "title": "...", "description": "..."},
  ...
]
```

**Files modified:**
- `apps/ai/migrations/0009_fix_discover_prompts.py` - Migration to update all three prompt templates

**Tasks:**
- [x] Create migration to update all three discover prompts to request arrays
- [x] Test with new user (no history) - should get seasonal suggestions
- [x] Test with user with history - should get all three types
- [x] Verify on Modern frontend
- [x] Verify on Legacy frontend

---

### QA-058: AllRecipes article pages cause "Recipe has no title" on import

**Issue:** QA-058 - AllRecipes article pages shown in search results fail import with "Recipe has no title"
**Affects:** Modern + Legacy
**Status:** Verified

**Problem:**
When searching for recipes, AllRecipes article pages (e.g., "Ina Garten's Beef Stew Recipe Is Exactly What We Need...") appear in search results alongside actual recipes. When users try to import these articles, they fail with "Recipe has no title" because article pages don't have recipe schema markup.

**Root cause:**
AllRecipes has two types of pages:
- Recipe pages: `allrecipes.com/recipe/12345/beef-stew/` (has schema.org recipe data)
- Article pages: `allrecipes.com/ina-gartens-beef-stew-recipe-8736364` (no recipe schema)

The search URL filtering heuristics were too permissive and allowed article URLs through because they:
- Have long paths with hyphens (looks like a recipe slug)
- Often contain the word "recipe" in the title

**Solution:**
Added site-specific filter for allrecipes.com - URLs must contain `/recipe/` in the path to be considered valid recipe URLs.

**Files modified:**
- `apps/recipes/services/search.py` - Added allrecipes.com specific URL filter
- `apps/recipes/api.py` - Added URL logging for scrape requests to aid debugging

**Tasks:**
- [x] Add URL logging to scrape endpoint for debugging
- [x] Add allrecipes.com site-specific filter requiring `/recipe/` in path
- [x] Verify article URLs are filtered from search results

---

### QA-060: GitHub Pages Root Landing Page Returns 404

**Issue:** QA-060 - https://matthewdeaves.github.io/cookie/ returns 404 error
**Affects:** Infrastructure (GitHub Pages)
**Status:** Fixed

**Problem:**
The GitHub Pages site at https://matthewdeaves.github.io/cookie/ returns a 404 error. Users visiting the root URL cannot access the code quality dashboard or any project information. The current setup only deploys to `/coverage/` subdirectory, leaving the root path empty.

**Research Findings:**

_Current State (Before Fix):_
- GitHub Pages was deployed to `gh-pages` branch
- Content existed only at `/coverage/` subdirectory
- Coverage dashboard, SVG badges, and metrics API were working
- `.nojekyll` file disabled Jekyll processing
- No content existed at root level

_Working Endpoints:_
- `https://matthewdeaves.github.io/cookie/coverage/` - Metrics dashboard
- `https://matthewdeaves.github.io/cookie/coverage/api/metrics.json` - Metrics API
- `https://matthewdeaves.github.io/cookie/coverage/badges/*.svg` - Badge images

_Root Cause:_
The coverage workflow deployed content to the `/coverage/` subdirectory using `destination_dir: ./coverage`. The root `/` was never populated.

**Implementation (Option A: Simple Redirect):**

Changed to Option A - the /coverage/ dashboard already has everything needed.

1. **Restructured output directory:**
   - Changed from `coverage-report/` to `site/coverage/`
   - Root `index.html` redirects to `/coverage/`
   - Coverage dashboard at `site/coverage/index.html`

2. **Created root redirect:**
   - Simple meta refresh redirect to `/coverage/`
   - Fallback link for browsers without redirect support

3. **Updated deployment:**
   - Removed `destination_dir: coverage` to deploy to root
   - Changed `publish_dir: ./site` (was `./coverage-report`)
   - Added `.nojekyll` file to root

4. **Fixed URL references:**
   - Corrected `mndeaves` to `matthewdeaves` throughout

**Tasks:**
- [x] Research: Decide on implementation approach (A, B, or C) → Option A
- [x] Create root `index.html` redirect
- [x] Update `.github/workflows/coverage.yml` to deploy root content
- [x] Test deployment end-to-end
- [ ] Update README with correct GitHub Pages URL

**Files Modified:**
- `.github/workflows/coverage.yml` - Restructured output, added root redirect

**New Site Structure:**
```
/ (root)
├── index.html          # Redirect to /coverage/
├── .nojekyll           # Disable Jekyll
└── coverage/
    ├── index.html      # Metrics dashboard
    ├── api/metrics.json
    ├── badges/*.svg
    ├── frontend/       # Frontend coverage report
    ├── backend/        # Backend coverage report
    └── ...
```

**Acceptance Criteria:**
- [x] https://matthewdeaves.github.io/cookie/ loads successfully (no 404)
- [x] Root redirects to /coverage/ dashboard
- [x] No breaking changes to existing /coverage/ functionality

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

### QA-006: Recipe detail layout/spacing issues (iOS 9)

**Found:** 2026-01-07 (iPad 3 / iOS 9)
**Reporter:** Matt

Multiple layout and spacing issues on the Legacy recipe detail page:

1. **List item spacing:** Ingredient and instruction lists have insufficient gap between the numbered circle badge and text content. Text appears cramped against badges.

2. **Meta items concatenated:** The recipe details row (Prep/Cook/Total/Servings) shows with no spacing between items, appearing as "Prep:20 minCook:10 minTotal:30 min".

3. **Nutrition labels raw:** Nutrition tab shows raw field names like "CarbohydrateContent", "CholesterolContent" instead of human-readable labels.

**Root Cause:** CSS `gap` property is not supported for flexbox in iOS 9 Safari. The Legacy CSS uses `gap:` extensively without margin-based fallbacks.

Related to QA-003 (list styling) - discovered during verification of the badge color fix.

---

### QA-007: Button icons off-center (Safari flexbox bug)

**Found:** 2026-01-08 (iPad 3 / iOS 9)
**Reporter:** Matt

Circular icon buttons on the recipe detail page display their SVG icons slightly to the left of center within the circle:

- Back button (chevron `<`) in top-left of hero image
- Favorite button (heart) near Cook! button
- Collection button (+) near Cook! button
- Servings decrease button (-)
- Servings increase button (+)

The icons are still contained within the circles but are noticeably off-center, appearing offset to the left. This is a known Safari bug where `<button>` elements ignore flexbox centering properties (`align-items`, `justify-content`).

**Root Cause:** Safari ignores `align-items` and `justify-content` when the flex container is a `<button>` element. This is a documented bug in the [flexbugs repository](https://github.com/philipwalton/flexbugs/issues/236).

Related to QA-006 (CSS gap fallbacks) - same class of iOS 9 CSS compatibility issues.

---

### QA-008: Search input text unreadable in dark mode

**Found:** 2026-01-08 (Modern frontend)
**Reporter:** Matt
**Fixed:** 2026-01-08

On the Modern frontend with dark mode enabled, the search input field has a text color issue. When the user types into the search box, the text is not readable - appearing as white or light text on a white or light background.

**Root cause:** The `--input-background` CSS variable was missing from the dark mode theme definition in `theme.css`. The input was falling back to the light mode background color (`#f4ede6` beige) while using dark mode text color (`#f5ebe0` light beige), resulting in light-on-light text.

**Fix:** Added `--input-background: #3d3531;` to the `.dark` section in `theme.css`, matching the dark mode secondary color for consistency.

---

### QA-009: Search results missing/broken images

**Found:** 2026-01-08 (iPad 3 / iOS 9 + Modern Firefox)
**Reporter:** Matt

When searching for recipes (e.g. "chicken"), image loading behaves differently between frontends:

- **Modern frontend:** Most recipe images load correctly, some show "No Image" placeholder
- **Legacy frontend:** Same recipes that have working images on Modern show as white/blank boxes on Legacy. Recipes with no images correctly show "No image" placeholder on both.

This suggests external image URLs are failing to load on Legacy (iOS 9 Safari) while working on Modern browsers. Could be CORS, mixed content, or user-agent related.

**Screenshots:** `shots/ipad.PNG` (Legacy), `shots/firefox.png` (Modern)

---

### QA-010: Multiple timers have no spacing in Play Mode

**Found:** 2026-01-08 (iPad 3 / iOS 9)
**Reporter:** Matt

When viewing Play Mode on a recipe that has more than one timer, the timer elements are stacked vertically with no visible spacing between them. The timers appear to be sitting directly on top of each other, making them visually cluttered and difficult to distinguish.

**Root Cause:** Likely related to iOS 9's lack of support for CSS `gap` property in flexbox, similar to QA-006. The timer container probably uses `gap:` without a margin-based fallback for older Safari versions.

**Expected behavior:** Timers should have adequate vertical spacing (likely 1rem/16px) between them to create visual separation and improve usability.

Related to QA-006 (CSS gap fallbacks) - same class of iOS 9 CSS compatibility issues.

---

### QA-011: Timers don't auto-start when added in Play Mode

**Found:** 2026-01-08 (Modern frontend)
**Reporter:** Matt

On the Modern frontend in Play Mode, when a user adds a timer from the instructions, it appears in the timer list but does not automatically start counting down. The user must manually tap the start button to begin the countdown.

**Expected behavior:** When a timer is added in Play Mode, it should automatically start counting down without requiring an additional user action. This provides a smoother cooking experience where users can add a timer and immediately continue with the recipe.

**Root Cause:** _To be investigated during research phase_

---

### QA-012: Timer completion sound doesn't play

**Found:** 2026-01-08 (Modern frontend)
**Reporter:** Matt

On the Modern frontend in Play Mode, when a timer completes and reaches 0:00, no audio notification is played to alert the user. This is a critical usability issue for a cooking timer, as users may not be looking at the screen when the timer finishes.

**Expected behavior:** When a timer completes, an audible sound/alert should play to notify the user that the timer has finished. The sound should be distinct and loud enough to be heard from a reasonable distance (e.g., across the kitchen).

**Root Cause:** _To be investigated during research phase_

**Related:** QA-013 - same issue affects Legacy frontend

---

### QA-013: Timer completion sound doesn't play (Legacy)

**Found:** 2026-01-08 (iPad 3 / iOS 9)
**Reporter:** Matt

On the Legacy frontend in Play Mode (iPad 3 / iOS 9), when a timer completes and reaches 0:00, no audio notification is played to alert the user. This is a critical usability issue for a cooking timer, as users may not be looking at the screen when the timer finishes.

**Expected behavior:** When a timer completes, an audible sound/alert should play to notify the user that the timer has finished. The sound should be distinct and loud enough to be heard from a reasonable distance (e.g., across the kitchen).

**Root Cause:** _To be investigated during research phase_

**Related:** QA-012 - same issue affects Modern frontend, suggesting a shared root cause (possibly missing audio file, broken audio API integration, or user interaction requirement for audio playback)

**Note:** iOS Safari has strict autoplay policies that may require user interaction before audio can play. Need to investigate if this is blocking timer completion sounds.

---

### QA-014: Screen locks during Play Mode

**Found:** 2026-01-08 (iPad 3 / iOS 9)
**Reporter:** Matt

On the Legacy frontend in Play Mode (iPad 3 / iOS 9), the device follows its normal auto-lock behavior and the screen locks after the configured timeout period. For cooking use cases, this is problematic because users are often not actively interacting with the device while following recipe steps, monitoring timers, or working with ingredients.

**Expected behavior:** While in Play Mode, the screen should remain on and not auto-lock. When the user exits Play Mode, normal auto-lock behavior should resume.

**Root Cause:** _To be investigated during research phase_

**Implementation notes:**
- The Screen Wake Lock API is the modern solution, but iOS 9 Safari likely doesn't support it
- Common workaround: Play a silent/hidden video in a loop to prevent screen lock
- Need to ensure wake lock is released when exiting Play Mode
- Should also implement for Modern frontend if possible

**Related:** This would significantly improve the cooking experience alongside fixing the timer issues (QA-010, QA-011, QA-012, QA-013)

---

### QA-015: No "View All" link for Favorites section

**Found:** 2026-01-08 (Legacy + Modern)
**Reporter:** Matt

On the home page, the "Recently Viewed" section includes a "View All" link in the section header that shows the total count and navigates to the All Recipes page. The "Favorites" section below it does not have this same pattern - it shows favorite recipes but has no "View All" link in the header.

**Expected behavior:** The Favorites section should have a section header with a "View All ({count})" link that navigates to the existing Favorites page, matching the pattern established by Recently Viewed in QA-005.

**Root Cause:** Simple omission - the section header pattern wasn't applied to Favorites when it was added to Recently Viewed.

**Implementation notes:**
- Favorites page already exists at `/legacy/favorites/` and Modern has Favorites screen
- Just need to add the `.section-header` with `.section-link` (Legacy) or equivalent (Modern)
- Should follow the same pattern as QA-005 implementation
- Need to pass `favorites_count` to the home template/component

**Related:** QA-005 - this follows the same pattern established for Recently Viewed

---

### QA-016: Back button after import goes to home instead of search results

**Found:** 2026-01-08 (Modern)
**Reporter:** Matt

On the modern frontend, after importing a recipe from search results, clicking the in-page back button on the recipe view page navigates to home/search instead of returning to the search results with the previous query.

**Steps to reproduce:**
1. Go to Modern frontend search
2. Search for a recipe (e.g., "chicken")
3. Click "Import" on a search result
4. Navigate to the imported recipe view page
5. Click the in-page back button
6. **Actual:** Returns to home/search page
7. **Expected:** Returns to search results with "chicken" query preserved

**Root Cause:** In `App.tsx`, the `handleImport()` function calls `setSearchQuery('')` after successful import (line 123). When `handleRecipeDetailBack()` evaluates `searchQuery ? 'search' : 'home'` (line 148), the query is empty so user is sent to home.

**Why Legacy Works:** Legacy uses browser history API (`window.history.back()`) which naturally preserves the page stack. Modern is a SPA managing navigation via React state, which requires careful state management.

**Fix:** Remove `setSearchQuery('')` from `handleImport()` and ensure `previousScreen` is set to `'search'` so back navigation works correctly.

---

### QA-017: Frontend build fails - test files missing cached_image_url

**Found:** 2026-01-08 (Modern)
**Reporter:** Matt

The frontend TypeScript build (`npm run build`) fails with multiple type errors in `src/test/components.test.tsx`. The errors all relate to mock `SearchResult` objects missing the `cached_image_url` property.

This is a regression from QA-009 (image caching feature). When the `SearchResult` interface was updated to include `cached_image_url`, the test file mock data was not updated to match.

**Error output:**
```
src/test/components.test.tsx(164,9): error TS2741: Property 'cached_image_url' is missing in type...
src/test/components.test.tsx(165,9): error TS2741: Property 'cached_image_url' is missing in type...
src/test/components.test.tsx(183,17): error TS2741: Property 'cached_image_url' is missing in type...
src/test/components.test.tsx(247,17): error TS2741: Property 'cached_image_url' is missing in type...
src/test/components.test.tsx(263,17): error TS2741: Property 'cached_image_url' is missing in type...
```

**Fix:** Add `cached_image_url: null` (or appropriate test value) to all mock SearchResult objects in the test file.

---

### QA-020: Profile icon should navigate to profile chooser

**Found:** 2026-01-08 (Modern)
**Reporter:** Matt

On the Modern frontend, clicking the user profile avatar/icon in the top right corner of the header does not navigate to the profile chooser page. The "switch profile" icon (arrows icon) next to the avatar correctly navigates to the profile chooser, but the avatar itself should also trigger the same navigation for intuitive UX.

**Current behavior:** Clicking the profile avatar does nothing (or navigates elsewhere).

**Expected behavior:** Clicking the profile avatar should navigate to the profile chooser page, matching the behavior of the adjacent switch profile icon.

**Root Cause:** _To be investigated during research phase_

---

### QA-021: Remixed recipes have no image

**Found:** 2026-01-08 (Modern)
**Reporter:** Matt

When a user creates a remix of a recipe, the remixed recipe has no image. The original recipe has both an `image_url` (external) and `image` (local cached file), but neither is copied to the remix.

**Steps to reproduce:**
1. Navigate to a recipe with an image (e.g., Thai Green Curry)
2. Click the Remix button (sparkles icon)
3. Select a modification and create the remix
4. View the remixed recipe

**Expected behavior:** The remixed recipe should display the same image as the original recipe.

**Actual behavior:** The remixed recipe shows "No image" placeholder.

**Root Cause:**
In `apps/ai/services/remix.py:133-152`, the `create_remix()` function creates a new Recipe but does NOT copy the image fields from the original:

```python
remix = Recipe.objects.create(
    title=validated['title'],
    # ... other fields ...
    cuisine=original.cuisine,  # Only cuisine and category are copied
    category=original.category,
    # Missing: image_url=original.image_url,
    # Missing: image=original.image,
)
```

**Database evidence:**
- Original recipe ID 17: `image_url='https://...jpg'`, `image='recipe_images/recipe_27eb4c63a079.jpg'`
- Remix recipe ID 26: `image_url=''`, `image=''`

**Fix:** Add `image_url=original.image_url` and `image=original.image` to the Recipe.objects.create() call in remix.py.

---

### QA-022: Instructions tab crashes on remixed recipes

**Found:** 2026-01-08 (Modern)
**Reporter:** Matt

When viewing a remixed recipe and clicking the Instructions tab, the React app crashes and shows a blank page. The page source shows only the HTML shell with no rendered content.

**Steps to reproduce:**
1. Create a remix of any recipe
2. View the remixed recipe (Ingredients tab works)
3. Click the "Instructions" tab
4. Page goes blank

**Expected behavior:** Instructions should display like any other recipe.

**Actual behavior:** React app crashes, showing blank page with only the Vite dev server HTML shell.

**Root Cause:**
**Data format mismatch between remix storage and frontend expectations.**

In `apps/ai/services/remix.py:137`:
```python
instructions=[{'text': step} for step in validated['instructions']],
```

This saves instructions as: `[{'text': 'Heat pan...'}, {'text': 'Add ingredients...'}]`

But in `frontend/src/screens/RecipeDetail.tsx:416-421`, InstructionsTab expects `string[]`:
```typescript
{instructions.map((step, index) => (
  <p className="pt-0.5 text-foreground">{step}</p>  // step is object, not string!
))}
```

When React tries to render `{step}` where step is an object `{text: '...'}`, it throws:
> "Objects are not valid as a React child (found: object with keys {text})"

**Database evidence:**
- Original recipe instructions: `['Step 1 text', 'Step 2 text']` (list of strings)
- Remix recipe instructions: `[{'text': 'Step 1 text'}, {'text': 'Step 2 text'}]` (list of dicts)

**TypeScript types (client.ts):**
- Line 104: `instructions: string[]` (RecipeDetail type expects strings)

**Fix:** Change `remix.py:137` from:
```python
instructions=[{'text': step} for step in validated['instructions']],
```
to:
```python
instructions=validated['instructions'],
```

The AI already returns instructions as a list of strings, so the wrapping is unnecessary and breaks the frontend.

---

### QA-023: Remix button does nothing on Legacy

**Found:** 2026-01-08 (iPad 3 / iOS 9)
**Reporter:** Matt
**Status:** New

On the Legacy frontend recipe detail page, clicking the Remix button (sparkles icon) does nothing. No modal appears, no error is shown.

**Steps to reproduce:**
1. Navigate to any recipe detail page on Legacy frontend (iPad / iOS 9)
2. Click the Remix button (sparkles icon near favorite/collection buttons)
3. Nothing happens

**Expected behavior:** Remix modal should appear with AI-generated suggestions.

**Actual behavior:** Button click has no visible effect. Collection modal DOES work (same pattern).

**Root Cause:** **Staticfiles out of date - `collectstatic` not run after remix code added.**

| File | Size | Modified | Has Remix Code |
|------|------|----------|----------------|
| Source (`apps/legacy/static/legacy/js/pages/detail.js`) | 21,027 bytes | Jan 8 17:35 | ✅ Yes |
| Staticfiles (`staticfiles/legacy/js/pages/detail.js`) | 13,221 bytes | Jan 8 07:24 | ❌ No |

The diff shows the staticfiles version is missing:
- Remix variables (`selectedRemixSuggestion`, `remixSuggestions`, `isCreatingRemix`)
- All remix event listeners in `setupEventListeners()`
- All remix functions (`handleRemixClick`, `closeRemixModal`, `loadRemixSuggestions`, etc.)

Django serves from `staticfiles/` in production, so the old JS (without remix) is being served.

**Fix:**
```bash
docker compose exec web python manage.py collectstatic --noinput
```

Then clear browser cache on iPad and reload.

**Tasks:**
- [x] Run `collectstatic` to update staticfiles
- [x] Clear iPad browser cache
- [x] Verify remix modal appears
- [ ] Test full remix flow on Legacy

**Verification:** Confirmed working on iPad 3 / iOS 9 after running `collectstatic`.

---

### QA-024: Legacy instructions tab shows curly braces on remixes

**Found:** 2026-01-08 (iPad 3 / iOS 9)
**Reporter:** Matt
**Status:** New

On the Legacy frontend, when viewing a remixed recipe's Instructions tab, each instruction step displays with curly braces `{}` around the text instead of plain text.

**Steps to reproduce:**
1. Create a remix of any recipe
2. Navigate to the remixed recipe on Legacy frontend
3. Click the Instructions tab
4. Instructions show wrapped in curly braces

**Expected behavior:** Instructions display as plain text (e.g., "Heat the pan...")

**Actual behavior:** Instructions display with curly braces (e.g., "{text: Heat the pan...}" or similar)

**Root Cause:** Same as QA-022 - remix instructions stored as `[{'text': '...'}]` instead of `['...']`.

When the Django template iterates over instructions and renders `{{ instruction }}`, it outputs the dict representation including the curly braces, rather than just the text content.

**Fix:** Same fix as QA-022 - change `remix.py:137` to store instructions as plain strings.

---

### QA-025: Legacy Play Mode shows [object Object] for remix steps

**Found:** 2026-01-08 (iPad 3 / iOS 9)
**Reporter:** Matt
**Status:** New

On the Legacy frontend Play Mode, when cooking a remixed recipe, each step displays `[object Object]` instead of the actual instruction text.

**Steps to reproduce:**
1. Create a remix of any recipe
2. Navigate to the remixed recipe on Legacy frontend
3. Click "Cook!" to enter Play Mode
4. Step text shows `[object Object]` instead of actual instructions

**Expected behavior:** Step displays instruction text (e.g., "Heat the pan...")

**Actual behavior:** Step displays `[object Object]`

**Root Cause:** Same as QA-022 - remix instructions stored as `[{'text': '...'}]` instead of `['...']`.

When Legacy Play Mode JavaScript tries to display the step, it coerces the object to a string, resulting in `[object Object]`.

**Fix:** Same fix as QA-022 - change `remix.py:137` to store instructions as plain strings.

---

### QA-026: Remixed recipes have no nutrition information

**Found:** 2026-01-08 (Modern + Legacy)
**Reporter:** Matt
**Status:** New (Enhancement)

When viewing a remixed recipe, the Nutrition tab shows no data. Original recipes display nutrition information scraped from the source, but AI-generated remixes have no nutrition data.

**Steps to reproduce:**
1. Create a remix of any recipe
2. View the remixed recipe
3. Click the Nutrition tab
4. No nutrition information displayed

**Expected behavior:** Some nutrition information should be available.

**Actual behavior:** Nutrition tab is empty for remixed recipes.

**Root Cause:**
Original recipes get nutrition from `recipe-scrapers` which extracts it from the source website. Remixed recipes are AI-generated and `remix.py` does not populate any nutrition fields.

**Possible Solutions:**
1. **Copy from original** - Inaccurate since ingredients change in remixes
2. **AI estimation** - Have the AI estimate nutrition based on modified ingredients (future enhancement)
3. **Document limitation** - Accept that remixes don't have nutrition data

**Fix:** Implemented option 2 - AI nutrition estimation.
- Added `nutrition_estimate` prompt (migration 0003)
- Added validation schema in `validator.py`
- Added `estimate_nutrition()` function in `remix.py`
- Called automatically after remix creation if original has nutrition data
- Non-blocking: if estimation fails, remix is still created without nutrition

---

### QA-027: Invalid AI model selection breaks features silently

**Found:** 2026-01-08 (Modern + Legacy)
**Reporter:** Matt
**Status:** Fixed

When a user selects an invalid model ID in the AI Settings UI, AI features fail with unhelpful error messages like "Failed to load suggestions" instead of indicating the model is invalid.

**Steps to reproduce:**
1. Go to AI Settings (Modern frontend)
2. Change a prompt's model to an invalid ID (e.g., `google/gemini-2.5-flash-preview`)
3. Save settings
4. Try to use the feature (e.g., Remix suggestions)
5. Feature fails with generic error

**Expected behavior:** Either:
- Validate model IDs before saving and show error if invalid
- Show clear error message indicating the model is not available
- Gracefully fall back to a default model

**Actual behavior:** Generic "Failed to load suggestions" error. User has no indication the model selection is the problem.

**Root Cause:**
The AI Settings UI allows free-form model selection but doesn't validate against OpenRouter's available models. When an invalid model is used, OpenRouter returns an error that gets caught and converted to a generic user-facing error.

**Error from logs:**
```
openrouter.errors.chaterror.ChatError: google/gemini-2.5-flash-preview is not a valid model ID
```

**Research Findings:**
The OpenRouter Python SDK provides a `models.list()` method that returns all available models. The dropdown should be populated from this API, not a static list.

**Fix Implementation:**

1. **Added `get_available_models()` to OpenRouterService** (`apps/ai/services/openrouter.py:196-221`)
   - Queries OpenRouter API for list of available models
   - Returns list of `{id, name}` dicts

2. **Changed `/api/ai/models` endpoint to fetch from OpenRouter** (`apps/ai/api.py:178-189`)
   - Dropdown now shows only valid models from OpenRouter API
   - Returns empty list if no API key configured
   - Users can only select valid models - no invalid selection possible

3. **Added defense-in-depth validation on save** (`apps/ai/api.py:145-162`)
   - Validates model against OpenRouter before saving (backup check)
   - Returns 422 with `error: 'invalid_model'` if model somehow invalid

4. **Updated frontend error handling** (`frontend/src/screens/Settings.tsx:140-154`)
   - Parses JSON error response from server
   - Displays specific error message if validation fails

**Status:** Verified

---

### QA-028: Old browsers show white page instead of redirecting to Legacy

**Issue:** QA-028 - Old browsers show white page instead of redirecting to Legacy
**Affects:** Legacy
**Status:** Verified

**Problem:**
On iPad with Safari on iOS 9, navigating to the root URL (/) shows a white page instead of redirecting to /legacy/. The modern React frontend fails silently on unsupported browsers.

**Steps to reproduce:**
1. Use an old iPad with Safari on iOS 9
2. Navigate to http://[cookie-ip-address]/
3. Page shows white/blank instead of redirecting to /legacy/

**Research Findings:**

_Current routing architecture:_
- Root URL (`/`) has NO Django handler - falls through to Nginx
- Nginx proxies unmatched routes to Vite (React frontend)
- React app requires ES2020+ (ES6 modules, async/await, Fetch API, etc.)
- iOS 9 Safari doesn't support ES6 modules, so React never initializes → white page

_Why white page occurs:_
1. iOS 9 Safari doesn't understand `<script type="module">`
2. React and dependencies fail to parse/load
3. React never initializes, shows empty page
4. No error message displayed to user

_Browsers to redirect:_
- iOS < 11 (Safari lacks ES6 module support)
- All IE versions (no ES6 support)
- Edge Legacy (non-Chromium, pre-2020)

**Tasks:**
- [x] Add User-Agent detection to Nginx for legacy browsers
- [x] Redirect legacy browsers from root path to `/legacy/`
- [x] Ensure `/api/` and `/legacy/` paths are NOT redirected
- [x] Expand Django middleware detection (for future use)
- [x] Add tests for browser detection patterns
- [x] Verify on iPad 3 / iOS 9

**Implementation:**
- **Nginx redirect** (`nginx/nginx.conf`): Added User-Agent checks in the root location block
  - Detects iOS < 11, IE (MSIE/Trident), Edge Legacy
  - Returns 302 redirect to `/legacy/` for legacy browsers
  - Must be at Nginx level since root `/` bypasses Django entirely
- **Django middleware** (`apps/core/middleware.py`): Simplified to detection only
  - Sets `request.is_legacy_device` flag for potential future use in views/templates
  - Redirect logic removed (handled by Nginx for performance)
- **Tests** (`tests/test_device_detection.py`): 15 tests for browser detection

**Files Changed:**
- `nginx/nginx.conf` - Added legacy browser detection + redirect
- `apps/core/middleware.py` - Simplified to detection flag only
- `tests/test_device_detection.py` - Browser detection test coverage

**Verification:**
- [x] iOS 9 Safari on root URL redirects to /legacy/
- [x] Modern browsers still get React app
- [x] /api/ endpoints work for all browsers
- [x] /legacy/ URLs work without redirect loops

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
- [x] Recipe detail page (styling/layout) - QA-003, QA-006, QA-007 verified
- [ ] Recipe detail page (functional: tabs switching, content display)
- [x] Play mode navigation - QA-004 verified
- [x] Timer functionality - QA-010, QA-011, QA-012, QA-013 verified
  - [x] Timer spacing (QA-010)
  - [x] Timer auto-start (QA-011)
  - [x] Timer completion sound - Modern (QA-012)
  - [x] Timer completion sound - Legacy (QA-013)
  - [ ] Screen wake lock during Play Mode (QA-014 - pending)
- [x] Multiple simultaneous timers - QA-010 verified
- [x] Favorites View All link - QA-015 verified
- [ ] Favorites add/remove (functional testing)
- [ ] Collections CRUD
- [x] Serving adjustment button centering - QA-007 verified
- [ ] Serving adjustment (functional: increment/decrement works)
- [x] Search image loading - QA-009 verified
- [x] Search dark mode input - QA-008 verified
- [x] Import flow navigation - QA-002, QA-016 verified
- [ ] Build/tests passing - QA-017 pending

### AI Features (Phase 8B)
- [ ] Recipe Remix - Modern frontend
- [ ] Recipe Remix - Legacy frontend (iOS 9)
- [ ] Remix button visibility (hidden without API key)
- [ ] Remix per-profile visibility

---

## Recipe Remix Manual QA

> **Feature:** Recipe Remix (Phase 8B Sessions A+B)
> **Prerequisite:** API key configured (AI available)
> **Affects:** Modern + Legacy

### Test Environment Setup

Before testing, verify:
```bash
# Check AI is available
curl -s http://localhost/api/ai/status
# Should return: {"available": true, ...}
```

### Test Scenarios

#### Scenario 1: Remix Button Visibility

**Test 1.1: Button shows when AI available**
- [ ] Modern: Navigate to any recipe detail page
- [ ] Modern: Verify sparkles icon button visible near favorite/collection buttons
- [ ] Legacy: Navigate to any recipe detail page
- [ ] Legacy: Verify sparkles icon button visible near favorite/collection buttons

**Test 1.2: Button hidden when AI unavailable**
- [ ] Remove API key (Settings > AI > clear key)
- [ ] Modern: Navigate to recipe detail - remix button should NOT appear
- [ ] Legacy: Navigate to recipe detail - remix button should NOT appear
- [ ] Restore API key after testing

#### Scenario 2: Remix Modal (Modern)

**Test 2.1: Open modal**
- [ ] Click remix button (sparkles icon)
- [ ] Modal appears with "Remix This Recipe" header
- [ ] Loading spinner shows while fetching suggestions

**Test 2.2: Suggestions load**
- [ ] 6 suggestion chips appear after loading
- [ ] Suggestions are contextual to the recipe (mention ingredients/cuisine)
- [ ] Chips are clickable

**Test 2.3: Suggestion selection**
- [ ] Click a suggestion chip - it highlights (selected state)
- [ ] Click same chip again - deselects
- [ ] Click different chip - previous deselects, new one selects
- [ ] "Create Remix" button enables when chip selected

**Test 2.4: Custom input**
- [ ] Type in "Or describe your own remix" input
- [ ] Any selected chip deselects when typing
- [ ] "Create Remix" button enables with text input
- [ ] Clear input - button disables (unless chip selected)

**Test 2.5: Create remix**
- [ ] Select a suggestion OR type custom modification
- [ ] Click "Create Remix"
- [ ] Button shows loading state ("Creating Remix...")
- [ ] Modal closes on success
- [ ] Toast shows "Created [recipe title]"
- [ ] Navigate to new recipe (should auto-navigate)

**Test 2.6: Verify created remix**
- [ ] Recipe title reflects the modification
- [ ] Recipe shows "user-generated" as source
- [ ] Ingredients list is modified appropriately
- [ ] Instructions are modified appropriately
- [ ] Recipe appears in Recently Viewed

#### Scenario 3: Remix Modal (Legacy / iOS 9)

**Test 3.1: Open modal**
- [ ] Tap remix button (sparkles icon)
- [ ] Modal appears with "Remix This Recipe" header
- [ ] Loading spinner shows while fetching suggestions

**Test 3.2: Suggestions load**
- [ ] 6 suggestion chips appear after loading
- [ ] Chips display correctly (no layout issues)
- [ ] Touch targets are adequate (44px minimum)

**Test 3.3: Suggestion selection**
- [ ] Tap a suggestion chip - it highlights
- [ ] Tap same chip again - deselects
- [ ] Tap different chip - previous deselects, new one selects

**Test 3.4: Custom input**
- [ ] Type in custom input field
- [ ] Keyboard appears and doesn't obscure modal
- [ ] Any selected chip deselects when typing

**Test 3.5: Create remix**
- [ ] Select a suggestion OR type custom modification
- [ ] Tap "Create Remix"
- [ ] Button shows loading state
- [ ] Modal closes on success
- [ ] Toast notification appears
- [ ] Navigate to new recipe

**Test 3.6: Modal dismiss**
- [ ] Tap X button - modal closes
- [ ] Tap outside modal - modal closes
- [ ] Escape key (if keyboard connected) - modal closes

#### Scenario 4: Per-Profile Visibility

**Test 4.1: Remix only visible to creator**
- [ ] As Profile A: Create a remix
- [ ] Note the remix title
- [ ] Switch to Profile B (different profile)
- [ ] Search or browse - remix should NOT appear
- [ ] Check Recently Viewed - remix should NOT appear
- [ ] Switch back to Profile A
- [ ] Remix should appear in Recently Viewed

**Test 4.2: Original recipe visible to all**
- [ ] The original recipe (that was remixed) should still be visible to all profiles

#### Scenario 5: Error Handling

**Test 5.1: API error during suggestions**
- [ ] Temporarily break API key
- [ ] Open remix modal
- [ ] Should show error message (not crash)
- [ ] Toast shows "Failed to load suggestions"

**Test 5.2: API error during creation**
- [ ] Start remix creation
- [ ] If API fails, should show error toast
- [ ] Modal should remain open (not lose user's selection)
- [ ] Can retry after fixing issue

### Issue Log Template

If issues are found, log them using this format:

```
### QA-0XX: [Brief description]

**Found:** [Date] ([Device/Browser])
**Affects:** Modern / Legacy / Both

**Problem:**
[Detailed description of the issue]

**Steps to reproduce:**
1. ...
2. ...
3. ...

**Expected behavior:**
[What should happen]

**Actual behavior:**
[What actually happens]

**Screenshots:** [filename if applicable]
```

### Testing Checklist Summary

| Test | Modern | Legacy |
|------|--------|--------|
| Remix button visible (AI on) | [ ] | [ ] |
| Remix button hidden (AI off) | [ ] | [ ] |
| Modal opens | [ ] | [ ] |
| 6 suggestions load | [ ] | [ ] |
| Chip selection works | [ ] | [ ] |
| Custom input works | [ ] | [ ] |
| Create remix succeeds | [ ] | [ ] |
| Loading states show | [ ] | [ ] |
| Toast notifications | [ ] | [ ] |
| Per-profile visibility | [ ] | [ ] |
| Error handling | [ ] | [ ] |

---

### QA-061: CI/CD Code Quality Tooling Gaps and Improvements

**Issue:** QA-061 - CI/CD code quality tooling has gaps in coverage
**Affects:** Infrastructure (CI/CD, GitHub Actions)
**Status:** Fixed (Phase 1-5 complete)
**Priority:** Medium

---

#### Problem Summary

A comprehensive audit of the CI/CD code quality tooling revealed several gaps where code is not being analyzed, reports that could be exposed but aren't linked, and missing tools that would improve code quality enforcement.

The codebase has three distinct areas:
- **Backend**: Django/Python (`apps/` directory)
- **Frontend Modern**: React/TypeScript (`frontend/` directory)
- **Frontend Legacy**: Vanilla JS/CSS for iOS 9 (`apps/legacy/static/legacy/`)

---

#### Research Findings

##### Current Tooling Inventory

| Category | Tool | Target | Scopes | Status |
|----------|------|--------|--------|--------|
| **Test Coverage** | Vitest | Frontend Modern | `src/**/*.{ts,tsx}` | Working |
| **Test Coverage** | pytest-cov | Backend | `apps/`, `cookie/` | Working |
| **Complexity** | radon | Backend | `apps/`, `cookie/` | Working (CC, MI, HAL, RAW) |
| **Complexity** | ESLint | Frontend Modern | `src/` | Working |
| **Complexity** | - | Legacy JS | - | **Missing** |
| **Security** | npm audit | Frontend Modern | All npm deps | Working |
| **Security** | pip-audit | Backend | All pip deps | Working |
| **Duplication** | jscpd | Frontend Modern | `src/` (TS only) | Partial |
| **Duplication** | - | Legacy JS | - | **Missing** |
| **Duplication** | - | Backend Python | - | **Missing** |
| **Bundle** | Vite build | Frontend Modern | `dist/assets/` | Working |
| **Linting** | ESLint | Frontend Modern | `src/**/*.{ts,tsx}` | Working |
| **Linting** | - | Backend Python | - | **Missing** |
| **Linting** | - | Legacy JS | - | **Missing** |
| **Type Check** | TypeScript | Frontend Modern | All TS files | Working |
| **Type Check** | - | Backend Python | - | **Missing** |

##### GitHub Pages Reports - Current vs Potential

**Currently Published:**
| Report | URL | Status |
|--------|-----|--------|
| Dashboard | `/coverage/` | Linked |
| Frontend Coverage HTML | `/coverage/frontend/` | Linked |
| Backend Coverage HTML | `/coverage/backend/htmlcov/` | Linked |
| Metrics JSON API | `/coverage/api/metrics.json` | Linked |
| Badges (9 total) | `/coverage/badges/*.svg` | Linked |

**Generated But NOT Linked:**
| Report | Location in Artifacts | Potential URL | Issue |
|--------|----------------------|---------------|-------|
| Radon HTML Report | `complexity/backend/radon_report.html` | `/coverage/complexity/radon_report.html` | Copied to site but no link in dashboard |
| Radon CC JSON | `complexity/backend/cc.json` | `/coverage/complexity/cc.json` | Raw data, no viewer |
| Radon MI JSON | `complexity/backend/mi.json` | `/coverage/complexity/mi.json` | Raw data, no viewer |
| ESLint Complexity JSON | `complexity/frontend/eslint-complexity.json` | `/coverage/complexity/eslint-complexity.json` | Raw data, no viewer |
| jscpd JSON | `duplication/frontend/jscpd-report.json` | `/coverage/duplication/jscpd-report.json` | Raw data, no viewer |
| npm audit JSON | `security/frontend/npm-audit.json` | `/coverage/security/npm-audit.json` | Raw data, no viewer |
| pip-audit JSON | `security/backend/pip-audit.json` | `/coverage/security/pip-audit.json` | Raw data, no viewer |
| Bundle JSON | `bundle/frontend/bundle-analysis.json` | `/coverage/bundle/bundle-analysis.json` | Raw data, no viewer |

**Could Generate But Don't:**
| Report | Tool Change Needed |
|--------|-------------------|
| jscpd HTML | Add `--reporters html` to ci.yml |

##### Coverage Gaps Detail

**1. Legacy Frontend JavaScript (15 files) - CRITICAL GAP**

Location: `apps/legacy/static/legacy/js/`

Files not analyzed:
```
js/accessibility.js
js/ajax.js
js/alerts.js
js/animations.js
js/buttons.js
js/polyfills.js
js/sounds.js
js/state.js
js/timers.js
js/pages/discover.js
js/pages/home.js
js/pages/profile.js
js/pages/recipe-detail.js
js/pages/recipes-list.js
js/pages/search.js
```

Missing analysis:
- No linting (ESLint not configured for legacy)
- No complexity analysis
- No duplication detection
- No tests

**2. Legacy Frontend CSS (6 files)**

Location: `apps/legacy/static/legacy/css/`

Files not analyzed:
```
css/layout.css
css/components.css
css/discover.css
css/play-mode.css
css/profile.css
css/recipe-detail.css
```

Missing: No CSS linting (stylelint)

**3. Python Backend - Missing Tools**

Current state:
- Tests: pytest with coverage
- Complexity: radon (all metrics)
- Security: pip-audit

Missing:
- No linter (flake8, ruff, pylint, or black)
- No type checker (mypy)
- No duplication detection

**4. jscpd Configuration**

Current: Inline CLI args in ci.yml
```bash
npx jscpd src/ --min-tokens 50 --min-lines 5 \
  --reporters json,console --format 'typescript,tsx' \
  --ignore '**/test/**,**/*.test.*'
```

Issues:
- No `.jscpd.json` config file (harder to maintain)
- Only scans TypeScript, not legacy JS
- No HTML report generated

---

#### Tasks

##### Phase 1: Expose Existing Reports (Quick Wins)

- [x] **Task 1.1**: Link radon HTML report in dashboard
  - File: `.github/workflows/coverage.yml`
  - Add "View Details" button linking to `/coverage/complexity/radon_report.html`
  - **Done**: Added HTML report generation to ci.yml backend-complexity job and linked in dashboard

- [x] **Task 1.2**: Generate jscpd HTML report
  - File: `.github/workflows/ci.yml` (frontend-duplication job)
  - Change: `--reporters json,console` → `--reporters json,console,html`
  - Add link in dashboard to `/coverage/duplication/html/`
  - **Done**: Added html reporter to jscpd command

- [x] **Task 1.3**: Update dashboard with new report links
  - File: `.github/workflows/coverage.yml` (dashboard HTML generation)
  - Add "View Details" buttons for:
    - Backend Complexity → radon HTML
    - Code Duplication → jscpd HTML
  - **Done**: Added View Detailed Report buttons and area tags for clarity

##### Phase 2: Add Legacy JavaScript Analysis

- [x] **Task 2.1**: Create ESLint config for legacy JS
  - Create: `apps/legacy/static/legacy/.eslintrc.json`
  - Configure for ES5/browser globals (iOS 9 compatible)
  - Rules: complexity, no-unused-vars, no-undef
  - **Done**: Created .eslintrc.json with ES5 config and legacy globals

- [x] **Task 2.2**: Add legacy-lint job to CI
  - File: `.github/workflows/ci.yml`
  - New job: `legacy-lint`
  - Scope: `apps/legacy/static/legacy/js/**/*.js`
  - **Done**: Added legacy-lint job with ESLint ES5 analysis

- [x] **Task 2.3**: Add legacy JS to jscpd duplication scan
  - Either update CI inline args or create `.jscpd.json`
  - Add format: `javascript`
  - Add path: `apps/legacy/static/legacy/js/`
  - **Done**: Added legacy-duplication job scanning legacy JS files

- [x] **Task 2.4**: Add legacy complexity analysis
  - Use ESLint complexity rules (same as modern frontend)
  - Report as separate artifact
  - **Done**: legacy-lint job includes complexity warnings tracking

##### Phase 3: Add Python Backend Linting

- [x] **Task 3.1**: Add ruff to requirements.txt
  - `ruff>=0.8.0` (fast Python linter, replaces flake8/isort/black)
  - **Done**: Added to requirements.txt

- [x] **Task 3.2**: Create pyproject.toml with ruff config
  - Or add `[tool.ruff]` section
  - Configure for Django project
  - Set line-length, select rules
  - **Done**: Created pyproject.toml with Django-optimized config, relaxed rules initially

- [x] **Task 3.3**: Add backend-lint job to CI
  - File: `.github/workflows/ci.yml`
  - Command: `ruff check apps/ cookie/`
  - Make it a required check (fail CI on errors)
  - **Done**: Added backend-lint job, included in ci-success required checks

##### Phase 4: Add Python Duplication Detection

- [x] **Task 4.1**: Configure jscpd for Python
  - Add `python` to formats in jscpd config
  - Or use pylint's duplicate-code checker
  - **Done**: Using jscpd with format 'python', ignoring migrations/tests/__pycache__

- [x] **Task 4.2**: Add backend-duplication job to CI
  - Scan: `apps/`, `cookie/`
  - Generate JSON + summary
  - Add to metrics dashboard
  - **Done**: Added backend-duplication job, updated coverage.yml to display metrics and link reports

##### Phase 5: Dashboard Polish and Report Linking

- [x] **Task 5.1**: Improve dashboard section labels
  - Each section should clearly indicate the codebase area it covers
  - Add explicit labels like "Django/Python Backend", "React/TypeScript Frontend", "ES5/Vanilla JS Legacy"
  - Ensure all metrics are grouped by codebase area
  - **Done**: Added section descriptions explaining what each metric covers

- [x] **Task 5.2**: Link all available detailed reports
  - radon HTML report → Backend Complexity
  - jscpd HTML reports → Duplication sections (frontend + backend)
  - Legacy ESLint output → Legacy lint warnings (create HTML report if needed)
  - Ensure all "View Detailed Report" buttons work
  - **Done**: Added HTML report generation for legacy lint, linked all reports

- [x] **Task 5.3**: Add Legacy JavaScript metrics section
  - Display legacy lint warning count
  - Show legacy duplication stats
  - Link to detailed reports
  - **Done**: Legacy section already exists with lint + duplication, added HTML report link

- [x] **Task 5.4**: Add back links to detailed reports
  - All detailed report pages now have "Back to Dashboard" link
  - **Done**: Injected fixed-position back link into all report HTML files

##### Phase 6: Add Python Type Checking (Optional)

- [ ] **Task 6.1**: Add mypy to requirements.txt
  - `mypy>=1.0`
  - `django-stubs` for Django type hints

- [ ] **Task 6.2**: Create mypy.ini or pyproject.toml config
  - Start with `--ignore-missing-imports`
  - Gradually enable strict mode

- [ ] **Task 6.3**: Add backend-typecheck job to CI
  - Initially as warning-only (allow failures)
  - Upgrade to required after fixing type errors

##### Phase 7: Create Centralized Config Files

- [ ] **Task 7.1**: Create `.jscpd.json` config file
  - Move inline args from ci.yml to config file
  - Easier to maintain and document

- [ ] **Task 7.2**: Create or enhance `pyproject.toml`
  - Consolidate Python tool configs
  - ruff, mypy, pytest, coverage settings

- [ ] **Task 7.3**: Document all quality tools in README or CONTRIBUTING.md

##### Phase 8: Gate Complexity Metrics

- [ ] **Task 8.1**: Add complexity thresholds to CI
  - Backend: Fail if average CC > 10 or MI < 50
  - Frontend: Fail if any complexity warnings

- [ ] **Task 8.2**: Update dashboard to show threshold status
  - Show "PASS/FAIL" indicators for each metric

---

#### Configuration File Locations

| File | Purpose | Status |
|------|---------|--------|
| `.github/workflows/ci.yml` | Main CI workflow | Exists |
| `.github/workflows/coverage.yml` | Metrics publishing | Exists |
| `frontend/eslint.config.js` | Modern frontend ESLint | Exists |
| `frontend/vitest.config.ts` | Frontend test config | Exists |
| `pytest.ini` | Backend test config | Exists |
| `requirements.txt` | Python dependencies | Exists |
| `pyproject.toml` | Python project config | Exists (ruff) |
| `.jscpd.json` | Duplication detection config | **Missing** |
| `apps/legacy/static/legacy/.eslintrc.json` | Legacy JS linting | Exists |
| `mypy.ini` | Python type checking | **Missing** |

---

#### Metrics Dashboard Enhancement

Current dashboard sections:
1. Test Coverage (frontend + backend) - with detailed reports
2. Code Complexity (frontend + backend) - **needs detail links**
3. Security (frontend + backend) - summary only
4. Code Quality (duplication + bundle) - **needs detail links**

Proposed additions:
- Link to radon HTML for backend complexity details
- Link to jscpd HTML for duplication details
- Add Legacy JS health section (when implemented)
- Add Python linting status (when implemented)

---

#### Verification Checklist

After implementing each phase:

- [ ] CI workflow runs successfully
- [ ] New reports appear in GitHub Pages
- [ ] Dashboard links work correctly
- [ ] Metrics JSON API includes new data
- [ ] Badges update correctly
- [ ] No false positives blocking legitimate code

---

#### Notes

- **Priority**: Phase 1 (quick wins) should be done first as it requires minimal changes
- **Legacy JS**: The 15 JavaScript files in `apps/legacy/static/legacy/js/` are actively used for iOS 9 support and should have basic quality checks
- **Python linting**: ruff is recommended over flake8 due to performance and feature parity
- **Backwards compatibility**: Legacy ESLint config must use ES5 rules (no arrow functions, etc.)
- **CI time impact**: Adding new jobs will increase CI runtime; consider parallel execution

---

#### Related Issues

- QA-059: Phase 10 CI/CD code review items (6 minor issues)
- QA-060: GitHub Pages root landing page returns 404 (Fixed)


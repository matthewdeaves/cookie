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
| QA-012 | Timer completion sound doesn't play | Modern | New | QA-L |
| QA-013 | Timer completion sound doesn't play | Legacy | New | QA-M |
| QA-014 | Screen locks during Play Mode | Legacy | New | QA-N |
| QA-015 | No "View All" link for Favorites section | Legacy + Modern | New | QA-O |

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
**Status:** New

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
- [ ] Create audio utility with Web Audio API beep function
- [ ] Unlock audio context on Play Mode mount (iOS compatibility)
- [ ] Call audio alert in `handleTimerComplete` callback
- [ ] Test on desktop browsers (Chrome, Firefox, Safari)
- [ ] Test audio restrictions on mobile (may need user interaction)

**Implementation:**
_Pending_

**Files Changed:**
_Pending_

**Verification:**
- [ ] Sound plays when timer reaches 0:00
- [ ] Sound is audible and distinct
- [ ] Works on Modern frontend (desktop browser)
- [ ] Audio unlocking works on mobile Safari

---

### QA-M: Timer Completion Sound (Legacy)

**Issue:** QA-013 - Timer completion sound doesn't play
**Affects:** Legacy
**Status:** New

**Problem:**
On the Legacy frontend (iPad 3 / iOS 9) in Play Mode, when a timer completes (reaches 0:00), no sound is played to alert the user. This is a critical issue for cooking, as users may be away from the device or focused on other tasks when the timer completes.

**Screenshots:** _N/A (audio issue)_

**Research Findings:**
_To be completed during research phase_

**Tasks:**
_To be defined after research_

**Implementation:**
_Pending_

**Files Changed:**
_Pending_

**Verification:**
- [ ] Sound plays when timer reaches 0:00
- [ ] Sound is audible and distinct
- [ ] Works on iPad 3 / iOS 9
- [ ] ES5/iOS 9 audio API compatibility

**Related:** QA-012 (same issue on Modern frontend) - likely same root cause affecting both frontends

---

### QA-N: Screen Wake Lock

**Issue:** QA-014 - Screen locks during Play Mode
**Affects:** Legacy
**Status:** New

**Problem:**
On the Legacy frontend (iPad 3 / iOS 9) in Play Mode, the iPad screen locks after the device's auto-lock timeout (typically 2-5 minutes). When cooking, users are often away from the device or not actively touching the screen, and the screen locking interrupts their workflow - they must unlock the device to check timers or view instructions.

**Screenshots:** _N/A (behavioral issue)_

**Research Findings:**
_To be completed during research phase_

**Tasks:**
_To be defined after research_

**Implementation:**
_Pending_

**Files Changed:**
_Pending_

**Verification:**
- [ ] Screen stays awake while in Play Mode
- [ ] Screen returns to normal auto-lock behavior when exiting Play Mode
- [ ] Works on iPad 3 / iOS 9
- [ ] Modern frontend behavior (should also implement if possible)

**Note:** This may require the Screen Wake Lock API or a workaround (e.g., playing a silent video loop). iOS 9 Safari may have limited support for wake lock functionality. Need to research available options for older iOS versions.

---

### QA-O: View All Link for Favorites

**Issue:** QA-015 - No "View All" link for Favorites section
**Affects:** Legacy + Modern
**Status:** New

**Problem:**
On the home page, the "Recently Viewed" section has a "View All" link that navigates to a dedicated page showing all recipes. However, the "Favorites" section (displayed below Recently Viewed) does not have a similar "View All" link. This creates an inconsistent UX pattern and makes it unclear to users that they can view all their favorites.

**Screenshots:** _To be added during testing_

**Research Findings:**
_To be completed during research phase_

**Tasks:**
_To be defined after research_

**Implementation:**
_Pending_

**Files Changed:**
_Pending_

**Verification:**
- [ ] "View All" link appears in Favorites section header on home page
- [ ] Link shows favorite count (e.g., "View All (12)")
- [ ] Clicking link navigates to existing Favorites page
- [ ] Works on Legacy (iPad 3 / iOS 9)
- [ ] Works on Modern (desktop browser)

**Note:** This should be simpler than QA-005 since the Favorites page already exists. We just need to add the section header with the "View All" link to match the Recently Viewed pattern.

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
- [ ] Timer functionality (CRITICAL) - In progress
- [x] Multiple simultaneous timers (QA-010 logged - spacing issue)
- [ ] Favorites add/remove
- [ ] Collections CRUD
- [ ] Serving adjustment UI

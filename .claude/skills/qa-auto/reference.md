# QA Reference: Complete Feature Inventory & Test Cases

This is the exhaustive test matrix for the Cookie app. Every item here is tested during a full QA audit, walking through the app as a real user would from a fresh database.

## Page Inventory

### Modern Frontend (React SPA at http://localhost:3000)

| Route | Screen | Key Elements |
|-------|--------|-------------|
| `/` | ProfileSelector | Profile cards, create profile button, avatar colors |
| `/home` | Home | Favorites tab, Discover tab, Recently Viewed, search bar, nav header |
| `/search?q=chicken` | Search | Results grid, source filter pills, Load More, result count, import buttons |
| `/search?q=xyznonexistent` | Search (empty) | Empty state message, no broken layout |
| `/favorites` | Favorites | Favorite recipe cards, unfavorite toggle, empty state |
| `/all-recipes` | AllRecipes | All owned recipes grid, recipe cards |
| `/collections` | Collections | Collection list, create button, empty state |
| `/collection/:id` | CollectionDetail | Collection recipes, remove button, delete collection, edit name |
| `/recipe/:id` | RecipeDetail | Image, title, metadata, tabs, action buttons, serving adjuster |
| `/recipe/:id/play` | PlayMode | Step display, nav buttons, timer panel, step counter |
| `/settings` | Settings | 6 tabs: General, Prompts, Sources, Selectors, Users, Danger |

### Legacy Frontend (ES5 at http://localhost:3000/legacy/)

| Route | Template | Key Elements |
|-------|----------|-------------|
| `/legacy/` | profile_selector.html | Profile cards, create form, avatar colors |
| `/legacy/home/` | home.html | Favorites, Discover, Recently Viewed, search bar, nav |
| `/legacy/search/?q=chicken` | search.html | Results, source pills, Load More, import buttons |
| `/legacy/search/?q=xyznonexistent` | search.html | Empty state |
| `/legacy/favorites/` | favorites.html | Favorites list, unfavorite toggle |
| `/legacy/all-recipes/` | all_recipes.html | All recipes list |
| `/legacy/collections/` | collections.html | Collection list, create button |
| `/legacy/collection/:id/` | collection_detail.html | Collection recipes, management |
| `/legacy/recipe/:id/` | recipe_detail.html | Full recipe detail, all tabs, actions |
| `/legacy/recipe/:id/play/` | play_mode.html | Play mode, timers, step navigation |
| `/legacy/settings/` | settings.html | All settings tabs |

## Interactive Element Inventory

Every button, modal, popup, toggle, dropdown, and form that exists in the app. Each one is tested during Phase 3 user journey testing.

### Buttons & Actions

| Element | Location | What it does | What to verify |
|---------|----------|-------------|----------------|
| Create Profile button | ProfileSelector | Opens create form | Form appears, accepts input |
| Profile card | ProfileSelector | Selects profile | Redirects to home, session set |
| Search input + submit | Nav header | Searches recipes | Results page loads with results |
| Import button | Search results | Imports a recipe | Toast notification, redirect to detail |
| Load More button | Search results | Loads next page | More results append, no duplicates |
| Source filter pills | Search results | Toggle sources | Results filter/unfilter |
| Favorite toggle | Recipe detail, recipe cards | Add/remove favorite | Icon state changes, favorites list updates |
| Add to Collection button | Recipe detail | Opens collection picker | Modal/dropdown with collections |
| Play Mode button | Recipe detail | Enters cooking mode | Full-screen play mode activates |
| Next/Previous buttons | Play mode | Navigate steps | Step counter updates, content changes |
| Timer +5/+10/+15 buttons | Play mode | Creates countdown timer | Timer appears in panel, counts down |
| Exit/Close button | Play mode | Exits cooking mode | Returns to recipe detail |
| Theme toggle | Settings > General | Switch light/dark | Theme applies immediately |
| Unit preference | Settings > General | Switch metric/imperial | Preference saves |
| Source toggle switches | Settings > Sources | Enable/disable sources | Source state saves |
| Test Source button | Settings > Sources | Tests a source | Returns success/failure |
| Bulk toggle | Settings > Sources | All on/all off | All sources change |
| Reset preview button | Settings > Danger | Shows data counts | Count summary appears |
| Delete profile button | Settings > Danger | Deletes profile | Confirmation dialog |

### Modals & Popups

| Modal | Trigger | Contents | What to verify |
|-------|---------|----------|----------------|
| Create Profile form | Create Profile button | Name input, color picker | Form submits, profile created |
| Add to Collection picker | Add to Collection button | Collection list, create option | Can select existing or create new |
| Create Collection form | Create Collection button or from picker | Name input | Validates name, creates collection |
| Remix modal (AI only) | Remix button | Suggestion pills, text input | Pills populate, submission works |
| Edit Prompt modal (AI only) | Click prompt in Settings | Prompt text editor, model selector | Edits save |
| Edit Selector modal | Click selector in Settings | Selector text editor | Edits save |
| Delete confirmation | Delete buttons | Warning text, confirm action | Requires explicit confirmation |
| Toast notifications | Various actions (import, favorite, etc.) | Success/error message | Appears and auto-dismisses |

### AI-Dependent UI Elements

These elements are only rendered when the OpenRouter API key is configured. When AI is unavailable, all of these are hidden — not disabled, not grayed out, completely absent from the DOM.

| Element | Page | AI Required |
|---------|------|-------------|
| Serving adjuster (+/- buttons) | Recipe detail | Yes + recipe has servings |
| Tips tab | Recipe detail | Yes |
| Remix button | Recipe detail | Yes |
| Remix modal with suggestions | Recipe detail (modal) | Yes |
| Discover tab content | Home | Yes |
| AI prompt settings tab | Settings | Yes |
| Generate Tips button | Recipe detail > Tips | Yes |
| Timer AI label | Play mode timer panel | Yes (falls back to generic) |

## Feature Test Matrix

### 1. Profile Management

| Test Case | Steps | Expected Result |
|-----------|-------|-----------------|
| Create profile | Click create, enter name, submit | Profile appears in list with avatar color |
| Select profile | Click profile card | Redirected to home, session set |
| Switch profile | Go to `/`, click different profile | Data changes to new profile's data |
| Update theme | Settings > General > toggle dark/light | Theme applies immediately |
| Update units | Settings > General > toggle metric/imperial | Unit preference saved |
| Delete profile | Settings > Danger > delete profile | Confirmation shown, profile removed |
| Data isolation | Switch profiles, check favorites/collections | Each profile sees only its own data |

### 2. Recipe Search

| Test Case | Steps | Expected Result |
|-----------|-------|-----------------|
| Basic search | Search "chicken" | Results grid with images, titles, sources |
| Empty search | Search "xyznonexistent" | Empty state message, no errors |
| Source filter pills | Click source pills to toggle | Results filter by selected sources |
| Load More | Click Load More | Additional results append |
| Result count | Check displayed count | Matches actual number of results |
| URL import | Paste a recipe URL in search | Detects URL, offers direct import |
| Image display | Check result images | Images load, fallback for missing |
| Multiple queries | Search "pasta", "cake", "soup" | Each returns relevant results |

### 3. Recipe Import & Detail

| Test Case | Steps | Expected Result |
|-----------|-------|-----------------|
| Import from search | Click import button on result | Toast, redirect to detail page |
| Recipe image | View detail page | Image loads, placeholder if missing |
| Ingredients tab | Click Ingredients tab | Ingredient list displays |
| Instructions tab | Click Instructions tab | Numbered steps display |
| Nutrition tab | Click Nutrition tab | Data or "not available" |
| Tips tab (AI on) | Click Tips tab | Tips load or generate button |
| Tips tab (AI off) | Check Tips tab | Tab hidden entirely |
| Recipe metadata | Check title, author, time, servings | All present and formatted |
| Source link | Check source URL | Links to original recipe |

### 4. Serving Adjustment (AI Feature)

| Test Case | Steps | Expected Result |
|-----------|-------|-----------------|
| Adjuster visible (AI on + servings) | View recipe with servings field | +/- buttons shown |
| Adjuster hidden (AI off) | View recipe without AI | No serving controls rendered |
| Adjuster hidden (no servings) | View recipe without servings | No serving controls rendered |
| Scale up | Click + | Ingredients scale via AI |
| Scale down | Click - | Ingredients scale via AI |

### 5. Favorites

| Test Case | Steps | Expected Result |
|-----------|-------|-----------------|
| Add favorite | Click heart/star on recipe | Icon fills, appears in favorites |
| Remove favorite | Click filled heart/star | Icon unfills, removed from favorites |
| Favorites page | Navigate to favorites | Shows all favorited recipes |
| Empty favorites | Remove all favorites | Empty state message |

### 6. Collections

| Test Case | Steps | Expected Result |
|-----------|-------|-----------------|
| Create collection | Click create, enter name | Collection appears in list |
| Add recipe | Use "Add to Collection" on recipe | Recipe added, confirmation shown |
| View collection | Click collection | Shows recipes in collection |
| Remove recipe | Remove recipe from collection | Recipe gone from collection |
| Delete collection | Delete entire collection | Collection removed, recipes NOT deleted |
| Duplicate name | Create collection with existing name | Error shown |

### 7. Play Mode

| Test Case | Steps | Expected Result |
|-----------|-------|-----------------|
| Enter play mode | Click Play on recipe detail | Full-screen cooking mode |
| Step navigation | Click Next/Previous | Steps advance/retreat correctly |
| Step counter | Check counter display | Shows "Step X of Y" accurately |
| Add timer | Click timer button (+5/+10/+15 min) | Timer starts in timer panel |
| Multiple timers | Add several timers | All run simultaneously |
| Timer label (AI on) | Add timer with AI enabled | Descriptive label |
| Timer label (AI off) | Add timer without AI | Generic label ("Timer 1") |
| Exit play mode | Click close/exit | Return to recipe detail |

### 8. Settings Tabs

| Test Case | Steps | Expected Result |
|-----------|-------|-----------------|
| General tab | Click General | Theme toggle, unit preference visible |
| Prompts tab (AI on) | Click Prompts | All 10 AI prompts listed and editable |
| Prompts tab (AI off) | Click Prompts | Tab hidden or empty state |
| Sources tab | Click Sources | All sources with toggle switches |
| Source test | Test a single source | Returns success/failure status |
| Bulk toggle | Toggle all sources on/off | All sources change state |
| Selectors tab | Click Selectors | CSS selectors for each source |
| Users tab | Click Users | All profiles with stats |
| Danger tab | Click Danger Zone | Reset preview, deletion controls |

### 9. Dark Mode

| Test Case | Steps | Expected Result |
|-----------|-------|-----------------|
| Toggle on | Settings > General > Dark | Dark theme applies |
| All pages dark | Visit every page | Consistent dark styling |
| No unstyled elements | Inspect carefully | No white boxes, unreadable text |
| Toggle off | Settings > General > Light | Light theme restores |
| Persistence | Refresh page after toggle | Theme preference persists |

### 10. View History

| Test Case | Steps | Expected Result |
|-----------|-------|-----------------|
| Record view | Open a recipe detail | Appears in "Recently Viewed" on home |
| Recent order | View multiple recipes | Most recent first |
| Limit | View many recipes | Shows max 6 (or configured limit) |

### 11. Cross-Frontend Consistency

| Check | What to Compare |
|-------|-----------------|
| Data parity | Same profile shows same data on both frontends |
| Feature parity | All core features work on both |
| Visual consistency | Similar layout, colors, spacing |
| Navigation | Same pages accessible on both |
| Error states | Empty states, loading states consistent |

### 12. Remix Features (AI)

| Test Case | Steps | Expected Result |
|-----------|-------|-----------------|
| Remix button visible (AI on) | View recipe detail | Remix button shown |
| Remix button hidden (AI off) | View recipe detail | No remix button |
| Open remix modal | Click remix | Modal with suggestions and text input |
| Remix suggestions | Check modal | 6 contextual suggestions displayed |
| Create remix | Enter modification, submit | New recipe with "(Remix)" suffix |

### 13. Discovery (AI)

| Test Case | Steps | Expected Result |
|-----------|-------|-----------------|
| Discover tab (AI on) | Home > Discover tab | Suggestions displayed |
| New user | No favorites/history | Only seasonal shown |
| Refresh | Click refresh | New suggestions generated |
| Search from suggestion | Click a suggestion | Executes search |

## UI/UX Improvement Tracking

During testing, note any UI/UX improvements that would enhance the user experience — even if they are not bugs. These go into the issue table with category "UI-UX" and are included in the speckit write-up. Examples:

- Empty states that lack helpful messaging or illustrations
- Buttons that are hard to find or poorly labeled
- Confusing navigation flows
- Missing loading indicators
- Inconsistent spacing, alignment, or typography between pages
- Touch targets smaller than 44x44px on the legacy frontend
- Missing keyboard navigation or focus indicators
- Pages that feel cluttered or lack visual hierarchy

These are not bugs — they are improvement opportunities. Track them separately from functional bugs but include them in the speckit spec so they can be prioritized and implemented.

## API Endpoints to Verify

Monitor network requests during testing. All should return appropriate status codes.

### Health & Status
- `GET /api/system/health/` — 200
- `GET /api/ai/status` — 200 (with AI availability info)
- `GET /api/recipes/cache/health/` — 200

### Core CRUD
- `GET /api/recipes/` — 200 with recipe list
- `GET /api/recipes/{id}/` — 200 with recipe detail
- `GET /api/favorites/` — 200 with favorites list
- `GET /api/collections/` — 200 with collections list
- `GET /api/profiles/` — 200 with profiles list
- `GET /api/history/` — 200 with history

### Search
- `GET /api/recipes/search/?q=chicken` — 200 with results
- `GET /api/sources/` — 200 with source list
- `GET /api/sources/enabled-count/` — 200

### AI (when available)
- `POST /api/ai/tips` — 200
- `POST /api/ai/scale` — 200
- `POST /api/ai/remix` — 200
- `POST /api/ai/remix-suggestions` — 200
- `POST /api/ai/timer-name` — 200
- `GET /api/ai/discover/{profile_id}/` — 200
- `GET /api/ai/prompts` — 200

## Per-Interaction Checklist

After every significant interaction (button click, form submit, modal open/close, navigation), run this quick check:

1. **Console**: `browser_console_messages` — any new errors?
2. **Network**: `browser_network_requests` — any failed requests?
3. **Visual**: Does the result look correct? Any layout shifts, missing elements, broken styles?
4. **Screenshot**: Take one if something looks wrong or if it's a key state

This catches issues at the moment they occur rather than discovering them later in log review.

## Legacy-Specific Checks

These are iOS 9.3 Safari specific concerns:

1. **No ES6 syntax errors** in Safari console — the #1 cause of legacy breakage
2. **Polyfills loaded first** — `polyfills.js` before all other scripts in base.html
3. **Touch events** — all interactive elements respond to touch (no hover-only interactions)
4. **Viewport** — proper mobile viewport meta tag
5. **CSS compatibility** — no CSS Grid, no CSS variables, no `calc()` with complex expressions
6. **Image formats** — WebP not supported on iOS 9; JPEG/PNG fallback required
7. **AJAX** — XMLHttpRequest (not fetch API) used for network requests
8. **Animations** — CSS transitions preferred over JS animations
9. **Memory** — iPad 2 has 512MB RAM; avoid large DOM trees, excessive event listeners
10. **Audio** — Must unlock audio context on first user interaction (iOS requirement)

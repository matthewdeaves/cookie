# QA Reference: Complete Feature Inventory & Test Cases

This is the exhaustive test matrix for the Cookie app. Every item here MUST be tested during a full QA audit.

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

## Feature Test Matrix

### 1. Profile Management

| Test Case | Steps | Expected Result | Frontend |
|-----------|-------|-----------------|----------|
| Create profile | Click create, enter name | Profile appears in list with auto-assigned avatar color | Both |
| Select profile | Click profile card | Redirected to home, session set | Both |
| Switch profile | Go to `/` or `/legacy/`, click different profile | Data changes to new profile's data | Both |
| Update theme | Settings > General > toggle dark/light | Theme applies immediately across all pages | Both |
| Update units | Settings > General > toggle metric/imperial | Unit preference saved | Both |
| Delete profile | Settings > Danger > delete profile | Confirmation shown with data preview, profile removed | Both |
| Data isolation | Switch profiles, check favorites/collections | Each profile sees only its own data | Both |

### 2. Recipe Search

| Test Case | Steps | Expected Result | Frontend |
|-----------|-------|-----------------|----------|
| Basic search | Search "chicken" | Results grid with images, titles, sources | Both |
| Empty search | Search "xyznonexistent" | Empty state message, no errors | Both |
| Source filter pills | Click source pills to toggle | Results filter by selected sources | Both |
| Load More | Scroll/click Load More | Additional results append | Both |
| Result count | Check displayed count | Matches actual number of results | Both |
| URL import | Paste a recipe URL in search | Detects URL, offers direct import | Both |
| Image display | Check result images | Images load (cached locally), WebP fallback works | Both |
| Multiple queries | Search "pasta", "cake", "soup" | Each returns relevant results | Both |

### 3. Recipe Import & Detail

| Test Case | Steps | Expected Result | Frontend |
|-----------|-------|-----------------|----------|
| Import from search | Click import button on result | Toast notification, redirect to detail page | Both |
| Recipe image | View detail page | Image loads, placeholder if missing | Both |
| Ingredients tab | Click Ingredients tab | Ingredient list displays correctly | Both |
| Instructions tab | Click Instructions tab | Numbered steps display | Both |
| Nutrition tab | Click Nutrition tab | Nutrition data or "not available" | Both |
| Tips tab (AI on) | Click Tips tab | Tips load or generate button shown | Both |
| Tips tab (AI off) | Click Tips tab | Tab hidden entirely | Both |
| Recipe metadata | Check title, author, time, servings | All present and formatted | Both |
| Source link | Check source URL | Links to original recipe | Both |

### 4. Serving Adjustment (AI Feature)

| Test Case | Steps | Expected Result | Frontend |
|-----------|-------|-----------------|----------|
| Adjuster visible (AI on + servings) | View recipe with servings field | +/- buttons shown | Both |
| Adjuster hidden (AI off) | Disable AI / remove key | No serving controls rendered | Both |
| Adjuster hidden (no servings) | View recipe without servings | No serving controls rendered | Both |
| Scale up | Click + to increase servings | Ingredients scale intelligently via AI | Both |
| Scale down | Click - to decrease servings | Ingredients scale intelligently via AI | Both |
| Unit preference | Toggle metric/imperial | Scaling uses correct units | Both |
| Cached result | Scale same recipe again | Returns cached (faster) | Both |

### 5. Favorites

| Test Case | Steps | Expected Result | Frontend |
|-----------|-------|-----------------|----------|
| Add favorite | Click heart/star on recipe | Icon fills, recipe appears in favorites | Both |
| Remove favorite | Click filled heart/star | Icon unfills, recipe removed from favorites | Both |
| Favorites page | Navigate to favorites | Shows all favorited recipes | Both |
| Empty favorites | Remove all favorites | Empty state message | Both |
| Duplicate prevention | Favorite same recipe twice | No duplicate, no error | Both |

### 6. Collections

| Test Case | Steps | Expected Result | Frontend |
|-----------|-------|-----------------|----------|
| Create collection | Click create, enter name | Collection appears in list | Both |
| Add recipe | Use "Add to Collection" on recipe | Recipe added, confirmation shown | Both |
| View collection | Click collection | Shows recipes in collection | Both |
| Remove recipe | Remove recipe from collection | Recipe gone from collection | Both |
| Delete collection | Delete entire collection | Collection removed, recipes NOT deleted | Both |
| Duplicate name | Create collection with existing name | Error shown | Both |
| Edit collection | Update name/description | Changes saved | Both |

### 7. Play Mode

| Test Case | Steps | Expected Result | Frontend |
|-----------|-------|-----------------|----------|
| Enter play mode | Click Play on recipe detail | Full-screen cooking mode | Both |
| Step navigation | Click Next/Previous | Steps advance/retreat correctly | Both |
| Step counter | Check counter display | Shows "Step X of Y" accurately | Both |
| Add timer | Click timer button (+5/+10/+15 min) | Timer starts in timer panel | Both |
| Multiple timers | Add several timers | All run simultaneously | Both |
| Timer completion | Wait for timer to finish | Audio alert + notification | Both |
| Timer label (AI on) | Add timer with AI enabled | Descriptive label (e.g. "Saut onions") | Both |
| Timer label (AI off) | Add timer without AI | Generic label (e.g. "Timer 1") | Both |
| Wake lock | Enter play mode, wait | Screen does not dim | Both |
| Exit play mode | Click close/exit | Return to recipe detail | Both |

### 8. Settings Tabs

| Test Case | Steps | Expected Result | Frontend |
|-----------|-------|-----------------|----------|
| General tab | Click General | Theme toggle, unit preference visible | Both |
| Prompts tab (AI on) | Click Prompts | All 10 AI prompts listed and editable | Both |
| Prompts tab (AI off) | Click Prompts | Tab hidden or appropriate empty state | Both |
| Sources tab | Click Sources | All search sources with toggle switches | Both |
| Source test | Test a single source | Returns success/failure status | Both |
| Bulk toggle | Toggle all sources on/off | All sources change state | Both |
| Selectors tab | Click Selectors | CSS selectors for each source | Both |
| Users tab | Click Users | All profiles with stats (favorites, collections, etc.) | Both |
| Danger tab | Click Danger Zone | Reset preview, deletion controls | Both |
| Reset preview | Click reset preview | Shows data counts, requires "RESET" confirmation | Both |

### 9. AI Feature Visibility

| State | Expected UI |
|-------|-------------|
| API key configured + valid | All 10 AI features visible and functional |
| API key missing | ALL AI UI hidden: no serving adjuster, no tips tab, no remix button, no discover tab, no remix suggestions |
| API key invalid | Same as missing — all hidden |
| API call fails (runtime) | Feature-specific graceful failure, no crash |

### 10. Dark Mode

| Test Case | Steps | Expected Result | Frontend |
|-----------|-------|-----------------|----------|
| Toggle on | Settings > General > Dark | Dark theme applies | Both |
| All pages dark | Visit every page | Consistent dark styling | Both |
| No unstyled elements | Inspect carefully | No white boxes, unreadable text, missing borders | Both |
| Toggle off | Settings > General > Light | Light theme restores | Both |
| Persistence | Refresh page after toggle | Theme preference persists | Both |

### 11. View History

| Test Case | Steps | Expected Result | Frontend |
|-----------|-------|-----------------|----------|
| Record view | Open a recipe detail | Appears in "Recently Viewed" on home | Both |
| Recent order | View multiple recipes | Most recent first | Both |
| Clear history | Clear history action | Recently Viewed section empty | Both |
| Limit | View many recipes | Shows max 6 (or configured limit) | Both |

### 12. Cross-Frontend Consistency

| Check | What to Compare |
|-------|-----------------|
| Data parity | Same profile shows same recipes, favorites, collections on both frontends |
| Feature parity | All core features work on both (AI features, search, play mode, settings) |
| Visual consistency | Similar layout, colors, spacing (not pixel-perfect but coherent) |
| Navigation | Same pages accessible on both |
| Error states | Empty states, loading states, error messages consistent |

### 13. Remix Features (AI)

| Test Case | Steps | Expected Result | Frontend |
|-----------|-------|-----------------|----------|
| Remix button visible (AI on) | View recipe detail | Remix button shown | Both |
| Remix button hidden (AI off) | View recipe detail without AI | No remix button | Both |
| Open remix modal | Click remix | Modal with suggestions and text input | Both |
| Remix suggestions | Check modal | 6 contextual suggestions displayed | Both |
| Create remix | Enter modification, submit | New recipe created with "(Remix)" suffix | Both |
| View original | On remix detail page | Link to original recipe | Both |
| View siblings | On remix detail page | Links to other remixes of same original | Both |

### 14. Discovery (AI)

| Test Case | Steps | Expected Result | Frontend |
|-----------|-------|-----------------|----------|
| Discover tab (AI on) | Home > Discover tab | Suggestions displayed | Both |
| Discover favorites | With favorites saved | Suggestions based on preferences | Both |
| Discover seasonal | Any time | Date-appropriate suggestions | Both |
| Discover new | With history | "Outside comfort zone" suggestions | Both |
| New user | No favorites/history | Only seasonal shown | Both |
| Refresh | Click refresh/re-discover | New suggestions generated | Both |
| Search from suggestion | Click a suggestion | Executes search with suggested query | Both |

## API Endpoints to Verify

During testing, monitor network requests for these endpoints. All should return appropriate status codes.

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

## Legacy-Specific Checks

These are iOS 9.3 Safari specific concerns to verify:

1. **No ES6 syntax errors** in Safari console — the #1 cause of legacy breakage
2. **Polyfills loaded first** — `polyfills.js` before all other scripts in base.html
3. **Touch events** — all interactive elements respond to touch (no hover-only interactions)
4. **Viewport** — proper mobile viewport meta tag
5. **CSS compatibility** — no CSS Grid (use flexbox or floats), no CSS variables, no `calc()` with complex expressions
6. **Image formats** — WebP not supported on iOS 9; JPEG/PNG fallback required
7. **AJAX** — XMLHttpRequest (not fetch API) used for network requests
8. **Animations** — CSS transitions preferred over JS animations; no `requestAnimationFrame` chaining
9. **Memory** — iPad 2 has 512MB RAM; avoid large DOM trees, excessive event listeners
10. **Audio** — Must unlock audio context on first user interaction (iOS requirement)

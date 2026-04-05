# QA Reference: Complete Feature Inventory & Test Cases

This is the exhaustive test matrix for the Cookie app. Every item here is tested during a full QA audit.

## Known Environment Issues

These are documented behaviors, not bugs. The QA skill must work around them.

### Session Cookie on HTTP (Production Container)

The `cookie-prod-app` container on port 80 runs with `DEBUG=False`, setting `SESSION_COOKIE_SECURE=True`. Over HTTP, browsers silently reject `Secure` cookies. **All authenticated API calls will 403 unless you manually inject session cookies.** See the SKILL.md environment section for the injection procedure.

Symptoms of a missing/expired session:
- `403 Forbidden` on `/api/recipes/scrape/`, `/api/favorites/`, `/api/collections/`, etc.
- Browser console: `Failed to load resource: the server responded with a status of 403`
- `selected_profile_id` cookie visible but `sessionid` cookie absent

### Port Allocation

| Port | Service | Notes |
|------|---------|-------|
| 80 | `cookie-prod-app` | Production container, `DEBUG=False`, `SESSION_COOKIE_SECURE=True` |
| 3000 | May be occupied by next-server or other process | Check with `ss -tlnp \| grep :3000` |
| 8000 | `cookie-web-1` (dev) | Not exposed to host by default |
| 5173 | `cookie-frontend-1` (dev) | Not exposed to host by default |

### Quotas API in Home Mode

`GET /api/ai/quotas` returns 404 intentionally in home mode (AUTH_MODE=home). This is expected. The legacy settings JS guards against this by only calling `loadQuotas()` when quota HTML sections exist (passkey mode only). If you see this 404 in the network tab, it's a false positive — verify no console error is generated.

## Page Inventory

### Modern Frontend (React SPA)

| Route | Screen | Key Elements |
|-------|--------|-------------|
| `/` | ProfileSelector | Profile cards, create profile button, avatar colors |
| `/home` | Home | Recently Viewed, My Favorites, Discover (AI), search bar, nav header |
| `/search?q=chicken` | Search | Results grid, source filter pills, Load More, result count, import buttons |
| `/favorites` | Favorites | Favorite recipe cards, unfavorite toggle, empty state |
| `/all-recipes` | AllRecipes | All owned recipes grid, filter input |
| `/collections` | Collections | Collection list, create button, empty state |
| `/collections/:id` | CollectionDetail | Collection recipes, remove button, delete collection |
| `/recipe/:id` | RecipeDetail | Image, title, metadata, tabs, action buttons, serving adjuster (AI) |
| `/recipe/:id/play` | PlayMode | Step display, nav buttons, timer panel, step counter |
| `/settings` | Settings | 6 tabs: General, AI Prompts, Sources, Selectors, Users, Danger Zone |

### Legacy Frontend (ES5 at `/legacy/`)

| Route | Template | Key Elements |
|-------|----------|-------------|
| `/legacy/` | profile_selector.html | Profile cards, create form, avatar colors |
| `/legacy/home/` | home.html | Recently Viewed, My Favorites, Discover (AI), search bar, nav |
| `/legacy/search/?q=chicken` | search.html | Results, source pills, Load More, import buttons |
| `/legacy/favorites/` | favorites.html | Favorites list, unfavorite toggle |
| `/legacy/all-recipes/` | all_recipes.html | All recipes list, filter input |
| `/legacy/collections/` | collections.html | Collection list, create button |
| `/legacy/collections/:id/` | collection_detail.html | Collection recipes, management |
| `/legacy/recipe/:id/` | recipe_detail.html | Full recipe detail, all tabs, actions |
| `/legacy/recipe/:id/play/` | play_mode.html | Play mode, timers, step navigation |
| `/legacy/settings/` | settings.html | All settings tabs |

## Interactive Element Inventory

### Buttons & Actions

| Element | Location | What to verify |
|---------|----------|----------------|
| Create Profile button | ProfileSelector | Form appears with name input, color picker, Cancel/Create |
| Profile card | ProfileSelector | Redirects to home, session established |
| Search input + Enter | Nav header / Home | Results page loads with results |
| Import button | Search results | Loading state, toast, redirect to detail. Re-inject session if 403 |
| Load More button | Search results | More results append, no duplicates |
| Source filter pills | Search results | Results filter, count text updates, "All Sources" resets |
| Favorite toggle | Recipe detail, recipe cards | Icon changes (outline/filled), favorites list updates |
| Add to Collection | Recipe detail | Modal with collection list or create new |
| Cook! button | Recipe detail | Full-screen play mode activates |
| Next/Previous | Play mode | Step counter updates, content changes, boundary states (disabled) |
| Timer +5/+10/+15 | Play mode | Timer appears, counts down, badge updates |
| Timer pause/reset/delete | Play mode timer card | Each button works independently |
| Exit play mode | Play mode X button | Returns to recipe detail |
| Recipe Details toggle | Recipe detail | Collapse/expand with arrow indicator |
| Theme toggle | Settings > General | Theme applies immediately |
| Unit preference | Settings > General | Saves metric/imperial |
| API key input | Settings > General | Test Key and Save Key buttons enable when text entered |
| Source toggles | Settings > Sources | Individual toggle, Enable All, Disable All |
| Test Source button | Settings > Selectors | Returns success/failure per source |
| Test All Sources | Settings > Selectors | Tests all sources |
| Edit selector | Settings > Selectors | Edit button opens inline editor |
| Edit prompt | Settings > AI Prompts | Edit button expands prompt card |
| Profile rename | Settings > Users | Pencil icon opens rename |
| Profile delete | Settings > Users | Trash icon with confirmation |
| Reset Database | Settings > Danger Zone | Red button with confirmation (do NOT confirm during testing) |
| Profile avatar (nav) | Nav header | Dropdown with "Log out" |
| Log out | Profile dropdown | Redirects to profile selector |

### Modals & Popups

| Modal | Trigger | What to verify |
|-------|---------|----------------|
| Create Profile form | Add Profile button | Name input, color picker, Cancel + Create (disabled until name entered) |
| Add to Collection picker | + button on recipe | Collection list, "Create New Collection" option |
| Create Collection form | From collection picker | Name input, "Create & Add Recipe" button |
| Remix modal (AI only) | Remix button | Suggestion pills, text input, submit |
| Toast notifications | Import, favorite, errors | Appears and auto-dismisses |
| Delete confirmation | Delete buttons | Warning text, requires explicit confirmation |

### AI-Dependent UI Elements

When AI is unavailable (no API key), ALL of these must be **completely hidden** — not disabled, not grayed out, not showing "AI unavailable", completely absent from the DOM.

| Element | Page | Conditions |
|---------|------|------------|
| Serving adjuster (+/- buttons) | Recipe detail | API key configured AND recipe has `servings` value |
| Tips tab / Generate Tips | Recipe detail | API key configured |
| Remix button | Recipe detail | API key configured |
| Remix suggestions | Remix modal | API key configured |
| Discover section | Home | API key configured |
| AI Prompts tab content | Settings | API key configured (tab may still show with warning) |
| Timer AI labels | Play mode | API key configured (falls back to generic "5 min") |
| Selector AI repair | Settings > Selectors | API key configured AND selector test fails |

## The 10 AI Features (for `--with-ai` testing)

Each feature uses a specific AI prompt stored in `AIPromptSettings`. All prompts are customizable via Settings > AI Prompts.

| # | Feature Key | API Endpoint | Where in UI | What it does |
|---|------------|-------------|-------------|-------------|
| 1 | `recipe_remix` | `POST /api/ai/remix` | Recipe detail > Remix button | Creates a modified version of a recipe |
| 2 | `remix_suggestions` | `POST /api/ai/remix-suggestions` | Remix modal > suggestion pills | Generates 6 contextual remix ideas |
| 3 | `serving_adjustment` | `POST /api/ai/scale` | Recipe detail > +/- buttons | AI-scales ingredient quantities |
| 4 | `tips_generation` | `POST /api/ai/tips` | Recipe detail > Tips tab | Generates cooking tips for a recipe |
| 5 | `discover_favorites` | `GET /api/ai/discover/{id}/` | Home > Discover | Suggests recipes based on favorites |
| 6 | `discover_seasonal` | `GET /api/ai/discover/{id}/` | Home > Discover | Suggests seasonal/holiday recipes |
| 7 | `discover_new` | `GET /api/ai/discover/{id}/` | Home > Discover | Suggests adventurous recipes |
| 8 | `search_ranking` | (transparent, used during search) | Search results | AI ranks search results by relevance |
| 9 | `timer_naming` | `POST /api/ai/timer-name` | Play mode timers | Generates descriptive timer names from step context |
| 10 | `selector_repair` | (used in selector testing) | Settings > Selectors | Suggests CSS selector fixes |

## Feature Test Matrix

### 1. Profile Management

| Test Case | Expected Result |
|-----------|-----------------|
| Create profile | Profile appears with avatar color, Create button disabled until name entered |
| Select profile | Redirected to home, session set, nav shows name |
| Switch profile | Data changes to new profile's data |
| Data isolation | Each profile sees only its own favorites, collections, history |
| Delete profile | Confirmation required, profile removed |

### 2. Recipe Search

| Test Case | Expected Result |
|-----------|-----------------|
| Search "chicken pasta" | Results grid with images, titles, sources, count (e.g. "114 results found") |
| Source filter click | Results filter to selected source, count updates (e.g. "20 results found") |
| "All Sources" click | Filter resets, full results return, count shows total |
| Load More | Additional results append without duplicates |
| Empty search "xyznonexistent" | Empty state message, no errors |
| URL paste | Detects URL, offers direct import |

### 3. Recipe Import & Detail

| Test Case | Expected Result |
|-----------|-----------------|
| Import from search | Button shows "Importing...", toast, redirect to detail |
| Import 403 | Re-inject session cookies, retry |
| Ingredients tab | Numbered ingredient list |
| Instructions tab | Numbered step list |
| Nutrition tab | Data grid or "not available" |
| Recipe Details toggle | Collapse/expand with arrow change |
| Source link | Links to original recipe URL |

### 4. Favorites

| Test Case | Expected Result |
|-----------|-----------------|
| Add favorite | Heart/icon fills, recipe appears in Favorites page |
| Remove favorite | Heart unfills, recipe removed from Favorites |
| Favorite from card | Heart on recipe card toggles |
| Empty favorites | Empty state with helpful message |

### 5. Collections

| Test Case | Expected Result |
|-----------|-----------------|
| Create collection | Appears in list with cover image from first recipe |
| Add recipe to collection | Recipe appears in collection detail |
| Remove recipe from collection | Removed from collection but NOT from All Recipes |
| Delete collection | Confirmation required, collection removed, recipes preserved |
| Create from recipe detail | "Create & Add Recipe" flow works |

### 6. Play Mode

| Test Case | Expected Result |
|-----------|-----------------|
| Enter play mode | Full-screen with step 1, green header bar |
| Step navigation | Next/Previous work, counter updates |
| Boundary states | Previous disabled on step 1, Next disabled on last step |
| Timer creation | Timer appears with countdown, pause/reset/delete buttons |
| Multiple timers | All run independently, badge shows count |
| Timer persistence | Timers survive step navigation |
| Exit | Returns to recipe detail |
| Wake lock | No CSP error for data:video/mp4 (media-src allows data:) |

### 7. Settings

| Test Case | Expected Result |
|-----------|-----------------|
| General tab | API key section, About with version |
| AI Prompts tab | 10 prompts listed (if AI), warning banner (if no AI) |
| Sources tab | 15 sources with toggles, bulk toggle |
| Selectors tab | CSS selectors, Test buttons, Edit |
| Users tab | Profile list with stats, edit/delete |
| Danger Zone | Reset Database (do not confirm) |
| No spurious errors | Settings page loads with 0 console errors in home mode |

### 8. Dark Mode

| Test Case | Expected Result |
|-----------|-----------------|
| Toggle on | Dark theme applies to all pages |
| Consistency | No white backgrounds, unreadable text, broken contrast |
| Toggle off | Light theme restores |
| Persistence | Theme persists across navigation |

### 9. AI Features (--with-ai only)

| Test Case | Expected Result |
|-----------|-----------------|
| Tips generation | Tips appear, contextually relevant |
| Serving +/- | Ingredients update via AI, not simple math |
| Remix modal | 6 suggestions populate, can submit |
| Remix result | New recipe created with remix indicator |
| Discover | Suggestions appear on home, clickable |
| Timer naming | Timers get descriptive AI names |
| Prompt editing | Edit/save/reset prompts in settings |
| Selector repair | AI fix suggested for broken selectors |

### 10. AI Hidden (--without-ai only)

| Element | Must be completely absent |
|---------|--------------------------|
| Serving +/- buttons | Not in DOM on recipe detail |
| Tips tab | Not in DOM on recipe detail |
| Remix button | Not in DOM on recipe detail |
| Discover section | Not in DOM on home page |
| Timer AI labels | Fallback to generic names |

## Per-Interaction Checklist

After every significant interaction:

1. **Console**: `browser_console_messages` level `error` — any new errors?
2. **Network**: Check for 4xx/5xx on API calls (ignore expected 404s)
3. **Visual**: Does the result look correct? Any layout shifts, missing elements?
4. **Session**: If 403, re-inject session cookies

## Legacy-Specific Checks (iOS 9.3 Safari)

Full ES5 and CSS rules are in `.claude/rules/es5-compliance.md` and enforced by PreToolUse hooks. During QA, watch for these runtime issues that hooks can't catch:

1. **Touch targets** — minimum 44x44px for all interactive elements
2. **Memory** — iPad 2 has 512MB RAM; avoid huge DOM trees or excessive event listeners
3. **Audio unlock** — iOS requires user interaction before playing audio (timer sounds)
4. **XMLHttpRequest** — verify no `fetch()` calls in legacy JS (hooks check syntax but not API usage)
5. **Image formats** — verify no WebP images served to legacy pages

## API Endpoints to Monitor

### Always available
- `GET /api/system/health/` — 200
- `GET /api/ai/status` — 200 (AI availability info)
- `GET /api/profiles/` — 200 (no auth required in home mode)
- `POST /api/profiles/` — 201 (create profile)
- `POST /api/profiles/{id}/select/` — 200 (set session)
- `GET /api/recipes/search/?q=...` — 200 (no auth required)

### Require session (will 403 without session cookie)
- `POST /api/recipes/scrape/` — 200/201
- `GET /api/recipes/` — 200
- `GET /api/recipes/{id}/` — 200
- `GET /api/favorites/` — 200
- `POST /api/favorites/{id}/` — 200
- `GET /api/collections/` — 200
- `POST /api/collections/` — 201
- `GET /api/history/` — 200

### AI endpoints (require session + API key)
- `POST /api/ai/tips` — 200
- `POST /api/ai/scale` — 200
- `POST /api/ai/remix` — 200
- `POST /api/ai/remix-suggestions` — 200
- `POST /api/ai/timer-name` — 200
- `GET /api/ai/discover/{profile_id}/` — 200
- `GET /api/ai/prompts` — 200
- `PUT /api/ai/prompts/{id}` — 200

### Expected "errors" (not bugs)
- `GET /api/ai/quotas` → 404 in home mode (intentional, JS handles gracefully)

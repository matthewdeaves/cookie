---
name: qa-auto
description: Full automated QA audit using Playwright MCP. Walks through every user journey — creating profiles, searching, importing, cooking, organizing — testing every button, modal, and popup. Supports testing with or without AI features. Documents bugs, then fixes them.
user_invocable: true
argument-hint: "[modern|legacy|both] [--with-ai|--without-ai] [--audit-only] [--skip-rebuild]"
---

# Automated QA Audit & Fix

You are a QA engineer running a full end-to-end audit of Cookie. You walk through every user journey as a real user would — creating a profile, searching for recipes, importing them, organizing into collections, cooking in play mode, adjusting settings — testing every button, modal, popup, and edge case.

Read [reference.md](reference.md) before starting — it has the complete feature inventory, page list, test matrix, and critical environment setup procedures.

<arguments>
- `$ARGUMENTS` defaults to `both` if empty
- `modern` / `legacy` / `both` — which frontend(s) to test
- `--with-ai` — test WITH OpenRouter API key configured (tests all 10 AI features)
- `--without-ai` — test WITHOUT API key (verify all AI UI is hidden, not disabled)
- If neither `--with-ai` nor `--without-ai` specified, auto-detect by checking `GET /api/ai/status`
- `--audit-only` — document findings but do not fix anything
- `--skip-rebuild` — skip the fresh build and test against the existing environment
</arguments>

<environment>
## Critical: Session Cookie Workaround

The production container (`cookie-prod-app`) serves on **port 80** with `DEBUG=False`, which sets `SESSION_COOKIE_SECURE=True` and `CSRF_COOKIE_SECURE=True`. Over HTTP, browsers silently reject `Secure` cookies — this means **all authenticated API calls will 403** unless you manually inject session cookies.

**You MUST do this before any authenticated testing:**

1. Create a session in the prod database:
   ```bash
   docker exec cookie-prod-app python manage.py shell -c "
   from django.contrib.sessions.backends.db import SessionStore
   s = SessionStore()
   s['profile_id'] = PROFILE_ID_HERE
   s.create()
   print(s.session_key)
   "
   ```

2. Inject cookies into the browser via `browser_evaluate`:
   ```javascript
   () => {
     document.cookie = "sessionid=SESSION_KEY_HERE; path=/";
     document.cookie = "csrftoken=abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890; path=/";
     return document.cookie;
   }
   ```

3. Verify the session works — make a test API call:
   ```javascript
   () => {
     return new Promise((resolve) => {
       var xhr = new XMLHttpRequest();
       xhr.open('GET', '/api/favorites/', true);
       xhr.onreadystatechange = function() {
         if (xhr.readyState === 4) resolve(xhr.status + ': ' + xhr.responseText.substring(0, 100));
       };
       xhr.send();
     });
   }
   ```
   If you get 403, the session injection failed — recreate and re-inject.

**Re-inject after every page navigation that creates a new browsing context.** The `sessionid` cookie set via JS is not `HttpOnly` and may not persist across all navigations. If an authenticated request suddenly 403s, re-inject.

| Service | URL | Notes |
|---------|-----|-------|
| Production app | http://localhost (port 80) | `cookie-prod-app` container, `DEBUG=False` |
| Dev backend | `docker compose exec web ...` | For running tests/lint only |
| Dev frontend | `docker compose exec frontend ...` | For running tests/lint only |
| Backend logs | `docker exec cookie-prod-app python manage.py shell -c "..."` | Production DB queries |
| Server logs | `docker logs cookie-prod-app --tail=200` | Gunicorn/Django logs |

**Important:** The dev containers (`cookie-web-1`, `cookie-frontend-1`) share code via volume mounts but have separate databases from the prod container. Code fixes apply to source files on disk. The prod container serves its own built static files — to verify legacy JS fixes on port 80, the prod container must be rebuilt: `docker compose -f docker-compose.prod.yml build && docker compose -f docker-compose.prod.yml up -d` (or equivalent).

Run all test/lint commands via dev containers: `docker compose exec web python -m pytest`, `docker compose exec frontend npm test`.
</environment>

<context_management>
This is a long task that will use significant context. Work through all phases — your context window will be automatically compacted if needed, so do not stop early due to token budget concerns.

To manage context efficiently:
- Save screenshots to `qa-screenshots/` directory (create it first)
- Use `browser_snapshot` (accessibility tree) for DOM inspection — it's cheaper than screenshots
- Only take screenshots at key states, not every click
- Check console errors in batches, not after every single action
</context_management>

---

## Phase Overview

```
Phase 1: Environment Setup       — health checks, session setup, AI detection
Phase 2: Empty State Audit       — visit every page with no data (if not --skip-rebuild)
Phase 3: User Journey Testing    — walk through every feature, every button
Phase 4: AI Feature Testing      — test all 10 AI features (--with-ai) or verify hidden (--without-ai)
Phase 5: Log & Error Audit       — review all logs after testing
Phase 6: Bug Report & Fix        — compile bugs, fix them, verify fixes
```

Create a task (TaskCreate) for each phase when you start it. Mark it done when complete. Between phases, output a short completion summary.

---

## Phase 1: Environment Setup

### If not `--skip-rebuild`: Fresh build

1. Stop containers and wipe the database volume:
   ```bash
   docker compose down -v
   ```

2. Rebuild and start containers:
   ```bash
   docker compose build --no-cache web
   docker compose up -d
   ```

3. Wait for services to be healthy: `docker compose ps`

### Health checks (always)

4. Check prod container is running: `docker ps --format "{{.Names}}\t{{.Status}}" | grep prod`
5. Check server logs: `docker logs cookie-prod-app --tail=30`
6. Test API: `curl -s http://localhost/api/system/health/`
7. Detect AI status: `curl -s http://localhost/api/ai/status` — note if API key is configured
8. Navigate to the frontend being tested and verify it loads
9. Create screenshot directory: `mkdir -p qa-screenshots`

### Session setup

10. Create a profile (or find existing ones):
    ```bash
    docker exec cookie-prod-app python manage.py shell -c "
    from apps.profiles.models import Profile
    for p in Profile.objects.all(): print(f'ID={p.id} Name={p.name}')
    "
    ```

11. Create a session and inject cookies (see environment section above)
12. Verify authenticated API calls work

**Exit criteria:** Environment healthy, session working, AI availability noted, screenshot directory ready.

---

## Phase 2: Empty State Audit

If `--skip-rebuild` was passed AND data exists, skip this phase.

Visit every page with no data to verify empty states render correctly.

<page_visit_order frontend="legacy">
1. `/legacy/` — profile selector (may have profiles or be empty)
2. `/legacy/home/` — empty favorites, no recently viewed
3. `/legacy/favorites/` — empty state message
4. `/legacy/all-recipes/` — empty state
5. `/legacy/collections/` — empty state
6. `/legacy/settings/` — all 6 tabs render
7. `/legacy/search/?q=chicken` — search works without data
</page_visit_order>

<page_visit_order frontend="modern">
Same pages without `/legacy/` prefix.
</page_visit_order>

For each page:
1. Navigate, wait for load
2. Take screenshot → `qa-screenshots/{frontend}-empty-{page}.png`
3. Check `browser_console_messages` for errors
4. Check `browser_network_requests` for 4xx/5xx (filter out expected 404s like `/api/ai/quotas` in home mode)
5. Note any issues

**Exit criteria:** Every page visited empty. Screenshots saved. Issues noted.

---

## Phase 3: User Journey Testing

Walk through the app as a real user, building up data naturally. Test on the frontend(s) specified in arguments.

**After every significant interaction:** check console errors and verify the action succeeded visually (snapshot or screenshot).

### 3a. Profile Creation & Selection

1. Navigate to profile selector
2. Click "Add Profile" / "Create Profile"
3. Enter name, select color, submit
4. Verify profile appears, select it
5. Verify home page loads with nav header showing profile name
6. Create a second profile for isolation testing later
7. Screenshot key states

### 3b. Search & Import

1. Search "chicken pasta" — verify results grid, images, source filter pills, result count
2. **Test source filtering** — click a source pill (e.g. allrecipes.com):
   - Verify results actually filter (only that source shown)
   - Verify result count text updates to match filtered count
   - Click "All Sources" to reset — verify full results return
3. Click "Load More" if visible — verify more results append
4. Search empty query "xyznonexistent" — verify empty state
5. **Import a recipe** — click Import button:
   - Verify loading state on button ("Importing...")
   - Verify toast notification
   - Verify redirect to recipe detail page
   - If 403 error: re-inject session cookies and retry
6. Import 2-3 more recipes for later testing
7. Screenshot search results and imported recipe

### 3c. Recipe Detail — Every Tab & Button

1. **Ingredients tab** — verify list with quantities
2. **Instructions tab** — verify numbered steps
3. **Nutrition tab** — verify data grid or "not available"
4. **Recipe Details collapse** — click to toggle, verify animation
5. **Favorite button** — click to favorite, verify icon changes to filled/pink
6. **Add to Collection** — click, verify modal, create a new collection, add recipe
7. **Source link** — verify external URL shown
8. **Cook! button** — click, verify play mode entry
9. Screenshot each tab state

### 3d. Play Mode

1. Verify full-screen cooking mode with step 1
2. Step counter shows "Step 1 of N"
3. Click Next — step advances, Previous enables
4. Click Previous — step retreats
5. **Timer buttons**: click +5 min — timer appears counting down with pause/reset/delete buttons
6. Add a second timer (+10 min) — both run independently
7. Timer badge shows count
8. Navigate steps — timers persist
9. Exit play mode — verify return to recipe detail
10. Screenshot play mode with active timers

### 3e. Favorites & Collections

1. Navigate to Favorites — verify favorited recipe appears
2. Unfavorite from card — verify removal, empty state
3. Re-favorite from recipe detail — verify reappears
4. Navigate to Collections — verify created collection appears
5. Click into collection — verify recipe inside
6. Create another collection from Collections page
7. Remove recipe from collection — verify removed but still in All Recipes
8. Screenshot key states

### 3f. All Recipes & Home

1. Navigate to All Recipes — verify all imported recipes shown with filter input
2. Navigate to Home — verify Recently Viewed and My Favorite Recipes sections
3. Screenshot both pages

### 3g. Settings — All Tabs

1. **General** — API key section (configured/not configured status), About section
2. **AI Prompts** — prompt cards with model badges (if AI), or warning banner (if no AI)
3. **Sources** — 15 sources with toggle switches, Enable All / Disable All, toggle one off and back on
4. **Selectors** — CSS selectors with Test buttons, Edit buttons
5. **Users** — profile list with stats, edit/delete buttons, quota labels
6. **Danger Zone** — Reset Database button (do NOT click confirm)
7. Check console errors on settings page — should be clean (no 404 on quotas in home mode)
8. Screenshot each tab

### 3h. Profile Isolation

1. Switch to second profile (via profile selector or log out)
2. Verify empty state — no favorites, no recently viewed from first profile
3. Switch back — verify first profile's data intact
4. Screenshot showing isolation

### 3i. Dark Mode (if supported)

1. Toggle dark mode in Settings > General
2. Visit Home, Search, Recipe detail, Settings — verify consistent dark styling
3. Toggle back to light mode
4. Screenshot dark mode on one page

### 3j. Log Out Flow

1. Click profile avatar in nav header — dropdown appears
2. Click "Log out" — verify redirect to profile selector
3. Screenshot

**Phase 3 exit criteria:** All subsections tested. Every button, modal, popup, and toggle exercised. Issues tracked.

---

## Phase 4: AI Feature Testing

If `--without-ai`: verify all 8 AI-dependent UI elements from the reference are **completely hidden** (not disabled, not grayed out — absent from DOM). Check on recipe detail, home page, and settings. Then skip to Phase 5.

If `--with-ai`: test all 10 AI features below. Each test should verify the API call succeeds, the UI updates correctly, and there are no console errors.

### 4a. Settings — API Key & Prompts

1. Settings > General — verify "Configured" status (green dot)
2. Settings > AI Prompts — verify all 10 prompts listed:
   - recipe_remix, serving_adjustment, tips_generation
   - discover_favorites, discover_seasonal, discover_new
   - search_ranking, timer_naming, remix_suggestions, selector_repair
3. Click Edit on a prompt — verify modal with system prompt, user prompt, model selector
4. Make a small edit, save, verify persistence
5. Reset to default, verify restoration
6. Screenshot the prompts tab

### 4b. Recipe Tips (tips_generation)

1. Navigate to a recipe detail
2. Find the Tips tab or Generate Tips button
3. Click generate — verify loading state, then tips appear
4. Verify tips are contextually relevant to the recipe
5. Screenshot tips

### 4c. Serving Adjustment (serving_adjustment)

1. On a recipe with servings value, find the serving adjuster controls
2. Click + to scale up — verify ingredients update via AI
3. Click - to scale down — verify ingredients update
4. If recipe has no servings, verify adjuster is hidden
5. Screenshot before/after scaling

### 4d. Recipe Remix (recipe_remix + remix_suggestions)

1. On recipe detail, find the Remix button
2. Click — verify remix modal opens
3. Verify remix suggestions populate (6 contextual suggestions)
4. Click a suggestion or type custom modification
5. Submit — verify loading, then new remixed recipe created
6. Verify remixed recipe has "(Remix)" or similar indicator
7. Screenshot the remix modal and result

### 4e. Discover Features (discover_favorites, discover_seasonal, discover_new)

1. Navigate to Home page
2. Find the Discover section/tab
3. Verify discover suggestions appear (based on favorites, seasonal, try-new)
4. Click a suggestion — verify it triggers a search
5. Click refresh — verify new suggestions
6. Screenshot discover section

### 4f. Search Ranking (search_ranking)

1. Search for a recipe — results should be AI-ranked when key is configured
2. Verify results load without errors
3. This is mostly transparent — just verify no errors

### 4g. Timer Naming (timer_naming)

1. Enter play mode on a recipe
2. Navigate to a step with time references (e.g. "cook for 5 to 7 minutes")
3. Add a timer — verify it gets an AI-generated descriptive name (not just "5 min")
4. Screenshot timer with AI name

### 4h. Selector Repair (selector_repair)

1. Settings > Selectors tab
2. Find the AI repair button (if a selector is broken/failing)
3. Test a source, if it fails verify the AI repair option appears
4. Screenshot

**Phase 4 exit criteria:** All 10 AI features tested (--with-ai) or all AI UI verified hidden (--without-ai).

---

## Phase 5: Log & Error Audit

1. Check server logs: `docker logs cookie-prod-app --tail=300 2>&1 | grep -i "error\|traceback\|warning\|500"`
2. Aggregate all unique browser console errors from Phases 2-4
3. Aggregate all failed network requests from Phases 2-4
4. Check for patterns — recurring errors, cascading failures

**Exit criteria:** All log sources reviewed. Issues catalogued.

---

## Phase 6: Bug Report & Fix

### 6a. Compile the bug list

Output a table with ALL findings:

| # | Severity | Frontend | Page | Description | Console/Network Error |
|---|----------|----------|------|-------------|----------------------|

Severity: Critical (crash/data loss), High (feature broken), Medium (degraded UX), Low (cosmetic)

### 6b. Fix bugs

If `--audit-only` was passed, stop here — output the bug table and exit.

Otherwise, fix each bug:
1. Read the source file before editing
2. Make the fix — hooks will automatically enforce ES5 compliance, CSS compatibility, template safety, and Docker usage
3. After legacy static file changes: `docker compose down && docker compose up -d` (collectstatic runs on start)

### 6c. Verify fixes

1. Re-navigate to affected pages, take "after" screenshots
2. Verify console errors are resolved
3. Run test suites:
   ```bash
   docker compose exec web python -m pytest
   docker compose exec frontend npm test
   ```
4. Run linters:
   ```bash
   docker compose exec web ruff check .
   docker compose exec frontend npm run lint
   ```

### 6d. Final output

1. **Bug table** with status (fixed / needs-attention / wont-fix)
2. **Files modified** with brief description
3. **Test results** — pass/fail
4. **Remaining issues** — anything that couldn't be fixed

---

## Operating Guidelines

<do>
- Complete all phases in order
- Test every button, modal, popup, toggle, and interactive element
- Walk through features as a real user would, building up data naturally
- Take screenshots at key states (not every single click)
- Check console errors after each page navigation and after actions that trigger API calls
- Re-inject session cookies if you get unexpected 403 errors
- Restart dev containers after legacy static file changes
- If a fix is risky or ambiguous, explain and let the user decide
</do>

<rules_and_hooks>
The following are enforced automatically — you do NOT need to memorize them, but you should understand why a hook might block your edit:

**PreToolUse hooks (settings.json)** — these run before every Edit/Write/Bash:
- `es5-syntax-check.sh` — blocks ES6+ syntax in legacy JS files
- `ios9-css-check.sh` — blocks incompatible CSS in legacy stylesheets
- `unsafe-template-check.sh` — blocks unsafe template patterns (XSS prevention)
- `docker-command-check.sh` — blocks bare Python/Node commands (must use `docker compose exec`)

**Rules files (.claude/rules/)** — loaded automatically into context:
- `es5-compliance.md` — full ES5/CSS compatibility rules for iOS 9.3 Safari
- `docker-environment.md` — all commands via Docker, container restart after static changes
- `django-security.md` — ORM only, CSRF, no secrets in code, SessionAuth patterns
- `ai-features.md` — hide AI UI when unavailable, fallback behavior, 10 feature keys
- `code-quality.md` — max 100 lines/function, max 15 cyclomatic complexity
- `react-security.md` — React-specific XSS prevention

If a hook blocks your edit, read the error message and fix the violation — do not try to bypass the hook.
</rules_and_hooks>

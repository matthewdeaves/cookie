---
name: qa-auto
description: Full automated QA audit using Playwright MCP. Rebuilds from a clean database, then walks through every user journey — creating profiles, searching, importing, cooking, organizing — testing every button, modal, and popup on both frontends. Documents bugs and UI/UX improvements via speckit, then asks the user what to fix.
user_invocable: true
argument-hint: "[modern|legacy|both] [--audit-only] [--screenshots-only] [--skip-rebuild]"
---

# Automated QA Audit & Fix

You are a QA engineer running a full end-to-end audit of Cookie from a clean database. You will build the app fresh, then walk through every user journey as a real user would — creating a profile, searching for recipes, importing them, organizing into collections, cooking in play mode, adjusting settings — testing every button, modal, popup, and edge case on both frontends.

After the audit, you document everything (bugs AND UI/UX improvement ideas) via speckit, present the full list to the user, and let them decide what to fix.

Read [reference.md](reference.md) before starting — it has the complete feature inventory, page list, and test matrix.

<arguments>
- `$ARGUMENTS` defaults to `both` if empty
- `modern` / `legacy` / `both` — which frontend(s) to test
- `--audit-only` — document findings but do not fix anything or run speckit
- `--screenshots-only` — just capture screenshots, no interaction testing
- `--skip-rebuild` — skip the fresh build and test against the existing environment
</arguments>

<environment>
| Service | URL | Notes |
|---------|-----|-------|
| Modern frontend | http://localhost:3000 | React SPA |
| Legacy frontend | http://localhost:3000/legacy/ | ES5 vanilla JS, iOS 9.3 Safari target |
| Backend API | http://localhost:8000 | Django/Gunicorn behind nginx |
| Backend logs | `docker compose logs web --tail=200` | Django/Gunicorn |
| Frontend logs | `docker compose logs frontend --tail=200` | Vite dev server |

Run all backend/frontend commands via `docker compose exec` — there is no Python or Node on the host machine.
</environment>

<context_management>
This is a long task that will use significant context. Work through all 8 phases — your context window will be automatically compacted if needed, so do not stop early due to token budget concerns.

If context is running low during later phases, save your progress: commit any pending fixes and output the remaining speckit commands the user should run manually.
</context_management>

---

## Phase Overview

```
Phase 1: Fresh Environment       — rebuild from scratch, health checks
Phase 2: Empty State Audit       — visit every page with no data
Phase 3: User Journey Testing    — walk through every feature, every button
Phase 4: Log & Error Audit       — review all logs after testing
Phase 5: Issue Documentation     — compile bugs + UI/UX improvements
Phase 6: Speckit Write-Up        — document everything via speckit
Phase 7: User Decision & Fix     — present findings, user says what to fix
Phase 8: Verification            — re-test fixes, run test suites & linters
```

Create a task (TaskCreate) for each phase when you start it. Mark it done when complete. Between phases, output a short completion summary:

```
## Phase N Complete: {Name}
- Findings: {bullet list}
- Issues found: {count}
- Next: Phase {N+1}
```

<example>
## Phase 1 Complete: Fresh Environment
- Containers rebuilt from scratch with empty database
- All 4 services healthy (db, web, frontend, nginx)
- Health endpoint: 200 OK
- AI status: unavailable (no OPENROUTER_API_KEY)
- Backend/frontend logs: clean
- Issues found: 0
- Next: Phase 2
</example>

---

## Phase 1: Fresh Environment

Start from a clean slate to catch first-run issues, empty state bugs, and setup flow problems invisible on a populated database.

If `--skip-rebuild` was passed, skip the rebuild steps and just run the health checks (steps 4-8).

### Rebuild steps

1. Stop containers and wipe the database volume:
   ```bash
   docker compose down -v
   ```
   The `-v` flag removes the `postgres-data` volume for a truly empty database.

2. Rebuild and start containers:
   ```bash
   docker compose build --no-cache web
   docker compose up -d
   ```

3. Wait for all services to be healthy. The `web` entrypoint auto-runs migrations and collectstatic:
   ```bash
   docker compose ps
   ```
   Confirm db, web, frontend, and nginx are running. If `web` is restarting, check logs.

### Health checks (run always)

4. `docker compose logs web --tail=50` — confirm "Starting Gunicorn" appears, no errors
5. `docker compose logs frontend --tail=50` — confirm Vite is ready, no errors
6. `curl -s http://localhost:8000/api/system/health/` — confirm 200
7. `curl -s http://localhost:8000/api/ai/status` — note AI availability (determines which UI elements should be visible)
8. `curl -s http://localhost:3000/` — confirm nginx is serving the frontend

**Exit criteria:** Fresh environment with empty database (or existing if `--skip-rebuild`). All services healthy. AI availability noted.

---

## Phase 2: Empty State Audit

Before creating any data, visit every page to verify empty states render correctly. An empty database is a valid state users encounter on first install.

<page_visit_order frontend="modern">
1. `/` (ProfileSelector) — should show create profile UI, no existing profiles
2. `/home` — should redirect to `/` since no profile is selected
3. `/favorites` — should redirect or show empty
4. `/all-recipes` — should redirect or show empty
5. `/collections` — should redirect or show empty
6. `/settings` — should redirect or show empty
7. `/search?q=chicken` — may work without a profile or may redirect
</page_visit_order>

<page_visit_order frontend="legacy">
Same pages at `/legacy/` prefix.
</page_visit_order>

For each page:
1. `browser_navigate` to the URL
2. `browser_wait_for` until loading finishes
3. `browser_take_screenshot` → `./screenshots/{frontend}-empty-{page}.png`
4. `browser_snapshot` — check DOM structure
5. `browser_console_messages` — record errors/warnings
6. `browser_network_requests` — flag 4xx/5xx responses
7. Review the screenshot: does the empty state look good? Is there a helpful message? Any broken layout?

After each page, reflect: are there console errors or network failures? Also note any UI/UX improvement ideas (e.g., "empty state could use an illustration", "redirect is jarring — should show a message instead").

**Exit criteria:** Every page visited in its empty state. Empty states documented. Screenshots saved. Bugs and UI/UX ideas noted.

---

## Phase 3: User Journey Testing

The core of the audit. Walk through the app as a real user would, starting from nothing and building up data. Test every button, modal, popup, dropdown, toggle, and interactive element you encounter.

Work through each journey on the **modern frontend first**, then repeat on the **legacy frontend**. After each subsection, report what worked and what failed, plus any UI/UX improvement ideas you notice from the screenshots and interactions.

<playwright_tips>
- `browser_click` timeout? Use `browser_evaluate` with `(el) => { el.click(); return 'clicked'; }` as workaround
- `browser_take_screenshot` hangs? Close browser and reopen, or use `browser_run_code`
- SPA navigation: `browser_evaluate` with `() => { window.history.pushState({}, '', '/path'); window.dispatchEvent(new PopStateEvent('popstate')); }`
- Use `browser_wait_for` after every navigation and after every action that triggers loading
- Take a screenshot after every significant interaction — not just page loads
</playwright_tips>

<what_to_track>
For every interaction, track two things:
1. **Bugs** — things that are broken (console errors, network failures, wrong behavior, crashes)
2. **UI/UX improvements** — things that work but could be better (poor empty states, confusing flows, inconsistent spacing, missing loading indicators, small touch targets, unclear labels, design inconsistencies between pages or frontends)

Both go into the Phase 5 issue table with different categories. Both get speckit'd in Phase 6.
</what_to_track>

### 3a. Profile Creation & Selection

Starting from the empty profile selector:

1. **Screenshot** the empty profile selector page
2. **Click "Create Profile"** button — verify the creation form/modal appears
3. **Enter a profile name** (e.g., "Test User") — verify the name input works
4. **Select an avatar color** if color picker is shown — click it, verify it responds
5. **Submit** the form — verify:
   - Toast/confirmation appears
   - New profile card appears in the list with the name and color
   - No console errors
6. **Click the profile card** to select it — verify:
   - Redirects to home page
   - Nav header shows the profile name
   - Session is established (subsequent API calls work)
7. **Screenshot** the home page after first login
8. **Create a second profile** — navigate back to `/`, create "Second User"
9. **Verify both profiles** appear in the selector list

Report 3a results before continuing.

### 3b. First-Run Home Page

After selecting the first profile:

1. **Check Home page tabs** — Favorites tab should show empty state, Discover tab depends on AI
2. **Verify Recently Viewed** section — should be empty or hidden
3. **Check the nav header** — profile name visible, all nav links present and clickable
4. **Click each nav link** (Home, Search, Favorites, All Recipes, Collections, Settings) — verify each navigates correctly
5. **Screenshot** each destination page in its empty state
6. **Test the search bar** in the nav header — type a query, verify it navigates to search results

Report 3b results before continuing.

### 3c. Search & Import

1. **Search "chicken"** — verify results grid with images, titles, source labels, result count, source filter pills
2. **Click each source filter pill** — verify results update when toggling
3. **Click "Load More"** (if visible) — verify more results append without duplicates
4. **Screenshot** the search results page
5. **Search "xyznonexistent"** — verify empty state, no errors, no broken layout
6. **Screenshot** the empty search results
7. **Search "pasta"** — **click Import** on a result — verify loading indicator, toast, redirect to detail
8. **Screenshot** the imported recipe detail page
9. **Import 2-3 more recipes** — these are needed for favorites, collections, and play mode testing

Report 3c results before continuing.

### 3d. Recipe Detail — Every Tab & Button

Using an imported recipe:

1. **Ingredients tab** — click, verify ingredient list
2. **Instructions tab** — click, verify numbered steps
3. **Nutrition tab** — click, verify data or "not available"
4. **Tips tab**: if AI available, click, verify tips or generate button; if AI unavailable, verify tab is hidden
5. **Serving adjuster**: if AI + servings, verify +/- buttons and test scaling; otherwise verify hidden
6. **Favorite button** — click heart/star, verify fill, click again to unfavorite, click once more to leave favorited
7. **"Add to Collection"** — click, verify modal/dropdown, create "Dinner Ideas" collection, add recipe, close modal
8. **Remix button** (AI only): click, verify modal with suggestions and text input, close without submitting; if AI off, verify hidden
9. **Source link** — verify original URL shown and clickable
10. **Play Mode button** — click, verify entry into play mode
11. **Screenshot** the recipe detail showing each tab

Report 3d results before continuing.

### 3e. Play Mode — Full Walkthrough

Enter play mode from a recipe with multiple instruction steps:

1. **Verify entry** — full-screen cooking mode, step 1 displayed
2. **Step counter** — verify "Step 1 of N" accuracy
3. **Click Next** — step 2 appears, counter updates
4. **Click Previous** — step 1 returns
5. **Navigate to a middle step** — click Next several times
6. **Timer buttons**:
   - Click +5 min — timer appears with ~5:00 countdown, check label
   - Click +10 min — second timer, both counting simultaneously
   - Click +15 min — third timer, all independent
7. **Screenshot** play mode with active timers
8. **Navigate to last step** — verify Next disabled/hidden on final step
9. **Navigate to first step** — verify Previous disabled/hidden
10. **Exit play mode** — click close/exit, verify return to recipe detail
11. **Screenshot** after exiting

Report 3e results before continuing.

### 3f. Favorites

1. **Navigate to Favorites** — verify the favorited recipe from 3d appears
2. **Verify recipe card** display (image, title)
3. **Unfavorite** from the card — verify removal from list
4. **Verify empty state**
5. **Screenshot** empty favorites
6. **Re-favorite** from recipe detail — return to favorites, verify it reappears
7. **Screenshot** favorites with a recipe

Report 3f results before continuing.

### 3g. Collections

1. **Navigate to Collections** — verify "Dinner Ideas" from 3d appears
2. **Click the collection** — verify detail page shows the recipe
3. **Screenshot** collection detail
4. **Create "Breakfast" collection** — verify form, submit, appears in list
5. **Try duplicate name** ("Dinner Ideas") — verify error
6. **Add a recipe to "Breakfast"** from recipe detail
7. **View "Breakfast"** — verify recipe is there
8. **Remove recipe** from collection — verify gone from collection but not from All Recipes
9. **Delete a collection** — verify confirmation dialog, confirm, verify removed
10. **Screenshot** after deletion

Report 3g results before continuing.

### 3h. Settings — Every Tab & Control

1. **General tab**: theme toggle (click, verify immediate change), unit preference (toggle, verify saves), API key section (verify renders). Screenshot
2. **AI Prompts tab**: if AI on, verify 10 prompts listed, click one to edit, verify modal, close. If AI off, verify hidden. Screenshot
3. **Sources tab**: verify toggles, toggle one off/on, click Test on a source, test bulk toggle. Screenshot
4. **Selectors tab**: verify list, click one to edit, verify form, close. Screenshot
5. **Users tab**: verify profile list with stats. Screenshot
6. **Danger Zone tab**: click reset preview (verify counts shown, do not confirm), check delete profile flow (do not delete). Screenshot

Report 3h results before continuing.

### 3i. Dark Mode Full Pass

1. **Toggle dark mode** in Settings > General
2. **Visit and screenshot** these pages: Home, Search results, Recipe detail, Play mode, Collections, Favorites, Settings (each tab), Profile selector
3. **Check for**: unstyled elements, white backgrounds, unreadable text, broken contrast
4. **Toggle back to light mode** — verify restoration
5. **Screenshot** one page in light mode

Report 3i results before continuing.

### 3j. AI Features (conditional)

If AI available: test remix (modal, submit, verify new recipe), serving adjustment, tips generation, discover tabs, search ranking, timer naming, remix suggestions.

If AI unavailable: verify on every page that all AI UI elements are hidden (not disabled/grayed out). Cookie hides AI features rather than showing them disabled.

Report 3j results before continuing.

### 3k. Profile Isolation & Switching

1. **Switch to second profile** ("Second User")
2. **Verify empty state** — no favorites, no recently viewed, no first profile's data
3. **Import a recipe** on this profile — verify isolated
4. **Switch back to first profile** — verify its data intact
5. **Screenshot** showing isolation

Report 3k results before continuing.

### 3l. View History

1. **View 3-4 recipe detail pages**
2. **Check home "Recently Viewed"** — verify reverse chronological order
3. **Verify limit** (max 6 or configured)
4. **Screenshot**

Report 3l results before continuing.

### 3m. Cross-Frontend Consistency (if testing both)

After modern frontend, repeat all journeys on legacy. Additionally:
1. **Data parity** — same profile, same data on both frontends
2. **Visual consistency** — similar layout, colors, spacing
3. **Navigation** — same pages accessible
4. **Empty states** — consistent messages
5. **Screenshot** side-by-side comparisons

Report 3m results.

**Phase 3 exit criteria:** All subsections (3a-3m) tested and reported. Every button, modal, popup, and toggle interacted with. Bugs and UI/UX improvement ideas tracked throughout.

---

## Phase 4: Log & Error Audit

Dedicated log review after all testing has generated traffic:

1. `docker compose logs web --tail=500` — tracebacks, 500 errors, deprecation warnings, DB errors, missing env vars
2. `docker compose logs frontend --tail=200` — build warnings, TypeScript errors, HMR failures
3. Aggregate all unique browser console errors from Phases 2-3
4. Aggregate all failed network requests from Phases 2-3

Reflect: are there patterns? Recurring errors? Issues that explain browser-side problems?

**Exit criteria:** All 4 log sources reviewed. New issues added to tracking.

---

## Phase 5: Issue & Improvement Documentation

Compile ALL findings from Phases 2-4 into a single table. This includes both **bugs** (things that are broken) and **UI/UX improvements** (things that work but could be better).

| Column | Values |
|--------|--------|
| ID | Sequential (QA-001, QA-002, ...) |
| Type | Bug / Improvement |
| Severity | Critical / High / Medium / Low |
| Frontend | Modern / Legacy / Both |
| Category | Crash / Console-error / Network-error / Accessibility / UI-UX / Design / Performance / Cross-frontend / Missing-feature |
| Page | Which page(s) affected |
| Description | What's wrong or what could be better |
| Screenshot | Reference to screenshot file |

<example>
| ID | Type | Severity | Frontend | Category | Page | Description | Screenshot |
|----|------|----------|----------|----------|------|-------------|------------|
| QA-001 | Bug | Critical | Both | Crash | ProfileSelector | Create profile button does nothing on first click | modern-empty-profile.png |
| QA-002 | Bug | High | Legacy | Console-error | PlayMode | Timer +5 button shows "++5 min" (doubled plus) | legacy-play-timers.png |
| QA-003 | Improvement | Medium | Modern | UI-UX | Home | Empty favorites state could use an illustration and "Add your first favorite" CTA | modern-empty-home.png |
| QA-004 | Improvement | Low | Both | Design | Search | Source filter pills have inconsistent spacing between frontends | modern-search.png |
| QA-005 | Improvement | Medium | Legacy | Accessibility | PlayMode | Timer buttons are 32x32px, below 44px touch target minimum | legacy-play-timers.png |
</example>

Output this complete table to the user. This is the deliverable of the audit — everything found, categorized and prioritized.

**Exit criteria:** Complete table output with every bug and every improvement idea from Phases 2-4.

---

## Phase 6: Speckit Write-Up

Document all findings (bugs and improvements) via speckit so they can be tracked and implemented. If `--audit-only` was passed, skip this phase.

<speckit_context>
Speckit creates feature artifacts under `specs/{branch-name}/` following a branch-naming convention like `###-feature-name`. Previous QA audits used this pattern (see `specs/005-fix-qa-audit-issues/` for reference).

The spec template requires user stories with acceptance scenarios. Map each issue (or group of related issues) to a user story. Both bugs and improvements become stories — bugs are framed as "user expects X but gets Y", improvements as "user would benefit from X".
</speckit_context>

### Step 1: Create the feature

```bash
bash .specify/scripts/bash/create-new-feature.sh "Fix QA audit issues" --short-name "fix-qa-audit-issues"
```

### Step 2: `/speckit.specify`

Invoke with a description covering ALL issues from the Phase 5 table — bugs and improvements. Group related issues into user stories:
- Critical/High bugs → P1 stories
- Medium bugs + high-value improvements → P2 stories
- Low bugs + nice-to-have improvements → P3 stories

<example>
`/speckit.specify Fix QA audit issues and improvements: (1) P1: Create profile button requires double-click on both frontends — first click is silently swallowed, (2) P1: Legacy timer buttons show doubled plus signs in play mode, (3) P2: Empty favorites state needs illustration and "Add your first favorite" call-to-action on both frontends, (4) P2: Settings General tab missing theme toggle and unit preference controls, (5) P3: Source filter pills have inconsistent spacing between modern and legacy frontends, (6) P3: Legacy play mode timer buttons are 32x32px — below 44px touch target minimum for iOS`
</example>

### Step 3: `/speckit.plan`

Invoke after spec. For visual/UI improvement stories, note that `/frontend-design` skill should be used.

### Step 4: `/speckit.tasks`

Invoke after plan. Generates tasks organized by user story.

### Step 5: `/speckit.analyze`

Cross-check all artifacts for consistency.

<fallback_if_context_low>
If context is running low, output the exact commands for the user:

```
# Run these in order:
bash .specify/scripts/bash/create-new-feature.sh "Fix QA audit issues" --short-name "fix-qa-audit-issues"
/speckit.specify {full description with ALL issues — paste from Phase 5 table}
/speckit.plan
/speckit.tasks
/speckit.analyze
```

Include the full issue descriptions so the user can paste directly.
</fallback_if_context_low>

**Exit criteria:** Feature branch and spec directory created. All 4 speckit skills invoked (or fallback commands provided). Artifacts in `specs/{branch-name}/`.

---

## Phase 7: User Decision & Fix

Present the complete findings to the user and ask what they want to fix now. This is a checkpoint — the user decides scope.

### 7a. Present the summary

Output the Phase 5 issue table (with updated speckit references) and ask:

```
Here are all {N} findings from the QA audit ({X} bugs, {Y} improvements).
They've been documented in specs/{branch-name}/.

What would you like me to fix now? You can:
- "Fix all bugs" — fix everything marked as Bug
- "Fix critical and high only" — just the urgent ones
- "Fix QA-001, QA-003, QA-005" — pick specific items
- "Fix all" — bugs and improvements
- "Nothing for now" — leave everything for later via speckit tasks
- Or describe in your own words what to prioritize
```

### 7b. Fix what the user requests

For each item the user selects:
1. Read the source file before editing
2. Make the fix
3. Test it (run relevant test suite or verify in browser)
4. Update the speckit tasks — mark completed tasks as done (`[x]`)

<fix_guidelines frontend="react">
- Use `/frontend-design` skill for visual/UI improvements
- Run tests after: `docker compose exec frontend npm test`
- Run lint after: `docker compose exec frontend npm run lint`
</fix_guidelines>

<fix_guidelines frontend="legacy">
Legacy code targets iOS 9.3 Safari. All JS in `apps/legacy/static/legacy/js/` uses ES5 only — hard compatibility constraint. Use `var`, `function(){}`, string concatenation. No ES6+ syntax.

- Use `/frontend-design` skill for CSS changes
- After any legacy static file change: `docker compose down && docker compose up -d`
- Verify changes deployed: check the file in `./staticfiles/`
</fix_guidelines>

<fix_guidelines frontend="backend">
- Run tests: `docker compose exec web python -m pytest`
- Check lint: `docker compose exec web ruff check .`
</fix_guidelines>

If a fix is risky or ambiguous, explain the risk and let the user decide.

**Exit criteria:** User-selected items fixed. Speckit tasks updated. Or user chose "nothing for now."

---

## Phase 8: Verification

Verify the codebase is healthy after fixes. If nothing was fixed in Phase 7, run just 8b and 8c as a baseline.

### 8a. Re-test fixed pages
For each fix: navigate to the page, take an "after" screenshot (`-fixed` suffix), verify the fix works, check console for zero new errors.

### 8b. Test suites
- `docker compose exec frontend npm test`
- `docker compose exec web python -m pytest`

### 8c. Linters
- `docker compose exec frontend npm run lint`
- `docker compose exec web ruff check .`

### 8d. Final log check
- `docker compose logs web --tail=200` — check for new errors

**Exit criteria:** All fixes verified. Test suites pass. Linters pass. Report pass/fail for each.

---

## Final Output

After all 8 phases:

1. **Pre-flight status** — container health, AI availability, fresh vs existing
2. **Full issue table** — all bugs and improvements with status (fixed / speckit'd / deferred)
3. **Before/after screenshots** — for visual changes
4. **Files modified** — with brief description of each change
5. **Log findings** — backend/frontend log issues
6. **Speckit artifacts** — link to `specs/{branch-name}/` with remaining tasks
7. **Test results** — pass/fail for all suites and linters
8. **Phase checklist:**
   - [ ] Phase 1: Fresh Environment
   - [ ] Phase 2: Empty State Audit
   - [ ] Phase 3: User Journey Testing
   - [ ] Phase 4: Log & Error Audit
   - [ ] Phase 5: Issue & Improvement Documentation
   - [ ] Phase 6: Speckit Write-Up
   - [ ] Phase 7: User Decision & Fix
   - [ ] Phase 8: Verification

---

## Operating Guidelines

<do>
- Complete all 8 phases in order
- Start from a fresh database (unless --skip-rebuild)
- Test every button, modal, popup, toggle, and interactive element — not just page loads
- Walk through features as a real user would, building up data naturally
- Take screenshots after every significant interaction, not just on page entry
- Check console errors and network requests after every interaction
- Track both bugs AND UI/UX improvement ideas throughout testing
- Review Docker logs thoroughly in Phase 4
- Run all speckit commands in Phase 6 before any fixing
- Present all findings to the user in Phase 7 and let them choose what to fix
- Keep legacy JS ES5-compliant (iOS 9.3 Safari compatibility requirement)
- Restart containers after legacy static file changes (collectstatic runs on start)
- Use `/frontend-design` skill for UI/visual improvements
- Run all Python/Node commands via `docker compose exec`
- If a fix is risky or ambiguous, explain and let the user decide
</do>

---
name: qa-auto
description: Full automated QA audit using Playwright MCP. Rebuilds from a clean database, then walks through every user journey — creating profiles, searching, importing, cooking, organizing — testing every button, modal, and popup on both frontends. Fixes issues and documents remaining work via speckit.
user_invocable: true
argument-hint: "[modern|legacy|both] [--fix] [--screenshots-only] [--skip-rebuild]"
---

# Automated QA Audit & Fix

You are a QA engineer running a full end-to-end audit of Cookie from a clean database. You will build the app fresh, then walk through every user journey as a real user would — creating a profile, searching for recipes, importing them, organizing into collections, cooking in play mode, adjusting settings — testing every button, modal, popup, and edge case on both frontends.

Read [reference.md](reference.md) before starting — it has the complete feature inventory, page list, and test matrix.

<arguments>
- `$ARGUMENTS` defaults to `both --fix` if empty
- `modern` / `legacy` / `both` — which frontend(s) to test
- `--fix` — fix issues found (default); omit to audit-only
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

If context is running low during Phases 6-8, save your progress: commit any pending fixes and output the remaining speckit commands the user should run manually. This is better than silently dropping phases.
</context_management>

---

## How Phases Work

This audit has 8 phases executed in order. Create a task (TaskCreate) for each phase when you start it. Mark it done when complete. Between phases, output a short completion summary:

```
## Phase N Complete: {Name}
- Findings: {bullet list}
- Issues found: {count}
- Next: Phase {N+1}
```

Each phase has exit criteria — satisfy them before moving on.

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

Start from a clean slate. This ensures the audit catches first-run issues, empty state bugs, and setup flow problems that would be invisible on a populated database.

If `--skip-rebuild` was passed, skip the rebuild steps and just run the health checks (steps 4-8).

### Rebuild steps

1. Stop any running containers and wipe the database volume:
   ```bash
   docker compose down -v
   ```
   The `-v` flag removes the `postgres-data` volume, giving a truly empty database.

2. Rebuild and start containers:
   ```bash
   docker compose build --no-cache web
   docker compose up -d
   ```

3. Wait for all services to be healthy. The `web` container's entrypoint automatically runs migrations and collectstatic on a fresh database:
   ```bash
   docker compose ps
   ```
   Confirm db, web, frontend, and nginx are all running. If `web` is restarting, check logs — likely a migration or database connectivity issue.

### Health checks (run always)

4. `docker compose logs web --tail=50` — scan for startup errors, confirm "Starting Gunicorn" appears
5. `docker compose logs frontend --tail=50` — scan for build errors, confirm Vite is ready
6. `curl -s http://localhost:8000/api/system/health/` — confirm 200
7. `curl -s http://localhost:8000/api/ai/status` — note AI availability (this determines which UI elements should be visible throughout testing)
8. `curl -s http://localhost:3000/` — confirm nginx is serving the frontend

**Exit criteria:** Fresh environment running with empty database (or existing environment if `--skip-rebuild`). All services healthy. AI availability noted.

---

## Phase 2: Empty State Audit

Before creating any data, visit every page on the targeted frontend(s) to verify empty states render correctly. An empty database is a valid state users encounter on first install.

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

For each page, run the full inspection checklist:
1. `browser_navigate` to the URL
2. `browser_wait_for` until loading finishes
3. `browser_take_screenshot` → `./screenshots/{frontend}-empty-{page}.png`
4. `browser_snapshot` — check DOM structure
5. `browser_console_messages` — record errors/warnings
6. `browser_network_requests` — flag 4xx/5xx responses
7. Review the screenshot: does the empty state look correct? Is there a helpful message? Any broken layout, missing images, or JS errors?

After each page, reflect: are there console errors or network failures? Add any issues to tracking.

**Exit criteria:** Every page visited in its empty state on targeted frontend(s). Empty states documented. Screenshots saved. Issues noted.

---

## Phase 3: User Journey Testing

This is the core of the audit. Walk through the app as a real user would, starting from nothing and building up data. Test every button, modal, popup, dropdown, toggle, and interactive element you encounter.

Work through each journey below on the **modern frontend first**, then repeat on the **legacy frontend**. After each journey subsection, report what worked and what failed.

<playwright_tips>
- `browser_click` timeout? Use `browser_evaluate` with `(el) => { el.click(); return 'clicked'; }` as workaround
- `browser_take_screenshot` hangs? Close browser and reopen, or use `browser_run_code`
- SPA navigation: `browser_evaluate` with `() => { window.history.pushState({}, '', '/path'); window.dispatchEvent(new PopStateEvent('popstate')); }`
- Use `browser_wait_for` after every navigation and after every action that triggers loading
- Take a screenshot after every significant interaction — not just page loads
</playwright_tips>

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
7. **Screenshot** the home page after first login — this is the first-run experience
8. **Create a second profile** — navigate back to `/`, click create, use a different name (e.g., "Second User"), submit
9. **Verify both profiles** appear in the selector list

Report 3a results before continuing.

### 3b. First-Run Home Page

After selecting the first profile:

1. **Check the Home page tabs** — Favorites tab should show empty state, Discover tab behavior depends on AI availability
2. **Verify Recently Viewed** section — should be empty or hidden
3. **Check the nav header** — profile name visible, all nav links present and clickable
4. **Click each nav link** (Home, Search, Favorites, All Recipes, Collections, Settings) — verify each navigates correctly
5. **Screenshot** each destination page in its empty state
6. **Test the search bar** in the nav header — type a query, verify it navigates to search results

Report 3b results before continuing.

### 3c. Search & Import

1. **Search "chicken"** — verify:
   - Results grid appears with images, titles, source labels
   - Result count is displayed
   - Source filter pills are shown
2. **Click each source filter pill** — verify results update when toggling sources on/off
3. **Click "Load More"** (if visible) — verify additional results append without duplicates
4. **Screenshot** the search results page
5. **Search "xyznonexistent"** — verify empty state message, no errors, no broken layout
6. **Screenshot** the empty search results
7. **Search "pasta"** — pick a result and **click the Import button** — verify:
   - Loading/progress indicator appears
   - Toast notification confirms import
   - Redirects to the recipe detail page
   - The imported recipe has all its data (title, image, ingredients, instructions)
8. **Screenshot** the imported recipe detail page
9. **Go back to search, import 2-3 more recipes** — these will be used for favorites, collections, and play mode testing later

Report 3c results before continuing.

### 3d. Recipe Detail — Every Tab & Button

Using one of the imported recipes:

1. **Ingredients tab** — click it, verify ingredient list displays
2. **Instructions tab** — click it, verify numbered steps display
3. **Nutrition tab** — click it, verify nutrition data or "not available" message
4. **Tips tab**:
   - If AI available: click it, verify tips load or "Generate Tips" button appears. Click "Generate Tips" if shown — verify tips appear
   - If AI unavailable: verify the tab is completely hidden (not disabled)
5. **Serving adjuster**:
   - If AI available AND recipe has servings: verify +/- buttons are visible. Click + to increase, verify ingredients update. Click - to decrease, verify ingredients update
   - If AI unavailable OR no servings: verify no serving controls are rendered
6. **Favorite button** — click the heart/star icon:
   - Verify icon fills/changes state
   - Verify no console errors
   - Click again to unfavorite — verify icon reverts
   - Click once more to leave it favorited (for later testing)
7. **"Add to Collection" button** — click it:
   - Verify a modal/dropdown appears
   - If no collections exist yet, verify the "create collection" option is shown
   - Create a new collection from this modal (e.g., "Dinner Ideas")
   - Verify the recipe is added, confirmation shown
   - Close the modal
8. **Remix button** (AI only):
   - If AI available: click it, verify remix modal appears with suggestion pills and text input. Click a suggestion pill — verify it populates. Close the modal without submitting
   - If AI unavailable: verify no remix button is rendered
9. **Source link** — verify the original recipe URL is shown and clickable
10. **Play Mode button** — click it, verify it enters play mode (tested in detail in 3e)
11. **Screenshot** the recipe detail page showing each tab

Report 3d results before continuing.

### 3e. Play Mode — Full Walkthrough

Enter play mode from a recipe that has multiple instruction steps:

1. **Verify entry** — full-screen cooking mode activates, step 1 is displayed
2. **Step counter** — verify "Step 1 of N" is shown accurately
3. **Click Next** — verify step 2 appears, counter updates to "Step 2 of N"
4. **Click Previous** — verify step 1 returns, counter updates back
5. **Navigate to a middle step** — click Next several times
6. **Timer buttons** — find the +5 min / +10 min / +15 min buttons:
   - Click +5 min — verify a timer appears in the timer panel with ~5:00 countdown
   - Check the timer label (AI-named if AI available, generic "Timer 1" otherwise)
   - Click +10 min — verify a second timer appears, both are counting down simultaneously
   - Click +15 min — verify a third timer appears, all three run independently
7. **Screenshot** the play mode with active timers
8. **Navigate to last step** — click Next until you reach the final step
9. **Verify "Next" is disabled or hidden** on the last step
10. **Verify "Previous" is disabled or hidden** on the first step (navigate back to check)
11. **Exit play mode** — click the close/exit button, verify return to recipe detail page
12. **Screenshot** after exiting

Report 3e results before continuing.

### 3f. Favorites

1. **Navigate to Favorites page** — verify the recipe you favorited in 3d appears
2. **Verify the recipe card** displays correctly (image, title)
3. **Click the unfavorite toggle** on the card — verify the recipe disappears from the list
4. **Verify empty state** appears after removing the last favorite
5. **Screenshot** the empty favorites state
6. **Go back to a recipe detail and re-favorite it** — return to favorites, verify it reappears
7. **Screenshot** favorites with a recipe

Report 3f results before continuing.

### 3g. Collections

1. **Navigate to Collections page** — verify the collection created in 3d ("Dinner Ideas") appears
2. **Click the collection** — verify the collection detail page shows the recipe added earlier
3. **Screenshot** the collection detail
4. **Click "Create Collection"** on the collections list page:
   - Verify the create form/modal appears
   - Enter name "Breakfast" — submit
   - Verify new collection appears in the list
5. **Try creating a collection with a duplicate name** ("Dinner Ideas") — verify error is shown
6. **Add another recipe** to "Breakfast" from a recipe detail page
7. **View "Breakfast" collection** — verify the recipe is there
8. **Remove a recipe** from a collection — verify it disappears from the collection (but not from All Recipes)
9. **Delete a collection** — verify confirmation dialog, confirm, verify collection is removed from list
10. **Screenshot** after deletion

Report 3g results before continuing.

### 3h. Settings — Every Tab & Control

Navigate to Settings and test every tab:

1. **General tab**:
   - Verify theme toggle (light/dark) is visible — click it, verify theme changes immediately
   - Verify unit preference selector — toggle it, verify it saves
   - Check API key section — verify it renders (don't enter a real key)
   - Screenshot the General tab
2. **AI Prompts tab**:
   - If AI available: verify all 10 prompts are listed. Click one to edit — verify edit modal/form opens. Verify model selector is present. Close without saving
   - If AI unavailable: verify tab is hidden or shows appropriate empty state
   - Screenshot
3. **Sources tab**:
   - Verify all search sources are listed with toggle switches
   - Toggle one source off — verify it saves
   - Toggle it back on — verify it saves
   - Click "Test" on a source — verify it returns success/failure status
   - Test bulk toggle (all on/all off) if available
   - Screenshot
4. **Selectors tab**:
   - Verify CSS selectors are listed for each source
   - Click one to view/edit — verify edit form opens
   - Close without saving
   - Screenshot
5. **Users tab**:
   - Verify profile list with stats (favorites count, collections count, recipes count)
   - Both test profiles should appear
   - Screenshot
6. **Danger Zone tab**:
   - Verify reset preview button — click it, verify data counts are shown
   - Verify the "type RESET to confirm" safeguard is present — do not actually type it
   - Verify profile deletion controls — check the confirmation flow but do not delete
   - Screenshot

Report 3h results before continuing.

### 3i. Dark Mode Full Pass

1. **Toggle dark mode** in Settings > General
2. **Visit these pages** and screenshot each:
   - Home page
   - Search results (search for something)
   - Recipe detail
   - Play mode (enter and exit quickly)
   - Collections
   - Favorites
   - Settings (each tab)
   - Profile selector
3. **Check for issues**: unstyled elements, white backgrounds leaking through, unreadable text, missing borders, broken contrast
4. **Toggle back to light mode** — verify everything restores
5. **Screenshot** one page in light mode to confirm restoration

Report 3i results before continuing.

### 3j. AI Features (conditional)

If AI is available (from Phase 1 check):
1. Test recipe remix — open modal, select a suggestion, submit, verify new recipe created with "(Remix)" suffix
2. Test serving adjustment — scale up and down, verify ingredients change
3. Test tips generation — generate tips, verify they display
4. Test discover — check favorites/seasonal/new tabs on home discover section
5. Test search ranking — compare results with/without AI ranking
6. Test timer naming — add a timer in play mode, verify descriptive AI label
7. Test remix suggestions — open remix modal, verify 6 contextual suggestions

If AI is unavailable: verify on every page visited that all AI UI elements are hidden (not disabled/grayed out). Cookie hides AI features rather than showing them in a disabled state — check that no serving adjuster, no tips tab, no remix button, no discover tab, and no remix suggestions are rendered.

Report 3j results before continuing.

### 3k. Profile Isolation & Switching

1. **Navigate to profile selector** (`/` or `/legacy/`)
2. **Switch to the second profile** ("Second User")
3. **Verify the home page** is empty — no favorites, no recently viewed, no recipes from the first profile
4. **Verify favorites page** is empty
5. **Verify collections page** is empty
6. **Verify all-recipes page** is empty
7. **Import a recipe on this profile** — verify it only appears for this profile
8. **Switch back to the first profile** — verify its data is intact (favorites, collections, recipes)
9. **Screenshot** showing data isolation

Report 3k results before continuing.

### 3l. View History

1. **View 3-4 recipe detail pages** in sequence
2. **Go to home page** — verify "Recently Viewed" section shows the recipes in reverse chronological order (most recent first)
3. **Verify the limit** — view many recipes, confirm only the most recent N are shown
4. **Screenshot** the recently viewed section

Report 3l results before continuing.

### 3m. Cross-Frontend Consistency (if testing both)

After completing modern frontend testing, repeat all journeys on the legacy frontend. Additionally:
1. **Verify data parity** — the same profile shows the same recipes, favorites, and collections on both frontends
2. **Compare visual consistency** — similar layout, colors, spacing (not pixel-perfect but coherent)
3. **Compare navigation** — same pages are accessible
4. **Compare empty states** — same messages/layout
5. **Screenshot** side-by-side comparisons of key pages

Report 3m results.

**Phase 3 exit criteria:** All journey subsections (3a-3m) tested and reported. Every button, modal, popup, and toggle on every page has been interacted with.

---

## Phase 4: Log & Error Audit

Dedicated log review after all browser testing has generated traffic. Run these fresh:

1. `docker compose logs web --tail=500` — look for tracebacks, 500 errors, deprecation warnings, database errors, missing env vars
2. `docker compose logs frontend --tail=200` — look for build warnings, TypeScript errors, HMR failures
3. Aggregate all unique browser console errors collected during Phases 2-3
4. Aggregate all failed network requests collected during Phases 2-3

Reflect on the log output: are there patterns? Recurring errors? Issues that explain browser-side problems from earlier phases?

**Exit criteria:** All 4 log sources reviewed. New issues added to tracking.

---

## Phase 5: Issue Documentation

Compile all findings from Phases 2-4 into a structured table and output it to the user.

| Column | Values |
|--------|--------|
| ID | Sequential (QA-001, QA-002, ...) |
| Severity | Critical / High / Medium / Low |
| Frontend | Modern / Legacy / Both |
| Category | Bug / UI-UX / Accessibility / Performance / Cross-frontend / Missing-feature |
| Page | Which page(s) affected |
| Description | What's wrong |
| Screenshot | Reference to screenshot file |
| Fix Status | Unfixed (updated in Phase 6) |

<example>
| ID | Severity | Frontend | Category | Page | Description | Screenshot | Fix Status |
|----|----------|----------|----------|------|-------------|------------|------------|
| QA-001 | Critical | Both | Bug | ProfileSelector | Create profile button does nothing on first click | modern-empty-profile.png | Unfixed |
| QA-002 | High | Legacy | Bug | PlayMode | Timer +5 button shows "++5 min" (doubled plus) | legacy-play-timers.png | Unfixed |
| QA-003 | Medium | Modern | UI-UX | Home | Empty favorites state has no illustration or helpful text | modern-empty-home.png | Unfixed |
</example>

**Exit criteria:** Complete issue table with every finding from Phases 2-4.

---

## Phase 6: Fix Issues (if --fix)

If `--fix` was not specified, skip to Phase 7 and mark all issues as "Audit-only."

Fix in priority order:
1. Critical bugs (broken functionality, crashes)
2. Console errors and network failures
3. Accessibility issues
4. Cross-frontend inconsistencies
5. Layout/spacing problems
6. Design polish

For each fix: read the source file first, make the change, test it (run the relevant test suite or verify in browser), then update the issue table status.

<fix_guidelines frontend="react">
- Use `/frontend-design` skill for visual/UI improvements to ensure production-grade design quality
- Run tests after: `docker compose exec frontend npm test`
- Run lint after: `docker compose exec frontend npm run lint`
</fix_guidelines>

<fix_guidelines frontend="legacy">
Legacy code targets iOS 9.3 Safari. All JS in `apps/legacy/static/legacy/js/` uses ES5 only — this is a hard compatibility constraint, not a style preference. Use `var`, `function(){}`, string concatenation. No ES6+ syntax.

- Use `/frontend-design` skill for CSS changes to maintain visual consistency
- After any legacy static file change: `docker compose down && docker compose up -d` (collectstatic runs on container start)
- Verify changes deployed: check the file in `./staticfiles/`
</fix_guidelines>

<fix_guidelines frontend="backend">
- Run tests: `docker compose exec web python -m pytest`
- Check lint: `docker compose exec web ruff check .`
</fix_guidelines>

If a fix is risky or ambiguous, document it as a recommendation rather than implementing it.

**Exit criteria:** Every issue addressed — fixed, deferred with reason, or marked needs-human-decision. Updated issue table output.

---

## Phase 7: Verification

Verify the codebase is healthy after fixes.

### 7a. Re-test fixed pages
For each "Fixed" issue: navigate to the affected page, take an "after" screenshot (save with `-fixed` suffix), verify the fix, check console for zero new errors.

### 7b. Test suites
Run both:
- `docker compose exec frontend npm test`
- `docker compose exec web python -m pytest`

### 7c. Linters
Run both:
- `docker compose exec frontend npm run lint`
- `docker compose exec web ruff check .`

### 7d. Final log check
- `docker compose logs web --tail=200` — check for new errors since Phase 4

**Exit criteria:** All fixes verified. All test suites pass. All linters pass. Report pass/fail for each.

---

## Phase 8: Speckit Write-Up

Document remaining (unfixed) QA work using speckit so it can be tracked and implemented later. If all issues were fixed in Phase 6, skip this phase — speckit is for tracking remaining work, not documenting completed work.

<speckit_context>
Speckit creates feature artifacts under `specs/{branch-name}/` following a branch-naming convention like `###-feature-name`. Previous QA audits used this pattern (see `specs/005-fix-qa-audit-issues/` for reference).

The spec template requires user stories with acceptance scenarios. Map each unfixed QA issue (or group of related issues) to a user story. The existing `specs/005-fix-qa-audit-issues/spec.md` shows the pattern: each bug becomes a story framed from the user's perspective.
</speckit_context>

### Step 1: Create the feature

Run the speckit setup script to create a new feature branch and spec directory:

```bash
bash .specify/scripts/bash/create-new-feature.sh "Fix QA audit issues" --short-name "fix-qa-audit-issues"
```

This creates a branch (`###-fix-qa-audit-issues`), a directory (`specs/###-fix-qa-audit-issues/`), and a blank spec from the template.

### Step 2: `/speckit.specify`

Invoke with a description summarizing the unfixed issues. Map each to a user story:
- Group related issues into one story
- Priority based on severity from Phase 5 (Critical/High → P1, Medium → P2, Low → P3)
- Acceptance scenarios derived from your QA test cases

<example>
For 3 unfixed issues:
- QA-003 (High): Discover tab fails on first load
- QA-007 (Medium): Settings missing theme toggle
- QA-011 (Low): Legacy timer buttons show doubled plus signs

Invoke: `/speckit.specify Fix QA audit issues found during comprehensive audit: (1) Discover suggestions fail on first load due to fetch abort handling, (2) Settings General tab missing theme toggle and unit preference controls, (3) Legacy play mode timer buttons display doubled plus signs`
</example>

### Step 3: `/speckit.plan`

Invoke after the spec is created. This generates `plan.md`, `research.md`, `data-model.md`, and `contracts/`. For visual/UI work, note that `/frontend-design` skill should be used during implementation.

### Step 4: `/speckit.tasks`

Invoke after the plan. This generates `tasks.md` with implementation tasks organized by user story. Mark tasks completed during Phase 6 as done (`[x]`).

### Step 5: `/speckit.analyze`

Invoke last to cross-check all artifacts for consistency.

<fallback_if_context_low>
If context is running low and you cannot invoke all speckit skills, output the exact commands for the user to run manually, with the feature description pre-written:

```
# Run these in order:
bash .specify/scripts/bash/create-new-feature.sh "Fix QA audit issues" --short-name "fix-qa-audit-issues"
/speckit.specify {paste the full description with all unfixed issues}
/speckit.plan
/speckit.tasks
/speckit.analyze
```

Include the full issue descriptions so the user can paste them directly.
</fallback_if_context_low>

**Exit criteria:** Feature branch and spec directory created. All 4 speckit skills invoked (or fallback commands provided). Artifacts in `specs/{branch-name}/`.

---

## Final Output

After all 8 phases, output a summary:

1. **Pre-flight status** — container health, AI availability, fresh vs existing environment
2. **Issue table** — all issues with severity, category, frontend, fix status
3. **Before/after screenshots** — for visual changes
4. **Files modified** — with brief description of each change
5. **Log findings** — backend/frontend log issues
6. **Remaining issues** — things needing human decision
7. **Recommendations** — future improvements
8. **Test results** — pass/fail for all test suites and linters
9. **Phase checklist:**
   - [ ] Phase 1: Fresh Environment
   - [ ] Phase 2: Empty State Audit
   - [ ] Phase 3: User Journey Testing
   - [ ] Phase 4: Log & Error Audit
   - [ ] Phase 5: Issue Documentation
   - [ ] Phase 6: Fix Issues
   - [ ] Phase 7: Verification
   - [ ] Phase 8: Speckit Write-Up

---

## Operating Guidelines

<do>
- Complete all 8 phases in order
- Start from a fresh database (unless --skip-rebuild)
- Test every button, modal, popup, toggle, and interactive element — not just page loads
- Walk through features as a real user would, building up data naturally
- Take screenshots after every significant interaction, not just on page entry
- Check console errors and network requests after every interaction
- Review Docker logs thoroughly in Phase 4
- Keep legacy JS ES5-compliant (iOS 9.3 Safari compatibility requirement)
- Restart containers after legacy static file changes (collectstatic runs on start)
- Run tests and linters in Phase 7
- Use `/frontend-design` skill for UI/visual improvements
- In Phase 8, create the feature branch/directory first, then invoke speckit skills in order (or provide fallback commands with full descriptions)
- Run all Python/Node commands via `docker compose exec`
- Document risky or ambiguous fixes as recommendations instead of implementing
</do>

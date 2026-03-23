---
name: qa-auto
description: Full automated QA audit using Playwright MCP. Tests every page and feature on both modern React and legacy ES5 frontends, checks logs and console errors, fixes issues using frontend-design skill for visual quality, and documents everything via speckit. Use when the user wants a comprehensive QA pass.
user_invocable: true
argument-hint: "[modern|legacy|both] [--fix] [--screenshots-only]"
---

# Automated QA Audit & Fix

You are a QA engineer running a systematic audit of Cookie's two frontends using Playwright MCP. Read [reference.md](reference.md) before starting — it has the full feature inventory and test cases.

<arguments>
- `$ARGUMENTS` defaults to `both --fix` if empty
- `modern` / `legacy` / `both` — which frontend(s) to test
- `--fix` — fix issues found (default); omit to audit-only
- `--screenshots-only` — just capture screenshots, no testing
</arguments>

<environment>
| Service | URL | Notes |
|---------|-----|-------|
| Modern frontend | http://localhost:3000 | React SPA |
| Legacy frontend | http://localhost:3000/legacy/ | ES5 vanilla JS, iOS 9.3 Safari target |
| Backend logs | `docker compose logs web --tail=200` | Django/Gunicorn |
| Frontend logs | `docker compose logs frontend --tail=200` | Vite dev server |

Run all backend/frontend commands via `docker compose exec` — there is no Python or Node on the host machine.
</environment>

<context_management>
This is a long task that will use significant context. Work through all 8 phases — your context window will be automatically compacted if needed, so do not stop early due to token budget concerns.

If you notice context is running low during Phases 6-8, save your progress: commit any pending fixes and output the remaining speckit commands the user should run manually. This is better than silently dropping phases.
</context_management>

---

## How Phases Work

This audit has 8 phases executed in order. Create a task (TaskCreate) for each phase when you begin it. Mark it done when complete. Between phases, output a short summary:

```
## Phase N Complete: {Name}
- Findings: {bullet list}
- Issues found: {count}
- Next: Phase {N+1}
```

Each phase has exit criteria — satisfy them before moving on.

<example>
## Phase 1 Complete: Pre-Flight Checks
- All 3 containers running (web, frontend, db)
- Health endpoint: 200 OK
- AI status: unavailable (no OPENROUTER_API_KEY)
- Backend logs: clean, no errors
- Frontend logs: clean, Vite ready
- Issues found: 0
- Next: Phase 2
</example>

---

## Phase 1: Pre-Flight Checks

Run all 5 checks before opening a browser:

1. `docker compose ps` — confirm web, frontend, db are all Up
2. `docker compose logs web --tail=50` — scan for startup errors
3. `docker compose logs frontend --tail=50` — scan for build errors
4. `curl -s http://localhost:8000/api/system/health/` — confirm 200
5. `curl -s http://localhost:8000/api/ai/status` — note AI availability (determines which UI elements should be visible later)

**Exit criteria:** All 5 checks run and reported. Stop if any critical check fails.

---

## Phase 2: Systematic Page Audit

Visit every page on the targeted frontend(s). The goal is to capture the baseline state — screenshots, console errors, network errors — before doing any deep interaction testing.

<page_visit_order frontend="modern">
1. `/` (ProfileSelector) — select a profile here
2. `/home` (Home)
3. `/search?q=chicken` (Search with results)
4. `/search?q=xyznonexistent` (Search empty state)
5. `/favorites` (Favorites)
6. `/all-recipes` (AllRecipes)
7. `/collections` (Collections)
8. `/collection/:id` (CollectionDetail) — use a real ID from collections page
9. `/recipe/:id` (RecipeDetail) — use a real ID from all-recipes
10. `/recipe/:id/play` (PlayMode) — same recipe
11. `/settings` (Settings — visit all 6 tabs)
</page_visit_order>

<page_visit_order frontend="legacy">
Same 11 pages at `/legacy/` prefix. Select a profile on `/legacy/` first.
</page_visit_order>

For each page:
1. `browser_navigate` to the URL
2. `browser_wait_for` until loading finishes
3. `browser_take_screenshot` → `./screenshots/{frontend}-{page}.png`
4. `browser_snapshot` — check DOM structure
5. `browser_console_messages` — record errors/warnings
6. `browser_network_requests` — flag 4xx/5xx responses
7. Review the screenshot for visual problems (layout, spacing, typography, color)

After visiting each page, reflect briefly: are there console errors or network failures? Add them to your issue tracking. Then proceed to the next page.

Select a profile first — click a profile name on `/` (modern) or `/legacy/` (legacy) before visiting authenticated pages. Create one if none exist.

<playwright_tips>
- `browser_click` timeout? Use `browser_evaluate` with `(el) => { el.click(); return 'clicked'; }` as workaround
- `browser_take_screenshot` hangs? Close browser and reopen, or use `browser_run_code`
- SPA navigation: `browser_evaluate` with `() => { window.history.pushState({}, '', '/path'); window.dispatchEvent(new PopStateEvent('popstate')); }`
- Use `browser_wait_for` after every navigation
</playwright_tips>

**Exit criteria:** Every page visited on every targeted frontend. Screenshots saved for all. Console and network checked for all. Report total pages visited and issues found.

---

## Phase 3: Feature-Deep Testing

Now test actual functionality beyond just page rendering. Work through each subsection below. After each subsection, note what worked and what failed — this creates a clear trail and prevents skipping.

### 3a. Search & Import
- Search "chicken" — verify results grid with images, titles, sources
- Toggle source filter pills — verify results change
- Click Load More — verify more results appear
- Search "xyznonexistent" — verify empty state, no errors
- Import a recipe from results — verify toast + redirect to detail
- (If URL import exists) Paste a recipe URL — verify direct import

Report 3a results before continuing.

### 3b. Recipe Detail
- Check all tabs: Ingredients, Instructions, Nutrition, Tips
- Check serving adjuster visibility (only visible if AI enabled AND recipe has servings)
- Toggle favorite (add/remove)
- Test "Add to Collection"
- Check remix button visibility (only if AI enabled)
- Enter Play Mode from detail page
- Check linked recipes section (original, remixes, siblings)

Report 3b results before continuing.

### 3c. Play Mode
- Navigate steps (Previous/Next) — verify step counter accuracy
- Create a timer (+5/+10/+15 min buttons) — verify it appears in timer panel
- Add multiple timers — verify all run simultaneously
- Check timer labels (AI-named vs generic)
- Verify close/exit returns to recipe detail

Report 3c results before continuing.

### 3d. Profile Management
- Create new profile (name + avatar color)
- Switch between profiles — verify data isolation
- Update profile settings (theme, unit preference)
- Check profile deletion flow (preview only — do not actually delete)

Report 3d results before continuing.

### 3e. Collections & Favorites
- Create a collection, add a recipe, view collection detail
- Remove recipe from collection
- Check favorites page — verify add/remove works
- Check empty states

Report 3e results before continuing.

### 3f. Settings (all 6 tabs)
- **General**: Theme toggle (light/dark), unit preference
- **AI Prompts**: List all prompts, edit one (if AI enabled); verify hidden if AI off
- **Sources**: Toggle source, test source, bulk toggle
- **Selectors**: View selectors, edit one
- **Users**: Profile list with stats
- **Danger Zone**: Reset preview (do not actually reset), profile deletion preview

Report 3f results before continuing.

### 3g. AI Features
If AI is available (from Phase 1), test: remix, serving adjustment, tips generation, discover (favorites/seasonal/new), search ranking, timer naming, remix suggestions.

If AI is unavailable: verify that all AI UI elements are hidden (not disabled/grayed out) on every page — this is a design requirement, not just nice-to-have. Cookie hides AI features rather than showing them in a disabled state.

Report 3g results before continuing.

### 3h. Dark Mode
- Toggle dark mode in settings
- Visit at least 5 representative pages — verify dark styles apply consistently
- Check for unstyled elements or contrast issues
- Toggle back to light mode and verify

Report 3h results before continuing.

### 3i. View History
- View a recipe, then check home for "Recently Viewed"
- Verify ordering (most recent first)

Report 3i results.

**Exit criteria:** All 9 subsections (3a-3i) tested and reported with results.

---

## Phase 4: Log & Error Audit

Dedicated log review phase. Run these commands fresh — even if you glanced at logs earlier, this phase is about a comprehensive sweep after all browser testing has generated traffic.

1. `docker compose logs web --tail=500` — look for tracebacks, 500 errors, deprecation warnings, database errors, missing env vars
2. `docker compose logs frontend --tail=200` — look for build warnings, TypeScript errors, HMR failures
3. Aggregate all unique browser console errors collected during Phases 2-3
4. Aggregate all failed network requests collected during Phases 2-3

Reflect on the log output: are there patterns? Recurring errors? Issues that explain browser-side problems you saw earlier?

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
| QA-001 | High | Both | Bug | Search | Source filter pills don't update result count | modern-search.png | Unfixed |
| QA-002 | Medium | Legacy | UI-UX | PlayMode | Timer panel overlaps step text on narrow screens | legacy-play.png | Unfixed |
| QA-003 | Low | Modern | Accessibility | Settings | Theme toggle missing aria-label | modern-settings.png | Unfixed |
</example>

**Exit criteria:** Complete issue table output with every issue from Phases 2-4. No finding left undocumented.

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

For each fix: read the source file first, make the change, test it (run the relevant test suite or verify in browser), then update the issue table status to "Fixed" or "Deferred" with reason.

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

Document all QA work using speckit for implementation tracking. Execute these 4 skills in order:

1. `/speckit.specify` — Create a spec covering: what was found, what was fixed, what remains unfixed and why
2. `/speckit.plan` — Document the implementation approach for remaining work (use `/frontend-design` within the plan for visual/UI work)
3. `/speckit.tasks` — Generate task list with completed tasks marked done
4. `/speckit.analyze` — Cross-check all artifacts for consistency

<fallback_if_context_low>
If context is running low and you cannot invoke all 4 speckit skills, output the commands the user should run manually:
```
/speckit.specify {description of QA findings}
/speckit.plan
/speckit.tasks
/speckit.analyze
```
This ensures the user can complete Phase 8 even if the conversation needs to end.
</fallback_if_context_low>

**Exit criteria:** All 4 speckit skills invoked (or fallback commands provided). Artifacts created in `.specify/` directory.

---

## Final Output

After all 8 phases, output a summary covering:

1. **Pre-flight status** — container health, AI availability
2. **Issue table** — all issues with severity, category, frontend, fix status
3. **Before/after screenshots** — for visual changes
4. **Files modified** — with brief description of each change
5. **Log findings** — backend/frontend log issues
6. **Remaining issues** — things needing human decision
7. **Recommendations** — future improvements
8. **Test results** — pass/fail for all test suites and linters
9. **Phase checklist:**
   - [ ] Phase 1: Pre-Flight Checks
   - [ ] Phase 2: Systematic Page Audit
   - [ ] Phase 3: Feature-Deep Testing
   - [ ] Phase 4: Log & Error Audit
   - [ ] Phase 5: Issue Documentation
   - [ ] Phase 6: Fix Issues
   - [ ] Phase 7: Verification
   - [ ] Phase 8: Speckit Write-Up

---

## Operating Guidelines

<do>
- Complete all 8 phases in order
- Visit every page on every targeted frontend
- Create a task for each phase and mark it done when complete
- Output a phase completion summary before moving to the next phase
- Take screenshots on every page visit
- Check console errors and network requests on every page
- Review Docker logs thoroughly in Phase 4
- Keep legacy JS ES5-compliant (iOS 9.3 Safari compatibility requirement)
- Restart containers after legacy static file changes (collectstatic runs on start)
- Run tests and linters in Phase 7
- Use `/frontend-design` skill for UI/visual improvements
- Invoke all 4 speckit skills in Phase 8 (or provide fallback commands)
- Run all Python/Node commands via `docker compose exec`
- Document risky or ambiguous fixes as recommendations instead of implementing
</do>

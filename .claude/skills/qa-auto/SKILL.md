---
name: qa-auto
description: Full automated QA audit using Playwright MCP. Tests every page and feature on both modern React and legacy ES5 frontends, checks logs and console errors, fixes issues using frontend-design skill for visual quality, and documents everything via speckit. Use when the user wants a comprehensive QA pass.
user_invocable: true
argument-hint: "[modern|legacy|both] [--fix] [--screenshots-only]"
---

# Automated QA Audit & Fix

You are a QA automation agent. Systematically test EVERY page and feature of Cookie using Playwright MCP, check all logs, fix issues, and document work via speckit.

**Read [reference.md](reference.md) before starting** — it contains the exhaustive feature inventory and test cases.

## Arguments

- `$ARGUMENTS` defaults to `both --fix` if empty
- `modern` / `legacy` / `both` — which frontend(s) to test
- `--fix` — fix issues found (default); omit to audit-only
- `--screenshots-only` — just capture screenshots, no testing

## Environment

| Service | URL | Notes |
|---------|-----|-------|
| Modern frontend | http://localhost:3000 | React SPA |
| Legacy frontend | http://localhost:3000/legacy/ | ES5 vanilla JS, iOS 9.3 Safari target |
| Backend logs | `docker compose logs web --tail=200` | Django/Gunicorn |
| Frontend logs | `docker compose logs frontend --tail=200` | Vite dev server |

ALL backend/frontend commands via `docker compose exec`. NO host Python/Node.

---

## CRITICAL: Phase Enforcement Protocol

This skill has 8 phases. You MUST complete ALL of them. The #1 failure mode is rushing through early phases and skipping later ones.

**Before starting each phase**, create a task for it using TaskCreate. **After completing each phase**, mark the task done and output a phase completion summary to the user with this format:

```
## ✓ Phase N Complete: {Phase Name}
- Key findings: {bullet list}
- Issues found: {count}
- Next: Phase {N+1}
```

**DO NOT start Phase N+1 until you have output the Phase N completion summary.**

If you find yourself wanting to combine phases or skip ahead — STOP. Each phase exists for a reason. The user expects all 8.

---

## Phase 1: Pre-Flight Checks

**Task name:** "Phase 1: Pre-Flight Checks"

Before any browser testing, run ALL 5 checks:

1. **Verify containers are running**: `docker compose ps` — all 3 containers (web, frontend, db) must be Up
2. **Check backend logs for startup errors**: `docker compose logs web --tail=50`
3. **Check frontend logs for build errors**: `docker compose logs frontend --tail=50`
4. **Hit health endpoint**: `curl -s http://localhost:8000/api/system/health/`
5. **Check AI status**: `curl -s http://localhost:8000/api/ai/status` — note whether AI features should be visible

**Phase 1 exit criteria:** All 5 checks run, results reported. If any check fails, report and stop.

Initialize a tracking variable for issues found:
```
ISSUES = []  # Will be populated throughout phases 2-4
```

---

## Phase 2: Systematic Page Audit

**Task name:** "Phase 2: Systematic Page Audit ({frontend_scope})"

Visit EVERY page listed in [reference.md](reference.md) on the targeted frontend(s). Track progress with a checklist — do not move on until every page is visited.

### Page visit order (modern):
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
11. `/settings` (Settings — visit ALL 6 tabs)

### Page visit order (legacy):
Same 11 pages but at `/legacy/` prefix. Select a profile on `/legacy/` first.

### Per-Page Checklist (do ALL of these for EACH page)

1. **Navigate** to the page via `browser_navigate`
2. **Wait** for content: `browser_wait_for` until loading spinners/skeletons disappear
3. **Screenshot**: `browser_take_screenshot` — save to `./screenshots/{frontend}-{page}.png`
4. **Accessibility snapshot**: `browser_snapshot` — inspect DOM structure
5. **Console errors**: `browser_console_messages` — capture ALL errors and warnings → add to ISSUES
6. **Network errors**: `browser_network_requests` — flag any 4xx/5xx → add to ISSUES
7. **Visual review**: Check layout, spacing, typography, color → add problems to ISSUES

**Phase 2 exit criteria:** Every page visited on every targeted frontend. Screenshots taken for all. Console and network checked for all. Report: "{X} pages visited, {Y} issues found so far."

### Login First

Click a profile name on `/` (modern) or `/legacy/` (legacy) before visiting authenticated pages. If no profiles exist, create one first.

### Playwright Tips

- `browser_click` timeout? Use `browser_evaluate` with `(el) => { el.click(); return 'clicked'; }` as workaround
- `browser_take_screenshot` hangs on "waiting for fonts"? Close browser and reopen, or use `browser_run_code`
- SPA navigation without losing session: `browser_evaluate` with `() => { window.history.pushState({}, '', '/path'); window.dispatchEvent(new PopStateEvent('popstate')); }`
- Always `browser_wait_for` after navigation

---

## Phase 3: Feature-Deep Testing

**Task name:** "Phase 3: Feature-Deep Testing ({frontend_scope})"

Go beyond page rendering — test actual functionality. Work through EACH subsection below. After completing each subsection, note what was tested and issues found.

### 3a. Search & Import
- Search "chicken" — verify results grid with images, titles, sources
- Toggle source filter pills — verify results change
- Click Load More / pagination — verify more results appear
- Search "xyznonexistent" — verify empty state, no errors
- Import a recipe from results — verify toast + redirect to detail
- (If URL import exists) Paste a recipe URL — verify direct import

**After 3a:** Report what worked, what failed.

### 3b. Recipe Detail
- Check ALL tabs: Ingredients, Instructions, Nutrition, Tips
- Check serving adjuster visibility (only if AI enabled AND recipe has servings)
- Toggle favorite (add/remove) — verify icon changes
- Test "Add to Collection" — verify it works
- Check remix button visibility (only if AI enabled)
- Enter Play Mode from detail page
- Check linked recipes section (original, remixes, siblings)

**After 3b:** Report what worked, what failed.

### 3c. Play Mode
- Navigate steps (Previous/Next) — verify step counter accuracy
- Create a timer (+5/+10/+15 min buttons) — verify it appears in timer panel
- Add multiple timers — verify all run simultaneously
- Check timer labels (AI-named vs generic)
- Verify close/exit returns to recipe detail

**After 3c:** Report what worked, what failed.

### 3d. Profile Management
- Create new profile (name + avatar color)
- Switch between profiles — verify data isolation
- Update profile settings (theme, unit preference)
- Check profile deletion flow (preview, DON'T actually delete)

**After 3d:** Report what worked, what failed.

### 3e. Collections & Favorites
- Create a collection, add a recipe, view collection detail
- Remove recipe from collection
- Check favorites page — verify add/remove works
- Check empty states

**After 3e:** Report what worked, what failed.

### 3f. Settings (ALL 6 tabs)
- **General**: Theme toggle (light/dark), unit preference
- **AI Prompts**: List all prompts, edit one (if AI enabled); verify hidden if AI off
- **Sources**: Toggle source, test source, bulk toggle
- **Selectors**: View selectors, edit one
- **Users**: Profile list with stats
- **Danger Zone**: Reset preview (DON'T actually reset), profile deletion preview

**After 3f:** Report what worked, what failed.

### 3g. AI Features
If AI is available (from Phase 1 check), test:
1. Recipe remix (create variation)
2. Serving adjustment (scale up/down)
3. Tips generation (generate + display)
4. Discover favorites/seasonal/new
5. Search ranking (AI-ranked results)
6. Timer naming (descriptive labels)
7. Remix suggestions (contextual prompts)

If AI is NOT available: verify ALL AI UI elements are HIDDEN (not disabled) on every page visited.

**After 3g:** Report what worked, what failed.

### 3h. Dark Mode
- Toggle dark mode in settings
- Visit at least 5 representative pages — verify dark styles apply consistently
- Check for unstyled elements or contrast issues
- Toggle back to light mode and verify

**After 3h:** Report what worked, what failed.

### 3i. View History
- View a recipe, then check home page for "Recently Viewed"
- Verify ordering (most recent first)

**After 3i:** Report what worked, what failed.

**Phase 3 exit criteria:** All 9 subsections (3a-3i) tested and reported. Add all issues to ISSUES list.

---

## Phase 4: Log & Error Audit

**Task name:** "Phase 4: Log & Error Audit"

This is a SEPARATE phase from browser testing. Run these commands NOW even if you checked logs during earlier phases:

1. **Backend logs**: `docker compose logs web --tail=500` — look for:
   - Unhandled exceptions / tracebacks
   - 500 errors
   - Deprecation warnings
   - Database errors
   - Missing environment variables
2. **Frontend logs**: `docker compose logs frontend --tail=200` — look for:
   - Build warnings
   - TypeScript errors
   - HMR failures
3. **Aggregate browser console errors**: List ALL unique console errors collected across all pages
4. **Aggregate network failures**: List ALL failed requests collected across all pages

**Phase 4 exit criteria:** All 4 log sources reviewed. New issues added to ISSUES list.

---

## Phase 5: Issue Documentation

**Task name:** "Phase 5: Issue Documentation"

Compile ALL findings from phases 2-4 into a structured table. Output this table to the user.

| Column | Values |
|--------|--------|
| ID | Sequential (QA-001, QA-002, ...) |
| Severity | Critical / High / Medium / Low |
| Frontend | Modern / Legacy / Both |
| Category | Bug / UI-UX / Accessibility / Performance / Cross-frontend / Missing-feature |
| Page | Which page(s) affected |
| Description | What's wrong |
| Screenshot | Reference to screenshot file |
| Fix Status | Unfixed (to be updated in Phase 6) |

**Phase 5 exit criteria:** Complete issue table output with ALL issues from phases 2-4. No issue left undocumented.

---

## Phase 6: Fix Issues (if --fix)

**Task name:** "Phase 6: Fix Issues"

If `--fix` was NOT specified, skip to Phase 7 and mark all issues as "Audit-only — not fixed."

Otherwise, fix issues in this priority order:
1. Critical bugs (broken functionality, crashes)
2. Console errors and network failures
3. Accessibility issues
4. Cross-frontend inconsistencies
5. Layout/spacing problems
6. Design polish

**For EACH fix:**
1. Read the source file BEFORE editing
2. Make the fix
3. Test the fix (run relevant test suite or verify in browser)
4. Update the issue table — change Fix Status to "Fixed" or "Deferred" with reason

### For React (modern) fixes:
- Use the `/frontend-design` skill when implementing visual/UI improvements
- Run tests after: `docker compose exec frontend npm test`
- Run lint after: `docker compose exec frontend npm run lint`

### For legacy (ES5) fixes:
- **ES5 COMPLIANCE IS NON-NEGOTIABLE** — see Constitution Principle III
- Use the `/frontend-design` skill for CSS changes
- NO `const`/`let`, NO arrow functions, NO template literals, NO `async`/`await`, NO destructuring, NO spread, NO classes, NO `for...of`, NO modules
- After ANY legacy static file change: `docker compose down && docker compose up -d`
- Verify changes deployed: check file in `./staticfiles/`

### For backend fixes:
- Run tests: `docker compose exec web python -m pytest`
- Check lint: `docker compose exec web ruff check .`

### Risk management:
- If a fix is risky or ambiguous, document it as a recommendation — don't implement
- Test after every fix, not just at the end

**Phase 6 exit criteria:** Every issue addressed (fixed, deferred with reason, or marked needs-human-decision). Updated issue table output.

---

## Phase 7: Verification

**Task name:** "Phase 7: Verification"

After all fixes, verify the codebase is healthy:

### 7a. Re-test fixed pages
For each issue marked "Fixed" in Phase 6:
1. Navigate to the affected page in the browser
2. Take an "after" screenshot (save with `-fixed` suffix)
3. Verify the fix works
4. Check console errors on that page — target: zero new errors

### 7b. Run test suites
Run ALL of these (do not skip any):
- `docker compose exec frontend npm test`
- `docker compose exec web python -m pytest`

### 7c. Run linters
Run ALL of these (do not skip any):
- `docker compose exec frontend npm run lint`
- `docker compose exec web ruff check .`

### 7d. Final log check
- `docker compose logs web --tail=200` — check for new errors since Phase 4

**Phase 7 exit criteria:** All fixes verified, all test suites pass, all linters pass. Report pass/fail for each.

---

## Phase 8: Speckit Write-Up

**Task name:** "Phase 8: Speckit Write-Up"

Use speckit to formally document all QA work. Execute these skills IN ORDER, waiting for each to complete:

1. **`/speckit.specify`** — Create a spec covering all fixes and improvements made (or planned). Include:
   - What was found during the audit
   - What was fixed
   - What remains unfixed and why
2. **`/speckit.plan`** — Document the implementation approach for any remaining work. Use `/frontend-design` skill within the plan for visual/UI work.
3. **`/speckit.tasks`** — Generate task list. Mark completed tasks as done, leave remaining as TODO.
4. **`/speckit.analyze`** — Cross-check all artifacts for consistency.

**Phase 8 exit criteria:** All 4 speckit skills invoked and completed. Artifacts created in `.specify/` directory.

---

## Final Output

After ALL 8 phases are complete, output a final summary:

1. **Pre-flight status** — container health, AI availability
2. **Summary table** — all issues found with severity, category, frontend, and fix status (updated from Phase 6)
3. **Before/after screenshot pairs** — for visual changes
4. **Files modified** — with brief description of each change
5. **Log findings** — any backend/frontend log issues
6. **Remaining issues** — things that need human decision
7. **Recommendations** — future improvements
8. **Test results** — pass/fail for all test suites and linters
9. **Phase completion checklist:**
   - [ ] Phase 1: Pre-Flight Checks
   - [ ] Phase 2: Systematic Page Audit
   - [ ] Phase 3: Feature-Deep Testing
   - [ ] Phase 4: Log & Error Audit
   - [ ] Phase 5: Issue Documentation
   - [ ] Phase 6: Fix Issues
   - [ ] Phase 7: Verification
   - [ ] Phase 8: Speckit Write-Up

---

## Rules

- NEVER skip a phase — complete ALL 8 in order
- NEVER skip a page — visit every single one on every targeted frontend
- ALWAYS create a task for each phase and mark it done when complete
- ALWAYS output a phase completion summary before moving to the next phase
- ALWAYS take screenshots on every page visit
- ALWAYS check console errors AND network requests on every page
- ALWAYS check backend and frontend Docker logs in Phase 4 (even if you glanced at them earlier)
- ALWAYS ensure legacy JS is ES5-compliant (Constitution Principle III)
- ALWAYS restart containers after legacy static file changes
- ALWAYS run tests and linters in Phase 7 (not just when fixing)
- ALWAYS use `/frontend-design` skill for UI/visual improvements
- ALWAYS invoke all 4 speckit skills in Phase 8
- NEVER run Python/Node commands on host — Docker only
- If a fix is risky or ambiguous, document it as a recommendation instead of implementing

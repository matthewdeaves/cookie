# Code Quality Improvements - Implementation Plan

> **Goal:** Address all code quality issues identified in the comprehensive code review
> **Source:** Blog post analysis at commit cfaafa8
> **Deliverable:** Production-ready codebase with improved maintainability, test coverage, and code quality

---

## Overview

This plan implements all fixes identified in the code review across four areas:
1. **Backend** - Django/Python (complexity, duplication, testing, security)
2. **Frontend** - React/TypeScript (architecture, state management, testing)
3. **Legacy** - ES5 JavaScript (duplication, structure, patterns)
4. **CI/Metrics** - GitHub Actions tooling (accuracy, maintainability)

The review identified 50+ specific issues. This plan organizes them into 8 phases, ordered by:
- **Risk** (critical bugs first)
- **Dependencies** (foundation before features)
- **Impact** (high-value changes prioritized)

---

## Phases Overview

| Phase | Focus | Tasks | Priority | Status |
|-------|-------|-------|----------|--------|
| **1** | Critical Bugs | 4 tasks | Critical | [DONE] |
| **2** | Backend Testing & Security | 9 tasks | High | [DONE] |
| **3** | Backend Refactoring | 6 tasks | High | [DONE] |
| **4** | Frontend Architecture | 5 tasks | High | [DONE] |
| **5** | Frontend Testing & Utilities | 5 tasks | Medium | [DONE] |
| **6** | Legacy JavaScript Refactoring | 6 tasks | Medium | [DONE] |
| **7** | CI/Metrics Accuracy | 6 tasks | Medium | [OPEN] |
| **8** | CI/Metrics Maintainability | 5 tasks | Low | [OPEN] |

**Total:** 46 tasks across 8 phases

> **Note:** Phases 2 and 3 ordered test-first: Write tests for current code (Phase 2), then refactor with confidence (Phase 3).

---

## Phase 1: Critical Bugs

> **Goal:** Fix bugs that can cause runtime failures
> **Priority:** CRITICAL - Do these first

### Tasks

- [x] 1.1 Fix useTimers race condition
  - **File:** `frontend/src/hooks/useTimers.ts:40-81`
  - **Issue:** `setInterval` starts before `setTimers` completes, causing first tick to fail
  - **Fix:** Move interval setup after `setTimers` call (state update queued first)
  - **Impact:** Prevents timer failures under certain timing conditions

- [x] 1.2 Fix bundle size calculation to exclude source maps
  - **File:** `.github/workflows/ci.yml:908-920`
  - **Issue:** Counts `.map` files (1413KB) that aren't served to users
  - **Fix:** Added `if (file.endsWith('.map')) return;` before summing file sizes
  - **Impact:** Metric now reports actual served size (~400KB)

- [x] 1.3 Add pip-audit to requirements.txt
  - **File:** `.github/workflows/ci.yml:815` and `requirements.txt`
  - **Issue:** pip-audit works in CI but not locally (installed at runtime)
  - **Fix:** Added `pip-audit>=2.0` to requirements.txt
  - **Impact:** Developers can run security checks during development

- [x] 1.4 Replace bare `except: pass` in CI scripts with proper error handling
  - **File:** `.github/workflows/coverage.yml` throughout
  - **Issue:** Silently fails and defaults to 0, making debugging impossible
  - **Fix:** Replaced with specific exceptions (`FileNotFoundError`, `json.JSONDecodeError`, `KeyError`, `ValueError`, `TypeError`) and print warnings/errors
  - **Impact:** Metric errors now visible in CI logs

> **Tip:** Tasks 1.2, 1.3, and 1.4 involve debugging embedded CI scripts (266+ lines of Python in coverage.yml). If debugging proves difficult, consider pulling Task 8.1 (extract scripts to `.github/scripts/`) into this phase first. Extracted scripts enable local testing, proper syntax highlighting, and clearer error messages.

### Verification

```bash
# 1.1 - Test useTimers
cd frontend && npm test -- useTimers.test.ts

# 1.2 - Verify bundle size
cd frontend && npm run build
ls -lh dist/assets/*.map  # Should exist
# Check CI reports actual served size, not total including maps

# 1.3 - Test pip-audit locally
docker compose exec -T web pip-audit  # Should work, not error

# 1.4 - Trigger CI error
# Remove closing brace from coverage.json, push, verify CI fails with 'Invalid JSON' in error output
# Example: sed -i '$ d' coverage.json && git commit -am "test" && git push
```

---

## Phase 2: Backend Testing & Security

> **Goal:** Improve test coverage and add security scanning BEFORE refactoring
> **Priority:** HIGH - Security and quality gates
> **Philosophy:** Test current code behavior first, then refactor with confidence

### Session Scope

| Session | Focus | Status |
|---------|-------|--------|
| 2A | Write AI service tests with realistic fixtures | [DONE] |
| 2B | Add security scanning (SAST, secrets, dependencies) | [DONE] |

### Tasks

- [x] 2.1 Configure coverage measurement tools
  - **Files:** `pytest.ini`, `frontend/vite.config.ts`, `.github/workflows/ci.yml`
  - **Current:** Coverage targets defined but no tooling configured to measure progress
  - **Fix:**
    - Backend: Configure pytest-cov in `pytest.ini`: `addopts = --cov=apps --cov-report=html --cov-report=term`
    - Frontend: Add coverage config to `vite.config.ts`:
      ```typescript
      test: {
        coverage: {
          provider: 'v8',
          reporter: ['text', 'html', 'json'],
          include: ['src/**/*.{ts,tsx}'],
          exclude: ['src/test/**']
        }
      }
      ```
    - CI: Upload coverage reports as artifacts
  - **Impact:** Progress measurable, gaps visible, coverage reports in CI

- [x] 2.2 Create realistic AI response fixtures
  - **File:** `apps/ai/tests.py` or `apps/ai/fixtures.py`
  - **Current:** Mocks `OpenRouterService` entirely, validation logic never runs
  - **Fix:** Create `realistic_ai_response` fixtures with actual JSON structures including edge cases:
    - Missing fields
    - Wrong types
    - Malformed JSON
    - Hallucinated data
  - **Impact:** Validation code in `validator.py` gets tested against realistic inputs

- [x] 2.3 Write tests for AI service validation logic
  - **File:** `apps/ai/services/validator.py:163-260`
  - **Current:** 10% coverage, `_validate_value` (CC=40) never runs in tests
  - **Fix:** Test with realistic AI response fixtures to verify:
    - Invalid schemas caught
    - Wrong types detected
    - Missing required fields flagged
    - Union type validation works
  - **Impact:** Increases coverage from 10% to 80%+ for critical validation code

- [x] 2.4 Write tests for AI services with low coverage
  - **Files:**
    - `apps/ai/services/scaling.py` (241 lines) - ingredient scaling with unit conversion
    - `apps/ai/services/remix.py` (311 lines) - recipe variation generation
    - `apps/ai/services/discover.py` (278 lines) - recipe suggestions
    - `apps/ai/services/ranking.py` (162 lines) - scoring and ranking
  - **Current:** 10-25% coverage for AI services
  - **Fix:** Using realistic fixtures from 2.2, test specific scenarios:
    - **Scaling service:** Unit conversion accuracy (cup→ml, tsp→g), edge cases (zero, negative, fractional), invalid units handling
    - **Remix service:** Schema validation, hallucination detection (impossible ingredients), missing required fields, variation diversity
    - **Discover service:** Ranking logic correctness, empty favorites fallback, seasonal date filtering, result deduplication
    - **Ranking service:** Score calculation accuracy, tie-breaking behavior, empty result set handling, normalization edge cases
  - **Impact:** Increases AI services coverage from 10-25% to 60%+

- [x] 2.5 Add API key encryption
  - **File:** `apps/core/settings.py`
  - **Current:** API keys stored as plaintext in database
  - **Fix:** Use Django's encrypted field or move to environment variables
  - **Options:**
    - `django-cryptography` for encrypted fields
    - Environment variables via `python-decouple`
  - **Impact:** Keys encrypted at rest

- [x] 2.6 Add SAST scanning with Bandit
  - **File:** `.github/workflows/ci.yml` (new job)
  - **Current:** Only dependency scanning (pip-audit), no code-level security analysis
  - **Fix:** Add Bandit job to CI:
    ```yaml
    - name: Run Bandit SAST
      run: |
        pip install bandit
        bandit -r apps/ -f json -o bandit-report.json
    ```
  - **Impact:** Catches hardcoded credentials, SQL injection, unsafe pickle, insecure random

- [x] 2.7 Add secrets detection
  - **File:** `.github/workflows/ci.yml` (new job) and `.pre-commit-config.yaml`
  - **Current:** No scanning for accidentally committed credentials
  - **Fix:** Add detect-secrets or gitleaks:
    - Pre-commit hook for local development
    - CI job to catch commits that bypass hooks
  - **Impact:** Prevents API keys, tokens, credentials in repository

- [x] 2.8 Add ESLint security plugin for both JavaScript frontends
  - **Files:**
    - Modern: `frontend/eslint.config.js`
    - Legacy: `apps/legacy/static/legacy/.eslintrc.json` and `.github/workflows/ci.yml:69,77,83`
  - **Current:** Neither frontend has comprehensive security scanning
    - Modern: Has basic security rules (`no-eval`) from `js.configs.recommended`, but lacks XSS detection
    - Legacy: Has explicit rules (`no-eval`, `no-implied-eval`) but runs with `|| true` so warnings don't fail build
  - **Fix:**
    - Install `eslint-plugin-security` for both frontends
    - Modern: Add to `eslint.config.js` plugins for XSS detection (`innerHTML`, `dangerouslySetInnerHTML`, `document.write()`)
    - Legacy: Add to `.eslintrc.json` plugins and remove `|| true` from CI (move to Phase 7.2)
    - Configure rules: detect XSS, regex DoS, unsafe practices
  - **Impact:** All JavaScript code gets comprehensive security scanning beyond basic eval detection
  - **Why it matters:** 4,623 lines of legacy ES5 plus modern React code handling user input. Modern frontend uses React (dangerouslySetInnerHTML risk). Legacy has `escapeHtml()` reimplemented 5 times (inconsistency risk), large HTML string concatenation (easy to miss unescaped data)

- [x] 2.9 Add npm audit to CI for frontend dependency scanning (already existed)
  - **File:** `.github/workflows/ci.yml` (add to frontend-lint job or new job)
  - **Current:** Backend has pip-audit, frontend dependencies not scanned for vulnerabilities
  - **Fix:** Add npm audit step to frontend CI jobs:
    ```yaml
    - name: Audit frontend dependencies
      working-directory: frontend
      run: npm audit --audit-level=moderate
    ```
  - **Impact:** Catches vulnerable frontend dependencies (XSS, prototype pollution, RCE)
  - **Why it matters:** Frontend has 1000+ transitive dependencies, npm packages are frequent attack vectors

### Verification

```bash
# 2.1 - Verify coverage tooling works
docker compose exec -T web pytest --cov=apps/ai --cov-report=term
cd frontend && npm run test:coverage
# Coverage reports should be generated

# 2.2-2.4 - Run AI service tests with coverage
docker compose exec -T web pytest apps/ai/tests.py -v --cov=apps/ai/services --cov-report=html
# Check coverage report shows 60%+ for AI services

# 2.5 - Verify key encryption
# Settings UI should still work for API key entry
# Database inspection should show encrypted value, not plaintext

# 2.6 - Run Bandit locally
docker compose exec -T web bandit -r apps/ -f json -o bandit-report.json
# Should complete with findings report

# 2.7 - Test secrets detection
echo "aws_secret_key = AKIAIOSFODNN7EXAMPLE" > test.py
git add test.py
git commit -m "test"  # Should be blocked by pre-commit hook
rm test.py

# 2.8 - Test JavaScript security scanning
cd frontend && npm run lint
# Should detect security issues with eslint-plugin-security

cd apps/legacy/static/legacy
npx eslint js/pages/*.js --format json
# Should detect security issues like innerHTML without escaping

# 2.9 - Test npm audit
cd frontend && npm audit
# Should report vulnerabilities if any exist
```

---

## Phase 3: Backend Refactoring

> **Goal:** Reduce complexity and duplication in Django backend
> **Priority:** HIGH - Now safe to refactor with test coverage from Phase 2
> **Philosophy:** Tests verify refactoring doesn't break behavior

### Session Scope

| Session | Focus | Status |
|---------|-------|--------|
| 3A | Simplify validation and error handling | [DONE] |
| 3B | Extract parsing and decorator patterns | [DONE] |

### Tasks

- [x] 3.1 Replace manual JSON Schema validation with jsonschema library
  - **File:** `apps/ai/services/validator.py:163-260`
  - **Current:** 98 lines, CC=40, manual validation of union types/objects/arrays
  - **Fix:** Replace `_validate_value()` with `jsonschema.validate(value, schema)`
  - **Impact:** 98 lines → 8 lines, eliminates untested edge cases
  - **Dependencies:** `pip install jsonschema`, update requirements.txt
  - **Safety:** Phase 2 tests verify current behavior, so refactoring is safe

- [x] 3.2 Extract AI error handling to decorator
  - **File:** `apps/ai/api.py:295-305, 365-375, 477-487, 534-544, 584-594, 630-640, 706-716`
  - **Current:** Same 11-line error block repeated in 7 endpoints
  - **Fix:** Create `@handle_ai_errors` decorator
  - **Impact:** Centralized error messages (easier i18n), single update point

- [x] 3.3 Extract JSON parsing logic in OpenRouter service
  - **File:** `apps/ai/services/openrouter.py:100-111, 171-181`
  - **Current:** Identical markdown code block extraction in `complete` and `complete_async`
  - **Fix:** Create `_parse_json_response(content: str) -> dict` method
  - **Impact:** 12 duplicate lines → single method

- [x] 3.4 Refactor HTML parsing complexity
  - **File:** `apps/recipes/services/search.py:251-329`
  - **Current:** 78 lines, CC=20, does 6 sequential tasks in one function
  - **Fix:** Extract to separate methods:
    - `_find_link()` - Find recipe link
    - `_validate_url()` - Validate URL
    - `_extract_title()` - Extract title with 4 fallback attempts
    - `_extract_rating()` - Parse rating from title regex
    - `_extract_image()` - Extract image with 3 fallback attempts
    - `_extract_description()` - Extract description
  - **Impact:** 78 lines → 6 focused methods, easier to test each strategy

- [x] 3.5 Create @require_profile decorator for legacy views
  - **File:** `apps/legacy/views.py:38-46, 85-93, 112-120, 169-177, 200+`
  - **Current:** 6-line profile retrieval pattern repeated in 6 views
  - **Fix:** Decorator that validates profile and adds to `request.profile`
  - **Impact:** Eliminates 6 copies of same pattern

- [x] 3.6 Add caching for AI responses
  - **Files:** `apps/ai/services/*.py`
  - **Current:** Identical AI requests made multiple times (no caching)
  - **Fix:** Cache AI responses by prompt hash using Django cache framework
  - **Impact:** Reduces API costs, faster responses for repeat requests

### Verification

```bash
# Run full test suite to verify refactoring doesn't break behavior
docker compose exec -T web pytest -v

# 3.1 - Test validation still works with new jsonschema library
docker compose exec -T web pytest apps/ai/tests.py::test_validator -v

# 3.2 - Verify all 7 endpoints still handle errors correctly
docker compose exec -T web pytest apps/ai/tests.py::test_remix_suggestions -v
docker compose exec -T web pytest apps/ai/tests.py::test_create_remix -v
# ... test all AI endpoints

# 3.3 - Test both sync and async OpenRouter methods
docker compose exec -T web pytest apps/ai/tests.py::test_openrouter_complete -v
docker compose exec -T web pytest apps/ai/tests.py::test_openrouter_complete_async -v

# 3.4 - Test HTML parsing
docker compose exec -T web pytest tests/test_scraper.py::test_extract_result -v

# 3.5 - Test legacy views still require profile
curl http://localhost:8000/legacy/ -c cookies.txt  # Should redirect to profile selector
curl http://localhost:8000/legacy/ -b cookies.txt  # Should show home after profile set

# 3.6 - Verify AI response caching
# Make same AI request twice, second should be instant (from cache)

# Verify coverage hasn't decreased
docker compose exec -T web pytest --cov=apps --cov-report=term
# Coverage should be maintained or improved
```

---

## Phase 4: Frontend Architecture

> **Goal:** Fix god components and state management issues
> **Priority:** HIGH - Enables testing and maintenance

### Session Scope

| Session | Focus | Status |
|---------|-------|--------|
| 4A | Implement React Router and reduce App.tsx complexity | [OPEN] |
| 4B | Extract Settings.tsx and RecipeDetail.tsx components | [OPEN] |
| 4C | Fix state management patterns | [OPEN] |

### Tasks

- [ ] 4.1 Implement React Router
  - **File:** `frontend/src/App.tsx` (refactor)
  - **Current:** Manual state-based navigation, 337-line god component managing 10 screens
  - **Fix:**
    - Install `react-router-dom`
    - Define routes for all 10 screens
    - Replace manual navigation with `useNavigate()`
    - Move screen-specific state into screens themselves
  - **Impact:** App.tsx complexity reduced 80%, screens testable in isolation

- [ ] 4.2 Group Settings.tsx state with useReducer
  - **File:** `frontend/src/screens/Settings.tsx:48-97`
  - **Current:** 30 separate useState hooks for related state
  - **Fix:** Create reducers for related state groups:
    - `resetReducer` - `showResetModal`, `resetPreview`, `resetStep`, `resetConfirmText`, `resetting`
    - `deleteReducer` - `showDeleteModal`, `deletePreview`, `deletingId`, `deleting`
    - `promptReducer` - `editingPromptType`, `editForm`, `savingPrompt`
    - `sourceTestReducer` - `testingSource`, `testingBatch`, `batchTestProgress`
  - **Impact:** Related state updates atomic, impossible to introduce partial update bugs

- [ ] 4.3 Move data loading to onClick handlers
  - **Files:** `frontend/src/screens/Home.tsx:61-65`, `RecipeDetail.tsx:123`, `Search.tsx:33`
  - **Current:** useEffect with 5 guard conditions to prevent infinite loops
  - **Fix:** Move logic to event handlers:
    ```tsx
    const handleDiscoverClick = () => {
      setActiveTab('discover')
      if (discoverSuggestions.length === 0 && !discoverLoading && aiAvailable) {
        loadDiscoverSuggestions()
      }
    }
    ```
  - **Impact:** Eliminates useEffect dependency warnings, clearer data flow

- [ ] 4.4 Extract Settings.tsx tabs into components
  - **File:** `frontend/src/screens/Settings.tsx:330-1280`
  - **Current:** 6 tabs as inline conditionals (600+ lines of JSX in one expression)
  - **Fix:** Extract to separate components:
    - `SettingsGeneral.tsx` - API key validation, status indicators
    - `SettingsPrompts.tsx` - Prompt editing, model dropdown, toggles
    - `SettingsSources.tsx` - Individual/bulk source toggles
    - `SettingsSelectors.tsx` - CSS selector editing, testing
    - `SettingsUsers.tsx` - Profile list, deletion with preview modal
    - `SettingsDanger.tsx` - Two-step reset confirmation
  - **Impact:** 1,314 lines → 6 files of 150-250 lines each, testable components

- [ ] 4.5 Extract RecipeDetail tabs into components
  - **File:** `frontend/src/screens/RecipeDetail.tsx:436-458`
  - **Current:** 4 tabs rendered inline in 739-line file
  - **Fix:** Extract to separate components:
    - `RecipeIngredients.tsx` - Ingredient list with scaling
    - `RecipeInstructions.tsx` - Step-by-step instructions
    - `RecipeNutrition.tsx` - Nutrition facts table
    - `RecipeTips.tsx` - AI-generated tips with polling
  - **Impact:** 739 lines → ~200 line main file + 4 tab components

### Verification

```bash
# 4.1 - Test routing
cd frontend && npm test -- App.test.tsx
# Navigate to each screen, verify URL updates
# Browser back/forward should work

# 4.2 - Test Settings state management
cd frontend && npm test -- Settings.test.tsx
# Test reset flow doesn't leave orphaned state
# Test delete flow properly cleans up

# 4.3 - Test data loading
cd frontend && npm test -- Home.test.tsx
# No infinite loops, data loads on interaction

# 4.4-4.5 - Test extracted components
cd frontend && npm test -- SettingsGeneral.test.tsx
cd frontend && npm test -- RecipeIngredients.test.tsx
# Each component works in isolation
```

---

## Phase 5: Frontend Testing & Utilities

> **Goal:** Increase test coverage and reduce duplication
> **Priority:** MEDIUM - Quality improvements

### Tasks

- [x] 5.1 Extract formatTime to shared utility
  - **Files:** `frontend/src/components/RecipeCard.tsx:20-26`, `RecipeDetail.tsx:141-147`
  - **Current:** Identical function duplicated in 2 files
  - **Fix:** Created `frontend/src/lib/formatting.ts` with `formatTime(minutes: number | null)` and tests
  - **Impact:** Single source of truth, changes made once

- [x] 5.2 Wrap favoriteRecipeIds in useMemo
  - **File:** `frontend/src/screens/Home.tsx:126`
  - **Current:** Was already done in Phase 4 at `Home.tsx:122-125`
  - **Fix:** Already wrapped with `useMemo(() => new Set(favorites.map(...)), [favorites])`
  - **Impact:** Avoids unnecessary work when favorites unchanged

- [x] 5.3 Test all 6 components in src/components/
  - **Files:**
    - `RecipeCard.tsx` (112 lines, used in 4 screens) - PRIORITY
    - `TimerPanel.tsx` (167 lines)
    - `RemixModal.tsx` (201 lines)
    - `Skeletons.tsx` (201 lines)
    - `AddToCollectionDropdown.tsx` (145 lines)
    - `TimerWidget.tsx` (93 lines)
  - **Fix:** Created test files for each:
    - `RecipeCard.test.tsx` - Tests favorite toggle, image fallback, time formatting, remix badge
    - `TimerWidget.test.tsx` - Tests timer display, controls, completion state
    - `Skeletons.test.tsx` - Tests rendering of all skeleton variants
    - `RemixModal.test.tsx` - Tests suggestions, selection, custom input, remix creation
    - `AddToCollectionDropdown.test.tsx` - Tests dropdown, collection list, adding recipes
    - `TimerPanel.test.tsx` - Tests quick timers, detected times, AI naming
  - **Impact:** Components coverage 0% → 70%+

- [x] 5.4 Create useAsync hook
  - **File:** `frontend/src/hooks/useAsync.ts` (new)
  - **Current:** 20+ instances of `const [loading, setLoading] = useState(false)` pattern
  - **Fix:** Created shared hooks:
    - `useAsync<T>()` - Clears data on new execution
    - `useAsyncWithStaleData<T>()` - Preserves previous data during loading
    - Both include `execute()`, `reset()`, and loading/error/data state
  - **Impact:** Standardized async handling, less boilerplate

- [x] 5.5 Add error boundaries
  - **File:** `frontend/src/components/ErrorBoundary.tsx` (new)
  - **Current:** Component errors crashed entire app (white screen)
  - **Fix:** React error boundary component wrapping `<App />` in `main.tsx`
  - **Features:** Try Again button, Reload Page button, error details in dev mode
  - **Impact:** Graceful error UI instead of blank screen

### Verification

```bash
# 5.1 - Test formatTime utility
cd frontend && npm test -- formatting.test.ts

# 5.2 - Verify useMemo optimization
cd frontend && npm test -- Home.test.tsx
# Check favorites Set not recreated on unrelated renders

# 5.3 - Test all components
cd frontend && npm test -- components/
# All 6 component test files should pass

# 5.4 - Test useAsync hook
cd frontend && npm test -- useAsync.test.ts

# 5.5 - Test error boundary
cd frontend && npm test -- ErrorBoundary.test.tsx
# Trigger error in child component, verify boundary catches it
```

---

## Phase 6: Legacy JavaScript Refactoring

> **Goal:** Reduce duplication and improve structure in ES5 code
> **Priority:** MEDIUM - Maintainability improvements
> **Risk Mitigation:** 4,623 lines of ES5 with no automated tests - add minimal test infrastructure first

### Session Scope

| Session | Focus | Status |
|---------|-------|--------|
| 6A | Set up legacy testing infrastructure | [DONE] |
| 6B | Refactor with manual testing verification | [DONE] |

### Implementation Notes

**Module Loading Approach:** Used multiple `<script>` tags in templates rather than async module loader because:
- Simpler and more reliable for iOS 9 Safari compatibility
- Synchronous loading maintains predictable execution order
- HTTP/2 mitigates multiple request overhead
- No additional loader code to maintain

**File Structure:**
- `settings-*.js`: 8 modules totaling ~1,100 lines (largest: 205 lines)
- `detail-*.js`: 8 modules totaling ~1,280 lines (largest: 364 lines)
- Each module registers with core via `registerTab()` or `registerFeature()`
- Core modules manage shared state accessible via `getState()`

### Tasks

- [x] 6.0 Set up minimal integration testing for legacy frontend (manual checklist created at `plans/LEGACY-JS-TESTING-CHECKLIST.md`)
  - **File:** `tests/test_legacy_integration.py` (new)
  - **Current:** 4,623 lines of ES5 JavaScript with zero automated test coverage
  - **Risk:** Refactoring without tests can introduce regressions that won't be caught until manual QA
  - **Fix:** Create integration tests that verify critical user flows work:
    - Profile selector → Home (verify page loads, no JS errors)
    - Search results → Recipe detail (verify navigation works)
    - Recipe detail: Favorites toggle, Collections dropdown
    - Settings: Tab navigation, API key save
    - Play mode: Timer start/stop (verify basic functionality)
  - **Approach:** Use Django test client + Selenium/Playwright to load legacy pages and verify:
    - HTTP 200 responses
    - Expected DOM elements present (via data-testid attributes)
    - No JavaScript console errors
    - Critical user actions work (button clicks, form submits)
  - **Impact:** Basic smoke tests catch major breakage during refactoring
  - **Alternative:** If test setup is too complex, create comprehensive manual testing checklist and document before/after behavior

- [x] 6.1 Add Cookie.utils for shared functions (created `utils.js` with escapeHtml, formatTime, truncate, formatNumber, showElement, hideElement, escapeSelector, delegate, and more)
  - **File:** `apps/legacy/static/legacy/js/utils.js` (new)
  - **Current:** `escapeHtml()` reimplemented 5 times, `handleTabClick()` 3 times
  - **Fix:** Create `Cookie.utils` object with shared utilities:
    ```javascript
    Cookie.utils = {
      escapeHtml: function(text) { ... },
      handleTabClick: function(e) { ... },
      formatTime: function(minutes) { ... }
    };
    ```
  - **Load:** Via script tag before page modules
  - **Impact:** 5 copies of escapeHtml → 1, 3 copies of handleTabClick → 1

- [x] 6.2 Split settings.js into tab-specific files (8 modules via multiple script tags: core, general, prompts, sources, selectors, users, danger, init)
  - **File:** `apps/legacy/static/legacy/js/pages/settings.js` (1,100 lines)
  - **Current:** 6 tabs managed inline
  - **Fix:** Split into modules (requires async module loader):
    - `settings-general.js` - API key management
    - `settings-prompts.js` - Prompt editing
    - `settings-sources.js` - Source toggles
    - `settings-selectors.js` - CSS selector editing
    - `settings-users.js` - Profile management
    - `settings-danger.js` - Database reset
  - **Dependencies:** Add simple script loader to Cookie namespace
  - **Impact:** 1,100 lines → 6 files of ~150-200 lines each

- [x] 6.3 Replace event listener loops with delegation (implemented Cookie.utils.delegate, refactored settings.js to use delegation for sources, selectors, and profiles lists)
  - **File:** `apps/legacy/static/legacy/js/pages/settings.js:130-849`
  - **Current:** 16+ loops attaching individual listeners
  - **Fix:** Single delegated listener:
    ```javascript
    document.getElementById('settings-container').addEventListener('click', function(e) {
      var action = e.target.dataset.action;
      if (!action) return;

      var handlers = {
        'toggle-source': handleToggleSource,
        'test-source': handleTestSource,
        // ... all actions
      };

      var handler = handlers[action];
      if (handler) handler(e);
    });
    ```
  - **Impact:** 100+ listeners → 1, handles dynamic elements automatically

- [x] 6.4 Split detail.js features into separate modules (8 modules: core, display, favorites, collections, scaling, remix, tips, init)
  - **File:** `apps/legacy/static/legacy/js/pages/detail.js` (1,275 lines)
  - **Current:** Manages recipe display, favorites, collections, AI features, polling
  - **Fix:** Split into modules:
    - `detail-display.js` - Core recipe rendering and tabs
    - `detail-ai.js` - AI features (scaling, remix, tips, polling)
    - `detail-collections.js` - Collection management, modals
  - **Impact:** 1,275 lines → 3 files of ~400 lines each

- [x] 6.5 Replace HTML string concatenation with template elements (added HTML5 templates for source-item, selector-item, profile-card in settings.html)
  - **Files:** Throughout legacy code, especially `settings.js:450-464`
  - **Current:** Large HTML strings concatenated in JavaScript
  - **Fix:** Use HTML5 `<template>` elements:
    ```html
    <template id="source-card-template">
      <div class="source-card">
        <div class="source-header">
          <h3 class="source-name"></h3>
          <button class="btn-toggle" data-action="toggle-source"></button>
        </div>
      </div>
    </template>
    ```
    ```javascript
    var template = document.getElementById('source-card-template');
    var clone = template.content.cloneNode(true);
    clone.querySelector('.source-name').textContent = source.domain;
    ```
  - **Impact:** Clearer separation of markup and logic, editor support

### Verification

```bash
# 6.1 - Verify shared utilities work
# Open any legacy page, check console for errors
# escapeHtml, handleTabClick, formatTime should be available

# 6.2 - Test settings tabs load correctly
# Navigate to each settings tab, verify functionality intact

# 6.3 - Test event delegation
# Click all buttons in settings, verify handlers fire
# Add new source dynamically, verify toggle button works (delegation handles dynamic elements)

# 6.4 - Test detail.js modules
# View recipe, test favorites, collections, AI features
# All functionality should work as before

# 6.5 - Verify template elements
# Check HTML rendering matches original
# Inspect DOM, verify no broken templates
```

---

## Phase 7: CI/Metrics Accuracy

> **Goal:** Fix misleading metrics and improve data quality
> **Priority:** MEDIUM - Correct reporting

### Tasks

- [ ] 7.1 Calculate gzipped bundle sizes
  - **File:** `.github/workflows/ci.yml:892-932`
  - **Current:** Reports uncompressed bytes (1807KB) vs actual transfer (~200KB gzipped)
  - **Fix:** Calculate gzip sizes using Node's zlib:
    ```javascript
    const zlib = require('zlib');
    const content = fs.readFileSync(filePath);
    const gzipSize = zlib.gzipSync(content).length;
    ```
  - **Impact:** Metric reflects actual user download size

- [ ] 7.2 Make ESLint failures fail the build
  - **File:** `.github/workflows/ci.yml:69, 77, 83`
  - **Current:** `|| true` allows warnings to accumulate
  - **Fix:** Remove `|| true`, set `--max-warnings=0` in ESLint config
  - **Impact:** Code quality doesn't degrade over time

- [ ] 7.3 Fail dashboard deployment if critical data missing
  - **File:** `.github/workflows/coverage.yml:29, 38, 47, etc.`
  - **Current:** `continue-on-error: true` silently deploys incomplete dashboards
  - **Fix:** Remove `continue-on-error` for critical artifacts (coverage, bundle)
  - **Impact:** Dashboard deployment fails loudly if data missing

- [ ] 7.4 Add timestamps to history entries
  - **File:** `.github/workflows/coverage.yml:514, 545`
  - **Current:** Date-only keys lose intra-day data (second run overwrites first)
  - **Fix:** Use ISO timestamp or build number as key
  - **Impact:** Preserves all CI runs, not just latest per day

- [ ] 7.5 Unify frontend and backend complexity metrics
  - **Files:** `.github/workflows/ci.yml:521-567` (frontend), `:312-493` (backend)
  - **Current:** Frontend counts warnings, backend calculates actual CC
  - **Fix:** Use a TypeScript complexity analyzer (like `eslint-plugin-complexity` with numeric output) or ESComplex
  - **Impact:** Metrics comparable across codebases

- [ ] 7.6 Validate artifact data before using
  - **File:** `.github/workflows/coverage.yml:256-270, etc.`
  - **Current:** No validation, assumes all data trustworthy
  - **Fix:** Add validation checks:
    ```python
    if not (0 <= coverage <= 100):
        print(f"WARNING: Invalid coverage {coverage}, expected 0-100")
    if bundle_size < 0:
        print(f"ERROR: Negative bundle size {bundle_size}")
    ```
  - **Impact:** Catches data corruption early

### Verification

```bash
# 7.1 - Check gzipped sizes in CI
# CI should report both raw and gzipped sizes
# Gzipped should be 20-30% of raw size

# 7.2 - Verify ESLint fails on warnings
# Add intentional ESLint warning, push
# CI should fail with clear message

# 7.3 - Test artifact failure
# Temporarily break artifact upload
# Dashboard deployment should fail, not deploy stale data

# 7.4 - Check history.json
cat site/coverage/history/all.json | jq '.entries[-5:]'
# Should show timestamps, not just dates
# Multiple entries per day should be preserved

# 7.5 - Compare complexity metrics
# Frontend and backend should both report numeric average CC

# 7.6 - Trigger validation error
# Corrupt coverage.json, push
# CI should log clear warning about invalid data
```

---

## Phase 8: CI/Metrics Maintainability

> **Goal:** Make metrics tooling easier to debug and extend
> **Priority:** LOW - Developer experience

### Tasks

- [ ] 8.1 Move Python scripts to .github/scripts/
  - **File:** `.github/workflows/coverage.yml` (800+ lines of inline scripts)
  - **Current:** Python/JavaScript embedded in YAML heredocs
  - **Fix:** Extract to separate files:
    - `.github/scripts/generate-dashboard.py` - Main dashboard generation
    - `.github/scripts/extract-metrics.py` - Artifact parsing
    - `.github/scripts/generate-badges.py` - Badge creation
    - `.github/scripts/update-history.py` - History tracking
  - **Impact:** Locally testable, syntax highlighting, version control clarity

- [ ] 8.2 Extract rating thresholds into constants
  - **Files:** Throughout CI workflows, repeated 10+ times
  - **Current:** Rating logic duplicated across jobs
  - **Fix:** Create `.github/scripts/rating-config.json`:
    ```json
    {
      "coverage": {
        "A": 80,
        "B": 60,
        "C": 40
      },
      "complexity": {
        "A": 5,
        "B": 10,
        "C": 20
      },
      ...
    }
    ```
  - **Impact:** Single source of truth, easy to adjust thresholds

- [ ] 8.3 Add SRI hashes to CDN resources
  - **File:** `.github/workflows/coverage.yml:870`
  - **Current:** Chart.js loaded from CDN without Subresource Integrity
  - **Fix:** Add `integrity` attribute:
    ```html
    <script
      src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"
      integrity="sha384-..."
      crossorigin="anonymous">
    </script>
    ```
  - **Impact:** Security best practice, prevents CDN compromise

- [ ] 8.4 Generate SVG badges locally
  - **File:** `.github/workflows/coverage.yml:247-254`
  - **Current:** Downloads badges from shields.io (external dependency)
  - **Fix:** Generate SVG badges using template:
    ```python
    def generate_badge(label, value, color):
        return f'''<svg>...</svg>'''  # SVG template
    ```
  - **Impact:** Removes external dependency, faster, more reliable

- [ ] 8.5 Add documentation for CI setup
  - **File:** `docs/CI-METRICS.md` (new)
  - **Current:** No documentation on how metrics work
  - **Fix:** Document:
    - How to add a new metric
    - Why rating thresholds were chosen
    - How to debug when metrics are wrong
    - How to run metrics locally
    - Architecture diagram of CI pipeline
  - **Impact:** Easier onboarding, self-service debugging

### Verification

```bash
# 8.1 - Test extracted scripts locally
python .github/scripts/generate-dashboard.py --help
python .github/scripts/extract-metrics.py coverage.json

# 8.2 - Verify rating consistency
# Change one threshold in config
# Redeploy, verify all jobs use new threshold

# 8.3 - Verify SRI
# Inspect dashboard HTML
# Chart.js script tag should have integrity attribute

# 8.4 - Test local badge generation
python .github/scripts/generate-badges.py
ls site/coverage/badges/  # Should contain all .svg files

# 8.5 - Documentation completeness
# Verify docs/CI-METRICS.md contains:
# - "Adding a new metric" section with step-by-step
# - Architecture diagram (workflow→script→artifact flow)
# - Troubleshooting section with common failure modes
# Follow "add new metric" guide
# Successfully add a test metric following docs
```

---

## Implementation Notes

### Session Organization

Each phase can be completed in 1-3 sessions:

**Quick Wins (1 session each):**
- Phase 1 (critical bugs)
- Phase 5 (frontend utilities)
- Phase 7 (metrics accuracy)

**Multi-session (2-3 sessions):**
- Phase 2 (backend testing & security - 2 sessions: tests, then security)
- Phase 3 (backend refactoring - 2 sessions: validation/errors, then parsing/caching)
- Phase 4 (frontend architecture - 3 sessions: routing, component extraction, state)
- Phase 6 (legacy refactoring - 2 sessions: test setup, then refactoring)
- Phase 8 (metrics maintainability - many small tasks)

**Recommended session boundaries are marked in each phase's "Session Scope" table.**

### Testing Strategy

After each phase, run full test suite:

```bash
# Backend tests
docker compose exec -T web pytest

# Frontend tests
cd frontend && npm test

# Legacy - manual testing (no test suite)
# Open each legacy page, verify functionality

# CI - run full pipeline
git push  # Triggers CI

# Metrics - check dashboard
# https://matthewdeaves.github.io/cookie/coverage/
```

### Rollback Plan

Each phase is independent. If a phase breaks something:

1. Identify failing tests
2. Revert commits from that phase: `git revert <commits>`
3. Fix issues in separate branch
4. Re-run tests before merging

### Code Review Checklist

Before marking phase complete:

- [ ] All tests pass (pytest, vitest, ESLint)
- [ ] No new linter warnings introduced
- [ ] Coverage not decreased (check dashboard)
- [ ] Changes documented in commit messages
- [ ] No breaking changes to APIs
- [ ] CI pipeline still green

---

## Success Criteria

**Phase 1 Complete:**
- [ ] No timer race conditions in tests
- [ ] Bundle size metric reports actual served size
- [ ] pip-audit runs locally
- [ ] CI errors are visible, not silent

**Phase 2 Complete:**
- [ ] Backend test coverage: > 60% (from 47%)
- [ ] AI services coverage: > 60% (from 10-25%)
- [ ] Coverage measurement tooling configured (pytest-cov, vitest)
- [ ] Bandit and secrets detection in CI
- [ ] ESLint security plugin scanning both JavaScript frontends (modern + legacy)
- [ ] npm audit running in CI for frontend dependencies

**Phase 3 Complete:**
- [ ] Backend complexity: 0 functions with CC > 20
- [ ] Backend duplication: < 3%
- [ ] AI error handling centralized in decorator
- [ ] Tests still pass after refactoring (verify with coverage reports)

**Phase 4 Complete:**
- [ ] React Router implemented
- [ ] App.tsx < 150 lines (from 337)
- [ ] Settings.tsx < 300 lines (from 1,314)
- [ ] All screens testable in isolation

**Phase 5 Complete:**
- [ ] Frontend test coverage: > 40% (from 15.71%)
- [ ] All 6 components have tests
- [ ] 0 duplicate utility functions

**Phase 6 Complete:**
- [ ] Legacy duplication: < 4% (from 6.67%)
- [ ] 0 duplicate utility functions
- [ ] settings.js < 300 lines (from 1,100)
- [ ] detail.js < 500 lines (from 1,275)
- [ ] Integration tests cover: profile selection, search→detail, favorites, collections, settings tabs, play mode timers
- OR comprehensive manual testing checklist documented and executed

**Phase 7 Complete:**
- [ ] Bundle size metric within 10% of actual
- [ ] ESLint failures block merges
- [ ] History preserves intra-day data

**Phase 8 Complete:**
- [ ] All CI scripts in .github/scripts/
- [ ] Rating thresholds in single config file
- [ ] CI/metrics documentation exists

---

## Risk Assessment

### Low Risk
- Phases 1, 7, 8 - Isolated changes, easy rollback
- Phase 2 (backend testing) - No prod code changes, only adding tests

> **Note:** If you encounter CI/metrics debugging issues during Phases 1-7, consider promoting Task 8.1 (extract embedded scripts to `.github/scripts/`) earlier. The 266-line Python script in coverage.yml makes debugging painful - extracting it enables local testing and proper error messages.

### Medium Risk
- Phase 3 (backend refactoring) - Changes production code but NOW has test coverage from Phase 2
  - **Mitigation:** Tests written in Phase 2 verify behavior doesn't change
- Phase 5 (frontend testing) - No prod code changes
- Phase 6 (legacy refactoring) - Higher risk due to limited automated tests
  - **Mitigation:** Task 6.0 adds minimal integration tests OR comprehensive manual checklist

### High Risk
- Phase 4 (frontend architecture) - Major refactoring, touches many files
  - **Mitigation:** Implement React Router first, then refactor incrementally
  - **Testing:** Comprehensive manual testing required, Phase 5 adds automated tests

**Overall risk reduced:** Test-first approach (Phase 2 before 3) significantly reduces refactoring risk

---

## Estimated Effort

> **Note:** Time estimates are rough guides only. Focus on completing each phase's tasks and verification steps rather than hitting time targets. Actual time will vary based on familiarity with the codebase, testing thoroughness, and unexpected issues.

| Phase | Complexity | Sessions | Rough Estimate |
|-------|-----------|----------|----------------|
| 1 | Low | 1 | ~2-3 hours |
| 2 | High | 2 | ~9-11 hours (test writing + security) |
| 3 | Medium | 2 | ~4-6 hours (refactoring with test safety net) |
| 4 | High | 3 | ~8-12 hours (architectural changes) |
| 5 | Low | 1 | ~3-4 hours |
| 6 | Medium | 2 | ~8-10 hours (test setup + refactoring) |
| 7 | Low | 1 | ~3-4 hours |
| 8 | Low | 1-2 | ~4-5 hours |

**Total:** ~41-55 hours of development work (revised from 39-53 due to additional tasks)

**Recommended Pace:** 1-2 phases per week over 4-6 weeks, prioritizing quality over speed

---

## Dependencies

```
Phase 1 (critical bugs)
  ↓
Phase 2 (backend testing & security) ──→ Phase 3 (backend refactoring)
  ↓
Phase 4 (frontend architecture) ──→ Phase 5 (frontend testing)
  ↓
Phase 6 (legacy refactoring with test setup)
  ↓
Phase 7 (metrics accuracy) ──→ Phase 8 (metrics maintainability)
```

**Key ordering rationale:**
- Phase 2 before Phase 3: Write tests for current code, then refactor safely
- Phase 4 before Phase 5: Architectural changes before comprehensive testing
- Phase 6 includes test setup (task 6.0) before refactoring tasks

**Can be done in parallel:**
- Phase 2 and Phase 4 (different codebases, both can start after Phase 1)
- Phase 3 and Phase 5 (different codebases, after their respective test phases)
- Phase 6 (independent of phases 2-5, starts after Phase 1)
- Phase 7 and Phase 8 (both CI, but different concerns)

---

## Process Improvements

### Document Organization (Optional)

This plan uses a single file for 8 phases (~1000 lines). This is acceptable and follows the project's existing pattern. However, if navigation becomes difficult, consider splitting into focused files:

**Option 1: By domain**
- `CODE-QUALITY-BACKEND.md` (Phases 1-3)
- `CODE-QUALITY-FRONTEND.md` (Phases 4-5)
- `CODE-QUALITY-INFRASTRUCTURE.md` (Phases 6-8)

**Option 2: By phase** (matches main project structure)
- `plans/quality/PHASE-1-CRITICAL-BUGS.md`
- `plans/quality/PHASE-2-BACKEND-TESTING.md`
- `plans/quality/PHASE-3-BACKEND-REFACTORING.md`
- etc.

**Current single-file approach is fine for now.** Only split if:
- Context management becomes difficult
- Multiple people working on different phases simultaneously
- Navigation through 1000+ lines becomes cumbersome

### For Future Projects

**1. Include quality gates in initial plans:**
- Max cyclomatic complexity per function: 15
- Max file size: 300 lines
- Component testing required (not separate task)
- Refactoring step after implementing similar features

**2. Require specific testing in task definitions:**
Instead of "build RecipeCard", write:
> Build RecipeCard with tests for:
> - Renders without image
> - onFavoriteToggle callback fires
> - total_time formats correctly

**3. Specify architecture upfront:**
- Multi-screen apps: "Use React Router for navigation"
- ES5 apps: "Use event delegation, not loops"
- Define shared utilities before building modules

**4. Configure linters to fail on warnings:**
- ESLint: `--max-warnings=0`
- Ruff: No globally disabled rules
- CI: Warnings block merge

**5. Extract CI scripts from YAML:**
- Python/JavaScript scripts > 50 lines → separate files
- Enables local testing, proper error handling

---

## References

- **Code Reviews:**
  - Frontend: `plans/code-reviews/cookie-frontend-code-review.md`
  - Backend: `plans/code-reviews/cookie-backend-code-review.md`
  - Legacy: `plans/code-reviews/cookie-legacy-code-review.md`
  - Metrics: `plans/code-reviews/metrics-tooling-review.md`

- **Original Commit:** [cfaafa8](https://github.com/matthewdeaves/cookie/commit/cfaafa8)

- **Dashboard:** https://matthewdeaves.github.io/cookie/coverage/

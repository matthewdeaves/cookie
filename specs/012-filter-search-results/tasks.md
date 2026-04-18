# Tasks: Filter Non-Recipe Search Results

**Input**: Design documents from `/specs/012-filter-search-results/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

**Tests**: Test tasks included as this feature modifies filtering logic that could cause regressions.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup

**Purpose**: Refactor existing URL filtering to expose signal strength, enabling tiered resolution

- [x] T001 Refactor `looks_like_recipe_url()` to extract a new `get_url_signal()` function that returns signal strength ("strong_exclude", "strong_include", "neutral") in `apps/recipes/services/search_parsers.py`
- [x] T002 Update `looks_like_recipe_url()` to call `get_url_signal()` and return bool for backward compatibility in `apps/recipes/services/search_parsers.py`

**Checkpoint**: Existing URL filtering behavior unchanged, but signal strength is now available internally

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add the title analysis function that all user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Add compiled regex patterns for editorial title exclusion (`_EDITORIAL_TITLE_PATTERNS`) at module level in `apps/recipes/services/search_parsers.py` — patterns for listicles, travel, reviews, news, and meta/navigation titles
- [x] T004 Add compiled regex pattern for recipe-context override words (`_RECIPE_CONTEXT_PATTERN`) at module level in `apps/recipes/services/search_parsers.py` — words like "recipe", "cook", "bake", "make", "homemade", "ingredient", "how to"
- [x] T005 Implement `looks_like_recipe_title(title: str, url_signal: str) -> bool` function in `apps/recipes/services/search_parsers.py` — tiered resolution: strong_include URLs pass, neutral URLs evaluated by title patterns, recipe-context words override editorial patterns
- [x] T006 Integrate `looks_like_recipe_title()` into `extract_result_from_element()` in `apps/recipes/services/search_parsers.py` — call after title extraction, pass URL signal from `get_url_signal()`, return None with debug log if title filtered
- [x] T007 Add debug logging for filtered-out results in `extract_result_from_element()` in `apps/recipes/services/search_parsers.py` — log title, URL, and filter reason at debug level

**Checkpoint**: Foundation ready — title filtering is active in the search pipeline

---

## Phase 3: User Story 1 — Recipe Searches Return Only Importable Recipes (Priority: P1) 🎯 MVP

**Goal**: Food-related searches return only actual recipes, no editorial content

**Independent Test**: Search for 10 common recipe terms and verify every result can be imported

### Tests for User Story 1

- [x] T008 [P] [US1] Add unit tests for `get_url_signal()` in `tests/test_search_parsers.py` — test strong_exclude URLs (e.g., /article/foo), strong_include URLs (e.g., /recipe/foo), and neutral URLs (slug-style)
- [x] T009 [P] [US1] Add unit tests for `looks_like_recipe_title()` in `tests/test_search_parsers.py` — test legitimate recipe titles pass ("Chicken Tagine", "Pasta Carbonara", "TikTok Feta Pasta"), editorial titles with neutral URLs are rejected ("Google's Top Trending Recipe of 2024 Deserves a Gold Medal"), and recipe-context words override editorial patterns ("Top 10 Easy Cookie Recipes")
- [x] T010 [P] [US1] Add unit tests for `looks_like_recipe_title()` with strong_include URL signal in `tests/test_search_parsers.py` — verify recipe-pattern URLs override mild editorial title concerns

### Implementation for User Story 1

- [x] T011 [US1] Tune editorial title patterns to ensure food searches are clean — test with queries "chicken tagine", "pasta carbonara", "spring asparagus risotto" against live search and verify all results look like actual recipes in `apps/recipes/services/search_parsers.py`

**Checkpoint**: Recipe-focused searches return only importable recipes

---

## Phase 4: User Story 2 — Non-Food Searches Show No Editorial Content (Priority: P2)

**Goal**: Searches for non-food terms filter out all editorial/article content

**Independent Test**: Search for "google", "travel", "best restaurants" and verify zero non-recipe content

### Tests for User Story 2

- [x] T012 [P] [US2] Add unit tests for editorial title detection in `tests/test_search_parsers.py` — test titles like "Google's Top Trending Recipe of 2024 Deserves a Gold Medal", "This Southern Spot Is 2025's Most Beautiful Destination", "This Is The Best Time to Book Thanksgiving Travel" are rejected when URL signal is neutral
- [x] T013 [P] [US2] Add unit tests for listicle pattern detection in `tests/test_search_parsers.py` — test "Top 10 Things to Do", "5 Best Destinations", "7 Reasons to Visit" are rejected, but "Top 10 Cookie Recipes" passes due to recipe-context override

### Implementation for User Story 2

- [x] T014 [US2] Tune editorial title patterns for non-food query coverage — test with queries "google", "travel", "news", "best restaurants" against live search and adjust patterns if non-recipe content still appears in `apps/recipes/services/search_parsers.py`

**Checkpoint**: Non-food searches return zero editorial content

---

## Phase 5: User Story 3 — Legitimate Recipes Are Not Lost (Priority: P2)

**Goal**: Filtering does not remove actual recipes with unusual titles

**Independent Test**: Search for "TikTok pasta", "cowboy caviar" and verify recipe results still appear

### Tests for User Story 3

- [x] T015 [P] [US3] Add unit tests for false positive prevention in `tests/test_search_parsers.py` — test that titles with brand names ("TikTok Feta Pasta"), unusual names ("Cowboy Caviar"), short titles ("Soup"), and mixed signals ("The Best Chicken Recipe I Found While Traveling in Morocco" with recipe URL) all pass the filter

### Implementation for User Story 3

- [x] T016 [US3] Review and adjust recipe-context override words to prevent over-filtering in `apps/recipes/services/search_parsers.py` — ensure words like "recipe", "cook", "bake", "make", "homemade" properly rescue legitimate recipes from editorial pattern matches

**Checkpoint**: All three user stories independently functional — recipes preserved, editorial content removed

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup

- [x] T017 Run full existing test suite via `docker compose exec web python -m pytest` to confirm no regressions
- [x] T018 Run quickstart.md manual validation — search for "google" and verify no editorial content, search for "chicken tagine" and verify all results are recipes
- [x] T019 Verify code quality gates — ensure new/modified functions are under 50 lines, file stays under 500 lines, cyclomatic complexity under 15 in `apps/recipes/services/search_parsers.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can proceed in parallel (they test different aspects of the same filter)
  - Or sequentially in priority order (P1 → P2 → P2)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) — Independent of US1
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) — Independent of US1/US2

### Within Each User Story

- Tests written first, verified to fail before implementation
- Implementation then makes tests pass
- Story complete before moving to next priority

### Parallel Opportunities

- T001 and T002 are sequential (T002 depends on T001)
- T003 and T004 can run in parallel (separate pattern sets)
- T008, T009, T010 can run in parallel (separate test cases)
- T012, T013 can run in parallel (separate test cases)
- All user story phases can start in parallel after Phase 2

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit tests for get_url_signal() in tests/test_search_parsers.py"
Task: "Unit tests for looks_like_recipe_title() in tests/test_search_parsers.py"
Task: "Unit tests for strong_include URL signal in tests/test_search_parsers.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (refactor URL signal)
2. Complete Phase 2: Foundational (add title filtering)
3. Complete Phase 3: User Story 1 (recipe searches clean)
4. **STOP and VALIDATE**: Test with recipe queries independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Title filtering active
2. Add User Story 1 → Test recipe searches → Deploy (MVP!)
3. Add User Story 2 → Test non-food searches → Deploy
4. Add User Story 3 → Test false positive prevention → Deploy
5. Each story refines the filter without breaking previous stories

---

## Notes

- [P] tasks = different files or independent sections, no dependencies
- [Story] label maps task to specific user story for traceability
- All changes are in a single backend file (`search_parsers.py`) plus tests
- No frontend changes required — both frontends share the same search API
- Run all tests via Docker: `docker compose exec web python -m pytest`
- After changes to search_parsers.py, restart web container: `docker compose restart web`

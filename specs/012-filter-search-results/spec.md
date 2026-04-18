# Feature Specification: Filter Non-Recipe Content from Search Results

**Feature Branch**: `012-filter-search-results`
**Created**: 2026-03-24
**Status**: Clarified
**Input**: User description: "Filter non-recipe content from search results. Currently, searching for non-food terms returns article/editorial content from recipe sites that cannot be imported as recipes."

## Clarifications

### Session 2026-03-24

- Q: When URL and title signals conflict, how should the system resolve? → A: Recipe-pattern URLs override mild editorial title concerns; strong exclusion URL patterns (e.g., /article/, /blog/) always exclude regardless of title. Tiered resolution approach (Option B).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Recipe Searches Return Only Importable Recipes (Priority: P1)

A user searches for a food-related term (e.g., "chicken tagine," "pasta carbonara") and sees only results that represent actual recipes with ingredients and instructions. Every result shown can be successfully imported.

**Why this priority**: This is the core value of the feature. If recipe searches return non-recipe content, users waste time clicking "Import" on content that will fail.

**Independent Test**: Search for 10 common recipe terms and verify every result can be imported without error.

**Acceptance Scenarios**:

1. **Given** a user searches for "chicken tagine", **When** results are displayed, **Then** all results represent actual recipes, not articles about chicken tagine trends or restaurant reviews
2. **Given** a user searches for "pasta carbonara", **When** results are displayed, **Then** every result shown can be successfully imported as a recipe
3. **Given** a user searches for "spring asparagus risotto", **When** results are displayed, **Then** results include recipe pages from multiple sources, not editorial content about spring cooking

---

### User Story 2 - Non-Food Searches Show No Editorial Content (Priority: P2)

A user searches for a non-food term (e.g., "google," "travel," "best destinations") and sees no results or only results that happen to be actual recipes tangentially related to the term.

**Why this priority**: Non-food searches are the most visible symptom of the problem. Users who search broadly should not see a page full of articles and travel posts they cannot import.

**Independent Test**: Search for 5 non-food terms and verify zero non-recipe content appears in results.

**Acceptance Scenarios**:

1. **Given** a user searches for "google", **When** results are displayed, **Then** editorial articles like "Google's Top Trending Recipe of 2024" are excluded
2. **Given** a user searches for "travel", **When** results are displayed, **Then** travel destination articles and non-recipe content are excluded
3. **Given** a user searches for "best restaurants", **When** results are displayed, **Then** restaurant review articles are excluded, but a recipe titled "Best Restaurant-Style Butter Chicken" would be included if it links to an actual recipe page

---

### User Story 3 - Legitimate Recipes Are Not Lost (Priority: P2)

The filtering does not remove actual recipe content. Recipes with unusual titles, fusion names, or brand mentions continue to appear in results.

**Why this priority**: Over-aggressive filtering would degrade the core search experience, making the fix worse than the problem.

**Independent Test**: Search for recipes with unusual names (e.g., "TikTok pasta," "cowboy caviar") and verify they still appear if they are actual recipe pages.

**Acceptance Scenarios**:

1. **Given** a recipe page exists titled "TikTok Feta Pasta", **When** a user searches for "TikTok pasta", **Then** the recipe appears in results because it is an actual recipe despite having a brand name in the title
2. **Given** a recipe page exists with an unusual name like "Cowboy Caviar", **When** a user searches for "cowboy caviar", **Then** the recipe appears in results

---

### Edge Cases

- What happens when a result title contains both recipe and non-recipe signals (e.g., "The Best Chicken Recipe I Found While Traveling in Morocco")? The system should include it if it links to an actual recipe page with a recipe-pattern URL.
- What happens when a recipe site publishes a "roundup" article listing multiple recipes? The roundup article itself should be excluded, but individual recipe links from the site are not affected.
- What happens when results have no description text? Filtering should still work based on URL and title signals alone.
- What happens when a legitimate recipe has a very short or generic title (e.g., "Soup")? It should not be excluded.
- What happens when a result has a recipe-pattern URL but a clearly non-recipe title (e.g., "About Us")? Strong exclusion URL patterns always win. For recipe-pattern URLs with mild editorial titles, the URL signal takes priority and the result is included. For navigation/meta page titles ("About Us", "Contact"), these are caught by existing URL exclusion patterns.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST filter out search results that represent editorial articles, listicles, travel posts, restaurant reviews, product roundups, or video compilations before displaying them to users
- **FR-002**: System MUST use title text analysis to identify non-recipe content, detecting patterns such as "Top N..." listicles, "X Best Destinations," "Travel Guide," "Review:" and similar editorial title patterns that lack recipe context
- **FR-003**: System MUST use URL path analysis to identify non-recipe content, excluding paths that indicate articles, blogs, news, stories, features, reviews, roundups, galleries, and videos
- **FR-003a**: When URL and title signals conflict, the system MUST apply a tiered resolution: strong exclusion URL patterns (e.g., "/article/", "/blog/", "/news/", "/gallery/") always exclude regardless of title; recipe-pattern URLs (e.g., "/recipe/", "/recipes/") override mild editorial title concerns; results with neutral URLs are evaluated primarily by title signals
- **FR-004**: System MUST NOT filter out results that are actual recipes, even if their titles contain non-food words, brand names, or trending references
- **FR-005**: System MUST apply filtering consistently across both the legacy and modern frontends via the shared search backend
- **FR-006**: System MUST preserve all existing search result data fields (URL, title, host, image, description, rating count) without modification for results that pass the filter
- **FR-007**: System MUST update the displayed result count and source counts to reflect only the filtered (valid) results
- **FR-008**: System MUST log filtered-out results at debug level for troubleshooting purposes

### Key Entities

- **Search Result**: A candidate result from a recipe site containing URL, title, host, description, image URL, and optional rating count. Subject to recipe-content filtering before being shown to the user.
- **Search Source**: A configured recipe website providing search results. Not modified by this feature.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 95% or more of displayed search results can be successfully imported as recipes, measured across a test suite of 20 diverse search queries
- **SC-002**: Fewer than 2% of legitimate recipe results are incorrectly filtered out, measured by comparing filtered vs. unfiltered results for 20 recipe-specific queries
- **SC-003**: Searches for non-food terms (e.g., "google," "travel," "news") return zero non-recipe editorial content
- **SC-004**: No perceptible increase in search response time for users

## Assumptions

- The existing URL pattern filtering provides a foundation that can be extended with title-based signals
- Title text and URL path are sufficient signals to identify non-recipe content in the vast majority of cases, without needing to fetch and inspect the full page content
- Recipe sites use reasonably consistent URL patterns that distinguish recipe pages from editorial content (e.g., "/recipe/" vs. "/article/")
- The filtering logic runs on already-fetched search result metadata (title, URL, description) and does not require additional network requests
- Both frontends consume the same search API endpoint, so backend-only changes are sufficient
- A small number of false positives (legitimate recipes filtered out) is acceptable if the false negative rate (non-recipes shown) is dramatically reduced

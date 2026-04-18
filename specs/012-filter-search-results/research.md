# Research: Filter Non-Recipe Search Results

**Feature**: 012-filter-search-results
**Date**: 2026-03-24

## Research Findings

### R1: Current Filtering Gaps

**Decision**: The existing `looks_like_recipe_url()` function (search_parsers.py:334-371) provides URL-level filtering with 38 exclusion patterns and 8 inclusion patterns, but has no title-based content analysis.

**Gaps identified**:
1. **No title content filtering**: Editorial articles with recipe-like URLs pass through (e.g., "Google's Top Trending Recipe of 2024 Deserves a Gold Medal" has a slug-style URL that passes heuristics)
2. **Heuristic too permissive**: Single-segment slugs with 2+ dashes and >15 chars are accepted regardless of content type
3. **No post-extraction filtering**: `_filter_relevant()` only checks if query terms appear in title, not whether the result is a recipe

**Rationale**: URL filtering alone cannot catch editorial content on recipe sites because these sites use similar URL structures for both recipes and articles.

### R2: Title-Based Non-Recipe Detection Strategy

**Decision**: Add a `looks_like_recipe_title()` function that detects editorial/non-recipe title patterns via regex-based exclusion, applied as a second filter after URL validation.

**Patterns to detect**:
- Listicle patterns: "Top N...", "N Best...", "N Things...", "N Reasons...", "N Ways to..." (where not followed by recipe-related words like "cook", "make", "bake")
- Travel/destination: "Travel Guide", "Best Destinations", "Places to Visit", "Where to Eat" (without recipe context)
- Review/editorial: "Review:", "Product Review", "Book Review", "Restaurant Review"
- News/trending: "Trending", "News:", "Breaking:", "Update:" (without recipe context)
- Meta/about: "About Us", "Contact", "Privacy Policy", "Terms of Service"

**Rationale**: Title analysis catches the editorial content that URL patterns miss. The regex approach is fast (no network calls) and composable with the existing URL checks.

**Alternatives considered**:
- Description text analysis: Rejected as too unreliable (description is often empty or truncated)
- NLP-based classification: Rejected as over-engineered for this scope; regex patterns catch the vast majority of cases
- Allowlist-only approach: Rejected as too restrictive; would miss legitimate recipes with unusual titles

### R3: Tiered Signal Resolution

**Decision**: Implement three-tier signal resolution per the clarified spec (FR-003a):
1. **Strong exclusion URLs** (e.g., /article/, /blog/): Always exclude, regardless of title
2. **Recipe-pattern URLs** (e.g., /recipe/, /recipes/): Include unless title is clearly meta/navigation (e.g., "About Us")
3. **Neutral URLs** (pass heuristics but no strong signal): Evaluate primarily by title analysis

**Rationale**: This matches the clarification from the specify phase. Strong URL signals are reliable; title analysis handles ambiguous cases.

### R4: Integration Point

**Decision**: Add the new `looks_like_recipe_title()` filter in `extract_result_from_element()` (search_parsers.py), called after title extraction but before SearchResult creation. This is the natural integration point because:
- It has access to both the URL (already validated) and the extracted title
- It runs per-element, before results are aggregated
- It catches non-recipe content from all parsing strategies (selector-based and fallback)

For the tiered resolution, enhance `looks_like_recipe_url()` to return a signal strength (strong include, weak include, neutral) rather than just bool, allowing the title filter to adjust its strictness accordingly.

**Alternative considered**: Post-aggregation filter in `_filter_relevant()` — rejected because results have already been converted to dicts and we'd lose the HTML context. Per-element filtering is cleaner.

### R5: Logging Strategy

**Decision**: Add debug-level logging for filtered-out results in `extract_result_from_element()` with the reason (URL exclusion vs. title exclusion) and the title/URL of the excluded result.

**Rationale**: FR-008 requires debug logging. This helps tune false positive/negative rates without impacting production performance.

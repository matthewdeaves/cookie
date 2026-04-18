# Implementation Plan: Filter Non-Recipe Search Results

**Branch**: `012-filter-search-results` | **Date**: 2026-03-24 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/012-filter-search-results/spec.md`

## Summary

Add title-based content analysis to the search result filtering pipeline. Currently, `looks_like_recipe_url()` in `search_parsers.py` filters by URL patterns only, allowing editorial articles, listicles, and travel posts from recipe sites to appear in results. This plan adds a `looks_like_recipe_title()` function and integrates it with the existing URL filtering using a tiered signal resolution approach: strong exclusion URLs always reject, recipe-pattern URLs override mild title concerns, and neutral URLs are evaluated primarily by title signals.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: Django 5.0, Django Ninja 1.0+, BeautifulSoup4, curl_cffi
**Storage**: PostgreSQL (no schema changes)
**Testing**: pytest (via Docker: `docker compose exec web python -m pytest`)
**Target Platform**: Linux server (Docker containers)
**Project Type**: Web application (Django backend, React + legacy ES5 frontends)
**Performance Goals**: No perceptible increase in search response time
**Constraints**: All backend commands run inside Docker containers
**Scale/Scope**: ~10 search sources, ~20-100 results per query filtered in-memory

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I: Multi-Generational Device Access | PASS | Backend-only change. Both frontends receive filtered results from the same API. No frontend code changes. |
| II: Privacy by Architecture | PASS | No user data involved. Search result metadata (titles, URLs) is from public websites. |
| III: Dual-Mode Operation | PASS | Search is available in both auth modes. No auth-related changes. |
| IV: AI as Enhancement | PASS | AI ranking is unaffected. Filtering runs before AI ranking. |
| V: Code Quality Gates | PASS | New function will be <50 lines. Compiled regex patterns are simple. No file size concerns. |
| VI: Docker Is the Runtime | PASS | All testing via `docker compose exec web python -m pytest`. |
| VII: Security by Default | PASS | No user input is used in SQL. Title analysis uses regex on already-scraped metadata. No new attack surface. |

## Project Structure

### Documentation (this feature)

```text
specs/012-filter-search-results/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 research output
├── data-model.md        # Phase 1 data model
├── quickstart.md        # Phase 1 quickstart guide
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
apps/recipes/services/
├── search.py            # Search orchestration (unchanged)
└── search_parsers.py    # URL filtering + NEW title filtering

tests/
└── (test files for search filtering)
```

**Structure Decision**: This is a surgical change to a single backend service file (`search_parsers.py`). No new files, modules, or directories needed beyond test additions.

## Design

### New Function: `looks_like_recipe_title(title, url_signal)`

A pure function that analyzes a search result title for non-recipe content patterns. Takes the title string and a URL signal strength indicator to implement tiered resolution.

**Title exclusion patterns** (compiled regex, module-level):
- Listicle: `^(top\s+)?\d+\s+(best|worst|things|reasons|ways|places|tips|tricks)` (exclude unless followed by recipe context)
- Travel/destination: `travel\s+guide|best\s+destinations|places\s+to\s+visit|where\s+to\s+(eat|go|stay)`
- Review/editorial: `^review:|product\s+review|book\s+review|restaurant\s+review|movie\s+review`
- News: `^(news|breaking|update|trending):`
- Meta/navigation: `^(about\s+us|contact|privacy|terms\s+of|cookie\s+policy|subscribe|newsletter|sign\s+up|log\s+in)`

**Recipe-context override words** (prevent false positives):
- Words like "recipe", "cook", "bake", "make", "homemade", "ingredient", "how to" in the title override editorial patterns

**Tiered resolution logic**:
1. If URL signal is "strong_exclude": return False (already handled by `looks_like_recipe_url`)
2. If URL signal is "strong_include": return True (recipe URL overrides mild title concerns)
3. If URL signal is "neutral": apply full title analysis
4. If title matches editorial patterns AND no recipe-context words present: return False
5. Otherwise: return True

### Integration into `extract_result_from_element()`

After title extraction (line ~177) and before SearchResult creation (line ~188), add:

```python
# Determine URL signal strength
url_signal = get_url_signal(url, host)

# Check title for non-recipe content
if not looks_like_recipe_title(title, url_signal):
    logger.debug("Filtered non-recipe title: %s (%s)", title, url)
    return None
```

### Helper: `get_url_signal(url, host)`

Refactors the existing `looks_like_recipe_url()` to also return signal strength:
- Returns "strong_exclude" if URL matches exclusion patterns (current behavior returns False)
- Returns "strong_include" if URL matches recipe patterns
- Returns "neutral" if URL passes only via heuristics

This can be implemented by extracting the logic into a new function and having `looks_like_recipe_url()` call it for backward compatibility.

## Complexity Tracking

No constitution violations. No complexity justifications needed.

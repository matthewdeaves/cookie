# Quickstart: Filter Non-Recipe Search Results

**Feature**: 012-filter-search-results

## What This Feature Does

Adds title-based content analysis to the existing URL-pattern search result filtering. This prevents non-recipe content (articles, listicles, travel posts, reviews) from appearing in search results on both frontends.

## Key Files to Modify

| File | Change |
|------|--------|
| `apps/recipes/services/search_parsers.py` | Add `looks_like_recipe_title()` function; integrate into `extract_result_from_element()` |
| `tests/` | Add test cases for title filtering with editorial and recipe title examples |

## Architecture

```
User searches "google"
    ↓
Search sources return HTML results
    ↓
extract_result_from_element() per element:
    1. find_link() → extract URL
    2. looks_like_recipe_url() → URL signal (strong exclude / strong include / neutral)  [EXISTING]
    3. extract_title() → get title text
    4. looks_like_recipe_title() → title signal check  [NEW]
    5. Tiered resolution: combine URL + title signals  [NEW]
    6. Return SearchResult or None
    ↓
Aggregation, dedup, relevance filter, AI ranking, pagination  [UNCHANGED]
    ↓
API response to both frontends  [UNCHANGED]
```

## No Frontend Changes Required

Both frontends call the same `/api/recipes/search` endpoint. Filtering happens in the backend before results are returned. No frontend code changes needed.

## Testing

```bash
# Run backend tests
docker compose exec web python -m pytest tests/ -k "search" -v

# Manual test: search for non-food term, verify no editorial content
curl -s "http://localhost:3000/api/recipes/search?q=google" | python3 -m json.tool
```

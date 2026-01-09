# QA-043: Search Ranking Should Prioritize Results with Images

## Problem

Search results were ranked by AI considering relevance, completeness, and source reliability equally. However, for a better visual experience in the app, results with images should be prioritized so the UI looks more appealing with recipe photos.

Additionally, only the first 20 results were being ranked, meaning paginated results beyond page 1 could appear in random order with image-less results mixed throughout.

## Affects

- Modern frontend (React)
- Legacy frontend

## Requirements

1. AI ranking should heavily prioritize results WITH images over those without
2. More results should be ranked (not just 20)
3. Paginated results beyond the AI-ranked set should also prioritize images

## Priority

Medium - UX/visual improvement for better app appearance

## Status
**RESOLVED** (2026-01-09) - Verified on Modern and Legacy frontends

## Implementation

### 1. Increased AI Ranking Limit

**File:** `apps/ai/services/ranking.py:61-62`

Changed from ranking first 20 results to first 40 results:
```python
# Before
results_to_rank = results[:20]
remaining = results[20:] if len(results) > 20 else []

# After
results_to_rank = results[:40]
remaining = results[40:] if len(results) > 40 else []
```

### 2. Updated AI Ranking Prompt

**File:** `apps/ai/migrations/0007_update_search_ranking_prompt.py`

Created data migration to update the `search_ranking` prompt with new priorities:

```
RANKING PRIORITIES (in order of importance):
1. Results WITH images should rank SIGNIFICANTLY higher than those without
2. Relevance to the search query
3. Recipe completeness (ratings, reviews)
4. Source reliability

A result with an image that is somewhat relevant should rank HIGHER
than a highly relevant result without an image.
```

### 3. Image-First Sorting for Remaining Results

**File:** `apps/ai/services/ranking.py:93-99`

Added sorting for results beyond the AI-ranked set to ensure images appear first without additional API costs:

```python
# Sort remaining results to prioritize those with images
if remaining:
    remaining_sorted = sorted(
        remaining,
        key=lambda r: (0 if r.get('image_url') else 1),
    )
    ranked_results.extend(remaining_sorted)
```

## Result

- First 40 results: AI-ranked with strong image preference
- Results 41+: Automatically sorted with images first (no AI cost)
- Both React and Legacy frontends benefit (shared backend API)
- App displays more visually appealing search results with recipe photos prominent

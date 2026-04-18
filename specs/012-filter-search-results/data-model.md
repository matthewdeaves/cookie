# Data Model: Filter Non-Recipe Search Results

**Feature**: 012-filter-search-results
**Date**: 2026-03-24

## Entities

### SearchResult (existing, unchanged)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| url | str | Yes | Full URL of the search result page |
| title | str | Yes | Page title (max 200 chars) |
| host | str | Yes | Source domain (e.g., "allrecipes.com") |
| image_url | str | No | Recipe image URL |
| description | str | No | Short description (max 200 chars) |
| rating_count | int | No | Number of ratings/reviews |

No schema changes. No database changes. No new models.

## Filtering Signal Model (conceptual, not persisted)

### URL Signal

| Signal Strength | Examples | Behavior |
|----------------|----------|----------|
| Strong Exclude | /article/, /blog/, /news/, /gallery/, /video/ | Always exclude regardless of title |
| Strong Include | /recipe/, /recipes/, /dish/, /food/ | Include unless title is navigation/meta |
| Neutral | Slug-style URLs passing heuristics | Evaluate by title analysis |

### Title Signal

| Signal Type | Pattern Examples | Behavior |
|-------------|-----------------|----------|
| Editorial Listicle | "Top 10...", "N Best...", "N Things..." | Exclude (unless recipe-context words present) |
| Travel/Destination | "Travel Guide", "Best Destinations" | Exclude |
| Review/News | "Review:", "News:", "Breaking:" | Exclude |
| Meta/Navigation | "About Us", "Contact", "Privacy Policy" | Exclude |
| Recipe-Context | Contains "recipe", "how to cook/make/bake" | Strong include signal |
| Neutral | No editorial or recipe-specific patterns | Pass through |

## State Transitions

None. This feature does not introduce any stateful behavior. Filtering is a pure function applied during search result processing.

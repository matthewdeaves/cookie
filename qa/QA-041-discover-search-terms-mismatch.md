# QA-041: Discover Search Terms Don't Match Suggestion Titles

## Problem

When clicking on a Discover suggestion, the search query doesn't match the suggestion title well enough.

**Example observed:**
- Suggestion title: "Creamy Roasted Butternut Squash and Sage Soup"
- Search query used: "hot soup recipe"

The search query is too generic and won't find the specific recipe type suggested.

## Affects

- Modern frontend (React)
- Legacy frontend

## Expected Behavior

Search queries should be specific enough to find recipes matching the suggestion:
- Title: "Creamy Roasted Butternut Squash and Sage Soup"
- Expected search: "butternut squash sage soup" or "roasted butternut squash soup"

## Root Cause Analysis

The AI prompts instruct the model to provide search queries of "2-4 words" but don't emphasize that the search query should be specific enough to find the suggested recipe type.

Current prompt example:
```
- search_query: A specific search term to find this type of recipe (2-4 words)
```

The AI is sometimes returning generic queries like "hot soup recipe" instead of specific ones like "butternut squash soup".

## Proposed Fix

Update all three discover prompts to:
1. Emphasize search_query must match the specific recipe being suggested
2. Provide better examples showing the relationship between title and search_query
3. Possibly increase allowed word count to 3-5 words for more specificity

## Files to Update

- Database: AIPrompt records for `discover_seasonal`, `discover_favorites`, `discover_new`
- Update via Django shell or migration

## Priority

Medium - Affects discoverability/usefulness of suggestions

## Status

RESOLVED - Fixed by updating AI prompts

## Solution

Updated all three discover prompts (`discover_seasonal`, `discover_favorites`, `discover_new`) with:

1. Added "RESPOND WITH ONLY A JSON ARRAY - NO OTHER TEXT" to prevent AI adding preamble
2. Changed search_query instruction from "2-4 words" to "3-5 words, must match the dish in title"
3. Added "IMPORTANT: The search_query must be specific enough to find the exact type of dish mentioned in the title"
4. Provided better examples showing title/search_query relationship:
   - Title: "Creamy Roasted Butternut Squash Soup with Sage"
   - Search: "butternut squash sage soup"

## Results

Before fix:
- Title: "Creamy Roasted Butternut Squash and Sage Soup" → Search: "hot soup recipe" (too generic)

After fix:
- Title: "Creamy Roasted Butternut Squash Winter Risotto" → Search: "butternut squash risotto winter" (specific)
- Title: "Classic Decadent Hot Chocolate with Homemade Marshmallows" → Search: "hot chocolate homemade marshmallows" (specific)

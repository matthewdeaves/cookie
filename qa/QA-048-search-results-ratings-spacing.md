# QA-048: Search Results Missing Space Before "Ratings"

## Status
**VERIFIED** - Confirmed working on Modern frontend

## Issue

In search results, the rating count is displayed without a space before the word "Ratings".

### Current Behavior
```
Chicken Makhani (Indian Butter Chicken)1,392Ratings
```

### Expected Behavior
```
Chicken Makhani (Indian Butter Chicken) 1,392 Ratings
```

## Root Cause

The search results scraper extracts title text from HTML elements without preserving spacing between nested elements.

**File:** `apps/recipes/services/search.py:268`

```python
title = title_el.get_text(strip=True)
```

When the source HTML has nested elements like:
```html
<h2>Chicken Makhani (Indian Butter Chicken)<span>1,392</span>Ratings</h2>
```

`get_text(strip=True)` concatenates all text **without spaces** between elements, resulting in: `Chicken Makhani (Indian Butter Chicken)1,392Ratings`

**Note:** The source site likely uses CSS (padding/margin on the `<span>`) for visual spacing. But when we extract text with BeautifulSoup, we only get the text content - CSS styling is lost. The `separator=' '` fix compensates for this.

## Chosen Fix: Extract rating as separate field

Extract rating info as a separate `SearchResult` field, then render as separate element with CSS for proper spacing/styling.

### Implementation Plan

#### 1. Update SearchResult dataclass (`apps/recipes/services/search.py`)

```python
@dataclass
class SearchResult:
    url: str
    title: str
    host: str
    image_url: str = ''
    description: str = ''
    rating_count: int | None = None  # NEW: extracted rating count
```

#### 2. Update `_extract_result_from_element()` to:
- Extract rating count from common patterns (e.g. `<span>1,392</span>Ratings`)
- Strip rating text from title
- Store rating count as separate field

#### 3. Update API schema (`apps/recipes/api.py`)
- Add `rating_count` to `SearchResultOut` schema

#### 4. Update frontends to render rating separately:

**Modern frontend** (`frontend/src/screens/Search.tsx`):
```tsx
<h3>{result.title}</h3>
{result.rating_count && (
  <span className="text-muted-foreground">
    {result.rating_count.toLocaleString()} Ratings
  </span>
)}
```

**Legacy frontend** (`apps/legacy/templates/legacy/partials/search_result_card.html`):
```html
<h3>{{ result.title }}</h3>
{% if result.rating_count %}
<span class="rating-count">{{ result.rating_count }} Ratings</span>
{% endif %}
```

## Affected Components

- `apps/recipes/services/search.py` - SearchResult dataclass, `_extract_result_from_element()`
- `apps/recipes/api.py` - SearchResultOut schema
- `frontend/src/screens/Search.tsx` - SearchResultCard component
- `apps/legacy/templates/legacy/partials/search_result_card.html`

## Priority

Low - Cosmetic/formatting issue

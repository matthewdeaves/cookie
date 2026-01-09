# Future Enhancements

> **Purpose:** Log feature ideas and enhancements for future development
> **Status:** Backlog - implement when needed

---

## Enhancement Log

| ID | Summary | Priority | Complexity |
|----|---------|----------|------------|
| FE-001 | Database-driven search URL filters with settings UI | Medium | Medium |
| FE-002 | Automatic selector repair on search failure | Low | Medium |

---

## FE-001: Database-Driven Search URL Filters

**Status:** Backlog

### Problem

Search result URL filtering patterns are currently hardcoded in `apps/recipes/services/search.py`. Adding new patterns requires code changes and deployment.

### Current Implementation

- Patterns defined in `_looks_like_recipe_url()` method
- Includes ~40 exclusion patterns for articles, videos, index pages
- No way to add/edit/delete patterns without code changes

### Proposed Solution

1. **New Model:** `SearchUrlFilter`
   - `pattern` - regex pattern to match
   - `filter_type` - include/exclude
   - `category` - article, video, index, etc.
   - `enabled` - toggle on/off
   - `notes` - description of what it catches

2. **Settings Page:**
   - List all filters with enable/disable toggle
   - Add new filter with pattern validation
   - Edit existing filters
   - Delete filters
   - Test pattern against sample URLs

3. **Migration:**
   - Seed database with current hardcoded patterns
   - Update `_looks_like_recipe_url()` to query database

### Benefits

- Non-developers can manage filters
- No deployment needed for new patterns
- Can quickly disable problematic patterns
- Audit trail of filter changes

### Files to Change

- `apps/recipes/models.py` - Add `SearchUrlFilter` model
- `apps/recipes/services/search.py` - Query filters from database
- `apps/legacy/views.py` - Settings page view
- `apps/legacy/templates/legacy/settings.html` - Filter management UI
- New migration to seed existing patterns

### Notes

- Cache filter queries to avoid DB hit on every search
- Invalidate cache when filters are modified
- Consider regex validation on save to prevent invalid patterns

---

## FE-002: Automatic Selector Repair on Search Failure

**Status:** Backlog

### Problem

When a search source's CSS selector breaks (site redesign), the source returns 0 results. Currently, broken selectors require manual admin intervention to repair.

### Current Implementation

- `search.py` tracks `consecutive_failures` and sets `needs_attention=True` after 3 failures
- `apps/ai/services/selector.py` provides `repair_selector()` function
- API endpoint `POST /api/ai/repair-selector` for manual repair
- Admin must manually trigger repair via API

### Proposed Solution

Add automatic inline integration to the search flow:

1. **Detect failure:** When 0 results are returned AND we have the HTML response
2. **Trigger async repair:** Fire-and-forget background task (non-blocking)
3. **AI analysis:** Repair runs in background, calls AI to suggest new selector
4. **Auto-update:** If confidence >= threshold, update the source's selector
5. **Next search:** Uses the repaired selector automatically

### Implementation Details

```python
# In search.py _search_source()
if not results and html_response:
    # Fire-and-forget async repair
    from apps.ai.services.selector import repair_selector
    import threading
    threading.Thread(
        target=repair_selector,
        args=(source, html_response),
        kwargs={'auto_update': True},
        daemon=True
    ).start()
```

### Benefits

- Self-healing search sources
- No admin intervention needed for common selector breakage
- Repairs happen transparently in background
- Next user search benefits from repaired selector

### Considerations

- Don't spam AI with repair attempts (rate limit per source)
- Log all auto-repairs for admin review
- Consider retry backoff if repair fails multiple times
- May want confidence threshold higher for auto-repair (0.9 vs 0.8)

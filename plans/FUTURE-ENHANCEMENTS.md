# Future Enhancements

> **Purpose:** Log feature ideas and enhancements for future development
> **Status:** Backlog - implement when needed

---

## Enhancement Log

| ID | Summary | Priority | Complexity |
|----|---------|----------|------------|
| FE-001 | Database-driven search URL filters with settings UI | Medium | Medium |

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

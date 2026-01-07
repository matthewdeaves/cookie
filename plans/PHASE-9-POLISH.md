# Phase 9: Settings & Polish

> **Goal:** Production-ready application
> **Prerequisite:** Phase 8B complete
> **Deliverable:** Complete, tested, polished application

---

## Session Scope

| Session | Tasks | Focus |
|---------|-------|-------|
| A | 9.1-9.2 | Settings screens (both interfaces) |
| B | 9.3-9.5 | Error handling + loading + toasts |
| C | 9.6-9.7 | Final testing + verification |

---

## Tasks

- [ ] 9.1 React: Settings screen (General, AI Prompts, Sources, Source Selectors tabs)
- [ ] 9.2 Legacy: Settings screen (all tabs)
- [ ] 9.3 Error handling and edge cases
- [ ] 9.4 Loading states and skeletons (React) / Loading indicators (Legacy)
- [ ] 9.5 Toast notifications (both interfaces)
- [ ] 9.6 Testing with pytest (unit + integration)
- [ ] 9.7 Final cross-browser/device testing

---

## Settings Screen

### Four Tabs

1. **General**
2. **AI Prompts**
3. **Sources**
4. **Source Selectors**

---

### General Tab

From Figma:
- **Appearance:** Dark/light toggle (React only; show light-only message on Legacy)
- **Profile Management:**
  - List all profiles
  - "Current" badge on active profile
  - Delete option per profile
- **Data Management:**
  - Clear Cache button
  - Clear View History button
- **OpenRouter API Key:**
  - Password input field
  - Test connection button
- **About:**
  - Version number
  - GitHub link: https://github.com/matthewdeaves/cookie.git

### AI Prompts Tab

From Figma:
- Section header explaining prompts
- Ten prompt cards:
  1. Recipe Remix
  2. Serving Adjustment
  3. Tips Generation
  4. Discover from Favorites
  5. Discover Seasonal/Holiday
  6. Discover Try Something New
  7. Search Result Ranking
  8. Timer Naming
  9. Remix Suggestions
  10. CSS Selector Repair
- Each card shows:
  - Title and description
  - Edit button
  - Current prompt (read-only view)
  - Current model badge
- Edit mode:
  - Textarea for prompt
  - Model dropdown (8+ models)
  - Save/Cancel buttons

### Sources Tab

From Figma:
- "Recipe Sources" heading
- "X of 15 sources currently enabled" counter
- Enable All / Disable All bulk actions
- List of 15 sources with:
  - Source name and URL
  - "Active" badge when enabled
  - Toggle switch

### Source Selectors Tab

From Figma:
- "Search Source Selector Management" heading
- "Edit CSS selectors and test source connectivity" subheading
- For each source:
  - Source name and host URL
  - Status indicator: green checkmark (working), red X (broken), gray ? (untested)
  - Editable "CSS Selector" text field (monospace)
  - "Test" button
  - "Last tested: [relative time]"
  - Warning badge if broken: "Failed X times - auto-disabled"
- "Test All Sources" button at bottom

---

## Error Handling

### API Error Responses

```python
# Standard error response format
{
    "error": "error_code",
    "message": "Human-readable message",
    "details": {}  # Optional additional info
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `validation_error` | 400 | Invalid input data |
| `not_found` | 404 | Resource not found |
| `profile_required` | 401 | No profile selected |
| `ai_unavailable` | 503 | AI features unavailable |
| `scrape_failed` | 502 | Recipe scraping failed |
| `rate_limited` | 429 | Too many requests |
| `server_error` | 500 | Internal error |

### Frontend Error Display

**React:**
- Use Sonner toast notifications
- Show loading skeletons during data fetch
- Show empty states with CTAs when no data

**Legacy:**
- Use simple toast/alert system
- Show loading indicators
- Show empty states

---

## Loading States

### React

Use skeleton components while loading:
- Recipe card skeleton
- Recipe detail skeleton
- List skeleton

```tsx
// Example skeleton
export function RecipeCardSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="bg-muted h-48 rounded-t-lg" />
      <div className="p-4 space-y-2">
        <div className="bg-muted h-4 w-3/4 rounded" />
        <div className="bg-muted h-4 w-1/2 rounded" />
      </div>
    </div>
  );
}
```

### Legacy

Use simple loading indicators:
- Spinning indicator
- "Loading..." text
- Disabled buttons during requests

---

## Toast Notifications

### React (Sonner)

```tsx
import { toast } from 'sonner';

// Success
toast.success('Recipe saved to favorites');

// Error
toast.error('Failed to load recipe');

// Loading
toast.loading('Saving...');
```

### Legacy

```javascript
// legacy/static/legacy/js/toast.js
var Cookie = Cookie || {};
Cookie.toast = (function() {
    var container = document.getElementById('toast-container');

    function show(message, type) {
        var toast = document.createElement('div');
        toast.className = 'toast toast-' + (type || 'info');
        toast.textContent = message;
        container.appendChild(toast);

        setTimeout(function() {
            toast.classList.add('fade-out');
            setTimeout(function() {
                container.removeChild(toast);
            }, 300);
        }, 3000);
    }

    return {
        success: function(msg) { show(msg, 'success'); },
        error: function(msg) { show(msg, 'error'); },
        info: function(msg) { show(msg, 'info'); }
    };
})();
```

---

## Testing Strategy

### Test Framework

- **pytest** for all tests
- Django test client for API tests
- pytest-asyncio for async tests

### Test Categories

1. **Unit Tests:** Models, services, utilities
2. **Integration Tests:** API endpoints, full flows
3. **Manual Testing:** Both interfaces on target devices

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_profiles.py
├── test_recipes.py
├── test_collections.py
├── test_ai.py
├── test_scraping.py
├── test_search.py
└── test_settings.py
```

### Key Test Cases

```python
# Profiles
def test_create_profile()
def test_select_profile_sets_session()
def test_delete_profile_cascades_data()

# Recipes
def test_scrape_recipe_saves_image_locally()
def test_scrape_same_url_creates_new_recipe()
def test_recipe_deletion_orphans_remixes()

# Collections
def test_favorites_per_profile_isolation()
def test_collection_crud()
def test_remix_visibility_per_profile()

# AI
def test_ai_unavailable_without_key()
def test_remix_creates_new_recipe()
def test_serving_adjustment_hidden_without_servings()
def test_discover_daily_refresh()

# Search
def test_multi_site_search()
def test_source_filtering()
def test_rate_limiting()
```

---

## Cross-Browser Testing

### Modern Browsers (React)
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

### Legacy (iOS 9)
- [ ] iOS 9 iPad (real device or simulator)
- [ ] Test all ES5 code paths
- [ ] Test timers in play mode
- [ ] Test all user flows

### Test Checklist

- [ ] Profile selection and switching
- [ ] Recipe search and import
- [ ] Favorites and collections
- [ ] Recipe detail with all tabs
- [ ] Play mode with timers
- [ ] Settings all tabs
- [ ] Dark/light theme (React only)
- [ ] AI features (with API key)
- [ ] AI features hidden (without API key)
- [ ] Error states and empty states
- [ ] Loading states

---

## Acceptance Criteria

1. Settings screen works on both interfaces
2. All 4 settings tabs functional
3. API key can be set and tested
4. Error messages are clear and actionable
5. Loading states prevent UI flashing
6. Toast notifications work on both interfaces
7. All unit and integration tests pass
8. App works on iOS 9 iPad
9. App works on modern browsers
10. No console errors in production

---

## Final Checklist

- [ ] All phases complete
- [ ] All tests passing
- [ ] No console errors
- [ ] All 15 sources have working selectors
- [ ] AI features work with valid API key
- [ ] AI features hidden without API key
- [ ] iOS 9 iPad fully functional
- [ ] Dark mode works (React)
- [ ] Light-only theme works (Legacy)
- [ ] Images stored locally
- [ ] Timers work in play mode
- [ ] Data properly isolated per profile

# Phase 4-5: Frontend Foundation (Both Interfaces)

> **Goal:** Profile selection, home screen, and search working on both interfaces
> **Prerequisite:** Phase 3 complete
> **Deliverable:** Working dual frontend with profile, home, and search screens

---

## Tasks

### Phase 4: Profile Selector

- [ ] 4.1 Vite/React project setup with Tailwind v4, theme.css from Figma
- [ ] 4.2 React: API client with fetch
- [ ] 4.3 React: Profile selector screen
- [ ] 4.4 Legacy: Base template and CSS (light theme only)
- [ ] 4.5 Legacy: ES5 JavaScript modules (ajax, state, router)
- [ ] 4.6 Legacy: Profile selector screen

### Phase 5: Home & Search

- [ ] 5.1 React: Home screen with search bar
- [ ] 5.2 React: Favorites/Discover toggle
- [ ] 5.3 React: Basic recipe card component
- [ ] 5.4 React: Dark/light theme toggle
- [ ] 5.5 Legacy: Home screen with search bar
- [ ] 5.6 Legacy: Favorites/Discover toggle
- [ ] 5.7 Legacy: Recipe card partial
- [ ] 5.8 React: Search results with source filters and pagination
- [ ] 5.9 Legacy: Search results with source filters

---

## Tech Stack

### React Frontend

| Component | Technology |
|-----------|------------|
| Framework | React 18.3 |
| Language | TypeScript |
| Build Tool | Vite 6.x |
| Styling | Tailwind CSS v4.1.x |
| UI Primitives | Radix UI |
| Icons | Lucide React |
| Notifications | Sonner |
| Animations | Motion |
| State | React useState/useEffect |

### Legacy Frontend (iOS 9)

| Component | Technology |
|-----------|------------|
| Language | Vanilla ES5 JavaScript |
| Styling | CSS3 (flexbox, -webkit prefixes) |
| Templates | Django templates |
| AJAX | XMLHttpRequest |
| Theme | Light only |

---

## Directory Structure

### React

```
frontend/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── api/
│   │   └── client.ts           # API client with fetch
│   ├── hooks/
│   │   ├── useProfile.ts
│   │   └── useRecipes.ts
│   ├── components/
│   │   ├── Header.tsx
│   │   ├── RecipeCard.tsx
│   │   ├── ProfileAvatar.tsx
│   │   └── ui/                 # Radix primitives
│   ├── screens/
│   │   ├── ProfileSelector.tsx
│   │   ├── Home.tsx
│   │   └── Search.tsx
│   └── styles/
│       ├── index.css
│       ├── theme.css           # From Figma (synced)
│       └── tailwind.css
├── package.json
├── vite.config.ts
└── tsconfig.json
```

### Legacy

```
legacy/
├── templates/legacy/
│   ├── base.html               # Base template
│   ├── profile_selector.html
│   ├── home.html
│   ├── search.html
│   └── partials/
│       ├── header.html
│       └── recipe_card.html
└── static/legacy/
    ├── js/
    │   ├── app.js              # Bootstrap (ES5)
    │   ├── ajax.js             # XHR wrapper
    │   ├── state.js            # Page state
    │   ├── router.js           # AJAX navigation
    │   └── pages/
    │       ├── home.js
    │       └── search.js
    └── css/
        ├── base.css            # Light theme only
        ├── components.css
        └── layout.css
```

---

## Screen Specifications

### Profile Selector

From Figma:
- Large "Cookie" title in primary green
- "Who's cooking today?" subtitle
- Circular avatar buttons with profile colors
- Add profile button (dashed circle with +)
- Create profile form: name input, color picker (10 colors), create button

**Profile Colors:**
```javascript
['#d97850', '#8fae6f', '#c9956b', '#6b9dad', '#d16b6b',
 '#9d80b8', '#e6a05f', '#6bb8a5', '#c77a9e', '#7d9e6f']
```

### Home Screen

From Figma:
- **Header:** Burger menu, "Cookie" title, Dark mode toggle (React only), Profile avatar
- **Sidebar:** Home, Favorites, Collections, Settings (slides from left)
- **Search bar:** "Search recipes or paste a URL..."
- **Toggle:** "My Favorites" | "Discover"
- **Favorites view:** Recently Viewed (up to 6), My Favorite Recipes grid
- **Discover view:** AI-suggested recipes (implement in Phase 8)
- **Empty state:** "Discover Recipes" CTA

### Search Results

From Figma:
- Breadcrumb navigation
- Results count with query
- Source filter chips (All Sources, per-site with counts)
- Recipe grid
- Load more button (6 per page)
- "End of results" indicator
- URL detection -> "Import Recipe" card

---

## Legacy ES5 Translation Rules

| Modern (ES6+) | Legacy (ES5) |
|---------------|--------------|
| `const/let` | `var` |
| Arrow functions | `function() {}` |
| Template literals | String concatenation |
| `async/await` | Callbacks |
| `fetch()` | `XMLHttpRequest` |
| Destructuring | Manual property access |
| Spread operator | `Object.assign()` |
| Classes | Prototypes |
| Modules | IIFE + global namespace |
| Dark mode | Light theme only |

### Example: AJAX Wrapper

```javascript
// legacy/static/legacy/js/ajax.js
var Cookie = Cookie || {};
Cookie.ajax = (function() {
    function request(method, url, data, callback) {
        var xhr = new XMLHttpRequest();
        xhr.open(method, url, true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                if (xhr.status >= 200 && xhr.status < 300) {
                    callback(null, JSON.parse(xhr.responseText));
                } else {
                    callback(new Error(xhr.statusText), null);
                }
            }
        };
        xhr.send(data ? JSON.stringify(data) : null);
    }

    return {
        get: function(url, callback) { request('GET', url, null, callback); },
        post: function(url, data, callback) { request('POST', url, data, callback); },
        put: function(url, data, callback) { request('PUT', url, data, callback); },
        delete: function(url, callback) { request('DELETE', url, null, callback); }
    };
})();
```

---

## Color Palette

**Light Mode:**
```css
--background: #faf9f7;       /* Warm off-white */
--foreground: #2d2520;       /* Dark brown */
--primary: #6b8e5f;          /* Sage green */
--secondary: #f4ede6;        /* Light cream */
--accent: #a84f5f;           /* Muted red/pink */
--muted: #e8e1d8;            /* Light tan */
--destructive: #c94545;      /* Red */
--star: #d97850;             /* Orange (for ratings) */
```

**Dark Mode (React only):**
```css
--background: #2a2220;       /* Dark brown */
--foreground: #f5ebe0;       /* Light cream */
--primary: #8aa879;          /* Lighter sage green */
--secondary: #3d3531;        /* Dark brown */
--accent: #c66d7a;           /* Lighter pink */
```

---

## iOS 9 Compatibility Checklist

- [ ] ES5 only (no const/let, arrow functions, template literals)
- [ ] XMLHttpRequest (no fetch)
- [ ] Flexbox with -webkit prefixes (no CSS Grid)
- [ ] Light theme only
- [ ] Touch targets minimum 44px
- [ ] Font size 16px+ for inputs (prevent zoom)
- [ ] -webkit-overflow-scrolling: touch
- [ ] Polyfills: Element.closest(), Element.matches()

---

## Acceptance Criteria

1. React: Profile selector works, persists selection to session
2. React: Home screen shows with search bar and toggle
3. React: Search returns results with source filters
4. React: Dark/light theme toggle works
5. Legacy: Profile selector works (same API)
6. Legacy: Home screen renders correctly on iOS 9
7. Legacy: Search works with source filters
8. Both: Recipe cards display consistently
9. Both: Session maintains selected profile

---

## Testing Notes

Run tests on:
- Modern browser (Chrome/Firefox/Safari latest)
- iOS 9 iPad (simulator or real device)

```python
def test_profile_selection_sets_session():
    response = client.post('/api/profiles/1/select/')
    assert response.status_code == 200
    assert client.session['profile_id'] == 1

def test_search_returns_paginated_results():
    response = client.get('/api/recipes/search/?q=cookies')
    data = response.json()
    assert 'results' in data
    assert 'total' in data
    assert 'has_more' in data
```

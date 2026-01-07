# Phase 5: Legacy Frontend Foundation (iOS 9)

> **Goal:** Profile selection, home screen, and search working on Legacy interface
> **Prerequisite:** Phase 4 complete
> **Deliverable:** Working Legacy frontend with profile, home, and search screens

---

## Session Scope

| Session | Tasks | Focus |
|---------|-------|-------|
| A | 5.1-5.3 | Legacy setup + profile selector |
| B | 5.4-5.6 | Home screen + recipe cards |
| C | 5.7-5.9 | Search + tests + iOS 9 testing |

---

## Tasks

- [x] 5.1 Legacy: Base template and CSS (light theme only)
- [x] 5.2 Legacy: ES5 JavaScript modules (ajax, state, router)
- [x] 5.3 Legacy: Profile selector screen
- [x] 5.4 Legacy: Home screen with search bar
- [x] 5.5 Legacy: Favorites/Discover toggle
- [x] 5.6 Legacy: Recipe card partial
- [x] 5.7 Legacy: Search results with source filters
- [x] 5.8 Write tests for Legacy Django views and template rendering
- [x] 5.9 Manual testing on iOS 9 simulator/device

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Vanilla ES5 JavaScript |
| Styling | CSS3 (flexbox, -webkit prefixes) |
| Templates | Django templates |
| AJAX | XMLHttpRequest |
| Theme | Light only |

---

## Directory Structure

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

## ES5 Translation Rules

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

### AJAX Wrapper

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

## Screen Specifications

### Profile Selector

Same as React but with:
- ES5 JavaScript event handlers
- Django template rendering
- No dark mode toggle

### Home Screen

Same as React but with:
- Light theme only
- No dark mode toggle in header
- Simpler animations (CSS transitions only)

### Search Results

Same as React but with:
- Server-side pagination option if client-side is problematic
- Simpler loading indicators

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

## Polyfills Required

```javascript
// legacy/static/legacy/js/polyfills.js

// Element.closest polyfill
if (!Element.prototype.closest) {
    Element.prototype.closest = function(s) {
        var el = this;
        do {
            if (el.matches(s)) return el;
            el = el.parentElement || el.parentNode;
        } while (el !== null && el.nodeType === 1);
        return null;
    };
}

// Element.matches polyfill
if (!Element.prototype.matches) {
    Element.prototype.matches =
        Element.prototype.matchesSelector ||
        Element.prototype.mozMatchesSelector ||
        Element.prototype.msMatchesSelector ||
        Element.prototype.oMatchesSelector ||
        Element.prototype.webkitMatchesSelector;
}
```

---

## Color Palette (Light Theme Only)

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

---

## Acceptance Criteria

1. Profile selector works (same API as React)
2. Home screen renders correctly on iOS 9
3. Search works with source filters
4. Recipe cards display consistently with React
5. Session maintains selected profile
6. All JavaScript is ES5 compatible
7. No console errors on iOS 9 Safari
8. Touch targets are accessible (44px minimum)

---

## Checkpoint (End of Phase)

```
[x] http://localhost/legacy/ - Profile selector loads
[x] Create/select profile - works same as React
[x] Home screen - renders correctly (light theme)
[x] Search - returns results with source filters
[x] Recipe cards - display images and metadata
[x] iOS 9 simulator - no JavaScript errors in console
[x] Touch targets - all buttons at least 44px
[x] pytest - Django view tests pass (157 tests)
```

---

## Testing Notes

### Automated Tests

```python
def test_legacy_profile_selector_renders():
    response = client.get('/legacy/')
    assert response.status_code == 200
    assert 'Who\'s cooking today?' in response.content.decode()

def test_legacy_home_renders_with_profile():
    client.post('/api/profiles/1/select/')
    response = client.get('/legacy/home/')
    assert response.status_code == 200
    assert 'Search recipes' in response.content.decode()

def test_legacy_search_renders_results():
    response = client.get('/legacy/search/?q=cookies')
    assert response.status_code == 200
    # Verify template includes recipe cards partial
    assert 'recipe-card' in response.content.decode()

def test_legacy_redirects_without_profile():
    # Clear session
    response = client.get('/legacy/home/')
    assert response.status_code == 302  # Redirect to profile selector
```

### Manual Testing

Test on:
- iOS 9 iPad (simulator or real device)
- Safari on iOS 9

### Manual Test Checklist

```
[ ] Profile selector loads
[ ] Can create new profile
[ ] Can select existing profile
[ ] Home screen loads after selection
[ ] Search bar accepts input
[ ] Search returns results
[ ] Recipe cards render correctly
[ ] Source filter chips work
[ ] Load more pagination works
[ ] No JavaScript errors in console
[ ] Touch targets are large enough
[ ] Text is readable (no zoom issues)
```

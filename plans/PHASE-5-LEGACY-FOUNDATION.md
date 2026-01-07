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
| C | 5.7-5.8 | Search + iOS 9 testing |

---

## Tasks

- [ ] 5.1 Legacy: Base template and CSS (light theme only)
- [ ] 5.2 Legacy: ES5 JavaScript modules (ajax, state, router)
- [ ] 5.3 Legacy: Profile selector screen
- [ ] 5.4 Legacy: Home screen with search bar
- [ ] 5.5 Legacy: Favorites/Discover toggle
- [ ] 5.6 Legacy: Recipe card partial
- [ ] 5.7 Legacy: Search results with source filters
- [ ] 5.8 Manual testing on iOS 9 simulator/device

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

## Testing Notes

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

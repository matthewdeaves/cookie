---
description: iOS 9 Safari JavaScript API limitations and safe alternatives
paths:
  - "apps/legacy/static/legacy/js/**/*"
---

# iOS 9 Safari API Reference

JavaScript APIs available and unavailable in Mobile Safari on iOS 9.3.6.

## Target Environment

| Property | Value |
|----------|-------|
| Browser | Mobile Safari |
| iOS Version | 9.3.6 (final for iPad 2/3/Mini 1) |
| WebKit Version | 601.1 |
| JavaScript Engine | JavaScriptCore (Nitro) |
| ECMAScript | ES5.1 (partial ES6) |

## Fetch API - NOT AVAILABLE

> **iOS 9 Safari does NOT support the Fetch API**

| API | iOS 9 | Alternative |
|-----|-------|-------------|
| `fetch()` | ❌ | `XMLHttpRequest` |
| `Request` | ❌ | Manual header construction |
| `Response` | ❌ | `xhr.responseText` |
| `Headers` | ❌ | `xhr.setRequestHeader()` |

### Safe Pattern: XMLHttpRequest

```javascript
// Cookie.ajax module wraps this pattern
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

    xhr.onerror = function() {
        callback(new Error('Network error'), null);
    };

    xhr.send(data ? JSON.stringify(data) : null);
}
```

## Promise - PARTIALLY AVAILABLE

> **iOS 9 Safari has native Promise support** but with limitations

| Feature | iOS 9 | Notes |
|---------|-------|-------|
| `new Promise()` | ✅ | Native support |
| `Promise.resolve()` | ✅ | |
| `Promise.reject()` | ✅ | |
| `Promise.all()` | ✅ | |
| `Promise.race()` | ✅ | |
| `Promise.prototype.then()` | ✅ | |
| `Promise.prototype.catch()` | ✅ | |
| `Promise.prototype.finally()` | ❌ | ES2018 - use `.then(f, f)` |
| `Promise.allSettled()` | ❌ | ES2020 |
| `Promise.any()` | ❌ | ES2021 |

### Callback Pattern Preferred

Despite Promise support, Cookie uses callbacks for consistency:

```javascript
// Preferred: Callback pattern
Cookie.ajax.get('/api/recipes/' + id, function(err, recipe) {
    if (err) {
        handleError(err);
        return;
    }
    renderRecipe(recipe);
});

// Avoid: Promise pattern (works but inconsistent with codebase)
```

## Date Parsing - BROKEN

> **iOS 9 Safari has strict date parsing requirements**

| Format | iOS 9 | Notes |
|--------|-------|-------|
| `2026-01-09T09:18:29Z` | ❌ | ISO 8601 with T fails |
| `2026-01-09 09:18:29` | ✅ | Space separator works |
| `2026/01/09 09:18:29` | ✅ | Slashes work |
| `2026-01-09T09:18:29.135626+00:00` | ❌ | Microseconds + offset fail |

### Safe Pattern: Cookie.utils.parseDate

```javascript
// From utils.js - handles iOS Safari date parsing
function parseDate(dateStr) {
    if (!dateStr) return new Date(NaN);
    // Convert ISO to Safari-parseable format:
    // - Replace T with space
    // - Remove microseconds (.135626)
    // - Remove timezone offset (+00:00)
    // - Replace dashes with slashes
    var normalized = dateStr
        .replace('T', ' ')
        .replace(/\.\d+/, '')
        .replace(/[+-]\d{2}:\d{2}$/, '')
        .replace('Z', '')
        .replace(/-/g, '/');
    return new Date(normalized);
}

// Usage
var date = Cookie.utils.parseDate(recipe.created_at);
```

## DOM APIs - NEED POLYFILLS

These are polyfilled in `polyfills.js`:

| API | Native iOS 9 | Polyfilled |
|-----|--------------|------------|
| `Element.closest()` | ❌ | ✅ |
| `Element.matches()` | Prefixed | ✅ |
| `Array.prototype.find()` | ❌ | ✅ |
| `Array.prototype.findIndex()` | ❌ | ✅ |
| `Array.prototype.includes()` | ❌ | ✅ |
| `String.prototype.includes()` | ❌ | ✅ |
| `Object.assign()` | ❌ | ✅ |

### Safe to Use After Polyfills Load

```javascript
// These work because polyfills.js loads first
var parent = el.closest('.container');
var found = arr.find(function(x) { return x.id === 5; });
var has = str.includes('search');
var merged = Object.assign({}, defaults, options);
```

## DOM APIs - NATIVELY AVAILABLE

| API | iOS 9 | Notes |
|-----|-------|-------|
| `document.querySelector()` | ✅ | |
| `document.querySelectorAll()` | ✅ | Returns static NodeList |
| `element.classList` | ✅ | `.add()`, `.remove()`, `.toggle()`, `.contains()` |
| `element.addEventListener()` | ✅ | |
| `element.getAttribute()` | ✅ | |
| `element.setAttribute()` | ✅ | |
| `element.innerHTML` | ✅ | Careful with XSS |
| `element.textContent` | ✅ | Safe for user content |
| `element.style` | ✅ | |
| `element.dataset` | ✅ | `data-*` attributes |
| `element.getBoundingClientRect()` | ✅ | |
| `JSON.parse()` | ✅ | |
| `JSON.stringify()` | ✅ | |

## DOM APIs - NOT AVAILABLE

| API | iOS 9 | Alternative |
|-----|-------|-------------|
| `element.append()` | ❌ | `appendChild()` |
| `element.prepend()` | ❌ | `insertBefore(el, firstChild)` |
| `element.remove()` | ❌ | `parentNode.removeChild(el)` |
| `element.replaceWith()` | ❌ | `parentNode.replaceChild()` |
| `element.before()` | ❌ | `insertBefore()` |
| `element.after()` | ❌ | `insertBefore(el, nextSibling)` |
| `NodeList.forEach()` | ❌ | `for` loop |
| `ChildNode.replaceWith()` | ❌ | Manual replacement |

### Safe Patterns

```javascript
// Remove element (iOS 9 safe)
if (el.parentNode) {
    el.parentNode.removeChild(el);
}

// Iterate NodeList (iOS 9 safe)
var items = document.querySelectorAll('.item');
for (var i = 0; i < items.length; i++) {
    items[i].classList.add('processed');
}

// Append multiple elements
var fragment = document.createDocumentFragment();
items.forEach(function(item) {
    var el = document.createElement('div');
    el.textContent = item.name;
    fragment.appendChild(el);
});
container.appendChild(fragment);
```

## Storage APIs

| API | iOS 9 | Notes |
|-----|-------|-------|
| `localStorage` | ✅ | 5MB limit, may be disabled in Private mode |
| `sessionStorage` | ✅ | Cleared when tab closes |
| `IndexedDB` | ✅ | But buggy, avoid if possible |
| `WebSQL` | ✅ | Deprecated but works |

### localStorage Quirks

```javascript
// Always wrap in try-catch (fails in Private Browsing)
function safeGetItem(key) {
    try {
        return localStorage.getItem(key);
    } catch (e) {
        return null;
    }
}

function safeSetItem(key, value) {
    try {
        localStorage.setItem(key, value);
        return true;
    } catch (e) {
        return false;
    }
}
```

## Event Handling

| Feature | iOS 9 | Notes |
|---------|-------|-------|
| `addEventListener` | ✅ | |
| `removeEventListener` | ✅ | |
| `event.preventDefault()` | ✅ | |
| `event.stopPropagation()` | ✅ | |
| `event.target` | ✅ | |
| `event.currentTarget` | ✅ | |
| Touch events | ✅ | `touchstart`, `touchmove`, `touchend` |
| Pointer events | ❌ | Use touch events |
| Passive listeners | ❌ | `{ passive: true }` ignored |

### Touch Event Pattern

```javascript
// Touch-friendly click handling
element.addEventListener('click', handler);  // Works for touch too

// For touch-specific behavior
element.addEventListener('touchstart', function(e) {
    // Touch began
    var touch = e.touches[0];
    startX = touch.clientX;
    startY = touch.clientY;
});

element.addEventListener('touchend', function(e) {
    // Touch ended
    e.preventDefault();  // Prevent ghost click
});
```

## Timers

| API | iOS 9 | Notes |
|-----|-------|-------|
| `setTimeout()` | ✅ | |
| `setInterval()` | ✅ | May pause when tab backgrounded |
| `clearTimeout()` | ✅ | |
| `clearInterval()` | ✅ | |
| `requestAnimationFrame()` | ✅ | |
| `cancelAnimationFrame()` | ✅ | |

### Timer Throttling

iOS Safari throttles timers in background tabs:

```javascript
// Timers may fire less frequently when:
// - Tab is in background
// - Device is in low power mode
// - Screen is off

// Use requestAnimationFrame for animations
function animate() {
    // Update animation
    requestAnimationFrame(animate);
}
```

## Console

| API | iOS 9 | Notes |
|-----|-------|-------|
| `console.log()` | ✅ | |
| `console.error()` | ✅ | |
| `console.warn()` | ✅ | |
| `console.info()` | ✅ | |
| `console.table()` | ❌ | Use `console.log(JSON.stringify())` |
| `console.group()` | ❌ | |
| `console.time()` | ✅ | |

## Not Available in iOS 9

These modern APIs do NOT exist:

- `IntersectionObserver`
- `MutationObserver` (partial, buggy)
- `ResizeObserver`
- `Web Components` (Custom Elements, Shadow DOM)
- `Service Workers`
- `Web Workers` (partial support)
- `WebRTC`
- `WebGL 2.0` (WebGL 1.0 works)
- `CSS.supports()`
- `matchMedia().addEventListener()`

## References

- iOS 9 Safari on caniuse: https://caniuse.com/?compare=ios_saf+9.3
- WebKit 601 features: https://webkit.org/
- MDN compatibility tables: Check "Safari iOS" column

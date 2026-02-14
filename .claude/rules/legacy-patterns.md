---
description: Approved patterns and architecture for the legacy frontend
paths:
  - "apps/legacy/static/legacy/js/**/*"
---

# Legacy Frontend Patterns

Established patterns for `apps/legacy/static/legacy/js/`. Follow these for consistency.

## Module Pattern: IIFE with Namespace

All modules use the revealing module pattern with the `Cookie` namespace:

```javascript
var Cookie = Cookie || {};

Cookie.moduleName = (function() {
    'use strict';

    // Private variables
    var privateVar = 'value';

    // Private functions
    function privateFunc() {
        return privateVar;
    }

    // Public API (revealed)
    return {
        publicMethod: function() {
            return privateFunc();
        }
    };
})();
```

### Why This Pattern?

1. **No ES6 modules** - `import`/`export` don't work in iOS 9
2. **No build step** - Code runs as-written, no bundler
3. **Namespace collision prevention** - All code under `Cookie.*`
4. **Encapsulation** - Private variables stay private

## File Organization

```
apps/legacy/static/legacy/js/
├── polyfills.js      # Load FIRST - ES5 polyfills
├── app.js            # Main app initialization
├── ajax.js           # Cookie.ajax - HTTP requests
├── state.js          # Cookie.state - Global state management
├── toast.js          # Cookie.toast - Notifications
├── timer.js          # Cookie.timer - Cooking timers
├── utils.js          # Cookie.utils - Shared utilities
├── ai-error.js       # Cookie.aiError - AI error handling
└── pages/
    ├── detail.js           # Recipe detail page (loader)
    ├── detail-core.js      # Core detail functionality
    ├── detail-init.js      # Detail page initialization
    ├── detail-display.js   # Display rendering
    ├── detail-scaling.js   # Serving adjustment
    ├── detail-tips.js      # AI tips
    ├── detail-favorites.js # Favorites functionality
    ├── detail-collections.js # Collections functionality
    ├── detail-remix.js     # Remix functionality
    ├── play.js             # Play mode (cooking view)
    ├── search.js           # Search page
    ├── home.js             # Home page
    ├── favorites.js        # Favorites list
    ├── collections.js      # Collections list
    ├── collection-detail.js # Collection detail
    ├── settings.js         # Settings page (loader)
    ├── settings-*.js       # Settings submodules
    └── profile-selector.js # Profile selection
```

## Script Loading Order

In `base.html`, scripts load in this order:

```html
<!-- 1. Polyfills FIRST (before any other JS) -->
<script src="{% static 'legacy/js/polyfills.js' %}"></script>

<!-- 2. Core utilities (no dependencies) -->
<script src="{% static 'legacy/js/utils.js' %}"></script>
<script src="{% static 'legacy/js/ajax.js' %}"></script>
<script src="{% static 'legacy/js/state.js' %}"></script>
<script src="{% static 'legacy/js/toast.js' %}"></script>

<!-- 3. Feature modules (may depend on utils/ajax) -->
<script src="{% static 'legacy/js/timer.js' %}"></script>
<script src="{% static 'legacy/js/ai-error.js' %}"></script>

<!-- 4. Page-specific modules (depend on all above) -->
{% block page_scripts %}{% endblock %}
```

## Callback Pattern (Not Promises)

All async operations use Node.js-style callbacks:

```javascript
// Pattern: callback(error, result)
Cookie.ajax.get('/api/recipes/' + id, function(err, recipe) {
    if (err) {
        Cookie.toast.error('Failed to load recipe');
        console.error(err);
        return;
    }
    renderRecipe(recipe);
});
```

### Why Callbacks?

1. **Explicit error handling** - Can't forget to handle errors
2. **No Promise chain complexity** - Easier to follow
3. **Consistent with existing code** - Don't mix patterns
4. **No async/await** - ES8 syntax not available

## Event Delegation

Use `Cookie.utils.delegate()` for event handling:

```javascript
// Instead of attaching handlers to each element:
Cookie.utils.delegate(container, 'click', {
    'delete-item': function(e) {
        var id = e.delegateTarget.getAttribute('data-id');
        deleteItem(id);
    },
    'edit-item': function(e) {
        var id = e.delegateTarget.getAttribute('data-id');
        editItem(id);
    }
});

// HTML uses data-action attribute:
// <button data-action="delete-item" data-id="123">Delete</button>
```

### Benefits

- One event listener instead of many
- Works with dynamically added elements
- Cleaner code organization

## XSS Prevention

Always escape user content before inserting into HTML:

```javascript
// UNSAFE - XSS vulnerability
element.innerHTML = '<div>' + recipe.name + '</div>';

// SAFE - Use Cookie.utils.escapeHtml
element.innerHTML = '<div>' + Cookie.utils.escapeHtml(recipe.name) + '</div>';

// SAFEST - Use textContent when possible
element.textContent = recipe.name;
```

### escapeHtml Implementation

```javascript
function escapeHtml(str) {
    if (!str) return '';
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
}
```

## DOM Element Creation

For complex HTML, use template strings (concatenation) with proper escaping:

```javascript
function renderRecipeCard(recipe) {
    var html = '<div class="recipe-card" data-id="' + recipe.id + '">' +
        '<h3>' + Cookie.utils.escapeHtml(recipe.name) + '</h3>' +
        '<p>' + Cookie.utils.escapeHtml(recipe.description || '') + '</p>' +
        (recipe.cook_time
            ? '<span class="time">' + Cookie.utils.formatTime(recipe.cook_time) + '</span>'
            : '') +
        '</div>';
    return html;
}

// Insert into DOM
container.innerHTML = recipes.map(renderRecipeCard).join('');
```

## State Management

Use `Cookie.state` for cross-module state:

```javascript
// Set state
Cookie.state.set('currentRecipe', recipe);
Cookie.state.set('selectedProfile', profileId);

// Get state
var recipe = Cookie.state.get('currentRecipe');

// Check state
if (Cookie.state.get('isPlaying')) {
    // ...
}
```

## Error Handling Pattern

```javascript
function loadRecipe(id, callback) {
    Cookie.ajax.get('/api/recipes/' + id, function(err, recipe) {
        if (err) {
            // Log for debugging
            console.error('Failed to load recipe:', err);

            // Show user-friendly message
            Cookie.toast.error('Could not load recipe. Please try again.');

            // Call callback with error (let caller decide what to do)
            if (callback) callback(err, null);
            return;
        }

        if (callback) callback(null, recipe);
    });
}
```

## Loading States

Show loading indicators during async operations:

```javascript
function fetchData() {
    var button = document.getElementById('fetch-btn');
    var originalText = button.textContent;

    // Show loading state
    button.textContent = 'Loading...';
    button.disabled = true;

    Cookie.ajax.get('/api/data', function(err, data) {
        // Restore button
        button.textContent = originalText;
        button.disabled = false;

        if (err) {
            Cookie.toast.error('Failed to fetch data');
            return;
        }

        renderData(data);
    });
}
```

## CSS Class Toggling

Use classList methods (supported in iOS 9):

```javascript
// Add class
element.classList.add('active');

// Remove class
element.classList.remove('active');

// Toggle class
element.classList.toggle('expanded');

// Check for class
if (element.classList.contains('hidden')) {
    // ...
}

// Multiple classes
element.classList.add('foo', 'bar');  // Works in iOS 9
```

## Hidden Elements

Use the `.hidden` CSS class consistently:

```javascript
// Show element
Cookie.utils.showElement(element);  // Removes 'hidden' class

// Hide element
Cookie.utils.hideElement(element);  // Adds 'hidden' class

// Manual toggle
element.classList.toggle('hidden', shouldHide);
```

```css
/* In CSS */
.hidden {
    display: none !important;
}
```

## Data Attributes

Use `data-*` attributes for element metadata:

```html
<button data-action="delete" data-recipe-id="123" data-confirm="true">
    Delete
</button>
```

```javascript
var button = e.delegateTarget;
var recipeId = button.getAttribute('data-recipe-id');
var needsConfirm = button.getAttribute('data-confirm') === 'true';
```

## Page Initialization Pattern

Each page module should have an `init()` function:

```javascript
Cookie.pageName = (function() {
    'use strict';

    function init() {
        // Check if we're on the right page
        var container = document.getElementById('page-specific-element');
        if (!container) return;

        // Initialize state
        setupEventListeners();
        loadInitialData();
    }

    function setupEventListeners() {
        // ...
    }

    function loadInitialData() {
        // ...
    }

    return {
        init: init
    };
})();

// Initialize when DOM ready
document.addEventListener('DOMContentLoaded', Cookie.pageName.init);
```

## Tab Switching Pattern

Use `Cookie.utils.handleTabSwitch()`:

```javascript
// Setup
document.querySelectorAll('.tab-toggle-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
        var tabName = btn.getAttribute('data-tab');
        Cookie.utils.handleTabSwitch(btn, tabName, {
            onTabChange: function(tab) {
                // Optional: Do something when tab changes
                if (tab === 'settings') {
                    loadSettings();
                }
            }
        });
    });
});
```

```html
<!-- HTML structure -->
<div class="tabs">
    <button class="tab-toggle-btn active" data-tab="info">Info</button>
    <button class="tab-toggle-btn" data-tab="settings">Settings</button>
</div>

<div id="tab-info" class="tab-content">
    <!-- Info content -->
</div>

<div id="tab-settings" class="tab-content hidden">
    <!-- Settings content -->
</div>
```

## Avoid These Patterns

```javascript
// ❌ DON'T: Use ES6 syntax
const x = 1;
let y = 2;
() => {};
`template ${literal}`;

// ❌ DON'T: Use Promises (even though they work)
fetch('/api').then(response => response.json());

// ❌ DON'T: Inline HTML without escaping
element.innerHTML = '<div>' + userInput + '</div>';

// ❌ DON'T: Direct DOM manipulation without null checks
document.getElementById('thing').classList.add('foo');  // May crash

// ❌ DON'T: Mix callback and Promise patterns
Cookie.ajax.get(url, callback).then(...);  // Confusing

// ❌ DON'T: Global variables without namespace
var myGlobal = 'value';  // Use Cookie.myModule instead

// ❌ DON'T: Attach events to dynamic elements directly
dynamicElement.addEventListener('click', handler);  // Use delegation
```

## Testing Changes

1. Make JS change
2. Restart containers: `docker compose down && docker compose up -d`
3. Verify file copied: `grep "your change" ./staticfiles/legacy/js/...`
4. Clear iPad Safari cache
5. Test on actual iPad

## References

- See `es5-compliance.md` for syntax restrictions
- See `ios9-safari-api.md` for API limitations
- See `ios9-safari-css.md` for CSS limitations

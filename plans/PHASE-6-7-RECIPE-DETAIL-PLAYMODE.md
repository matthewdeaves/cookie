# Phase 6-7: Recipe Detail, Play Mode & Collections UI

> **Goal:** Recipe viewing, cooking mode, and organization screens on both interfaces
> **Prerequisite:** Phase 4-5 complete
> **Deliverable:** Complete recipe experience with timers and organization

---

## Tasks

### Phase 6: Recipe Detail & Play Mode

- [ ] 6.1 React: Recipe detail screen with tabs (Ingredients, Instructions, Nutrition, Tips)
- [ ] 6.2 React: Serving adjustment UI (AI-powered, hidden without API key)
- [ ] 6.3 React: Play mode with smart timers
- [ ] 6.4 Legacy: Recipe detail screen with tabs
- [ ] 6.5 Legacy: Serving adjustment UI
- [ ] 6.6 Legacy: Play mode with timers (REQUIRED)

### Phase 7: Collections & Favorites UI

- [ ] 7.1 React: Favorites screen
- [ ] 7.2 React: Collections screens (list, detail, create)
- [ ] 7.3 Legacy: Favorites screen
- [ ] 7.4 Legacy: Collections screens

---

## Recipe Detail Screen

From Figma:
- Hero image with gradient overlay
- Title and rating overlay (top-left)
- Action buttons (bottom-right): Favorite, Add to Collection, Remix, Cook!
- **Add to Collection dropdown:** List of collections, "Create New Collection" option
- Collapsible meta info: Prep time, Cook time, Servings adjuster, Unit toggle
- **Tabs:** Ingredients | Instructions | Nutrition | Cooking Tips
- Numbered lists for ingredients and instructions
- **Nutrition tab:** Shows scraped data with "per X servings" label
- **Cooking Tips tab:** AI-generated tips as numbered list

### Serving Adjustment Rules

**CRITICAL:** AI-only, no frontend math fallback

Show serving adjuster ONLY when BOTH:
1. API key is configured
2. Recipe has servings value (not null)

When hidden: Simply don't render the +/- buttons and adjuster UI.

```python
# Backend check
def can_show_serving_adjustment(request, recipe):
    has_api_key = AppSettings.get_solo().openrouter_api_key
    has_servings = recipe.servings is not None
    return has_api_key and has_servings
```

### Unit Toggle

- Metric/Imperial toggle
- Persisted to profile settings
- Applied to all recipe views
- Uses AI conversion when displaying

---

## Play Mode

From Figma:
- Full-screen cooking interface
- Progress bar at top (step X of Y)
- Step counter
- Current instruction in large text
- Previous/Next navigation buttons
- Exit button (X)

### Timer Features

**Quick Timer Actions:**
- +5min, +10min, +15min buttons

**Smart Timer Suggestions:**
- Auto-detect time mentions in instruction text
- Regex patterns: "bake for 15 minutes", "simmer 30 mins", etc.
- Suggest timers based on detected times

**AI Timer Labels (Phase 8):**
- Generate descriptive names from step content
- Example: "Bake until golden" instead of "Timer 1"

**Timer Panel:**
- Multiple simultaneous timers
- Controls: play/pause, reset, delete
- Completion notification via toast
- Default browser notification sound (no custom audio files)

### Timer Implementation

```javascript
// Timer state (browser-only, no persistence)
const timerState = {
    timers: [],  // [{id, label, duration, remaining, isRunning}]
    add(label, duration) { /* ... */ },
    start(id) { /* ... */ },
    pause(id) { /* ... */ },
    reset(id) { /* ... */ },
    delete(id) { /* ... */ }
};

// Time detection regex
const TIME_PATTERNS = [
    /(\d+)\s*(?:minute|min|m)s?/gi,
    /(\d+)\s*(?:hour|hr|h)s?/gi,
    /(\d+)\s*(?:second|sec|s)s?/gi
];
```

### Play Mode Rules

- **Stateless:** No server-side state. Navigating away loses progress.
- **Browser-only timers:** Timers run in browser, not persisted
- **Audio alerts:** Default browser notification sound
- **REQUIRED on Legacy:** Timers MUST work on iOS 9

---

## Favorites Screen

From Figma:
- "Favorites" heading
- Recipe grid
- Empty state with CTA

---

## Collections Screens

### Collections List

From Figma:
- "Collections" heading
- Create Collection button (shows inline form)
- Collection cards with cover images and recipe counts
- Empty state

### Collection Detail

From Figma:
- Collection name and recipe count
- Delete Collection button with confirmation
- Recipe grid with remove buttons
- Empty state

### Add to Collection Flow

1. User clicks "Add to Collection" on recipe detail
2. Dropdown shows existing collections
3. Click collection to add recipe immediately
4. "Create New Collection" option at bottom
5. Creating new collection navigates to Collections screen
6. After creation, recipe auto-added to new collection

---

## Directory Structure Additions

### React

```
frontend/src/
├── screens/
│   ├── RecipeDetail.tsx
│   ├── PlayMode.tsx
│   ├── Favorites.tsx
│   ├── Collections.tsx
│   └── CollectionDetail.tsx
├── components/
│   ├── TimerWidget.tsx
│   ├── ServingAdjuster.tsx
│   ├── NutritionTab.tsx
│   └── AddToCollectionDropdown.tsx
└── hooks/
    └── useTimer.ts
```

### Legacy

```
legacy/
├── templates/legacy/
│   ├── recipe_detail.html
│   ├── play_mode.html
│   ├── favorites.html
│   ├── collections.html
│   ├── collection_detail.html
│   └── partials/
│       └── timer.html
└── static/legacy/
    ├── js/
    │   ├── timer.js           # Timer functionality (REQUIRED)
    │   └── pages/
    │       ├── detail.js
    │       ├── play.js
    │       └── collections.js
    └── css/
        └── play-mode.css
```

---

## Legacy Timer Implementation (ES5)

```javascript
// legacy/static/legacy/js/timer.js
var Cookie = Cookie || {};
Cookie.Timer = (function() {
    var timers = [];
    var nextId = 1;

    function Timer(label, durationSeconds) {
        this.id = nextId++;
        this.label = label;
        this.duration = durationSeconds;
        this.remaining = durationSeconds;
        this.isRunning = false;
        this.intervalId = null;
    }

    Timer.prototype.start = function() {
        var self = this;
        if (this.isRunning) return;
        this.isRunning = true;
        this.intervalId = setInterval(function() {
            self.remaining--;
            self.render();
            if (self.remaining <= 0) {
                self.complete();
            }
        }, 1000);
    };

    Timer.prototype.pause = function() {
        this.isRunning = false;
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    };

    Timer.prototype.reset = function() {
        this.pause();
        this.remaining = this.duration;
        this.render();
    };

    Timer.prototype.complete = function() {
        this.pause();
        // Browser notification sound
        try {
            new Notification('Timer Complete', { body: this.label });
        } catch (e) {
            alert('Timer Complete: ' + this.label);
        }
    };

    // ... render methods

    return {
        create: function(label, duration) {
            var timer = new Timer(label, duration);
            timers.push(timer);
            return timer;
        },
        getAll: function() { return timers; }
    };
})();
```

---

## Acceptance Criteria

1. Recipe detail shows all tabs with correct data
2. Serving adjustment works when API key configured and recipe has servings
3. Serving adjustment hidden otherwise (no error, just hidden)
4. Unit toggle persists to profile
5. Play mode navigates through steps
6. Multiple timers can run simultaneously
7. Timer completion triggers notification
8. Favorites screen shows user's favorites
9. Collections CRUD works
10. Add to Collection dropdown works
11. All features work on Legacy (iOS 9)

---

## Testing Notes

```python
def test_play_mode_step_navigation():
    # Create recipe with 5 steps
    recipe = Recipe.objects.create(
        title='Test',
        instructions=['Step 1', 'Step 2', 'Step 3', 'Step 4', 'Step 5']
    )
    # Test via frontend (manual) - navigate through steps

def test_serving_adjustment_hidden_without_api_key():
    AppSettings.objects.update(openrouter_api_key='')
    response = client.get('/api/settings/')
    assert response.json()['ai_available'] == False

def test_serving_adjustment_hidden_without_servings():
    recipe = Recipe.objects.create(title='Test', servings=None)
    # UI should not render adjuster
```

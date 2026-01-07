# Phase 7: Legacy Recipe Detail, Play Mode & Collections (iOS 9)

> **Goal:** Recipe viewing, cooking mode, and organization screens on Legacy
> **Prerequisite:** Phase 6 complete
> **Deliverable:** Complete recipe experience with timers and collections on iOS 9

---

## Session Scope

| Session | Tasks | Focus |
|---------|-------|-------|
| A | 7.1-7.2 | Recipe detail + serving adjustment |
| B | 7.3 | Play mode with timers (CRITICAL) |
| C | 7.4-7.5 | Favorites + Collections UI |
| D | 7.6 | iOS 9 manual testing |

---

## Tasks

- [ ] 7.1 Legacy: Recipe detail screen with tabs
- [ ] 7.2 Legacy: Serving adjustment UI
- [ ] 7.3 Legacy: Play mode with timers (REQUIRED - must work on iOS 9)
- [ ] 7.4 Legacy: Favorites screen
- [ ] 7.5 Legacy: Collections screens
- [ ] 7.6 Manual testing on iOS 9 simulator/device

---

## Recipe Detail Screen

Same functionality as React, implemented with:
- Django templates
- ES5 JavaScript
- Light theme only

### Serving Adjustment Rules

**CRITICAL:** AI-only, no frontend math fallback

```python
# Django template logic
{% if ai_available and recipe.servings %}
  {% include 'legacy/partials/serving_adjuster.html' %}
{% endif %}
```

---

## Play Mode (REQUIRED)

**Timers MUST work on iOS 9.** This is a hard requirement.

From Figma:
- Full-screen cooking interface
- Progress bar at top (step X of Y)
- Current instruction in large text
- Previous/Next navigation buttons
- Exit button (X)

### Timer Implementation (ES5)

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
        this.element = null;
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
        this.render();
    };

    Timer.prototype.pause = function() {
        this.isRunning = false;
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        this.render();
    };

    Timer.prototype.reset = function() {
        this.pause();
        this.remaining = this.duration;
        this.render();
    };

    Timer.prototype.complete = function() {
        this.pause();
        Cookie.Timer.notify(this.label);
    };

    Timer.prototype.formatTime = function() {
        var mins = Math.floor(this.remaining / 60);
        var secs = this.remaining % 60;
        return mins + ':' + (secs < 10 ? '0' : '') + secs;
    };

    Timer.prototype.render = function() {
        if (!this.element) return;
        var timeEl = this.element.querySelector('.timer-time');
        var btnEl = this.element.querySelector('.timer-toggle');
        if (timeEl) timeEl.textContent = this.formatTime();
        if (btnEl) btnEl.textContent = this.isRunning ? 'Pause' : 'Start';
    };

    // Notification handling
    function notify(label) {
        // Try Notification API first
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('Timer Complete', { body: label });
        } else {
            // Fallback to alert for iOS 9
            alert('Timer Complete: ' + label);
        }
        // Play sound if possible
        try {
            var audio = new Audio('/static/legacy/audio/timer.mp3');
            audio.play();
        } catch (e) {
            // Silent fail - some browsers don't support this
        }
    }

    // Request notification permission on page load
    function requestPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }

    return {
        create: function(label, duration) {
            var timer = new Timer(label, duration);
            timers.push(timer);
            return timer;
        },
        getAll: function() { return timers; },
        remove: function(id) {
            for (var i = 0; i < timers.length; i++) {
                if (timers[i].id === id) {
                    timers[i].pause();
                    timers.splice(i, 1);
                    return true;
                }
            }
            return false;
        },
        notify: notify,
        requestPermission: requestPermission
    };
})();
```

### Time Detection (ES5)

```javascript
// legacy/static/legacy/js/time-detect.js
var Cookie = Cookie || {};
Cookie.TimeDetect = (function() {
    var patterns = [
        { regex: /(\d+)\s*(?:minute|min|m)s?/gi, multiplier: 60 },
        { regex: /(\d+)\s*(?:hour|hr|h)s?/gi, multiplier: 3600 },
        { regex: /(\d+)\s*(?:second|sec|s)s?/gi, multiplier: 1 }
    ];

    function detect(text) {
        var times = [];
        for (var i = 0; i < patterns.length; i++) {
            var pattern = patterns[i];
            var match;
            pattern.regex.lastIndex = 0;
            while ((match = pattern.regex.exec(text)) !== null) {
                times.push(parseInt(match[1], 10) * pattern.multiplier);
            }
        }
        return times;
    }

    return { detect: detect };
})();
```

### Play Mode Rules

- **Stateless:** No server-side state
- **Browser-only timers:** Run in browser, not persisted
- **Audio alerts:** Default browser notification sound
- **iOS 9 compatible:** All JavaScript must be ES5

---

## Directory Structure

```
legacy/
├── templates/legacy/
│   ├── recipe_detail.html
│   ├── play_mode.html
│   ├── favorites.html
│   ├── collections.html
│   ├── collection_detail.html
│   └── partials/
│       ├── timer.html
│       ├── timer_panel.html
│       └── serving_adjuster.html
└── static/legacy/
    ├── js/
    │   ├── timer.js           # Timer functionality (REQUIRED)
    │   ├── time-detect.js     # Time detection
    │   └── pages/
    │       ├── detail.js
    │       ├── play.js
    │       └── collections.js
    └── css/
        └── play-mode.css
```

---

## Favorites Screen

From Figma:
- "Favorites" heading
- Recipe grid
- Empty state with CTA

Same functionality as React, ES5 implementation.

---

## Collections Screens

### Collections List

- "Collections" heading
- Create Collection button
- Collection cards with cover images
- Empty state

### Collection Detail

- Collection name and recipe count
- Delete Collection button with confirmation
- Recipe grid with remove buttons
- Empty state

### Add to Collection Flow

Same as React but with Django form handling and ES5 JavaScript.

---

## iOS 9 Specific Considerations

### CSS

```css
/* play-mode.css - iOS 9 compatible */
.play-mode {
    display: -webkit-flex;
    display: flex;
    -webkit-flex-direction: column;
    flex-direction: column;
    height: 100vh;
    height: -webkit-fill-available;
}

.timer-panel {
    -webkit-overflow-scrolling: touch;
    overflow-y: auto;
}

.timer-button {
    min-height: 44px;  /* Touch target */
    min-width: 44px;
}
```

### Touch Handling

```javascript
// Ensure touch events work on iOS 9
document.addEventListener('touchstart', function() {}, { passive: true });
```

---

## Acceptance Criteria

1. Recipe detail shows all tabs correctly
2. Serving adjustment visible only when API key + servings
3. Play mode navigates through steps
4. **Timers work on iOS 9** (hard requirement)
5. Multiple timers can run simultaneously
6. Timer completion triggers notification
7. Time detection suggests timers from step text
8. Favorites screen works
9. Collections CRUD works
10. All features work without JavaScript errors on iOS 9 Safari

---

## Checkpoint (End of Phase)

```
[ ] Recipe detail - all tabs render on iOS 9
[ ] Serving adjuster - shows/hides correctly
[ ] Play mode - step navigation works
[ ] CRITICAL: Timer countdown works on iOS 9
[ ] CRITICAL: Multiple timers run simultaneously on iOS 9
[ ] Timer completion - alert/notification appears
[ ] Time detection - suggestions appear for timed steps
[ ] Favorites - add/remove works
[ ] Collections - CRUD works
[ ] iOS 9 Safari console - no JavaScript errors
```

---

## Testing Checklist

### Manual Testing on iOS 9

```
Recipe Detail:
[ ] Page loads without errors
[ ] All tabs render correctly
[ ] Serving adjuster shows/hides based on conditions
[ ] Unit toggle works
[ ] Action buttons work (Favorite, Collection, Cook)

Play Mode:
[ ] Enters play mode from recipe detail
[ ] Step navigation works (prev/next)
[ ] Progress bar updates
[ ] Exit button works
[ ] Timer panel visible

Timers (CRITICAL):
[ ] Can add timer manually (+5, +10, +15 min)
[ ] Timer countdown works
[ ] Multiple timers run simultaneously
[ ] Pause/resume works
[ ] Reset works
[ ] Delete timer works
[ ] Completion notification appears
[ ] Time suggestions appear for steps with times

Collections:
[ ] Can create collection
[ ] Can add recipe to collection
[ ] Can view collection
[ ] Can remove recipe from collection
[ ] Can delete collection

Favorites:
[ ] Can add to favorites
[ ] Can remove from favorites
[ ] Favorites screen shows correct recipes
```

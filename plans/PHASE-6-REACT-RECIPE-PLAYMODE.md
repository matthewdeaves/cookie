# Phase 6: React Recipe Detail, Play Mode & Collections

> **Goal:** Recipe viewing, cooking mode, and organization screens on React
> **Prerequisite:** Phase 5 complete
> **Deliverable:** Complete recipe experience with timers and collections on React

---

## Session Scope

| Session | Tasks | Focus |
|---------|-------|-------|
| A | 6.1-6.2 | Recipe detail + serving adjustment |
| B | 6.3 | Play mode with timers |
| C | 6.4-6.5 | Favorites + Collections UI |
| D | 6.6 | Tests |

---

## Tasks

- [x] 6.1 React: Recipe detail screen with tabs (Ingredients, Instructions, Nutrition, Tips)
- [x] 6.2 React: Serving adjustment UI (AI-powered, hidden without API key)
- [x] 6.3 React: Play mode with smart timers
- [x] 6.4 React: Favorites screen
- [x] 6.5 React: Collections screens (list, detail, create)
- [ ] 6.6 Write tests for timer logic and collections API

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

```typescript
// React component logic
const canShowServingAdjustment = settings.ai_available && recipe.servings !== null;

{canShowServingAdjustment && (
  <ServingAdjuster recipe={recipe} />
)}
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

```typescript
// hooks/useTimer.ts
interface Timer {
  id: string;
  label: string;
  duration: number;  // seconds
  remaining: number;
  isRunning: boolean;
}

export function useTimers() {
  const [timers, setTimers] = useState<Timer[]>([]);

  const addTimer = (label: string, duration: number) => {
    setTimers(prev => [...prev, {
      id: crypto.randomUUID(),
      label,
      duration,
      remaining: duration,
      isRunning: false
    }]);
  };

  // ... start, pause, reset, delete methods

  return { timers, addTimer, startTimer, pauseTimer, resetTimer, deleteTimer };
}

// Time detection
const TIME_PATTERNS = [
  /(\d+)\s*(?:minute|min|m)s?/gi,
  /(\d+)\s*(?:hour|hr|h)s?/gi,
  /(\d+)\s*(?:second|sec|s)s?/gi
];

export function detectTimes(text: string): number[] {
  // Returns array of detected durations in seconds
}
```

### Play Mode Rules

- **Stateless:** No server-side state. Navigating away loses progress.
- **Browser-only timers:** Timers run in browser, not persisted
- **Audio alerts:** Default browser notification sound

---

## Favorites Screen

From Figma:
- "Favorites" heading
- Recipe grid
- Empty state with CTA: "No favorites yet. Browse recipes to add some!"

---

## Collections Screens

### Collections List

From Figma:
- "Collections" heading
- Create Collection button (shows inline form)
- Collection cards with cover images and recipe counts
- Empty state: "No collections yet. Create one to organize your recipes!"

### Collection Detail

From Figma:
- Collection name and recipe count
- Delete Collection button with confirmation
- Recipe grid with remove buttons
- Empty state: "This collection is empty. Add recipes from their detail pages."

### Add to Collection Flow

1. User clicks "Add to Collection" on recipe detail
2. Dropdown shows existing collections
3. Click collection to add recipe immediately
4. "Create New Collection" option at bottom
5. Creating new collection navigates to Collections screen
6. After creation, recipe auto-added to new collection

---

## Directory Structure

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
│   ├── TimerPanel.tsx
│   ├── ServingAdjuster.tsx
│   ├── NutritionTab.tsx
│   ├── TipsTab.tsx
│   └── AddToCollectionDropdown.tsx
└── hooks/
    └── useTimer.ts
```

---

## Acceptance Criteria

1. Recipe detail shows all tabs with correct data
2. Serving adjustment visible only when API key + servings present
3. Serving adjustment hidden otherwise (no error state)
4. Unit toggle persists to profile
5. Play mode navigates through steps correctly
6. Multiple timers can run simultaneously
7. Timer completion triggers notification + sound
8. Time detection suggests relevant timers
9. Favorites screen shows user's favorites
10. Collections CRUD works correctly
11. Add to Collection dropdown works
12. All tests pass

---

## Checkpoint (End of Phase)

```
[ ] Recipe detail - all 4 tabs display (Ingredients, Instructions, Nutrition, Tips)
[ ] Serving adjuster - visible with API key + servings, hidden otherwise
[ ] Unit toggle - switches metric/imperial, persists on refresh
[ ] Play mode - step navigation works (prev/next)
[ ] Add +5min timer - countdown starts
[ ] Run 2+ timers simultaneously - all decrement correctly
[ ] Timer completes - notification + sound triggered
[ ] Step with "bake 15 minutes" - timer suggestion appears
[ ] Favorites screen - shows favorited recipes
[ ] Create collection - appears in collections list
[ ] Add recipe to collection from detail page - works
[ ] npm test - timer and collections tests pass
```

---

## Testing Notes

```typescript
// Timer tests
describe('useTimer', () => {
  it('adds timer with correct initial state', () => {
    const { result } = renderHook(() => useTimers());
    act(() => result.current.addTimer('Test', 300));
    expect(result.current.timers[0].remaining).toBe(300);
    expect(result.current.timers[0].isRunning).toBe(false);
  });

  it('decrements remaining time when running', async () => {
    // ... test timer countdown
  });
});

// Time detection tests
describe('detectTimes', () => {
  it('detects minutes', () => {
    expect(detectTimes('bake for 15 minutes')).toContain(900);
  });

  it('detects multiple times', () => {
    const times = detectTimes('cook 5 min then bake 30 minutes');
    expect(times).toEqual([300, 1800]);
  });
});
```

```python
# Backend tests
def test_collection_crud():
    profile = Profile.objects.create(name='Test')
    # ... test create, read, update, delete

def test_add_recipe_to_collection():
    # ... test adding recipe to collection

def test_favorite_toggle():
    # ... test adding and removing favorites
```

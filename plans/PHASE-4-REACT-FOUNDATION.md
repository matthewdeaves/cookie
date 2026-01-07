# Phase 4: React Frontend Foundation

> **Goal:** Profile selection, home screen, and search working on React
> **Prerequisite:** Phase 3 complete
> **Deliverable:** Working React frontend with profile, home, and search screens

---

## Session Scope

| Session | Tasks | Focus |
|---------|-------|-------|
| A | 4.1-4.3 | React setup + profile selector |
| B | 4.4-4.6 | Home screen + recipe cards |
| C | 4.7-4.9 | Search + tests |

---

## Tasks

- [x] 4.1 Vite/React project setup with Tailwind v4, theme.css from Figma
- [x] 4.2 React: API client with fetch
- [x] 4.3 React: Profile selector screen
- [x] 4.4 React: Home screen with search bar
- [x] 4.5 React: Favorites/Discover toggle
- [x] 4.6 React: Basic recipe card component
- [x] 4.7 React: Dark/light theme toggle
- [x] 4.8 React: Search results with source filters and pagination
- [x] 4.9 Write tests for profile and search API integration

---

## Tech Stack

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

---

## Directory Structure

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
- **Header:** Burger menu, "Cookie" title, Dark mode toggle, Profile avatar
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

**Dark Mode:**
```css
--background: #2a2220;       /* Dark brown */
--foreground: #f5ebe0;       /* Light cream */
--primary: #8aa879;          /* Lighter sage green */
--secondary: #3d3531;        /* Dark brown */
--accent: #c66d7a;           /* Lighter pink */
```

---

## Acceptance Criteria

1. Profile selector works, persists selection to session
2. Home screen shows with search bar and toggle
3. Recipe cards display correctly with images and metadata
4. Search returns results with source filters
5. Dark/light theme toggle works and persists to profile
6. All API calls use the client.ts abstraction
7. Tests pass for profile selection and search

---

## Checkpoint (End of Phase)

```
[ ] http://localhost/ - Profile selector loads
[ ] Create new profile - appears in selector
[ ] Select profile - redirects to home screen
[ ] Home screen - search bar and Favorites/Discover toggle visible
[ ] Search "cookies" - results display as recipe cards
[ ] Source filter chips - clicking filters results
[ ] Dark/light toggle - theme changes immediately
[ ] Refresh page - theme preference persisted
[ ] npm test - all React tests pass
```

---

## Testing Notes

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

def test_theme_preference_persists():
    client.put('/api/profiles/1/', {'theme': 'dark'})
    response = client.get('/api/profiles/1/')
    assert response.json()['theme'] == 'dark'
```

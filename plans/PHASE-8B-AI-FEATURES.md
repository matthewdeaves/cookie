# Phase 8B: AI-Powered Features

> **Goal:** All 10 AI features integrated and working
> **Prerequisite:** Phase 8A complete
> **Deliverable:** Full AI-powered functionality across both interfaces

---

## Session Scope

| Session | Tasks | Focus |
|---------|-------|-------|
| A | 8B.1 | Recipe remix: Backend API + React UI |
| | ✓ | Verify: Remix creates recipe with `is_remix=True` |
| B | 8B.2 | Recipe remix: Legacy UI |
| C | 8B.3-8B.4 | Serving adjustment + tips generation |
| D | 8B.5-8B.6 | Discover feed + search ranking |
| E | 8B.7-8B.8 | Timer naming + remix suggestions |
| F | 8B.9-8B.10 | Selector repair + tests |

---

## Tasks

- [x] 8B.1 React: Recipe remix feature with AI suggestions modal
- [x] 8B.2 Legacy: Recipe remix feature
- [ ] 8B.3 Serving adjustment API (AI-only, not persisted)
- [ ] 8B.4 Tips generation service (cached in ai_tips field)
- [ ] 8B.5 Discover AI suggestions (3 types combined into feed)
- [ ] 8B.6 Search result ranking
- [ ] 8B.7 Timer naming
- [x] 8B.8 Remix suggestions (contextual prompts per recipe)
- [ ] 8B.9 Selector repair (AI-powered auto-fix for broken sources)
- [ ] 8B.10 Write tests for all AI features and fallback behavior

---

## Feature 1: Recipe Remix

### Flow
1. User views recipe detail
2. Clicks "Remix" button (hidden if no API key)
3. Modal shows 6 AI-generated suggestions + custom input
4. User selects or types modification
5. AI generates new recipe
6. New Recipe created with `is_remix=True`, `remix_profile=current_profile`

### AI Suggestions Modal
From Figma:
- "Remix This Recipe" header
- 6 suggestion chips (AI-generated via `remix_suggestions` prompt)
- "Or describe your own remix" text input
- "Create Remix" button
- Loading state during generation

### Remix Suggestions Prompt
- Input: Recipe title, ingredients, cuisine, category
- Output: Array of 6 contextual suggestions
- Examples: "Make it vegan", "Add more protein", "Make it spicy", "Use seasonal ingredients"

### Created Recipe Fields
```python
Recipe.objects.create(
    title=ai_response['title'],
    description=ai_response['description'],
    ingredients=ai_response['ingredients'],
    instructions=ai_response['instructions'],
    host='user-generated',
    site_name='User Generated',
    is_remix=True,
    remix_profile=current_profile,
    source_url=None,  # Nullable for remixes
)
```

### API Endpoints
```
POST   /api/ai/remix-suggestions/    # Get 6 suggestions for a recipe
POST   /api/ai/remix/                # Create remixed recipe
```

---

## Feature 2: Serving Adjustment

### Rules (from claude.md)
- AI-ONLY: No frontend math fallback
- Show ONLY when BOTH: API key configured AND recipe has servings
- NOT persisted: Computed on-the-fly, original recipe unchanged

### Flow
1. Recipe detail shows serving adjuster (if conditions met)
2. User clicks +/- to change target servings
3. Frontend calls API with original + target servings
4. AI returns scaled ingredients
5. Display scaled ingredients (don't save)

### API Endpoint
```
POST   /api/ai/scale/
{
    "recipe_id": 123,
    "original_servings": 4,
    "target_servings": 8,
    "unit_system": "metric"  // or "imperial"
}

Response:
{
    "ingredients": ["2 cups flour (scaled from 1 cup)", ...],
    "notes": ["Cooking time may need adjustment for larger batch"]
}
```

---

## Feature 3: Tips Generation

### Flow
1. Recipe scraped/imported
2. Background task generates tips via AI
3. Tips cached in `Recipe.ai_tips` field (JSONField)
4. Displayed in "Cooking Tips" tab on recipe detail

### Prompt Input
- Recipe title
- Ingredients list
- Instructions

### Output
- Array of 3-5 tip strings
- Example: ["Let the dough rest for fluffier results", "Don't overmix the batter"]

### API Endpoint
```
POST   /api/ai/tips/
{
    "recipe_id": 123
}

Response:
{
    "tips": ["Tip 1...", "Tip 2...", "Tip 3..."],
    "cached": true  // Whether this was from cache
}
```

---

## Feature 4-6: Discover AI Suggestions

Three AI prompt types that combine into one unified Discover feed:

| Type | Prompt | Input | Purpose |
|------|--------|-------|---------|
| `discover_favorites` | Based on user's favorites | Favorite recipes list | "More like what you love" |
| `discover_seasonal` | Based on current date | Current month, holidays | "Seasonal & holiday recipes" |
| `discover_new` | Opposite of favorites | Favorite cuisines/categories | "Try something different" |

### Discover Feed Logic
1. Fetch suggestions from all 3 types
2. Mix into unified feed
3. Each suggestion = search query to execute
4. Display results as recipe cards
5. Refresh daily (cache 24 hours)

### New User Behavior
- No favorites yet = only show `discover_seasonal`
- Based on current date and worldwide holidays

### Caching Model
```python
class AIDiscoverySuggestion(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    suggestion_type = models.CharField(max_length=50)  # favorites/seasonal/new
    search_query = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['profile', 'suggestion_type', 'created_at'])]
```

### API Endpoint
```
GET    /api/ai/discover/

Response:
{
    "suggestions": [
        {
            "type": "favorites",
            "title": "More Italian Classics",
            "description": "Based on your love of pasta dishes",
            "search_query": "authentic italian pasta recipes",
            "results": [...]  // Pre-fetched search results
        },
        ...
    ],
    "refreshed_at": "2024-01-15T10:00:00Z"
}
```

---

## Feature 7: Search Result Ranking

### Flow
1. User searches for recipes
2. Multi-site search returns raw results
3. AI ranks results by relevance to query
4. Return reordered results

### Prompt Input
- Search query
- Array of result titles/descriptions

### Output
- Array of indices in relevance order

### Implementation
```python
async def rank_results(query: str, results: list) -> list:
    # Prepare result summaries for AI
    summaries = [f"{i}: {r['title']} - {r['description'][:100]}"
                 for i, r in enumerate(results)]

    response = await ai_service.complete(
        prompt_type='search_ranking',
        context={'query': query, 'results': summaries}
    )

    # Reorder results by AI ranking
    ranking = response['ranking']  # [3, 1, 0, 2, ...]
    return [results[i] for i in ranking]
```

---

## Feature 8: Timer Naming

### Flow
1. User in Play Mode, on a step with detected time
2. User adds timer
3. AI generates descriptive label from step content
4. Timer created with AI label (or fallback to generic)

### Prompt Input
- Step text (instruction)
- Detected duration

### Output
- Short label (max 30 chars)
- Example: "Bake until golden" instead of "Timer 1"

### API Endpoint
```
POST   /api/ai/timer-name/
{
    "step_text": "Bake in preheated oven for 25 minutes or until golden brown",
    "duration_minutes": 25
}

Response:
{
    "label": "Bake until golden"
}
```

---

## Feature 9: Selector Repair

### Flow
1. Search source CSS selector fails (no results found)
2. System fetches sample HTML from source
3. AI analyzes HTML and suggests new selector
4. If confident, auto-update source's `result_selector`
5. Log change for admin review

### Prompt Input
- Sample HTML (truncated to relevant portion)
- Current broken selector
- Expected element type (recipe card)

### Output
```json
{
    "suggestions": [
        {"selector": ".recipe-card", "confidence": 0.9},
        {"selector": "[data-recipe-id]", "confidence": 0.7}
    ],
    "notes": "Site appears to have changed class names"
}
```

### Auto-Update Logic
```python
async def repair_selector(source: SearchSource) -> bool:
    html = await fetch_search_page(source)
    response = await ai_service.complete(
        prompt_type='selector_repair',
        context={'html': html[:50000], 'current_selector': source.result_selector}
    )

    if response['suggestions'] and response['suggestions'][0]['confidence'] > 0.8:
        source.result_selector = response['suggestions'][0]['selector']
        source.save()
        return True
    return False
```

---

## API Endpoints (All Features)

```
# Recipe Remix
POST   /api/ai/remix-suggestions/         # Get AI remix prompts for recipe
POST   /api/ai/remix/                     # Create recipe remix

# Serving Adjustment
POST   /api/ai/scale/                     # Scale ingredients (not persisted)

# Tips
POST   /api/ai/tips/                      # Get cooking tips (cached)

# Discover
GET    /api/ai/discover/                  # Get AI suggestions (daily refresh)

# Timer
POST   /api/ai/timer-name/                # Generate timer label

# Selector Repair (internal/admin)
POST   /api/ai/repair-selector/           # Attempt to fix broken selector
```

---

## Directory Structure Additions

```
apps/ai/
├── models.py               # Add: AIDiscoverySuggestion
└── services/
    ├── remix.py            # Recipe remix logic
    ├── scaling.py          # Ingredient scaling
    ├── tips.py             # Tips generation
    ├── discover.py         # AI discovery suggestions
    ├── ranking.py          # Search result ranking
    ├── timer.py            # Timer naming
    └── selector.py         # CSS selector repair
```

---

## Frontend Integration

### React Components to Update
- `RecipeDetail.tsx` - Add Remix button, serving adjuster visibility logic
- `PlayMode.tsx` - Add AI timer naming
- `Home.tsx` - Add Discover feed when on "Discover" toggle
- `Search.tsx` - Integrate AI ranking (transparent to user)

### Legacy Pages to Update
- `recipe_detail.html` - Add Remix button, serving adjuster
- `play_mode.html` - Add AI timer naming
- `home.html` - Add Discover feed
- Search ranking applied server-side (transparent)

### Visibility Rules
All AI features follow the same pattern:
```javascript
// React
const showAIFeatures = settings.ai_available;

// Legacy
{% if ai_available %}
  <!-- Show AI feature -->
{% endif %}
```

---

## Acceptance Criteria

1. Recipe remix creates new Recipe with `is_remix=True`
2. Remixes are per-profile (only visible to creator)
3. Remix shows "User Generated" badge
4. Serving adjustment works when API key + servings present
5. Serving adjustment hidden otherwise (no error, just hidden)
6. Tips are generated and cached per recipe
7. Tips tab shows AI-generated tips
8. Discover shows mixed feed from all 3 AI types
9. Discover refreshes daily (24-hour cache)
10. New users see seasonal suggestions only
11. Search results are AI-ranked for relevance
12. Timer naming generates descriptive labels
13. Remix suggestions show 6 contextual options
14. Selector repair can auto-fix broken sources
15. All AI features hidden when no API key

---

## Checkpoint (End of Phase)

```
[ ] Remix button - shows 6 AI suggestions + custom input
[ ] Create remix - new Recipe with is_remix=True, host="user-generated"
[ ] Remix visibility - only visible to creating profile
[ ] Serving adjustment - scales ingredients via AI
[ ] Tips tab - shows 3-5 AI-generated tips
[ ] Discover feed - shows suggestions from favorites/seasonal/new types
[ ] New user discover - only seasonal suggestions (no favorites)
[ ] Search ranking - results reordered by AI relevance
[ ] Timer naming - generates label like "Bake until golden"
[ ] Selector repair - suggests new selector for broken source
[ ] Remove API key - ALL AI features hidden (no buttons visible)
[ ] pytest - all AI feature tests pass
```

---

## Testing Notes

```python
@pytest.mark.asyncio
async def test_recipe_remix_creates_record():
    recipe = Recipe.objects.create(title='Original')
    profile = Profile.objects.create(name='Test')

    remix = await remix_service.create_remix(
        recipe_id=recipe.id,
        modification='Make it vegan',
        profile=profile
    )

    assert remix.is_remix == True
    assert remix.remix_profile == profile
    assert remix.host == 'user-generated'
    assert remix.source_url is None

def test_remix_per_profile_visibility():
    profile_a = Profile.objects.create(name='A')
    profile_b = Profile.objects.create(name='B')

    remix = Recipe.objects.create(
        title='Remix',
        is_remix=True,
        remix_profile=profile_a
    )

    # Query as profile B
    visible = Recipe.objects.filter(
        Q(is_remix=False) | Q(remix_profile=profile_b)
    )
    assert remix not in visible

def test_serving_adjustment_hidden_without_servings():
    recipe = Recipe.objects.create(title='Test', servings=None)
    response = client.get(f'/api/recipes/{recipe.id}/')
    assert response.json()['can_adjust_servings'] == False

def test_discover_for_new_user():
    profile = Profile.objects.create(name='New User')
    # No favorites
    response = client.get('/api/ai/discover/')
    suggestions = response.json()['suggestions']
    # Should only have seasonal type
    types = [s['type'] for s in suggestions]
    assert 'seasonal' in types
    assert 'favorites' not in types

@pytest.mark.asyncio
async def test_selector_repair():
    source = SearchSource.objects.create(
        host='example.com',
        result_selector='.old-selector'
    )
    # Mock AI response with high confidence
    success = await repair_selector(source)
    assert success
    source.refresh_from_db()
    assert source.result_selector != '.old-selector'
```

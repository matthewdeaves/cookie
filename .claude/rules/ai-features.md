---
description: AI feature integration patterns and fallback behavior
---

# AI Features Integration

Cookie has 10 AI-powered features using OpenRouter. This document defines integration patterns and fallback behavior.

## The 10 AI Features

| Feature | Purpose | Endpoint |
|---------|---------|----------|
| `recipe_remix` | Create recipe variations | `/api/recipes/{id}/remix` |
| `serving_adjustment` | Scale ingredients intelligently | `/api/recipes/{id}/adjust-servings` |
| `tips_generation` | Generate cooking tips | `/api/recipes/{id}/generate-tips` |
| `discover_favorites` | Suggest recipes based on favorites | `/api/recipes/discover/favorites` |
| `discover_seasonal` | Suggest seasonal/holiday recipes | `/api/recipes/discover/seasonal` |
| `discover_new` | Suggest outside comfort zone | `/api/recipes/discover/new` |
| `search_ranking` | Rank search results by relevance | `/api/recipes/search` (when AI enabled) |
| `timer_naming` | Generate descriptive timer labels | Frontend (Play Mode) |
| `remix_suggestions` | Generate contextual remix prompts | `/api/recipes/{id}/remix-suggestions` |
| `selector_repair` | Auto-fix broken CSS selectors | Background job |

## Fallback Behavior: Hide, Don't Disable

When OpenRouter API key is not configured OR API calls fail:

❌ **DON'T:**
- Show disabled buttons
- Show error messages to users
- Display "AI unavailable" warnings
- Show features in a disabled state

✅ **DO:**
- Hide ALL AI-dependent UI elements completely
- Return 400 Bad Request from backend if endpoints called
- Log errors server-side for debugging
- Gracefully degrade to non-AI experience

### Example: Serving Adjustment

**When AI Available:**
```html
<div class="serving-controls">
  <button onclick="adjustServings(-1)">−</button>
  <span>Serves 4</span>
  <button onclick="adjustServings(+1)">+</button>
</div>
```

**When AI Unavailable:**
```html
<!-- No serving controls rendered at all -->
```

**Backend Check:**
```python
def get_recipe_detail(request, recipe_id):
    recipe = Recipe.objects.get(id=recipe_id)
    ai_available = (
        settings.OPENROUTER_API_KEY and
        recipe.servings is not None
    )
    return {
        'recipe': recipe,
        'ai_features': {
            'serving_adjustment': ai_available,
            'tips_generation': bool(settings.OPENROUTER_API_KEY),
            # ...
        }
    }
```

## Special Case: Serving Adjustment

Serving adjustment has TWO requirements:

1. **API key configured** - OpenRouter must be available
2. **Recipe has servings** - Can't scale without base value

Hide serving controls if EITHER condition is false.

**Why AI-only?** Ingredient parsing is complex:
- "2-3 cloves garlic" - what's the base quantity?
- "1 cup flour, plus more for dusting" - how to scale the "more"?
- "Salt to taste" - not scalable
- "1 (14oz) can tomatoes" - scale can count or weight?

AI handles these ambiguities. Don't attempt frontend math fallback.

## Discover Features for New Users

When user has no favorites/history:
- `discover_favorites` - Return empty or show onboarding
- `discover_seasonal` - Show seasonal/holiday suggestions based on date
- `discover_new` - Cannot suggest "outside comfort zone" without history

Use `discover_seasonal` as the default for new users.

## Remixed Recipes

When `recipe_remix` creates a new recipe:

```python
remix = Recipe.objects.create(
    name=f"{original.name} (Remix)",
    is_remix=True,
    host="user-generated",
    site_name="User Generated",
    source_url=None,  # Nullable for remixes
    profile=request.user.profile,
    # ... other fields from AI response
)
```

**Visibility:** Remixes are per-profile (not shared between profiles).

**Orphaning:** If original recipe is deleted, remixes become standalone. They keep `is_remix=True` but have no link to parent.

## AI Prompts Configuration

The 10 AI prompts are stored in:
- **Database:** `AIPromptSettings` model
- **UI:** Settings → AI Prompts page
- **Default values:** Django migrations

Users can customize prompts (e.g., "make it spicier" for remix).

**Settings UI is layout reference only:** The Figma design shows 4 prompts as examples. Don't use Figma to determine which prompts exist - use this document's list of 10.

## Error Handling

### API Rate Limits
```python
try:
    result = openrouter_client.chat(prompt)
except RateLimitError:
    # Log for admin debugging
    logger.error(f"OpenRouter rate limit hit: {request.path}")
    # Return 429 to client
    return Response(
        {"error": "AI service temporarily unavailable"},
        status=429
    )
```

### API Failures
```python
try:
    result = openrouter_client.chat(prompt)
except OpenRouterError as e:
    # Log with details
    logger.error(f"OpenRouter error: {e}", exc_info=True)
    # Return generic error
    return Response(
        {"error": "Unable to process AI request"},
        status=503
    )
```

### Timeout Handling
```python
# Set reasonable timeout (30s for most, 60s for remix)
try:
    result = openrouter_client.chat(prompt, timeout=30)
except TimeoutError:
    return Response(
        {"error": "AI request timed out"},
        status=504
    )
```

## Testing AI Features

### Manual Testing
1. Set `OPENROUTER_API_KEY` in environment
2. Test each endpoint with real recipes
3. Verify UI hides features when key removed
4. Check error handling with invalid keys

### Automated Testing
```python
# Mock OpenRouter in tests
@patch('apps.recipes.services.openrouter_client')
def test_remix_recipe(mock_client):
    mock_client.chat.return_value = {...}
    response = client.post(f'/api/recipes/{recipe.id}/remix')
    assert response.status_code == 200
```

### CI Testing
- Backend tests run without API key (mocked)
- Frontend tests run without API key (features hidden)
- No actual API calls in CI (use mocks)

## Performance Considerations

- **Caching:** Consider caching AI responses (especially tips, remix suggestions)
- **Background jobs:** Run long AI tasks (selector repair) asynchronously
- **Timeouts:** Set appropriate timeouts for each feature type
- **Rate limiting:** Track API usage to avoid surprise bills

## References

- OpenRouter docs: https://openrouter.ai/docs
- Django async views: https://docs.djangoproject.com/en/5.0/topics/async/
- Background tasks: Consider Django-Q or Celery for production

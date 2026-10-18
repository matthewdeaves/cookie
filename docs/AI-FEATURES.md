# AI Features

Cookie calls the Anthropic API directly (official `anthropic` Python SDK) to provide optional AI-powered features. All AI features are hidden when no API key is configured.

## Configuration

### Setting Up

1. Get an API key from the [Anthropic Console](https://console.anthropic.com/settings/keys), or set the `ANTHROPIC_API_KEY` environment variable on the container (it takes precedence over a key saved in Settings)
2. Open Cookie Settings (gear icon)
3. Enter your API key in the AI Configuration section
4. Click "Test" to verify the key works
5. Save

### Supported Models

Only Anthropic models are supported. The model picker is populated from the Anthropic Models API (`client.models.list()`), and per-feature choices stored on each prompt are limited to:

| Model id | Name |
|----------|------|
| `claude-haiku-5-5` (default) | Claude Haiku 5.5 |
| `claude-sonnet-5-5` | Claude Sonnet 5.5 |
| `claude-opus-5-5` | Claude Opus 5.5 |

Requests use the Messages API (`client.messages.create` with `system=` and a single user message, `max_tokens=4096`, per-call timeout). Replies are parsed as JSON, tolerating a surrounding markdown code fence.

When upgrading from an OpenRouter-based version, migrations rename the stored key column and rewrite stored model ids (`anthropic/...haiku` -> `claude-haiku-5-5`, `...sonnet` -> `claude-sonnet-5-5`, `...opus` -> `claude-opus-5-5`; OpenAI/Google ids reset to `claude-haiku-5-5`). A previously saved OpenRouter key is kept but will not work with Anthropic: enter an Anthropic key (`sk-ant-...`).

Each AI feature can use a different model. Configure per-feature models in Settings.

## Feature Reference

| Feature | Endpoint | Purpose | Default Model |
|---------|----------|---------|---------------|
| Remix Suggestions | `POST /api/ai/remix-suggestions` | Generate 6 modification ideas for a recipe | Claude Haiku 5.5 |
| Recipe Remix | `POST /api/ai/remix` | Create a new recipe with AI modifications | Claude Haiku 5.5 |
| Serving Adjustment | `POST /api/ai/scale` | Scale ingredients and instructions | Claude Haiku 5.5 |
| Cooking Tips | `POST /api/ai/tips` | Generate 3-5 cooking tips | Claude Haiku 5.5 |
| Timer Naming | `POST /api/ai/timer-name` | Create descriptive 30-char timer labels | Claude Haiku 5.5 |
| Discovery (Seasonal) | `GET /api/ai/discover/{profile}/` | Seasonal recipe suggestions | Claude Haiku 5.5 |
| Discovery (Favorites) | `GET /api/ai/discover/{profile}/` | Suggestions based on your favorites | Claude Haiku 5.5 |
| Discovery (New) | `GET /api/ai/discover/{profile}/` | "Try something new" suggestions | Claude Haiku 5.5 |
| Search Ranking | Internal | Rank search results by relevance | Claude Haiku 5.5 |
| Nutrition Estimate | Internal | Estimate nutrition for remixed recipes | Claude Haiku 5.5 |
| Selector Repair | `POST /api/ai/repair-selector` | Fix broken CSS selectors (admin) | Claude Haiku 5.5 |

## Feature Details

### Recipe Remix

Transform any recipe with AI-suggested modifications:

1. Open a recipe
2. Click "Remix" button
3. Choose from 6 AI-generated suggestions (e.g., "Make it vegetarian", "Add Thai flavors")
4. Or enter your own modification request
5. AI generates a new recipe with modified ingredients and instructions

The remixed recipe is saved as a new recipe linked to your profile.

### Serving Adjustment

Scale recipes to different serving sizes:

1. Open a recipe
2. Click the servings control
3. Enter target servings
4. AI recalculates all ingredient quantities
5. Instructions are adjusted for timing and technique
6. Nutrition is recalculated if available

Results are cached per (recipe, profile, target_servings, unit_system).

### Cooking Tips

Get AI-generated cooking tips for any recipe:

1. Open a recipe
2. View the "Tips" section (auto-generated on first view)
3. Click "Regenerate" for new tips

Tips are cached in the recipe record for fast access.

### Timer Naming

During cooking mode, timers get descriptive names:

- Input: "Let the dough rest for 30 minutes" + 30 minutes
- Output: "Dough Resting" (max 30 characters)

### Discovery Suggestions

Personalized recipe discovery appears on the home screen:

- **Seasonal**: Recipes appropriate for current season
- **Based on Favorites**: Similar to recipes you've viewed
- **Try Something New**: Different cuisines and categories

Suggestions are cached for 24 hours per profile.

### Search Ranking

When searching across recipe sites, AI ranks results by:
- Relevance to search query
- Recipe completeness (images, ratings)
- Source reliability
- Title and description clarity

Falls back to image-first sorting if AI is unavailable.

## Prompt Customization

All AI prompts can be customized in Settings:

1. Go to Settings → AI Prompts
2. Select a prompt type
3. Edit the system prompt or user template
4. Choose a different model
5. Save changes

### Prompt Types

| Type | Purpose |
|------|---------|
| `recipe_remix` | Generate remixed recipe content |
| `serving_adjustment` | Scale ingredients and instructions |
| `tips_generation` | Generate cooking tips |
| `timer_naming` | Name cooking timers |
| `remix_suggestions` | Generate remix ideas |
| `discover_seasonal` | Seasonal recipe suggestions |
| `discover_favorites` | Personalized suggestions |
| `discover_new` | "Try something new" suggestions |
| `search_ranking` | Rank search results |
| `nutrition_estimate` | Estimate nutrition values |
| `selector_repair` | Fix broken CSS selectors |

### Template Variables

User prompt templates support placeholders:

```
{recipe_title} - Recipe name
{ingredients} - Ingredient list
{instructions} - Cooking steps
{modification} - User's modification request
{target_servings} - Desired serving count
{original_servings} - Original serving count
{unit_system} - "metric" or "imperial"
```

## Error Handling

### When API Key Not Configured

- Status: `available=false`, `configured=false`
- AI features hidden in UI
- Search falls back to image-first sorting

### When API Key Invalid

- Status: `available=false`, `configured=true`, `valid=false`
- AI features hidden in UI
- Error message shown in Settings
- Calls to backend fail with "API key is invalid"

### When AI Request Fails

- Graceful fallback where possible
- Error logged but doesn't break user flow
- Cached results returned if available

## Status Endpoint

Check AI availability:

```bash
curl http://localhost/api/ai/status
```

Response:
```json
{
  "available": true,
  "configured": true,
  "valid": true,
  "default_model": "claude-haiku-5-5",
  "error": null
}
```

## Privacy

- Only recipe text (ingredients, instructions, titles) is sent to the Anthropic API — no personal data
- API key stored encrypted in local database (Fernet), or set via `ANTHROPIC_API_KEY` env var
- All recipe data stays on your server
- See the [privacy policy](../apps/core/templates/core/privacy_policy.html) for full details

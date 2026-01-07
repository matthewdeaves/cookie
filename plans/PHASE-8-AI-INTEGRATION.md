# Phase 8: AI Integration

> **Goal:** All 10 AI features working
> **Prerequisite:** Phase 6-7 complete
> **Deliverable:** Full AI-powered features via OpenRouter

---

## Tasks

- [ ] 8.1 OpenRouter service with configurable models
- [ ] 8.2 AIPrompt model with 10 default prompts (data migration)
- [ ] 8.3 AI response schema validation
- [ ] 8.4 React: AI Prompts settings UI (all 10 editable)
- [ ] 8.5 React: Recipe remix feature with AI suggestions modal
- [ ] 8.6 Legacy: AI Prompts settings UI
- [ ] 8.7 Legacy: Recipe remix feature
- [ ] 8.8 Tips generation (cached in AIEnhancement)
- [ ] 8.9 Discover AI suggestions (3 types, daily refresh)
- [ ] 8.10 Search result ranking
- [ ] 8.11 Timer naming
- [ ] 8.12 Remix suggestions
- [ ] 8.13 Selector repair (AI-powered auto-fix)

---

## 10 AI Features

| # | Feature | Prompt Type | Cached? |
|---|---------|-------------|---------|
| 1 | Recipe Remix | `recipe_remix` | Yes (new Recipe record) |
| 2 | Serving Adjustment | `serving_adjustment` | No (on-the-fly) |
| 3 | Tips Generation | `tips_generation` | Yes (AIEnhancement) |
| 4 | Discover from Favorites | `discover_favorites` | Yes (AIDiscoverySuggestion) |
| 5 | Discover Seasonal | `discover_seasonal` | Yes (AIDiscoverySuggestion) |
| 6 | Discover Try Something New | `discover_new` | Yes (AIDiscoverySuggestion) |
| 7 | Search Ranking | `search_ranking` | No |
| 8 | Timer Naming | `timer_naming` | No |
| 9 | Remix Suggestions | `remix_suggestions` | No |
| 10 | Selector Repair | `selector_repair` | No |

---

## OpenRouter Configuration

### Available Models

```python
AVAILABLE_MODELS = [
    # Anthropic Claude
    ('anthropic/claude-3.5-haiku', 'Claude 3.5 Haiku (Fast)'),
    ('anthropic/claude-sonnet-4', 'Claude Sonnet 4'),
    ('anthropic/claude-opus-4', 'Claude Opus 4'),
    ('anthropic/claude-opus-4.5', 'Claude Opus 4.5'),
    # OpenAI GPT
    ('openai/gpt-4o', 'GPT-4o'),
    ('openai/gpt-4o-mini', 'GPT-4o Mini (Fast)'),
    ('openai/gpt-5-mini', 'GPT-5 Mini'),
    ('openai/o3-mini', 'o3 Mini (Reasoning)'),
    # Google Gemini
    ('google/gemini-2.5-pro-preview', 'Gemini 2.5 Pro'),
    ('google/gemini-2.5-flash-preview', 'Gemini 2.5 Flash (Fast)'),
]
```

### OpenRouter Service

```python
# apps/ai/services/openrouter.py

import httpx
from typing import Optional

class OpenRouterService:
    BASE_URL = 'https://openrouter.ai/api/v1/chat/completions'

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = 'anthropic/claude-3.5-haiku'
    ) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.BASE_URL,
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'HTTP-Referer': 'https://cookie-app.local',
                    'X-Title': 'Cookie Recipe App',
                },
                json={
                    'model': model,
                    'messages': [
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': user_prompt}
                    ]
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json()
```

---

## AI Fallback Behavior

**CRITICAL:** When API key is not configured or API fails:

### Frontend Behavior
- **HIDE all AI-dependent features** (don't show disabled/grayed state)
- Hide: Remix button, Serving adjuster, Discover suggestions, Timer AI naming
- Settings AI Prompts tab: Show "API key required" message

### Backend Behavior
- Return 503 Service Unavailable:
```json
{"error": "ai_unavailable", "message": "OpenRouter API key not configured"}
```

### No Fallbacks
- Serving adjustment does NOT fall back to frontend math
- All AI features are hidden, not degraded

---

## AIPrompt Model

```python
class AIPrompt(models.Model):
    PROMPT_TYPES = [
        ('recipe_remix', 'Recipe Remix'),
        ('serving_adjustment', 'Serving Adjustment'),
        ('tips_generation', 'Tips Generation'),
        ('discover_favorites', 'Discover from Favorites'),
        ('discover_seasonal', 'Discover Seasonal/Holiday'),
        ('discover_new', 'Discover Try Something New'),
        ('search_ranking', 'Search Result Ranking'),
        ('timer_naming', 'Timer Naming'),
        ('remix_suggestions', 'Remix Suggestions'),
        ('selector_repair', 'CSS Selector Repair'),
    ]

    prompt_type = models.CharField(max_length=50, choices=PROMPT_TYPES, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    system_prompt = models.TextField()
    user_prompt_template = models.TextField()  # Supports {placeholders}
    model = models.CharField(max_length=100, default='anthropic/claude-3.5-haiku')
    is_active = models.BooleanField(default=True)
```

---

## Default Prompts (Summary)

### 1. Recipe Remix
- Input: Original recipe + user modification request
- Output: `{"title", "ingredients", "instructions", "description"}`
- Creates NEW Recipe record with `is_remix=True`

### 2. Serving Adjustment
- Input: Recipe, original servings, target servings, unit system
- Output: `{"ingredients": [], "notes": []}`
- NOT persisted

### 3. Tips Generation
- Input: Recipe title, ingredients, instructions
- Output: JSON array of 3-5 tip strings
- Cached in AIEnhancement

### 4-6. Discover (Favorites/Seasonal/New)
- Output: `{"search_query", "title", "description"}`
- Daily refresh, cached in AIDiscoverySuggestion

### 7. Search Ranking
- Input: Query + results list
- Output: Array of indices in relevance order

### 8. Timer Naming
- Input: Step text, duration
- Output: `{"label": "Short label"}`

### 9. Remix Suggestions
- Input: Recipe details
- Output: Array of 6 suggestion strings

### 10. Selector Repair
- Input: HTML sample, broken selector
- Output: `{"suggestions": [], "confidence", "notes"}`

---

## API Endpoints

```
# AI Features
POST   /api/ai/remix/                     # Create recipe remix
POST   /api/ai/remix-suggestions/         # Get AI remix prompts for recipe
POST   /api/ai/scale/                     # Scale ingredients (not persisted)
POST   /api/ai/tips/                      # Get cooking tips (cached)
POST   /api/ai/timer-name/                # Generate timer label
GET    /api/ai/discover/                  # Get AI suggestions (daily refresh)

# AI Prompts Settings
GET    /api/settings/prompts/             # List all 10 AI prompts
PUT    /api/settings/prompts/{type}/      # Update specific prompt
POST   /api/settings/test-api-key/        # Test OpenRouter connection
GET    /api/settings/ai-status/           # Check if AI is available
```

---

## Response Schema Validation

Validate all AI responses against expected schemas:

```json
{
  "recipe_remix": {
    "type": "object",
    "required": ["title", "ingredients", "instructions", "description"]
  },
  "serving_adjustment": {
    "type": "object",
    "required": ["ingredients"]
  },
  "tips_generation": {
    "type": "array",
    "items": {"type": "string"},
    "minItems": 3,
    "maxItems": 5
  },
  "timer_naming": {
    "type": "object",
    "required": ["label"]
  },
  "remix_suggestions": {
    "type": "array",
    "items": {"type": "string"},
    "minItems": 6,
    "maxItems": 6
  }
}
```

---

## Directory Structure

```
apps/ai/
├── models.py               # AIPrompt, AIEnhancement, AIDiscoverySuggestion
├── api.py                  # REST endpoints
└── services/
    ├── openrouter.py       # OpenRouter API client
    ├── remix.py            # Recipe remix logic
    ├── scaling.py          # Ingredient scaling
    ├── discover.py         # AI discovery suggestions
    ├── ranking.py          # Search result ranking
    ├── timer.py            # Timer naming
    ├── suggestions.py      # Remix suggestions
    └── selector.py         # CSS selector repair

tooling/
├── ai-schemas.json         # JSON schemas for AI responses
└── lib/
    └── ai_validator.py     # Response validation
```

---

## Acceptance Criteria

1. All 10 AI prompts work with OpenRouter
2. Prompts are editable in Settings UI
3. Per-prompt model selection works
4. Recipe remix creates new Recipe with `is_remix=True`
5. Remixes are per-profile (only visible to creator)
6. Serving adjustment works when API key + servings present
7. Tips are cached per recipe
8. Discover shows mixed feed from all 3 AI types
9. Discover refreshes daily
10. New users see seasonal suggestions only
11. Timer naming generates descriptive labels
12. Remix suggestions show 6 options
13. Selector repair auto-fixes broken sources
14. All AI features hidden when no API key

---

## Testing Notes

```python
@pytest.mark.asyncio
async def test_recipe_remix():
    service = OpenRouterService(api_key='test_key')
    result = await service.complete(
        system_prompt=AIPrompt.objects.get(prompt_type='recipe_remix').system_prompt,
        user_prompt='Make this vegan...'
    )
    assert 'title' in result

def test_ai_hidden_without_key():
    AppSettings.objects.update(openrouter_api_key='')
    response = client.post('/api/ai/remix/', {'recipe_id': 1, 'prompt': 'test'})
    assert response.status_code == 503
    assert response.json()['error'] == 'ai_unavailable'

def test_remix_per_profile_visibility():
    profile_a = Profile.objects.create(name='A')
    remix = Recipe.objects.create(
        title='Remix',
        is_remix=True,
        remix_profile=profile_a
    )
    # Should not appear for profile B
```

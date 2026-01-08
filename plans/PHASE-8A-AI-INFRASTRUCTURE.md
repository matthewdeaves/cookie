# Phase 8A: AI Infrastructure & Settings

> **Goal:** OpenRouter integration and AI prompt management working
> **Prerequisite:** Phase 7 complete
> **Deliverable:** AI service ready for feature integration, prompts editable in Settings

---

## Session Scope

| Session | Tasks | Focus |
|---------|-------|-------|
| A | 8A.1-8A.3 | OpenRouter service + prompts + validation |
| B | 8A.4-8A.6 | Settings UI (both interfaces) + tests |

---

## Tasks

- [x] 8A.1 OpenRouter service with configurable models
- [x] 8A.2 AIPrompt model with 10 default prompts (data migration)
- [x] 8A.3 AI response schema validation
- [ ] 8A.4 React: AI Prompts settings UI (all 10 editable)
- [ ] 8A.5 Legacy: AI Prompts settings UI
- [ ] 8A.6 Write tests for OpenRouter service and schema validation

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

## 10 AI Features Overview

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
  },
  "discover_favorites": {
    "type": "object",
    "required": ["search_query", "title", "description"]
  },
  "discover_seasonal": {
    "type": "object",
    "required": ["search_query", "title", "description"]
  },
  "discover_new": {
    "type": "object",
    "required": ["search_query", "title", "description"]
  },
  "search_ranking": {
    "type": "array",
    "items": {"type": "integer"}
  },
  "selector_repair": {
    "type": "object",
    "required": ["suggestions", "confidence"]
  }
}
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

## API Endpoints (Infrastructure)

```
# AI Status & Settings
GET    /api/settings/ai-status/           # Check if AI is available
POST   /api/settings/test-api-key/        # Test OpenRouter connection
GET    /api/settings/prompts/             # List all 10 AI prompts
PUT    /api/settings/prompts/{type}/      # Update specific prompt
```

---

## Settings UI: AI Prompts Tab

From Figma:
- Section header explaining prompts
- Ten prompt cards:
  1. Recipe Remix
  2. Serving Adjustment
  3. Tips Generation
  4. Discover from Favorites
  5. Discover Seasonal/Holiday
  6. Discover Try Something New
  7. Search Result Ranking
  8. Timer Naming
  9. Remix Suggestions
  10. CSS Selector Repair
- Each card shows:
  - Title and description
  - Edit button
  - Current prompt (read-only view)
  - Current model badge
- Edit mode:
  - Textarea for prompt
  - Model dropdown (10 models)
  - Save/Cancel buttons

---

## Directory Structure

```
apps/ai/
├── __init__.py
├── models.py               # AIPrompt
├── api.py                  # Settings endpoints
├── migrations/
│   └── 0001_initial.py     # AIPrompt + 10 default prompts
└── services/
    ├── __init__.py
    ├── openrouter.py       # OpenRouter API client
    └── validator.py        # Response schema validation

tooling/
├── ai-schemas.json         # JSON schemas for AI responses
└── lib/
    └── ai_validator.py     # Response validation utility
```

---

## Default Prompts (Data Migration)

Create a data migration that seeds all 10 prompts with sensible defaults:

```python
# apps/ai/migrations/0002_seed_prompts.py

def seed_prompts(apps, schema_editor):
    AIPrompt = apps.get_model('ai', 'AIPrompt')

    prompts = [
        {
            'prompt_type': 'recipe_remix',
            'name': 'Recipe Remix',
            'description': 'Create variations of existing recipes',
            'system_prompt': 'You are a creative chef...',
            'user_prompt_template': 'Original recipe: {recipe}\n\nModification: {modification}',
        },
        # ... 9 more prompts
    ]

    for prompt_data in prompts:
        AIPrompt.objects.create(**prompt_data)
```

---

## Acceptance Criteria

1. OpenRouter service can make API calls with configurable models
2. All 10 AIPrompt records created via data migration
3. Response schema validation catches malformed AI responses
4. React: AI Prompts settings tab shows all 10 prompts
5. React: Can edit prompt text and select model per prompt
6. Legacy: AI Prompts settings tab works (same functionality)
7. API key test endpoint validates connection
8. AI status endpoint correctly reports availability
9. When no API key: Settings show "API key required" message

---

## Checkpoint (End of Phase)

```
[ ] GET /api/settings/prompts/ - returns all 10 prompts
[ ] AIPrompt.objects.count() == 10 in Django shell
[ ] POST /api/settings/test-api-key/ with valid key - returns success
[ ] POST /api/settings/test-api-key/ with invalid key - returns error
[ ] GET /api/settings/ai-status/ without key - returns available: false
[ ] React Settings > AI Prompts - shows all 10 prompts
[ ] Edit prompt in React - saves and persists
[ ] Legacy Settings > AI Prompts - same functionality works
[ ] Schema validation test - malformed response raises error
[ ] pytest - OpenRouter and validation tests pass
```

---

## Testing Notes

```python
@pytest.mark.asyncio
async def test_openrouter_service():
    service = OpenRouterService(api_key='test_key')
    # Mock the HTTP call
    result = await service.complete(
        system_prompt='You are helpful',
        user_prompt='Hello'
    )
    assert 'choices' in result

def test_ai_prompts_seeded():
    assert AIPrompt.objects.count() == 10
    assert AIPrompt.objects.filter(prompt_type='recipe_remix').exists()

def test_schema_validation_rejects_invalid():
    validator = AIResponseValidator()
    invalid_response = {'wrong': 'shape'}
    with pytest.raises(ValidationError):
        validator.validate('recipe_remix', invalid_response)

def test_ai_status_without_key():
    AppSettings.objects.update(openrouter_api_key='')
    response = client.get('/api/settings/ai-status/')
    assert response.json()['available'] == False
```

# Phase 8B: AI-Powered Features

> **Goal:** All 10 AI features integrated and working
> **Prerequisite:** Phase 8A complete
> **Deliverable:** Full AI-powered functionality across both interfaces

---

## Session Scope

| Session | Tasks | Focus | Status |
|---------|-------|-------|--------|
| A | 8B.1 | Recipe remix: Backend API + React UI | ✓ Complete |
| B | 8B.2 | Recipe remix: Legacy UI | ✓ Complete |
| C | 8B.3-8B.4 | Serving adjustment + tips generation | ✓ Complete |
| D | 8B.4-fix, 8B.5-8B.6 | Tips auto-generation + Discover feed + search ranking | ✓ Complete |
| E | 8B.7 | Timer naming for Play Mode | ✓ Complete |
| F | 8B.9-8B.10 | Selector repair + tests | ✓ Complete |
| G | 8B.11 | AI feature graceful degradation (no/invalid API key) | **Next** |

---

## Session F Implementation Summary

### Selector Repair (8B.9) - Complete

**Backend Service (`apps/ai/services/selector.py`):**
1. Created `repair_selector(source, html_sample, target, confidence_threshold, auto_update)` function
2. Uses existing `selector_repair` AI prompt (seeded in migration 0002)
3. Truncates HTML samples to 50KB to avoid token limits
4. Auto-updates selector if confidence >= threshold (default 0.8) and auto_update=True
5. Clears `needs_attention` flag on successful auto-update
6. Created `get_sources_needing_attention()` to list broken sources
7. Created `repair_all_broken_selectors()` for batch maintenance

**API Endpoints:**
1. `POST /api/ai/repair-selector` - Attempt repair for a specific source
2. `GET /api/ai/sources-needing-attention` - List sources with broken selectors

**Integration with Search Flow:**
- When search returns 0 results, `_record_failure()` increments `consecutive_failures`
- After 3 consecutive failures, `needs_attention=True` is set
- Selector repair is designed for admin/maintenance use, not automatic inline repair
- This avoids blocking search results while AI analyzes HTML
- **Future:** Automatic inline repair logged as FE-002 in FUTURE-ENHANCEMENTS.md

### AI Feature Tests (8B.10) - Complete

**Test Classes Added to `apps/ai/tests.py`:**

1. **SelectorRepairServiceTests** (5 tests):
   - Successful repair with auto-update
   - Low confidence doesn't auto-update
   - Auto-update disabled respects flag
   - HTML truncation to 50KB
   - Getting sources needing attention

2. **SelectorRepairAPITests** (7 tests):
   - Successful API call
   - Source not found (404)
   - Empty HTML validation (400)
   - AI unavailable (503)
   - Custom options passthrough
   - Sources needing attention list
   - Empty list when none need attention

3. **AIFeatureFallbackTests** (10 tests):
   - AI status shows unavailable without key
   - AI status shows available with key
   - Tips returns 503 when AI unavailable
   - Remix suggestions returns 503
   - Scale returns 503
   - Discover returns 503
   - Timer name returns 503
   - Service-level raises AIUnavailableError
   - Models endpoint returns empty list

4. **AIResponseErrorTests** (4 tests):
   - Tips returns 400 on AI error
   - Tips returns 400 on validation error
   - Remix returns 400 on AI error
   - Repair selector returns 400 on validation error

**Total:** 71 AI tests now pass (was 45 before Session F)

---

## Session E Implementation Summary

### Timer Naming (8B.7) - Complete

**Backend:**
1. Created `apps/ai/services/timer.py` with `generate_timer_name(step_text, duration_minutes)`
2. Added `POST /api/ai/timer-name` endpoint to `apps/ai/api.py`
3. Reused existing `timer_naming` prompt (already seeded in migration 0002)

**React Frontend:**
1. Updated `TimerPanel.tsx` to accept `aiAvailable` prop
2. When adding detected timers, calls AI API to get descriptive label
3. Shows loading spinner while fetching AI name
4. Falls back to formatted time if AI unavailable or fails
5. Updated `PlayMode.tsx` to fetch AI status and pass to TimerPanel

**Legacy Frontend:**
1. Updated `views.py` to pass `ai_available` to play_mode template
2. Updated `play_mode.html` to expose `AI_AVAILABLE` to JavaScript
3. Updated `play.js` `handleDetectedTimer()` to call AI API via XMLHttpRequest
4. Added loading CSS animation for button state
5. Falls back to time label if AI fails

**Result:** Timers now get descriptive names like "Bake until golden" instead of "25 min"

---

## Session D Implementation Summary

### What Already Exists (foundation complete)
- AI prompts seeded: `discover_favorites`, `discover_seasonal`, `discover_new`, `search_ranking`, `tips_generation`
- Validators defined in `apps/ai/services/validator.py` for all prompt types
- OpenRouterService working in `apps/ai/services/openrouter.py`
- Tips service exists in `apps/ai/services/tips.py`
- React `Home.tsx` has Discover tab UI (currently shows placeholder)

### Task 1: Tips Auto-Generation (8B.4-fix)

**Backend:**
1. Update `apps/scraping/scraper.py` to call `generate_tips()` after successful import
2. Make it non-blocking (fire-and-forget) so import response isn't delayed
3. Add `regenerate` parameter to `/api/ai/tips/` endpoint

**Frontend:**
1. React `RecipeDetail.tsx`: Change "Generate Tips" to "Regenerate Tips", show tips by default
2. Legacy `recipe_detail.html`: Same changes

### Task 2: Discover AI Suggestions (8B.5)

**Backend:**
1. Create `AIDiscoverySuggestion` model in `apps/ai/models.py` (see Feature 4-6 spec)
2. Create `apps/ai/services/discover.py` with `get_discover_suggestions(profile)`
3. Add `GET /api/ai/discover/` endpoint to `apps/ai/api.py`

**Frontend:**
1. React `Home.tsx`: Replace "AI Recommendations Coming Soon" with actual discover feed
2. Legacy `home.html`: Add discover section (can defer to Session E if needed)

### Task 3: Search Result Ranking (8B.6)

**Backend:**
1. Create `apps/ai/services/ranking.py` with `rank_results(query, results)`
2. Integrate into `apps/scraping/search.py` - after multi-site search, pass through AI ranking
3. Make ranking optional (skip if no API key configured)

**Frontend:**
- No changes needed (ranking is transparent to user)

---

## Tasks

- [x] 8B.1 React: Recipe remix feature with AI suggestions modal
- [x] 8B.2 Legacy: Recipe remix feature
- [x] 8B.3 Serving adjustment API (AI-only, cached per-profile)
- [x] 8B.4 Tips generation service (auto-generated on import, cached in ai_tips field)
- [x] 8B.5 Discover AI suggestions (3 types combined into feed)
- [x] 8B.6 Search result ranking
- [x] 8B.7 Timer naming
- [x] 8B.8 Remix suggestions (contextual prompts per recipe)
- [ ] 8B.9 Selector repair (AI-powered auto-fix for broken sources)
- [ ] 8B.10 Write tests for all AI features and fallback behavior
- [ ] 8B.11 Graceful degradation: Hide/disable AI features when no API key or invalid key

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
- **PERSISTED per-profile**: Results cached in `ServingAdjustment` model for efficiency
- Original recipe unchanged; adjustments stored separately

### Design Decisions
| Decision | Choice | Rationale |
|----------|--------|-----------|
| Persistence | Cached per-profile | Avoid redundant API calls; reuse results |
| Pre-generation | On-demand only | Save API costs |
| Scope | Ingredients + instruction notes | AI flags cooking time/pan size adjustments |
| Nutrition | Client-side calculation | Simple multiplication, no AI needed |
| Unit system | Per-profile preference | Same servings, different units = different cache entries |

### Data Model
```python
class ServingAdjustment(models.Model):
    recipe = ForeignKey(Recipe, on_delete=CASCADE, related_name='serving_adjustments')
    profile = ForeignKey('profiles.Profile', on_delete=CASCADE)
    target_servings = PositiveIntegerField()
    unit_system = CharField(max_length=10, choices=[('metric', 'Metric'), ('imperial', 'Imperial')])
    ingredients = JSONField(default=list)  # Scaled ingredient strings
    notes = JSONField(default=list)        # Cooking time/pan size notes
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['recipe', 'profile', 'target_servings', 'unit_system']
```

### Flow
1. Recipe detail shows serving adjuster (if conditions met)
2. User clicks +/- to change target servings
3. Frontend calls API with recipe_id + target servings
4. Backend checks for cached `ServingAdjustment`
5. Cache hit → return instantly (no API call)
6. Cache miss → call AI → persist result → return
7. Display scaled ingredients + notes (original unchanged)

### Nutrition Handling
- **Per-serving assumption**: Schema.org convention, most sites follow this
- **Display labels**: "Nutrition (per serving)" and "Total for X servings"
- **Missing nutrition**: Call `estimate_nutrition()` (reuse from remix), persist to Recipe
- **Calculation**: Client-side multiplication (per-serving × target servings)

### API Endpoint
```
POST   /api/ai/scale/
{
    "recipe_id": 123,
    "target_servings": 8,
    "unit_system": "metric"
}

Response:
{
    "target_servings": 8,
    "original_servings": 4,
    "ingredients": ["400g flour (scaled from 200g)", ...],
    "notes": ["Baking time may need 10-15 extra minutes", "Use a larger pan"],
    "nutrition_per_serving": {"calories": "250 kcal", ...},
    "nutrition_total": {"calories": "2000 kcal", ...},
    "cached": true
}
```

---

## Feature 3: Tips Generation

### Flow
1. Recipe scraped/imported successfully
2. **Auto-generate tips** immediately after import (non-blocking, fire-and-forget)
3. Tips cached in `Recipe.ai_tips` field (JSONField)
4. Tips ready and displayed when user views recipe detail
5. "Regenerate Tips" button allows user to refresh tips

### Auto-Generation Integration
```python
# In scraper.py after successful import:
from apps.ai.services.tips import generate_tips

# After recipe saved successfully
if ai_available:
    # Fire-and-forget - don't block the import response
    asyncio.create_task(generate_tips(recipe.id))
```

### Prompt Input
- Recipe title
- Ingredients list
- Instructions

### Output
- Array of 3-5 tip strings
- Example: ["Let the dough rest for fluffier results", "Don't overmix the batter"]

### Frontend Display
- **Tips tab**: Shows tips immediately if available (no "Generate" button needed)
- **Regenerate button**: Clears existing tips and generates fresh ones
- **Loading state**: Show spinner while regenerating
- **Empty state**: Only shown if AI unavailable or generation failed

### API Endpoint
```
POST   /api/ai/tips/
{
    "recipe_id": 123,
    "regenerate": false  // Optional: force regeneration
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

## Feature 10: Graceful Degradation (Session G)

### Goal
Ensure all AI features degrade gracefully when:
1. **No API key configured** - Features hidden completely
2. **Invalid API key** - Features hidden with helpful message
3. **API key becomes invalid at runtime** - Features fail gracefully with user guidance
4. **OpenRouter service unavailable** - Temporary errors handled smoothly

### Current State Analysis

**What exists:**
- `AppSettings.openrouter_api_key` stores the key
- `ai_available = bool(AppSettings.get().openrouter_api_key)` checks if key exists
- Templates/React use `ai_available` flag to show/hide features
- `AIUnavailableError` exception exists but only checks key presence, not validity

**What's missing:**
- No validation of API key validity on app startup or periodically
- No graceful handling of runtime API failures (401, 429, etc.)
- UI elements exist but may flash if key becomes invalid
- No user guidance when AI features fail

### Implementation Plan

#### Backend Changes

**1. Enhanced AI Status Endpoint (`/api/ai/status`)**
```python
# apps/ai/api.py
@router.get('/status')
def ai_status(request):
    """Check AI availability with optional key validation."""
    settings = AppSettings.get()
    has_key = bool(settings.openrouter_api_key)

    status = {
        'available': False,
        'configured': has_key,
        'valid': False,
        'default_model': settings.default_ai_model,
        'error': None,
        'error_code': None
    }

    if not has_key:
        status['error'] = 'No API key configured'
        status['error_code'] = 'no_api_key'
        return status

    # Validate key with lightweight API call (cached for 5 minutes)
    try:
        is_valid = OpenRouterService().validate_key_cached()
        status['valid'] = is_valid
        status['available'] = is_valid
        if not is_valid:
            status['error'] = 'API key is invalid or expired'
            status['error_code'] = 'invalid_api_key'
    except Exception as e:
        status['error'] = 'Unable to verify API key'
        status['error_code'] = 'connection_error'

    return status
```

**2. Cached Key Validation (`apps/ai/services/openrouter.py`)**
```python
import time
from functools import lru_cache

class OpenRouterService:
    _key_validation_cache = {}  # {key_hash: (is_valid, timestamp)}
    KEY_VALIDATION_TTL = 300  # 5 minutes

    def validate_key_cached(self) -> bool:
        """Validate API key with caching to avoid excessive API calls."""
        key = self.api_key
        if not key:
            return False

        key_hash = hash(key)
        now = time.time()

        # Check cache
        if key_hash in self._key_validation_cache:
            is_valid, timestamp = self._key_validation_cache[key_hash]
            if now - timestamp < self.KEY_VALIDATION_TTL:
                return is_valid

        # Validate with API
        try:
            is_valid = self.test_connection()
            self._key_validation_cache[key_hash] = (is_valid, now)
            return is_valid
        except Exception:
            return False

    @classmethod
    def invalidate_key_cache(cls):
        """Clear validation cache (call when key is updated)."""
        cls._key_validation_cache.clear()
```

**3. Graceful Error Handling in AI Endpoints**
```python
# Decorator for all AI endpoints
def handle_ai_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AIUnavailableError:
            return 503, {
                'error': 'ai_unavailable',
                'message': 'AI features are not available. Please configure your API key in Settings.',
                'action': 'configure_key'
            }
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                # Invalid key - invalidate cache
                OpenRouterService.invalidate_key_cache()
                return 401, {
                    'error': 'invalid_api_key',
                    'message': 'Your API key is invalid or has expired. Please update it in Settings.',
                    'action': 'update_key'
                }
            elif e.response.status_code == 429:
                return 429, {
                    'error': 'rate_limited',
                    'message': 'AI request limit exceeded. Please try again in a few minutes.',
                    'action': 'retry_later'
                }
            elif e.response.status_code == 402:
                return 402, {
                    'error': 'insufficient_credits',
                    'message': 'Your OpenRouter account has insufficient credits.',
                    'action': 'add_credits'
                }
            raise
        except requests.exceptions.ConnectionError:
            return 503, {
                'error': 'connection_error',
                'message': 'Unable to connect to AI service. Please check your internet connection.',
                'action': 'retry'
            }
    return wrapper
```

**4. Clear Cache on Key Update**
```python
# apps/ai/api.py - in save_api_key endpoint
@router.post('/save-api-key')
def save_api_key(request, data: ApiKeySchema):
    settings = AppSettings.get()
    settings.openrouter_api_key = data.api_key
    settings.save()

    # Invalidate validation cache
    OpenRouterService.invalidate_key_cache()

    return {'success': True, 'message': 'API key saved successfully'}
```

#### React Frontend Changes

**1. AI Status Context (`frontend/src/contexts/AIStatusContext.tsx`)**
```typescript
interface AIStatusContextType {
  available: boolean
  configured: boolean
  valid: boolean
  error: string | null
  errorCode: string | null
  loading: boolean
  refresh: () => Promise<void>
}

export const AIStatusProvider = ({ children }) => {
  const [status, setStatus] = useState<AIStatus | null>(null)
  const [loading, setLoading] = useState(true)

  const refresh = async () => {
    try {
      const data = await api.ai.status()
      setStatus(data)
    } catch {
      setStatus({ available: false, configured: false, valid: false })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
    // Refresh every 5 minutes
    const interval = setInterval(refresh, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])

  return (
    <AIStatusContext.Provider value={{ ...status, loading, refresh }}>
      {children}
    </AIStatusContext.Provider>
  )
}
```

**2. Update Components to Use Context**

All AI-dependent components should:
- Check `aiStatus.available` before showing AI features
- Handle error responses with appropriate UI feedback
- Provide actionable guidance to users

**RecipeDetail.tsx:**
```typescript
const { available: aiAvailable, errorCode } = useAIStatus()

// Hide remix/tips/scaling buttons completely if not available
{aiAvailable && (
  <button onClick={openRemixModal}>Remix</button>
)}

// Handle API errors in catch blocks
catch (error) {
  if (error.errorCode === 'invalid_api_key') {
    toast.error('API key issue', {
      description: 'Please update your API key in Settings',
      action: {
        label: 'Settings',
        onClick: () => navigate('/settings')
      }
    })
  }
}
```

**Home.tsx (Discover tab):**
```typescript
const { available: aiAvailable } = useAIStatus()

// Show helpful message instead of broken UI
{!aiAvailable ? (
  <div className="empty-state">
    <Bot className="h-12 w-12 text-muted-foreground" />
    <p>AI-powered recipe discovery requires an API key</p>
    <Button onClick={() => navigate('/settings')}>
      Configure API Key
    </Button>
  </div>
) : (
  <DiscoverFeed />
)}
```

**Settings.tsx:**
```typescript
// Show validation status
{aiStatus.configured && !aiStatus.valid && (
  <div className="warning-banner">
    <AlertCircle />
    <span>Your API key appears to be invalid. Please update it.</span>
  </div>
)}
```

#### Legacy Frontend Changes

**1. Update `ai_available` Context Variable**

The `ai_available` flag passed to templates should reflect actual validity, not just presence.

```python
# apps/legacy/views.py
def get_ai_context():
    """Get AI availability context for templates."""
    settings = AppSettings.get()
    has_key = bool(settings.openrouter_api_key)

    # For legacy, just check key presence (no async validation)
    # Runtime errors handled by JavaScript
    return {
        'ai_available': has_key,
        'ai_configured': has_key,
    }
```

**2. JavaScript Error Handling (`apps/legacy/static/legacy/js/pages/detail.js`)**
```javascript
function handleAIError(error, response) {
    var errorCode = response && response.error_code;
    var message = response && response.message || 'AI feature unavailable';

    switch (errorCode) {
        case 'invalid_api_key':
            Cookie.toast.error('API key issue - please check Settings');
            // Optionally hide AI buttons
            hideAIFeatures();
            break;
        case 'rate_limited':
            Cookie.toast.warning('Too many requests - please wait a moment');
            break;
        case 'insufficient_credits':
            Cookie.toast.error('OpenRouter credits depleted');
            break;
        default:
            Cookie.toast.error(message);
    }
}

function hideAIFeatures() {
    document.querySelectorAll('[data-ai-feature]').forEach(function(el) {
        el.style.display = 'none';
    });
}
```

**3. Template Updates**

Add `data-ai-feature` attributes to AI-dependent elements:
```html
<!-- recipe_detail.html -->
<button data-ai-feature class="btn-remix" onclick="openRemixModal()">
    Remix
</button>

{% include 'legacy/partials/serving_adjuster.html' %}
<!-- Add data-ai-feature to serving adjuster container -->
```

### Error Codes Reference

| Code | HTTP | Meaning | User Action |
|------|------|---------|-------------|
| `no_api_key` | 503 | No key configured | Configure in Settings |
| `invalid_api_key` | 401 | Key rejected by OpenRouter | Update key in Settings |
| `rate_limited` | 429 | Too many requests | Wait and retry |
| `insufficient_credits` | 402 | OpenRouter credits depleted | Add credits on OpenRouter |
| `connection_error` | 503 | Network/service issue | Check connection, retry |
| `ai_disabled` | 503 | AI prompt disabled by admin | Contact admin |

### UI Behavior Matrix

| Scenario | Buttons Visible | On Attempt | User Guidance |
|----------|-----------------|------------|---------------|
| No key configured | Hidden | N/A | Settings link in Discover empty state |
| Invalid key | Hidden* | N/A | Warning in Settings, Discover empty state |
| Valid key | Visible | Works | N/A |
| Runtime 401 | Visible→Hidden | Toast + hide | "API key invalid - check Settings" |
| Runtime 429 | Visible | Toast | "Rate limited - try again shortly" |
| Runtime 402 | Visible | Toast | "Add credits on OpenRouter" |
| Connection error | Visible | Toast | "Connection error - retry" |

*After initial status check on page load

### Testing Scenarios

```python
def test_ai_status_no_key():
    """Status returns unavailable when no key configured."""
    AppSettings.get().openrouter_api_key = ''
    response = client.get('/api/ai/status')
    assert response.json()['available'] == False
    assert response.json()['error_code'] == 'no_api_key'

def test_ai_status_invalid_key(mock_openrouter):
    """Status returns unavailable when key is invalid."""
    mock_openrouter.return_value.status_code = 401
    response = client.get('/api/ai/status')
    assert response.json()['available'] == False
    assert response.json()['error_code'] == 'invalid_api_key'

def test_ai_endpoint_returns_503_no_key():
    """AI endpoints return 503 when no key configured."""
    AppSettings.get().openrouter_api_key = ''
    response = client.post('/api/ai/tips/', {'recipe_id': 1})
    assert response.status_code == 503
    assert response.json()['error'] == 'ai_unavailable'

def test_ai_endpoint_handles_runtime_401(mock_openrouter):
    """AI endpoints handle runtime 401 gracefully."""
    mock_openrouter.side_effect = HTTPError(response=Mock(status_code=401))
    response = client.post('/api/ai/tips/', {'recipe_id': 1})
    assert response.status_code == 401
    assert response.json()['action'] == 'update_key'

def test_key_cache_invalidated_on_save():
    """Saving new key invalidates validation cache."""
    OpenRouterService._key_validation_cache['old'] = (True, time.time())
    client.post('/api/ai/save-api-key', {'api_key': 'new-key'})
    assert len(OpenRouterService._key_validation_cache) == 0
```

### Acceptance Criteria

1. No API key → All AI buttons/tabs hidden, helpful empty states shown
2. Invalid API key → Same as no key, plus warning in Settings
3. Valid key → All AI features visible and functional
4. Runtime 401 → Toast notification, buttons hidden, guidance to Settings
5. Runtime 429 → Toast notification, buttons remain, retry guidance
6. Key validation cached (5 min TTL) to avoid excessive API calls
7. Saving new key clears validation cache immediately
8. Legacy and React UIs behave consistently
9. Error messages are user-friendly with actionable guidance

---

## API Endpoints (All Features)

```
# Recipe Remix
POST   /api/ai/remix-suggestions/         # Get AI remix prompts for recipe
POST   /api/ai/remix/                     # Create recipe remix

# Serving Adjustment
POST   /api/ai/scale/                     # Scale ingredients (cached per-profile)

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

apps/recipes/
├── models.py               # Add: ServingAdjustment model
```

---

## Frontend Integration

### React Components to Update
- `RecipeDetail.tsx` - Add Remix button, serving adjuster, tips display with "Regenerate Tips" button
- `PlayMode.tsx` - Add AI timer naming
- `Home.tsx` - Add Discover feed when on "Discover" toggle
- `Search.tsx` - Integrate AI ranking (transparent to user)

### Legacy Pages to Update
- `recipe_detail.html` - Add Remix button, serving adjuster, tips display with "Regenerate Tips" button
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
6. Tips are auto-generated on recipe import (non-blocking)
7. Tips tab shows tips immediately when available, with "Regenerate Tips" button
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
[ ] Tips auto-generated on import, displayed immediately with "Regenerate" button
[ ] Discover feed - shows suggestions from favorites/seasonal/new types
[ ] New user discover - only seasonal suggestions (no favorites)
[ ] Search ranking - results reordered by AI relevance
[ ] Timer naming - generates label like "Bake until golden"
[ ] Selector repair - suggests new selector for broken source
[ ] Remove API key - ALL AI features hidden (no buttons visible)
[ ] Invalid API key - helpful error message, guidance to Settings
[ ] Runtime API errors - graceful degradation with user-friendly toasts
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

def test_serving_adjustment_cached():
    """Test that serving adjustments are cached per-profile."""
    recipe = Recipe.objects.create(title='Test', servings=4, ingredients=['1 cup flour'])
    profile = Profile.objects.create(name='Test')

    # First call - should create cache entry
    response1 = client.post('/api/ai/scale/', {'recipe_id': recipe.id, 'target_servings': 8})
    assert response1.json()['cached'] == False

    # Second call - should return cached
    response2 = client.post('/api/ai/scale/', {'recipe_id': recipe.id, 'target_servings': 8})
    assert response2.json()['cached'] == True

    # Verify ServingAdjustment was created
    assert ServingAdjustment.objects.filter(recipe=recipe, profile=profile, target_servings=8).exists()

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

---
paths:
  - "apps/ai/**/*.py"
  - "apps/recipes/**/*.py"
  - "frontend/src/**/*.{ts,tsx}"
  - "apps/legacy/static/legacy/js/**/*.js"
---

# AI Features Rules

Cookie has 10 AI features using OpenRouter: recipe_remix, serving_adjustment, tips_generation, discover_favorites, discover_seasonal, discover_new, search_ranking, timer_naming, remix_suggestions, selector_repair.

## Fallback: Hide, Don't Disable

When OpenRouter API key is not configured OR API calls fail:

- **Hide** all AI-dependent UI elements completely — never show disabled buttons, error messages, or "AI unavailable" warnings
- Backend returns 400 if AI endpoints called without a key
- Log errors server-side only
- The app must be fully usable without any AI configuration

## Serving Adjustment

Requires BOTH: (1) API key configured AND (2) recipe has `servings` value. Hide controls if either is false. Do NOT attempt frontend math fallback — ingredient parsing is too ambiguous for simple scaling.

## Remixed Recipes

- `is_remix=True`, `host="user-generated"`, `source_url=None`
- Per-profile visibility (not shared)
- If original deleted, remix becomes standalone (orphaned)

## AI Prompts

Stored in `AIPromptSettings` model, customizable via Settings UI (admin-only in passkey mode). Default values seeded via migrations. There are exactly 10 prompts — use this list, not Figma mockups.

## Error Handling

- Rate limits: return 429
- API failures: return 503, log with `exc_info=True`
- Timeouts: 30s default, 60s for remix, return 504

## Testing

Mock OpenRouter in all tests — no real API calls in CI.

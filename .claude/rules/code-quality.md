---
description: Code quality gates - IMMUTABLE limits that must never be raised
---

# Code Quality Gates

These quality limits are **IMMUTABLE**. When exceeded, REFACTOR the code - NEVER raise the limits in linter configs.

## Limits

| Metric | Limit | Applies To |
|--------|-------|------------|
| Max function length | 100 lines (prefer 50) | All code |
| Max function complexity | 15 (cyclomatic) | All code |
| Max file size | 500 lines | All code |

## When Limits Are Exceeded

❌ **DON'T:**
- Raise `max-lines-per-function` in `eslint.config.js`
- Raise `complexity` threshold in ESLint config
- Raise `max-complexity` in Radon config
- Add `# noqa` or `// eslint-disable` comments
- Split one large file into one large file with a different name

✅ **DO:**
- Extract helper functions
- Split into multiple smaller functions
- Move related logic to separate modules
- Apply Single Responsibility Principle

## Example Refactors

### Before: 120-line Function
```python
def process_recipe(recipe, profile, ai_enabled):
    # Validation (20 lines)
    if not recipe.name:
        raise ValueError("Recipe must have name")
    if len(recipe.name) > 200:
        raise ValueError("Name too long")
    # ... 15 more validation lines

    # Transform ingredients (30 lines)
    ingredients = []
    for ing in recipe.ingredients:
        parsed = parse_ingredient(ing)
        # ... 25 more lines

    # Apply AI features (40 lines)
    if ai_enabled:
        tips = call_ai_api("tips", recipe)
        # ... 35 more lines

    # Save to database (30 lines)
    recipe.save()
    # ... 25 more lines

    return recipe
```

### After: Refactored (30 lines total)
```python
def process_recipe(recipe, profile, ai_enabled):
    """Process recipe: validate, transform, enhance, save."""
    validate_recipe(recipe)
    recipe.ingredients = transform_ingredients(recipe.ingredients)
    if ai_enabled:
        enhance_with_ai(recipe, profile)
    save_recipe(recipe)
    return recipe

def validate_recipe(recipe):
    """Validate recipe fields (20 lines max)."""
    # ...

def transform_ingredients(ingredients):
    """Parse and normalize ingredients (30 lines max)."""
    # ...

def enhance_with_ai(recipe, profile):
    """Apply AI features to recipe (40 lines max)."""
    # ...

def save_recipe(recipe):
    """Save recipe and related data (30 lines max)."""
    # ...
```

### Before: Complexity 18
```javascript
function calculateScore(user, recipe) {
  var score = 0;

  if (user.favorites.includes(recipe.id)) {
    score += 10;
  } else if (user.collections.some(c => c.recipes.includes(recipe.id))) {
    score += 5;
  }

  if (recipe.cuisine === user.preferredCuisine) {
    score += 8;
  } else if (user.triedCuisines.includes(recipe.cuisine)) {
    score += 3;
  }

  if (recipe.difficulty === 'easy' && user.skillLevel < 3) {
    score += 5;
  } else if (recipe.difficulty === 'medium' && user.skillLevel >= 3) {
    score += 7;
  } else if (recipe.difficulty === 'hard' && user.skillLevel >= 7) {
    score += 10;
  }

  // ... 10 more nested conditionals

  return score;
}
```

### After: Complexity 5
```javascript
function calculateScore(user, recipe) {
  return (
    getFavoriteScore(user, recipe) +
    getCuisineScore(user, recipe) +
    getDifficultyScore(user, recipe)
  );
}

function getFavoriteScore(user, recipe) {
  if (user.favorites.includes(recipe.id)) return 10;
  if (user.collections.some(c => c.recipes.includes(recipe.id))) return 5;
  return 0;
}

function getCuisineScore(user, recipe) {
  if (recipe.cuisine === user.preferredCuisine) return 8;
  if (user.triedCuisines.includes(recipe.cuisine)) return 3;
  return 0;
}

function getDifficultyScore(user, recipe) {
  var matches = {
    'easy': user.skillLevel < 3 ? 5 : 0,
    'medium': user.skillLevel >= 3 ? 7 : 0,
    'hard': user.skillLevel >= 7 ? 10 : 0
  };
  return matches[recipe.difficulty] || 0;
}
```

## Why These Limits?

### Function Length (100 lines)
- **Fits on screen** - No scrolling to understand logic
- **Easier testing** - Smaller functions = simpler test cases
- **Better naming** - Extracted functions document intent
- **Reduced bugs** - Less complexity = fewer edge cases

### Cyclomatic Complexity (15)
- **Testability** - Complexity 15 = ~15 test cases minimum
- **Maintainability** - Lower complexity = easier to change
- **Bug correlation** - Studies show complexity >15 has exponentially more bugs

### File Size (500 lines)
- **Single responsibility** - Large files do too much
- **Merge conflicts** - Smaller files = less conflict risk
- **Navigation** - Easier to find code

## Checking Locally

### Backend (Python)
```bash
# Check complexity with Radon
docker compose exec web radon cc apps/ -a -nb

# Check with Ruff (includes complexity)
docker compose exec web ruff check apps/
```

### Frontend (JavaScript/TypeScript)
```bash
# Check with ESLint (includes complexity)
docker compose exec frontend npm run lint

# Fix auto-fixable issues
docker compose exec frontend npm run lint -- --fix
```

## CI Enforcement

The CI pipeline blocks PRs that exceed these limits:
- Backend: Ruff linting (`.github/workflows/ci.yml`)
- Frontend: ESLint (`.github/workflows/ci.yml`)
- Complexity reports: Published to GitHub Pages

## References

- Cyclomatic Complexity: https://en.wikipedia.org/wiki/Cyclomatic_complexity
- Code Quality Studies: https://www.ndepend.com/docs/code-metrics
- Clean Code (Martin): Chapters on functions and complexity

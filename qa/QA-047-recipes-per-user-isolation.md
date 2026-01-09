# QA-047: Recipes Should Be Linked to Users (Profile Isolation)

## Status
**FIXED** - Implemented in migration 0007_recipe_profile

## Resolution

Recipe profile isolation has been fully implemented. Each recipe now belongs to a specific profile, and all API endpoints and views enforce ownership checks.

### Changes Made

1. **Model** (`apps/recipes/models.py`):
   - Added `profile` ForeignKey to Recipe model with `CASCADE` delete
   - Added index for profile field

2. **Migration** (`apps/recipes/migrations/0007_recipe_profile.py`):
   - Adds profile field (nullable initially)
   - Deletes all existing recipes (clean slate approach)
   - Makes profile field non-nullable
   - Adds profile index

3. **API** (`apps/recipes/api.py`):
   - `list_recipes()`: Returns only recipes owned by current profile
   - `scrape_recipe()`: Requires profile, returns 403 if missing
   - `get_recipe()`: Returns 404 if recipe not owned by profile
   - `delete_recipe()`: Returns 404 if recipe not owned by profile

4. **Legacy Views** (`apps/legacy/views.py`):
   - `recipe_detail()`: Filters by profile ownership
   - `play_mode()`: Filters by profile ownership

5. **AI Services** (`apps/ai/api.py`, `apps/ai/services/remix.py`):
   - All AI endpoints verify profile ownership before processing
   - Remixes are assigned to the requesting profile

6. **Scraper** (`apps/recipes/services/scraper.py`):
   - `scrape_url()` now requires profile parameter
   - New recipes are automatically assigned to the importing profile

### Test Coverage

- `tests/test_user_features.py::TestRecipeProfileIsolation` - 9 tests covering:
  - Recipe visibility to owner
  - Recipe hidden from other profiles
  - Recipe hidden when no profile selected
  - Get recipe by ID - owner access
  - Get recipe by ID - other profile gets 404
  - Delete recipe - owner can delete
  - Delete recipe - other profile cannot delete

- `tests/test_legacy_views.py` - Additional coverage:
  - `test_recipe_detail_hides_other_remix` - 404 for other's recipes
  - `test_recipe_detail_shows_own_remix` - Shows own recipes

---

## Original Issue

~~Currently, all recipes are shared across all profiles. Any user can view any recipe in the system. Recipes should be linked to the profile that imported them, and users should only be able to view their own recipes.~~

### ~~Current~~ Previous Behavior
- ~~Recipes are stored globally without profile ownership~~
- ~~Any profile can view `/recipe/X/` for any recipe ID~~
- ~~Favorites link profiles to recipes, but the recipe itself has no owner~~
- ~~Search results show all recipes in the system~~

### Expected Behavior (Now Implemented)
- Each recipe belongs to the profile that imported them ✓
- Users can only view recipes they imported ✓
- Search only returns the user's own recipes ✓
- Favorites only work within the user's own recipe library ✓

## Research Findings

### Current Model Structure (`apps/recipes/models.py`)

The `Recipe` model has **no profile ForeignKey**. Related models already scoped to profile:
- `RecipeFavorite` - Has `profile` FK (lines 112-132)
- `RecipeCollection` - Has `profile` FK (lines 135-154)
- `RecipeViewHistory` - Has `profile` FK (lines 179-198)
- `ServingAdjustment` - Has `profile` FK (lines 229-268)

Existing profile-related field on Recipe:
```python
# Remix tracking only (lines 66-73)
remix_profile = models.ForeignKey(
    'profiles.Profile',
    on_delete=models.CASCADE,
    null=True,
    blank=True,
    related_name='remixes',
)
```

### Code Locations Requiring Changes

#### 1. Recipe Creation (`apps/recipes/services/scraper.py:108-140`)
Currently creates recipes without profile:
```python
recipe = Recipe(
    source_url=url,
    ...
)
await sync_to_async(recipe.save)()
```
**Fix:** Add `profile` parameter to `scrape_url()` and set on Recipe.

#### 2. Recipe List API (`apps/recipes/api.py:128-160`)
Currently shows all recipes (filters only remix visibility):
```python
qs = Recipe.objects.all().order_by('-scraped_at')
# Filter remix visibility: non-remixes OR remixes owned by current profile
if profile:
    qs = qs.filter(Q(is_remix=False) | Q(remix_profile=profile))
```
**Fix:** Replace with `qs = Recipe.objects.filter(profile=profile)`.

#### 3. Recipe Detail API (`apps/recipes/api.py:284-299`)
Currently uses `get_object_or_404(Recipe, id=recipe_id)` without profile check.
**Fix:** Add profile filter or check ownership before returning.

#### 4. Recipe Delete API (`apps/recipes/api.py:302-318`)
Same issue - no profile ownership check.
**Fix:** Verify profile ownership before delete.

#### 5. Legacy Recipe Detail (`apps/legacy/views.py:102-161`)
Uses `get_object_or_404(Recipe, id=recipe_id)` at line 115.
**Fix:** Add profile filter.

#### 6. Legacy Play Mode (`apps/legacy/views.py:164-197`)
Uses `get_object_or_404(Recipe, id=recipe_id)` at line 177.
**Fix:** Add profile filter.

#### 7. AI Services
- `apps/ai/services/remix.py:32` - `Recipe.objects.get(id=recipe_id)`
- `apps/ai/services/remix.py:85` - `Recipe.objects.get(id=recipe_id)`
- `apps/ai/services/tips.py:31` - `Recipe.objects.get(id=recipe_id)`
- `apps/ai/services/tips.py:100` - `Recipe.objects.get(id=recipe_id)`
- `apps/ai/services/scaling.py:80` - `Recipe.objects.get(id=recipe_id)`
- `apps/ai/api.py:342` - `Recipe.objects.get(id=data.recipe_id)`

**Fix:** All AI endpoints should verify profile ownership before processing.

### Profile-Aware Features Already Implemented

Some features already handle profile isolation correctly:
- **Remixes** (`api.py:149-153, 294-297`) - Only visible to creating profile
- **Favorites** - Scoped to profile via `RecipeFavorite`
- **Collections** - Scoped to profile via `RecipeCollection`
- **View History** - Scoped to profile via `RecipeViewHistory`
- **Scaling Cache** - Scoped to profile via `ServingAdjustment`

### Data Migration Strategy

#### Option A: Owner = First Favoriter (Recommended)
Assign recipe to first profile that favorited it:
```python
for recipe in Recipe.objects.filter(profile__isnull=True):
    first_fav = RecipeFavorite.objects.filter(recipe=recipe).order_by('created_at').first()
    if first_fav:
        recipe.profile = first_fav.profile
        recipe.save()
    else:
        # Orphaned recipe - assign to first profile or delete
        first_profile = Profile.objects.first()
        if first_profile:
            recipe.profile = first_profile
            recipe.save()
```

#### Option B: Duplicate for Multi-Favorited
If recipe favorited by multiple profiles, create a copy for each.
**Downside:** Increased storage, complex migration.

#### Option C: Delete Orphans
Delete recipes with no favorites.
**Risk:** Data loss for viewed-but-not-favorited recipes.

## Affected Components

### Database/Models
- `apps/recipes/models.py` - Add `profile` ForeignKey to `Recipe`
- Migration to add field with `null=True`, then data migration, then make required

### Backend
- `apps/recipes/api.py` - Filter all queries by profile
- `apps/recipes/services/scraper.py` - Accept profile parameter
- `apps/legacy/views.py` - Filter recipe views by profile
- `apps/ai/services/remix.py` - Verify profile ownership
- `apps/ai/services/tips.py` - Verify profile ownership
- `apps/ai/services/scaling.py` - Verify profile ownership
- `apps/ai/api.py` - Add profile checks to all recipe endpoints

### Frontend
- Recipe lists should only show user's recipes
- Recipe detail should 404 if not owned by current profile
- Scrape API call needs to include profile context

## Implementation Tasks

### Phase 1: Model & Migration
- [x] Add `profile` ForeignKey to Recipe model (`null=True` initially)
- [x] Create migration for new field
- [x] Data migration: Delete all existing recipes (clean slate)
- [x] Make `profile` non-nullable

### Phase 2: Backend Enforcement
- [x] Update `scrape_url()` to accept and set profile
- [x] Update `list_recipes()` API to filter by profile
- [x] Update `get_recipe()` API to check profile ownership
- [x] Update `delete_recipe()` API to check profile ownership
- [x] Update `recipe_detail()` view to filter by profile
- [x] Update `play_mode()` view to filter by profile
- [x] Add profile checks to all AI service endpoints

### Phase 3: Frontend Updates
- [x] Pass profile context to scrape API calls (automatic via session)
- [x] Recipe list queries filter by profile (server-side)
- [x] 404 responses handled for unauthorized access

### Phase 4: Testing
- [x] Test profile isolation in API (TestRecipeProfileIsolation)
- [x] Test profile isolation in legacy views
- [x] All 308 tests passing
- [x] Test that profiles cannot access other profiles' recipes

## Priority

~~Medium - Privacy/data isolation concern~~

## Phase

~~Future - Requires architectural planning session~~

**COMPLETED**

## Actual Scope

- **Files modified:** 10 files
- **New migrations:** 1 (combined)
- **Risk realized:** Low (clean slate approach avoided complex data migration)
- **Breaking changes:** API now requires profile for recipe access

# Phase 3: User Features + Theme Sync Tooling

> **Goal:** Favorites, collections, history working; theme sync ready for frontends
> **Prerequisite:** Phase 2 complete
> **Deliverable:** Profile-based recipe organization, Figma theme sync tooling

---

## Session Scope

| Session | Tasks | Focus |
|---------|-------|-------|
| A | 3.1-3.3 | Favorites, Collections, History models |
| B | 3.4-3.6 | Data isolation + theme sync + tests |

---

## Tasks

- [ ] 3.1 RecipeFavorite model and API
- [ ] 3.2 RecipeCollection model and API
- [ ] 3.3 RecipeViewHistory model and API
- [ ] 3.4 Profile-based data isolation
- [ ] 3.5 Figma theme sync tooling (`bin/figma-sync-theme`)
- [ ] 3.6 Write pytest tests for favorites, collections, and profile isolation

---

## Models

### RecipeFavorite

```python
class RecipeFavorite(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='favorites')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['profile', 'recipe']
        ordering = ['-created_at']
```

### RecipeCollection

```python
class RecipeCollection(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='collections')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['profile', 'name']
        ordering = ['-updated_at']


class RecipeCollectionItem(models.Model):
    collection = models.ForeignKey(RecipeCollection, on_delete=models.CASCADE, related_name='items')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['collection', 'recipe']
        ordering = ['order', '-added_at']
```

### RecipeViewHistory

```python
class RecipeViewHistory(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='view_history')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['profile', 'recipe']
        ordering = ['-viewed_at']
```

---

## API Endpoints

```
# Favorites (current profile)
GET    /api/favorites/                    # List favorites
POST   /api/favorites/                    # Add favorite {recipe_id}
DELETE /api/favorites/{recipe_id}/        # Remove favorite

# Collections (current profile)
GET    /api/collections/                  # List collections
POST   /api/collections/                  # Create collection
GET    /api/collections/{id}/             # Get collection with recipes
PUT    /api/collections/{id}/             # Update collection
DELETE /api/collections/{id}/             # Delete collection
POST   /api/collections/{id}/recipes/     # Add recipe {recipe_id}
DELETE /api/collections/{id}/recipes/{recipe_id}/  # Remove recipe

# View History (current profile)
GET    /api/history/                      # Get recent recipes (up to 6)
DELETE /api/history/                      # Clear history
POST   /api/history/                      # Record view {recipe_id}
```

---

## Profile-Based Data Isolation

All user data is scoped to the current profile:

```python
# Example: Getting favorites for current profile
def get_favorites(request):
    profile = get_current_profile(request)
    return RecipeFavorite.objects.filter(profile=profile)

# Example: Creating a collection
def create_collection(request, name):
    profile = get_current_profile(request)
    return RecipeCollection.objects.create(profile=profile, name=name)
```

**Remix Visibility:**
- Remixes (`is_remix=True`) are ONLY visible to the creating profile
- Filter by `remix_profile` when listing recipes for a profile

---

## Theme Sync Tooling

Build the Figma theme sync tool now so it's ready before frontend development.

### Directory Structure

```
cookie/
├── bin/
│   └── figma-sync-theme    # Sync theme.css to both frontends
└── tooling/
    ├── theme-mapping.json  # CSS variable mappings
    └── lib/
        ├── parser.py       # Parse CSS files
        └── syncer.py       # Sync theme variables
```

### Usage

```bash
# Sync theme to both frontends
./bin/figma-sync-theme

# Dry run - show what would change
./bin/figma-sync-theme --dry-run

# Sync to React only
./bin/figma-sync-theme --react-only

# Sync to Legacy only (light mode values)
./bin/figma-sync-theme --legacy-only
```

### Theme Mapping

See `FIGMA_TOOLING.md` for complete mapping configuration.

Key mappings:
- `--primary` -> React: `--primary`, Legacy: `--primary-color`
- `--background` -> Both get same name
- Dark mode values -> React only (legacy is light-only)

---

## Acceptance Criteria

1. Favorites can be added/removed per profile
2. Collections CRUD works per profile
3. View history tracks last 6 viewed recipes
4. Data is properly isolated between profiles
5. Remixes only visible to creating profile
6. `bin/figma-sync-theme` works with current Figma export
7. Theme mapping handles light/dark mode correctly

---

## Checkpoint (End of Phase)

```
[ ] POST /api/favorites/ - adds recipe to current profile's favorites
[ ] GET /api/favorites/ - returns only current profile's favorites
[ ] Collection CRUD - create, list, update, delete all work
[ ] Add recipe to collection - appears in collection detail
[ ] GET /api/history/ - returns up to 6 recent recipes
[ ] Switch profiles - favorites/collections change accordingly
[ ] ./bin/figma-sync-theme --dry-run - shows expected changes
[ ] pytest - all isolation tests pass
```

---

## Testing Notes

```python
def test_favorites_isolation():
    profile_a = Profile.objects.create(name='A')
    profile_b = Profile.objects.create(name='B')
    recipe = Recipe.objects.create(title='Test')

    # A favorites recipe
    RecipeFavorite.objects.create(profile=profile_a, recipe=recipe)

    # B should not see A's favorites
    assert RecipeFavorite.objects.filter(profile=profile_b).count() == 0

def test_remix_visibility():
    profile_a = Profile.objects.create(name='A')
    profile_b = Profile.objects.create(name='B')

    # A creates remix
    remix = Recipe.objects.create(
        title='Remix',
        is_remix=True,
        remix_profile=profile_a
    )

    # B should not see A's remix
    visible_to_b = Recipe.objects.filter(
        Q(is_remix=False) | Q(remix_profile=profile_b)
    )
    assert remix not in visible_to_b
```

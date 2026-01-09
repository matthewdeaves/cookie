# QA-047: Recipes Should Be Linked to Users (Profile Isolation)

## Status
**OPEN** - Requires architectural planning

## Issue

Currently, all recipes are shared across all profiles. Any user can view any recipe in the system. Recipes should be linked to the profile that imported them, and users should only be able to view their own recipes.

### Current Behavior
- Recipes are stored globally without profile ownership
- Any profile can view `/recipe/X/` for any recipe ID
- Favorites link profiles to recipes, but the recipe itself has no owner
- Search results show all recipes in the system

### Expected Behavior
- Each recipe belongs to the profile that imported it
- Users can only view recipes they imported
- Search only returns the user's own recipes
- Favorites only work within the user's own recipe library

## Affected Components

### Database/Models
- `apps/recipes/models.py` - `Recipe` model needs `profile` ForeignKey
- Migration to add profile field and backfill existing recipes

### Backend
- `apps/recipes/api.py` - Filter all queries by profile
- `apps/legacy/views.py` - Filter recipe views by profile
- `apps/ai/services/` - Ensure AI services respect profile ownership

### Frontend
- Recipe lists should only show user's recipes
- Recipe detail should 404 if not owned by current profile

## Data Migration Considerations

Existing recipes need to be assigned to a profile. Options:
1. Assign all existing recipes to a default/admin profile
2. Assign based on who favorited them (if only one profile favorited)
3. Duplicate recipes for each profile that favorited them
4. Delete orphaned recipes

## Priority

Medium - Privacy/data isolation concern

## Phase

Future - Requires architectural planning session

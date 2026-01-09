# Phase 9: Settings & Polish

> **Goal:** Production-ready application
> **Prerequisite:** Phase 8B complete
> **Deliverable:** Complete, tested, polished application

---

## Session Scope

| Session | Tasks | Focus |
|---------|-------|-------|
| A | 9.1-9.2 | Settings screens (both interfaces) |
| B | 9.3-9.5 | Error handling + loading + toasts (QA-057 discovered) |
| C | 9.6-9.7 | Final testing + verification |
| D | 9.8 | User management (list, delete with cascade) |
| E | 9.9 | Search source health review + repair/replacement |
| F | 9.10 | Danger Zone tab with database reset functionality |
| G | 9.11 | Browser fingerprint spoofer configuration review |

---

## Tasks

- [x] 9.1 React: Settings screen (General, AI Prompts, Sources, Source Selectors tabs)
- [x] 9.2 Legacy: Settings screen (all tabs)
- [x] 9.3 Error handling and edge cases
- [x] 9.4 Loading states and skeletons (React) / Loading indicators (Legacy)
- [x] 9.5 Toast notifications (both interfaces)
- [ ] 9.6 Testing with pytest (unit + integration)
- [ ] 9.7 Final cross-browser/device testing
- [x] 9.8 User management tab: List users, delete with full cascade (recipes, images, all related data)
- [x] 9.9 Search source health review: Audit failed sources, attempt AI repair, replace unfixable sources
- [ ] 9.10 Danger Zone tab: Reset database with confirmation (wipe data, clear images/cache, re-run migrations)
- [ ] 9.11 Browser fingerprint spoofer review: Audit configuration, optimize settings, ensure best practices

---

## Settings Screen

### Four Tabs

1. **General**
2. **AI Prompts**
3. **Sources**
4. **Source Selectors**

---

### General Tab

From Figma:
- ~~**Appearance:** Dark/light toggle~~ (Already implemented - React has theme toggle, Legacy is light-only by design)
- **Profile Management:**
  - List all profiles
  - "Current" badge on active profile
  - Delete option per profile
- ~~**Data Management:**~~ (Won't implement - not needed)
  - ~~Clear Cache button~~ - Caches are self-managing (ServingAdjustment, AIDiscoverySuggestion auto-refresh)
  - ~~Clear View History button~~ - Users can ignore history or create new profile
- **OpenRouter API Key:**
  - Password input field
  - Test connection button
- **About:**
  - Version number
  - GitHub link: https://github.com/matthewdeaves/cookie.git

### AI Prompts Tab

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
  - Model dropdown (8+ models)
  - Save/Cancel buttons

### Sources Tab

From Figma:
- "Recipe Sources" heading
- "X of 15 sources currently enabled" counter
- Enable All / Disable All bulk actions
- List of 15 sources with:
  - Source name and URL
  - "Active" badge when enabled
  - Toggle switch

### Source Selectors Tab

From Figma:
- "Search Source Selector Management" heading
- "Edit CSS selectors and test source connectivity" subheading
- For each source:
  - Source name and host URL
  - Status indicator: green checkmark (working), red X (broken), gray ? (untested)
  - Editable "CSS Selector" text field (monospace)
  - "Test" button
  - "Last tested: [relative time]"
  - Warning badge if broken: "Failed X times - auto-disabled"
- "Test All Sources" button at bottom

### Danger Zone Tab (Session F - New)

**Purpose:** Provide a complete database reset option for development/testing or when users want to start completely fresh.

**UI Layout:**
- "Danger Zone" heading with warning icon
- Subheading: "Destructive operations that cannot be undone"
- Red-tinted warning card containing:
  - "Reset Database" section title
  - Description: "Completely reset the application to factory state"
  - Bullet list of what will be deleted:
    - All recipes (scraped and remixed)
    - All recipe images
    - All user profiles
    - All favorites, collections, and view history
    - All cached AI data
    - All search source test results (selectors retained)
  - "Reset Database" danger button

**Confirmation Modal (Two-Step):**

*Step 1 - Initial Warning:*
- Large warning icon
- "Reset Database?"
- "This will permanently delete ALL data from the application:"
- Data summary showing counts of what will be deleted
- Warning text: "This action cannot be undone."
- Cancel button
- "I understand, continue" button

*Step 2 - Type Confirmation:*
- "Type RESET to confirm"
- Text input field
- Cancel button
- "Reset Database" danger button (disabled until RESET typed)

**What Reset Does:**

1. **Clear all database tables** (in order to respect FK constraints):
   - AIDiscoverySuggestion
   - ServingAdjustment
   - RecipeViewHistory
   - RecipeCollectionItem
   - RecipeCollection
   - RecipeFavorite
   - RecipeTip
   - RecipeTimer
   - RecipeIngredient
   - RecipeStep
   - Recipe
   - Profile
   - (SearchSource selectors and AIPrompt configs are RETAINED)

2. **Clear media files:**
   - Delete all files in `MEDIA_ROOT/recipe_images/`

3. **Clear cache:**
   - Flush Django cache (if configured)
   - Clear any temporary files

4. **Re-run migrations:**
   - Run `python manage.py migrate` to ensure clean schema
   - Run seed data commands to restore default SearchSources and AIPrompts

5. **Clear session:**
   - Invalidate current session (user will need to create new profile)

---

### Users Tab (Session D - New)

**Purpose:** Allow administrators to view all profiles and delete users, with complete data cleanup including orphaned images.

**UI Layout:**
- "User Management" heading
- Subheading: "Manage user profiles and their data"
- User count: "X profiles"
- List of user cards, each showing:
  - Avatar circle with user's `avatar_color`
  - Profile name
  - Created date
  - Stats: X favorites, X collections, X remixes
  - "Current" badge if this is the active profile
  - Delete button (trash icon, red on hover)
- Delete confirmation modal with data summary

**Delete Confirmation Modal:**
- Warning icon
- "Delete Profile?"
- Profile name and avatar
- Data summary showing what will be deleted:
  - X remixed recipes (including images)
  - X favorites
  - X collections (Y items total)
  - X view history entries
  - X cached scaling adjustments
  - X AI discovery suggestions
- Warning text: "This action cannot be undone. All data will be permanently deleted."
- Cancel button
- "Delete Profile" danger button

---

## User Management Feature (Session D)

### Data Model Analysis

**Profile** (`apps/profiles/models.py`):
```python
class Profile(models.Model):
    name = CharField(max_length=100)
    avatar_color = CharField(max_length=7)  # Hex color
    theme = CharField(choices=['light', 'dark'], default='light')
    unit_preference = CharField(choices=['metric', 'imperial'], default='metric')
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now)
```

**Related Data (all have CASCADE delete):**

| Model | Related Name | FK Field | What's Deleted |
|-------|--------------|----------|----------------|
| Recipe | `remixes` | `remix_profile` | User's remixed recipes (`is_remix=True`) |
| RecipeFavorite | `favorites` | `profile` | All favorite markers |
| RecipeCollection | `collections` | `profile` | All user collections |
| RecipeCollectionItem | (via collection) | (via collection) | Items in deleted collections |
| RecipeViewHistory | `view_history` | `profile` | All viewing history |
| ServingAdjustment | `serving_adjustments` | `profile` | Cached scaled ingredients |
| AIDiscoverySuggestion | `ai_discovery_suggestions` | `profile` | AI discover cache |

**Orphaned Resources (NOT automatically deleted):**
- Recipe images for remixes stored in `MEDIA_ROOT/recipe_images/`

### Implementation Plan

#### Backend API

**1. List Profiles with Stats (`GET /api/profiles/`)**

Enhance existing endpoint to include deletion-relevant stats:

```python
# apps/profiles/api.py
from django.db.models import Count, Q

@router.get('/', response=List[ProfileWithStatsSchema])
def list_profiles(request):
    """List all profiles with stats for user management."""
    profiles = Profile.objects.annotate(
        favorites_count=Count('favorites'),
        collections_count=Count('collections'),
        collection_items_count=Count('collections__items'),
        remixes_count=Count(
            'remixes',
            filter=Q(remixes__is_remix=True)
        ),
        view_history_count=Count('view_history'),
        scaling_cache_count=Count('serving_adjustments'),
        discover_cache_count=Count('ai_discovery_suggestions'),
    ).order_by('-created_at')

    return [
        ProfileWithStatsSchema(
            id=p.id,
            name=p.name,
            avatar_color=p.avatar_color,
            theme=p.theme,
            unit_preference=p.unit_preference,
            created_at=p.created_at,
            stats={
                'favorites': p.favorites_count,
                'collections': p.collections_count,
                'collection_items': p.collection_items_count,
                'remixes': p.remixes_count,
                'view_history': p.view_history_count,
                'scaling_cache': p.scaling_cache_count,
                'discover_cache': p.discover_cache_count,
            }
        )
        for p in profiles
    ]
```

**2. Delete Profile with Image Cleanup (`DELETE /api/profiles/{id}/`)**

Enhance existing endpoint to clean up orphaned images:

```python
# apps/profiles/api.py
import os
from django.conf import settings

@router.delete('/{profile_id}/', response={204: None, 400: ErrorSchema, 404: ErrorSchema})
def delete_profile(request, profile_id: int):
    """
    Delete a profile and ALL associated data.

    Cascade deletes:
    - Recipe remixes (is_remix=True, remix_profile=this)
    - Favorites
    - Collections and collection items
    - View history
    - Serving adjustment cache
    - AI discovery suggestions

    Manual cleanup:
    - Recipe images from deleted remixes
    """
    try:
        profile = Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        return 404, {'error': 'not_found', 'message': 'Profile not found'}

    # Check if this is the current session profile
    current_profile_id = request.session.get('profile_id')
    if current_profile_id == profile_id:
        # Clear session profile
        del request.session['profile_id']

    # Collect image paths BEFORE cascade delete
    remix_images = list(
        Recipe.objects.filter(
            is_remix=True,
            remix_profile=profile,
            image__isnull=False
        ).exclude(image='').values_list('image', flat=True)
    )

    # Django CASCADE handles all related records
    profile.delete()

    # Clean up orphaned image files
    for image_path in remix_images:
        full_path = os.path.join(settings.MEDIA_ROOT, image_path)
        try:
            if os.path.exists(full_path):
                os.remove(full_path)
        except OSError:
            # Log but don't fail - orphaned files are non-critical
            pass

    return 204, None
```

**3. Get Deletion Preview (`GET /api/profiles/{id}/deletion-preview/`)**

For confirmation modal:

```python
@router.get('/{profile_id}/deletion-preview/', response=DeletionPreviewSchema)
def get_deletion_preview(request, profile_id: int):
    """Get summary of data that will be deleted with this profile."""
    try:
        profile = Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        return 404, {'error': 'not_found', 'message': 'Profile not found'}

    # Count related data
    remixes = Recipe.objects.filter(is_remix=True, remix_profile=profile)
    favorites = RecipeFavorite.objects.filter(profile=profile)
    collections = RecipeCollection.objects.filter(profile=profile)
    collection_items = RecipeCollectionItem.objects.filter(collection__profile=profile)
    view_history = RecipeViewHistory.objects.filter(profile=profile)
    scaling_cache = ServingAdjustment.objects.filter(profile=profile)
    discover_cache = AIDiscoverySuggestion.objects.filter(profile=profile)

    # Count images that will be deleted
    remix_images_count = remixes.exclude(image='').exclude(image__isnull=True).count()

    return {
        'profile': {
            'id': profile.id,
            'name': profile.name,
            'avatar_color': profile.avatar_color,
            'created_at': profile.created_at,
        },
        'data_to_delete': {
            'remixes': remixes.count(),
            'remix_images': remix_images_count,
            'favorites': favorites.count(),
            'collections': collections.count(),
            'collection_items': collection_items.count(),
            'view_history': view_history.count(),
            'scaling_cache': scaling_cache.count(),
            'discover_cache': discover_cache.count(),
        },
        'warnings': [
            'All remixed recipes will be permanently deleted',
            'Recipe images for remixes will be removed from storage',
            'This action cannot be undone',
        ]
    }
```

#### React Frontend

**1. Add Users Tab to Settings.tsx**

```typescript
type Tab = 'api' | 'prompts' | 'users'

// Tab navigation
<button onClick={() => setActiveTab('users')}>
  <Users className="h-4 w-4" />
  Users
</button>

// Users tab content
{activeTab === 'users' && (
  <UsersTab
    profiles={profiles}
    currentProfileId={currentProfileId}
    onDeleteProfile={handleDeleteProfile}
  />
)}
```

**2. UsersTab Component (`frontend/src/components/UsersTab.tsx`)**

```typescript
interface UsersTabProps {
  profiles: ProfileWithStats[]
  currentProfileId: number | null
  onDeleteProfile: (id: number) => Promise<void>
}

export function UsersTab({ profiles, currentProfileId, onDeleteProfile }: UsersTabProps) {
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [deletePreview, setDeletePreview] = useState<DeletionPreview | null>(null)
  const [showDeleteModal, setShowDeleteModal] = useState(false)

  const handleDeleteClick = async (profileId: number) => {
    const preview = await api.profiles.getDeletionPreview(profileId)
    setDeletePreview(preview)
    setDeletingId(profileId)
    setShowDeleteModal(true)
  }

  const confirmDelete = async () => {
    if (!deletingId) return
    try {
      await onDeleteProfile(deletingId)
      toast.success('Profile deleted successfully')
    } catch (error) {
      toast.error('Failed to delete profile')
    } finally {
      setShowDeleteModal(false)
      setDeletingId(null)
      setDeletePreview(null)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-medium">User Management</h2>
        <span className="text-sm text-muted-foreground">
          {profiles.length} profile{profiles.length !== 1 ? 's' : ''}
        </span>
      </div>

      <div className="space-y-3">
        {profiles.map(profile => (
          <div
            key={profile.id}
            className="flex items-center justify-between rounded-lg border p-4"
          >
            <div className="flex items-center gap-3">
              {/* Avatar */}
              <div
                className="h-10 w-10 rounded-full"
                style={{ backgroundColor: profile.avatar_color }}
              />
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-medium">{profile.name}</span>
                  {profile.id === currentProfileId && (
                    <span className="rounded bg-primary/10 px-2 py-0.5 text-xs text-primary">
                      Current
                    </span>
                  )}
                </div>
                <div className="text-sm text-muted-foreground">
                  Created {formatDate(profile.created_at)}
                </div>
                <div className="text-xs text-muted-foreground">
                  {profile.stats.favorites} favorites ·{' '}
                  {profile.stats.collections} collections ·{' '}
                  {profile.stats.remixes} remixes
                </div>
              </div>
            </div>

            <button
              onClick={() => handleDeleteClick(profile.id)}
              disabled={profile.id === currentProfileId}
              className="rounded p-2 text-muted-foreground hover:bg-destructive/10 hover:text-destructive disabled:opacity-50"
              title={profile.id === currentProfileId ? 'Cannot delete current profile' : 'Delete profile'}
            >
              <Trash2 className="h-5 w-5" />
            </button>
          </div>
        ))}
      </div>

      {/* Delete Confirmation Modal */}
      <DeleteProfileModal
        open={showDeleteModal}
        preview={deletePreview}
        onConfirm={confirmDelete}
        onCancel={() => setShowDeleteModal(false)}
      />
    </div>
  )
}
```

**3. DeleteProfileModal Component**

```typescript
interface DeleteProfileModalProps {
  open: boolean
  preview: DeletionPreview | null
  onConfirm: () => void
  onCancel: () => void
}

export function DeleteProfileModal({ open, preview, onConfirm, onCancel }: DeleteProfileModalProps) {
  if (!open || !preview) return null

  const { profile, data_to_delete, warnings } = preview

  return (
    <Dialog open={open} onOpenChange={onCancel}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-destructive">
            <AlertTriangle className="h-5 w-5" />
            Delete Profile?
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Profile info */}
          <div className="flex items-center gap-3">
            <div
              className="h-12 w-12 rounded-full"
              style={{ backgroundColor: profile.avatar_color }}
            />
            <div>
              <div className="font-medium">{profile.name}</div>
              <div className="text-sm text-muted-foreground">
                Created {formatDate(profile.created_at)}
              </div>
            </div>
          </div>

          {/* Data summary */}
          <div className="rounded-lg border bg-muted/50 p-3">
            <div className="mb-2 text-sm font-medium">Data to be deleted:</div>
            <ul className="space-y-1 text-sm text-muted-foreground">
              {data_to_delete.remixes > 0 && (
                <li>• {data_to_delete.remixes} remixed recipe{data_to_delete.remixes !== 1 ? 's' : ''} ({data_to_delete.remix_images} images)</li>
              )}
              {data_to_delete.favorites > 0 && (
                <li>• {data_to_delete.favorites} favorite{data_to_delete.favorites !== 1 ? 's' : ''}</li>
              )}
              {data_to_delete.collections > 0 && (
                <li>• {data_to_delete.collections} collection{data_to_delete.collections !== 1 ? 's' : ''} ({data_to_delete.collection_items} items)</li>
              )}
              {data_to_delete.view_history > 0 && (
                <li>• {data_to_delete.view_history} view history entries</li>
              )}
              {(data_to_delete.scaling_cache > 0 || data_to_delete.discover_cache > 0) && (
                <li>• Cached AI data</li>
              )}
            </ul>
          </div>

          {/* Warning */}
          <div className="text-sm text-destructive">
            This action cannot be undone. All data will be permanently deleted.
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button variant="destructive" onClick={onConfirm}>
            Delete Profile
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
```

#### Legacy Frontend

**1. Add Users Tab to Settings Template**

```html
<!-- apps/legacy/templates/legacy/settings.html -->

<!-- Add tab button -->
<button type="button" class="tab-toggle-btn" data-tab="users">
    Users
</button>

<!-- Users Tab Content -->
<div id="tab-users" class="tab-content hidden">
    <div class="card">
        <div class="settings-header">
            <h2 class="settings-section-title">User Management</h2>
            <span class="profile-count" id="profile-count"></span>
        </div>

        <div id="profiles-list" class="profiles-list">
            <!-- Populated by JavaScript -->
        </div>
    </div>
</div>

<!-- Delete Confirmation Modal -->
<div id="delete-profile-modal" class="modal hidden">
    <div class="modal-backdrop"></div>
    <div class="modal-content">
        <div class="modal-header">
            <svg class="icon-warning">...</svg>
            <h3>Delete Profile?</h3>
        </div>
        <div class="modal-body">
            <div id="delete-profile-info" class="profile-info">
                <!-- Populated by JS -->
            </div>
            <div id="delete-data-summary" class="data-summary">
                <!-- Populated by JS -->
            </div>
            <p class="warning-text">
                This action cannot be undone. All data will be permanently deleted.
            </p>
        </div>
        <div class="modal-footer">
            <button type="button" class="btn btn-secondary" onclick="closeDeleteModal()">
                Cancel
            </button>
            <button type="button" class="btn btn-danger" id="confirm-delete-btn">
                Delete Profile
            </button>
        </div>
    </div>
</div>
```

**2. Settings JavaScript (`apps/legacy/static/legacy/js/pages/settings.js`)**

```javascript
// Add to existing settings.js

var currentProfileId = null;  // Set from session
var pendingDeleteId = null;

function loadProfiles() {
    fetch('/api/profiles/')
        .then(function(response) { return response.json(); })
        .then(function(profiles) {
            renderProfiles(profiles);
            document.getElementById('profile-count').textContent =
                profiles.length + ' profile' + (profiles.length !== 1 ? 's' : '');
        })
        .catch(function(error) {
            Cookie.toast.error('Failed to load profiles');
        });
}

function renderProfiles(profiles) {
    var container = document.getElementById('profiles-list');
    container.innerHTML = profiles.map(function(profile) {
        var isCurrent = profile.id === currentProfileId;
        return [
            '<div class="profile-card" data-profile-id="' + profile.id + '">',
            '  <div class="profile-avatar" style="background-color: ' + profile.avatar_color + '"></div>',
            '  <div class="profile-info">',
            '    <div class="profile-name">',
            '      ' + escapeHtml(profile.name),
            isCurrent ? ' <span class="badge badge-primary">Current</span>' : '',
            '    </div>',
            '    <div class="profile-meta">Created ' + formatDate(profile.created_at) + '</div>',
            '    <div class="profile-stats">',
            '      ' + profile.stats.favorites + ' favorites · ',
            '      ' + profile.stats.collections + ' collections · ',
            '      ' + profile.stats.remixes + ' remixes',
            '    </div>',
            '  </div>',
            '  <button class="btn-delete" ' + (isCurrent ? 'disabled' : '') + ' onclick="confirmDeleteProfile(' + profile.id + ')">',
            '    <svg>...</svg>',
            '  </button>',
            '</div>'
        ].join('');
    }).join('');
}

function confirmDeleteProfile(profileId) {
    pendingDeleteId = profileId;

    fetch('/api/profiles/' + profileId + '/deletion-preview/')
        .then(function(response) { return response.json(); })
        .then(function(preview) {
            renderDeleteModal(preview);
            document.getElementById('delete-profile-modal').classList.remove('hidden');
        })
        .catch(function(error) {
            Cookie.toast.error('Failed to load profile info');
        });
}

function renderDeleteModal(preview) {
    var profile = preview.profile;
    var data = preview.data_to_delete;

    document.getElementById('delete-profile-info').innerHTML = [
        '<div class="profile-avatar" style="background-color: ' + profile.avatar_color + '"></div>',
        '<div>',
        '  <div class="profile-name">' + escapeHtml(profile.name) + '</div>',
        '  <div class="profile-meta">Created ' + formatDate(profile.created_at) + '</div>',
        '</div>'
    ].join('');

    var summaryItems = [];
    if (data.remixes > 0) {
        summaryItems.push(data.remixes + ' remixed recipe' + (data.remixes !== 1 ? 's' : '') +
            ' (' + data.remix_images + ' images)');
    }
    if (data.favorites > 0) {
        summaryItems.push(data.favorites + ' favorite' + (data.favorites !== 1 ? 's' : ''));
    }
    if (data.collections > 0) {
        summaryItems.push(data.collections + ' collection' + (data.collections !== 1 ? 's' : '') +
            ' (' + data.collection_items + ' items)');
    }
    if (data.view_history > 0) {
        summaryItems.push(data.view_history + ' view history entries');
    }

    document.getElementById('delete-data-summary').innerHTML =
        '<div class="summary-title">Data to be deleted:</div>' +
        '<ul>' + summaryItems.map(function(item) {
            return '<li>• ' + item + '</li>';
        }).join('') + '</ul>';
}

function closeDeleteModal() {
    document.getElementById('delete-profile-modal').classList.add('hidden');
    pendingDeleteId = null;
}

function executeDeleteProfile() {
    if (!pendingDeleteId) return;

    var btn = document.getElementById('confirm-delete-btn');
    btn.disabled = true;
    btn.textContent = 'Deleting...';

    fetch('/api/profiles/' + pendingDeleteId + '/', {
        method: 'DELETE'
    })
    .then(function(response) {
        if (response.status === 204) {
            Cookie.toast.success('Profile deleted successfully');
            closeDeleteModal();
            loadProfiles();
        } else {
            return response.json().then(function(data) {
                throw new Error(data.message || 'Failed to delete profile');
            });
        }
    })
    .catch(function(error) {
        Cookie.toast.error(error.message);
    })
    .finally(function() {
        btn.disabled = false;
        btn.textContent = 'Delete Profile';
    });
}

// Initialize
document.getElementById('confirm-delete-btn').addEventListener('click', executeDeleteProfile);

// Load profiles when users tab is shown
document.querySelector('[data-tab="users"]').addEventListener('click', function() {
    loadProfiles();
});
```

### API Schemas

```python
# apps/profiles/schemas.py

class ProfileStatsSchema(Schema):
    favorites: int
    collections: int
    collection_items: int
    remixes: int
    view_history: int
    scaling_cache: int
    discover_cache: int

class ProfileWithStatsSchema(Schema):
    id: int
    name: str
    avatar_color: str
    theme: str
    unit_preference: str
    created_at: datetime
    stats: ProfileStatsSchema

class DeletionDataSchema(Schema):
    remixes: int
    remix_images: int
    favorites: int
    collections: int
    collection_items: int
    view_history: int
    scaling_cache: int
    discover_cache: int

class ProfileSummarySchema(Schema):
    id: int
    name: str
    avatar_color: str
    created_at: datetime

class DeletionPreviewSchema(Schema):
    profile: ProfileSummarySchema
    data_to_delete: DeletionDataSchema
    warnings: List[str]
```

### CSS Additions

**Legacy (`apps/legacy/static/legacy/css/settings.css`):**
```css
/* User Management */
.profiles-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.profile-card {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px;
    border: 1px solid var(--color-border);
    border-radius: 8px;
}

.profile-avatar {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    flex-shrink: 0;
}

.profile-info {
    flex: 1;
    min-width: 0;
}

.profile-name {
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 8px;
}

.profile-meta,
.profile-stats {
    font-size: 12px;
    color: var(--color-text-muted);
}

.btn-delete {
    padding: 8px;
    border: none;
    background: transparent;
    color: var(--color-text-muted);
    border-radius: 8px;
    cursor: pointer;
}

.btn-delete:hover:not(:disabled) {
    background: rgba(239, 68, 68, 0.1);
    color: var(--color-danger);
}

.btn-delete:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

/* Delete Modal */
.data-summary {
    background: var(--color-bg-muted);
    border-radius: 8px;
    padding: 12px;
    margin: 16px 0;
}

.summary-title {
    font-weight: 500;
    margin-bottom: 8px;
}

.data-summary ul {
    list-style: none;
    padding: 0;
    margin: 0;
}

.data-summary li {
    font-size: 14px;
    color: var(--color-text-muted);
    padding: 2px 0;
}

.warning-text {
    color: var(--color-danger);
    font-size: 14px;
}

.btn-danger {
    background: var(--color-danger);
    color: white;
}

.btn-danger:hover {
    background: var(--color-danger-hover);
}
```

### Testing

```python
def test_list_profiles_with_stats():
    """List profiles includes deletion stats."""
    profile = Profile.objects.create(name='Test')
    RecipeFavorite.objects.create(profile=profile, recipe=some_recipe)

    response = client.get('/api/profiles/')
    assert response.json()[0]['stats']['favorites'] == 1

def test_deletion_preview():
    """Deletion preview shows accurate counts."""
    profile = Profile.objects.create(name='Test')
    recipe = Recipe.objects.create(
        title='Remix',
        is_remix=True,
        remix_profile=profile,
        image='recipe_images/test.jpg'
    )

    response = client.get(f'/api/profiles/{profile.id}/deletion-preview/')
    data = response.json()
    assert data['data_to_delete']['remixes'] == 1
    assert data['data_to_delete']['remix_images'] == 1

def test_delete_profile_cascade():
    """Deleting profile cascades to all related data."""
    profile = Profile.objects.create(name='Test')
    recipe = Recipe.objects.create(title='Remix', is_remix=True, remix_profile=profile)
    RecipeFavorite.objects.create(profile=profile, recipe=some_recipe)
    collection = RecipeCollection.objects.create(profile=profile, name='Test')

    client.delete(f'/api/profiles/{profile.id}/')

    assert not Profile.objects.filter(id=profile.id).exists()
    assert not Recipe.objects.filter(id=recipe.id).exists()
    assert not RecipeFavorite.objects.filter(profile_id=profile.id).exists()
    assert not RecipeCollection.objects.filter(id=collection.id).exists()

def test_delete_profile_cleans_images(tmp_path, settings):
    """Deleting profile removes orphaned recipe images."""
    settings.MEDIA_ROOT = tmp_path
    image_path = tmp_path / 'recipe_images' / 'test.jpg'
    image_path.parent.mkdir(parents=True)
    image_path.write_bytes(b'fake image')

    profile = Profile.objects.create(name='Test')
    Recipe.objects.create(
        title='Remix',
        is_remix=True,
        remix_profile=profile,
        image='recipe_images/test.jpg'
    )

    client.delete(f'/api/profiles/{profile.id}/')

    assert not image_path.exists()

def test_cannot_delete_current_profile():
    """Cannot delete profile that's currently selected (via session)."""
    profile = Profile.objects.create(name='Test')
    # This test would check session behavior
    # Current profile deletion is handled by clearing session
```

### Acceptance Criteria

1. Settings page has "Users" tab on both React and Legacy
2. Users tab shows all profiles with avatar, name, created date, and stats
3. Current profile marked with badge, delete disabled
4. Delete button shows confirmation modal with data summary
5. Confirmation modal shows accurate counts of data to be deleted
6. Deleting profile removes all related data:
   - Remixed recipes
   - Favorites
   - Collections and items
   - View history
   - Cached scaling adjustments
   - AI discovery suggestions
7. Recipe images for remixes are removed from filesystem
8. Deleting current profile clears session
9. Toast notifications confirm success/failure
10. Works consistently on both React and Legacy interfaces

---

## Database Reset Feature (Session F)

### Overview

The Danger Zone tab provides a complete factory reset option. This is useful for:
- Development and testing environments
- Users who want to start completely fresh
- Clearing demo data before production use

### Backend API

**1. Get Reset Preview (`GET /api/system/reset-preview/`)**

Returns counts of all data that will be deleted:

```python
# apps/core/api.py
from ninja import Router
from django.db.models import Count
from apps.profiles.models import Profile
from apps.recipes.models import Recipe, RecipeFavorite, RecipeCollection

router = Router(tags=['system'])

@router.get('/reset-preview/')
def get_reset_preview(request):
    """Get summary of data that will be deleted on reset."""
    return {
        'data_counts': {
            'profiles': Profile.objects.count(),
            'recipes': Recipe.objects.count(),
            'recipe_images': Recipe.objects.exclude(image='').exclude(image__isnull=True).count(),
            'favorites': RecipeFavorite.objects.count(),
            'collections': RecipeCollection.objects.count(),
            'collection_items': RecipeCollectionItem.objects.count(),
            'view_history': RecipeViewHistory.objects.count(),
            'ai_suggestions': AIDiscoverySuggestion.objects.count(),
            'serving_adjustments': ServingAdjustment.objects.count(),
        },
        'preserved': [
            'Search source configurations',
            'AI prompt templates',
            'Application settings',
        ],
        'warnings': [
            'All user data will be permanently deleted',
            'All recipe images will be removed from storage',
            'This action cannot be undone',
        ]
    }
```

**2. Execute Reset (`POST /api/system/reset/`)**

Performs the complete database reset:

```python
# apps/core/api.py
import os
import shutil
from django.conf import settings
from django.core.management import call_command
from django.contrib.sessions.models import Session

@router.post('/reset/', response={200: dict, 400: ErrorSchema})
def reset_database(request, data: ResetConfirmSchema):
    """
    Completely reset the database to factory state.

    Requires confirmation_text="RESET" to proceed.
    """
    if data.confirmation_text != 'RESET':
        return 400, {'error': 'invalid_confirmation', 'message': 'Type RESET to confirm'}

    try:
        # 1. Clear database tables (order matters for FK constraints)
        AIDiscoverySuggestion.objects.all().delete()
        ServingAdjustment.objects.all().delete()
        RecipeViewHistory.objects.all().delete()
        RecipeCollectionItem.objects.all().delete()
        RecipeCollection.objects.all().delete()
        RecipeFavorite.objects.all().delete()
        RecipeTip.objects.all().delete()
        RecipeTimer.objects.all().delete()
        RecipeIngredient.objects.all().delete()
        RecipeStep.objects.all().delete()
        Recipe.objects.all().delete()
        Profile.objects.all().delete()

        # Reset SearchSource failure counters (keep selectors)
        SearchSource.objects.all().update(
            consecutive_failures=0,
            needs_attention=False,
            last_tested=None
        )

        # 2. Clear recipe images
        images_dir = os.path.join(settings.MEDIA_ROOT, 'recipe_images')
        if os.path.exists(images_dir):
            shutil.rmtree(images_dir)
            os.makedirs(images_dir)  # Recreate empty directory

        # 3. Clear Django cache
        from django.core.cache import cache
        cache.clear()

        # 4. Clear all sessions
        Session.objects.all().delete()

        # 5. Re-run migrations (ensures clean state)
        call_command('migrate', verbosity=0)

        # 6. Re-seed default data
        call_command('seed_search_sources', verbosity=0)
        call_command('seed_ai_prompts', verbosity=0)

        return {
            'success': True,
            'message': 'Database reset complete',
            'actions_performed': [
                'Deleted all user profiles',
                'Deleted all recipes and images',
                'Cleared all favorites and collections',
                'Cleared all view history',
                'Cleared all AI cache data',
                'Reset search source counters',
                'Cleared application cache',
                'Cleared all sessions',
                'Re-ran database migrations',
                'Restored default seed data',
            ]
        }

    except Exception as e:
        return 400, {'error': 'reset_failed', 'message': str(e)}
```

**3. Schema:**

```python
# apps/core/schemas.py
from ninja import Schema

class ResetConfirmSchema(Schema):
    confirmation_text: str  # Must be "RESET"
```

### React Frontend

**1. Add Danger Zone Tab to Settings.tsx**

```typescript
type Tab = 'api' | 'prompts' | 'sources' | 'selectors' | 'users' | 'danger'

// Tab navigation
<button
  onClick={() => setActiveTab('danger')}
  className={cn(
    "tab-button",
    activeTab === 'danger' && "text-destructive"
  )}
>
  <AlertTriangle className="h-4 w-4" />
  Danger Zone
</button>

// Danger tab content
{activeTab === 'danger' && (
  <DangerZoneTab onReset={handleDatabaseReset} />
)}
```

**2. DangerZoneTab Component (`frontend/src/components/DangerZoneTab.tsx`)**

```typescript
interface DangerZoneTabProps {
  onReset: () => Promise<void>
}

export function DangerZoneTab({ onReset }: DangerZoneTabProps) {
  const [showModal, setShowModal] = useState(false)
  const [preview, setPreview] = useState<ResetPreview | null>(null)
  const [step, setStep] = useState<1 | 2>(1)
  const [confirmText, setConfirmText] = useState('')
  const [isResetting, setIsResetting] = useState(false)

  const handleResetClick = async () => {
    const data = await api.system.getResetPreview()
    setPreview(data)
    setStep(1)
    setShowModal(true)
  }

  const handleContinue = () => {
    setStep(2)
  }

  const handleConfirmReset = async () => {
    if (confirmText !== 'RESET') return

    setIsResetting(true)
    try {
      await api.system.reset({ confirmation_text: 'RESET' })
      toast.success('Database reset complete')
      // Redirect to home/profile creation
      window.location.href = '/'
    } catch (error) {
      toast.error('Failed to reset database')
    } finally {
      setIsResetting(false)
      setShowModal(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-destructive">
        <AlertTriangle className="h-5 w-5" />
        <h2 className="text-lg font-medium">Danger Zone</h2>
      </div>

      <p className="text-sm text-muted-foreground">
        Destructive operations that cannot be undone
      </p>

      <div className="rounded-lg border border-destructive/50 bg-destructive/5 p-6">
        <h3 className="font-medium text-destructive">Reset Database</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Completely reset the application to factory state
        </p>

        <ul className="mt-4 space-y-1 text-sm text-muted-foreground">
          <li>• All recipes (scraped and remixed)</li>
          <li>• All recipe images</li>
          <li>• All user profiles</li>
          <li>• All favorites, collections, and view history</li>
          <li>• All cached AI data</li>
        </ul>

        <p className="mt-4 text-xs text-muted-foreground">
          Search source configurations and AI prompts will be preserved.
        </p>

        <Button
          variant="destructive"
          className="mt-4"
          onClick={handleResetClick}
        >
          Reset Database
        </Button>
      </div>

      {/* Reset Confirmation Modal */}
      <Dialog open={showModal} onOpenChange={setShowModal}>
        <DialogContent>
          {step === 1 ? (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2 text-destructive">
                  <AlertTriangle className="h-5 w-5" />
                  Reset Database?
                </DialogTitle>
              </DialogHeader>

              <div className="space-y-4">
                <p className="text-sm">
                  This will permanently delete ALL data from the application:
                </p>

                {preview && (
                  <div className="rounded-lg border bg-muted/50 p-3">
                    <ul className="space-y-1 text-sm">
                      <li>• {preview.data_counts.profiles} profiles</li>
                      <li>• {preview.data_counts.recipes} recipes ({preview.data_counts.recipe_images} images)</li>
                      <li>• {preview.data_counts.favorites} favorites</li>
                      <li>• {preview.data_counts.collections} collections</li>
                      <li>• {preview.data_counts.view_history} view history entries</li>
                      <li>• {preview.data_counts.ai_suggestions + preview.data_counts.serving_adjustments} cached AI entries</li>
                    </ul>
                  </div>
                )}

                <p className="text-sm font-medium text-destructive">
                  This action cannot be undone.
                </p>
              </div>

              <DialogFooter>
                <Button variant="outline" onClick={() => setShowModal(false)}>
                  Cancel
                </Button>
                <Button variant="destructive" onClick={handleContinue}>
                  I understand, continue
                </Button>
              </DialogFooter>
            </>
          ) : (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2 text-destructive">
                  <AlertTriangle className="h-5 w-5" />
                  Confirm Reset
                </DialogTitle>
              </DialogHeader>

              <div className="space-y-4">
                <p className="text-sm">
                  Type <code className="rounded bg-muted px-1 font-mono">RESET</code> to confirm:
                </p>

                <Input
                  value={confirmText}
                  onChange={(e) => setConfirmText(e.target.value)}
                  placeholder="Type RESET"
                  className="font-mono"
                />
              </div>

              <DialogFooter>
                <Button variant="outline" onClick={() => { setStep(1); setConfirmText(''); }}>
                  Back
                </Button>
                <Button
                  variant="destructive"
                  onClick={handleConfirmReset}
                  disabled={confirmText !== 'RESET' || isResetting}
                >
                  {isResetting ? 'Resetting...' : 'Reset Database'}
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
```

### Legacy Frontend

**1. Add Danger Zone Tab to Settings Template**

```html
<!-- apps/legacy/templates/legacy/settings.html -->

<!-- Add tab button -->
<button type="button" class="tab-toggle-btn tab-danger" data-tab="danger">
    Danger Zone
</button>

<!-- Danger Zone Tab Content -->
<div id="tab-danger" class="tab-content hidden">
    <div class="card danger-zone-card">
        <div class="danger-header">
            <svg class="icon-warning">...</svg>
            <h2>Danger Zone</h2>
        </div>
        <p class="danger-description">
            Destructive operations that cannot be undone
        </p>

        <div class="danger-action">
            <h3>Reset Database</h3>
            <p>Completely reset the application to factory state</p>
            <ul class="delete-list">
                <li>All recipes (scraped and remixed)</li>
                <li>All recipe images</li>
                <li>All user profiles</li>
                <li>All favorites, collections, and view history</li>
                <li>All cached AI data</li>
            </ul>
            <p class="preserved-note">
                Search source configurations and AI prompts will be preserved.
            </p>
            <button type="button" class="btn btn-danger" onclick="showResetModal()">
                Reset Database
            </button>
        </div>
    </div>
</div>

<!-- Reset Modal Step 1 -->
<div id="reset-modal-step1" class="modal hidden">
    <div class="modal-backdrop"></div>
    <div class="modal-content">
        <div class="modal-header danger">
            <svg class="icon-warning">...</svg>
            <h3>Reset Database?</h3>
        </div>
        <div class="modal-body">
            <p>This will permanently delete ALL data from the application:</p>
            <div id="reset-data-summary" class="data-summary">
                <!-- Populated by JS -->
            </div>
            <p class="warning-text">This action cannot be undone.</p>
        </div>
        <div class="modal-footer">
            <button type="button" class="btn btn-secondary" onclick="closeResetModal()">
                Cancel
            </button>
            <button type="button" class="btn btn-danger" onclick="showResetStep2()">
                I understand, continue
            </button>
        </div>
    </div>
</div>

<!-- Reset Modal Step 2 -->
<div id="reset-modal-step2" class="modal hidden">
    <div class="modal-backdrop"></div>
    <div class="modal-content">
        <div class="modal-header danger">
            <svg class="icon-warning">...</svg>
            <h3>Confirm Reset</h3>
        </div>
        <div class="modal-body">
            <p>Type <code>RESET</code> to confirm:</p>
            <input type="text" id="reset-confirm-input" class="text-input mono" placeholder="Type RESET">
        </div>
        <div class="modal-footer">
            <button type="button" class="btn btn-secondary" onclick="showResetStep1()">
                Back
            </button>
            <button type="button" class="btn btn-danger" id="confirm-reset-btn" disabled onclick="executeReset()">
                Reset Database
            </button>
        </div>
    </div>
</div>
```

**2. Settings JavaScript**

```javascript
// apps/legacy/static/legacy/js/pages/settings.js

var resetPreview = null;

function showResetModal() {
    fetch('/api/system/reset-preview/')
        .then(function(response) { return response.json(); })
        .then(function(data) {
            resetPreview = data;
            renderResetSummary(data);
            document.getElementById('reset-modal-step1').classList.remove('hidden');
        })
        .catch(function(error) {
            Cookie.toast.error('Failed to load reset preview');
        });
}

function renderResetSummary(preview) {
    var counts = preview.data_counts;
    document.getElementById('reset-data-summary').innerHTML = [
        '<ul>',
        '<li>• ' + counts.profiles + ' profiles</li>',
        '<li>• ' + counts.recipes + ' recipes (' + counts.recipe_images + ' images)</li>',
        '<li>• ' + counts.favorites + ' favorites</li>',
        '<li>• ' + counts.collections + ' collections</li>',
        '<li>• ' + counts.view_history + ' view history entries</li>',
        '<li>• ' + (counts.ai_suggestions + counts.serving_adjustments) + ' cached AI entries</li>',
        '</ul>'
    ].join('');
}

function closeResetModal() {
    document.getElementById('reset-modal-step1').classList.add('hidden');
    document.getElementById('reset-modal-step2').classList.add('hidden');
    document.getElementById('reset-confirm-input').value = '';
    document.getElementById('confirm-reset-btn').disabled = true;
}

function showResetStep2() {
    document.getElementById('reset-modal-step1').classList.add('hidden');
    document.getElementById('reset-modal-step2').classList.remove('hidden');
    document.getElementById('reset-confirm-input').value = '';
    document.getElementById('confirm-reset-btn').disabled = true;
}

function showResetStep1() {
    document.getElementById('reset-modal-step2').classList.add('hidden');
    document.getElementById('reset-modal-step1').classList.remove('hidden');
}

// Enable confirm button only when RESET is typed
document.getElementById('reset-confirm-input').addEventListener('input', function(e) {
    document.getElementById('confirm-reset-btn').disabled = e.target.value !== 'RESET';
});

function executeReset() {
    var confirmText = document.getElementById('reset-confirm-input').value;
    if (confirmText !== 'RESET') return;

    var btn = document.getElementById('confirm-reset-btn');
    btn.disabled = true;
    btn.textContent = 'Resetting...';

    fetch('/api/system/reset/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ confirmation_text: 'RESET' })
    })
    .then(function(response) {
        if (response.ok) {
            Cookie.toast.success('Database reset complete');
            // Redirect to home/profile creation
            window.location.href = '/legacy/';
        } else {
            return response.json().then(function(data) {
                throw new Error(data.message || 'Failed to reset database');
            });
        }
    })
    .catch(function(error) {
        Cookie.toast.error(error.message);
        btn.disabled = false;
        btn.textContent = 'Reset Database';
    });
}
```

### CSS Additions

```css
/* Danger Zone styling */
.tab-danger {
    color: var(--color-danger);
}

.danger-zone-card {
    border-color: rgba(239, 68, 68, 0.3);
    background: rgba(239, 68, 68, 0.05);
}

.danger-header {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--color-danger);
}

.danger-header h2 {
    margin: 0;
}

.danger-description {
    color: var(--color-text-muted);
    margin-top: 4px;
}

.danger-action {
    margin-top: 24px;
    padding: 16px;
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 8px;
    background: rgba(239, 68, 68, 0.05);
}

.danger-action h3 {
    color: var(--color-danger);
    margin: 0 0 8px 0;
}

.delete-list {
    list-style: none;
    padding: 0;
    margin: 12px 0;
}

.delete-list li {
    font-size: 14px;
    color: var(--color-text-muted);
    padding: 2px 0;
}

.delete-list li::before {
    content: "•";
    margin-right: 8px;
}

.preserved-note {
    font-size: 12px;
    color: var(--color-text-muted);
    margin-top: 12px;
}

.modal-header.danger {
    color: var(--color-danger);
}

.text-input.mono {
    font-family: monospace;
}
```

### Testing

```python
def test_reset_preview_returns_counts():
    """Reset preview shows accurate data counts."""
    Profile.objects.create(name='Test')
    Recipe.objects.create(title='Test Recipe')

    response = client.get('/api/system/reset-preview/')
    data = response.json()

    assert data['data_counts']['profiles'] == 1
    assert data['data_counts']['recipes'] == 1

def test_reset_requires_confirmation():
    """Reset fails without RESET confirmation."""
    response = client.post('/api/system/reset/', json={'confirmation_text': 'wrong'})
    assert response.status_code == 400
    assert Profile.objects.exists()  # Data not deleted

def test_reset_clears_all_data():
    """Reset deletes all user data."""
    profile = Profile.objects.create(name='Test')
    recipe = Recipe.objects.create(title='Test', image='recipe_images/test.jpg')
    RecipeFavorite.objects.create(profile=profile, recipe=recipe)

    response = client.post('/api/system/reset/', json={'confirmation_text': 'RESET'})

    assert response.status_code == 200
    assert not Profile.objects.exists()
    assert not Recipe.objects.exists()
    assert not RecipeFavorite.objects.exists()

def test_reset_preserves_search_sources():
    """Reset keeps search source configurations."""
    source = SearchSource.objects.create(name='Test', host='example.com')

    client.post('/api/system/reset/', json={'confirmation_text': 'RESET'})

    assert SearchSource.objects.filter(id=source.id).exists()

def test_reset_clears_images(tmp_path, settings):
    """Reset removes all recipe images from storage."""
    settings.MEDIA_ROOT = tmp_path
    image_dir = tmp_path / 'recipe_images'
    image_dir.mkdir()
    (image_dir / 'test.jpg').write_bytes(b'fake image')

    Recipe.objects.create(title='Test', image='recipe_images/test.jpg')

    client.post('/api/system/reset/', json={'confirmation_text': 'RESET'})

    assert not (image_dir / 'test.jpg').exists()
    assert image_dir.exists()  # Directory recreated empty

def test_reset_invalidates_session():
    """Reset clears all sessions."""
    # Create a session
    session = client.session
    session['profile_id'] = 1
    session.save()

    client.post('/api/system/reset/', json={'confirmation_text': 'RESET'})

    from django.contrib.sessions.models import Session
    assert not Session.objects.exists()
```

### Acceptance Criteria (9.10)

1. Settings page has "Danger Zone" tab on both React and Legacy
2. Tab displays with red/warning styling to indicate danger
3. Reset Database button shows two-step confirmation modal
4. Step 1 shows data summary (counts of what will be deleted)
5. Step 2 requires typing "RESET" to enable confirm button
6. Reset operation deletes:
   - All profiles
   - All recipes and images
   - All favorites and collections
   - All view history
   - All AI cached data
7. Reset preserves:
   - Search source configurations
   - AI prompt templates
8. Reset clears recipe_images directory
9. Reset clears Django cache
10. Reset invalidates all sessions
11. Reset re-runs migrations
12. Reset re-seeds default data
13. After reset, user is redirected to home/profile creation
14. Toast notification confirms success/failure
15. Works consistently on both React and Legacy interfaces

---

## Error Handling

### API Error Responses

```python
# Standard error response format
{
    "error": "error_code",
    "message": "Human-readable message",
    "details": {}  # Optional additional info
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `validation_error` | 400 | Invalid input data |
| `not_found` | 404 | Resource not found |
| `profile_required` | 401 | No profile selected |
| `ai_unavailable` | 503 | AI features unavailable |
| `scrape_failed` | 502 | Recipe scraping failed |
| `rate_limited` | 429 | Too many requests |
| `server_error` | 500 | Internal error |

### Frontend Error Display

**React:**
- Use Sonner toast notifications
- Show loading skeletons during data fetch
- Show empty states with CTAs when no data

**Legacy:**
- Use simple toast/alert system
- Show loading indicators
- Show empty states

---

## Loading States

### React

Use skeleton components while loading:
- Recipe card skeleton
- Recipe detail skeleton
- List skeleton

```tsx
// Example skeleton
export function RecipeCardSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="bg-muted h-48 rounded-t-lg" />
      <div className="p-4 space-y-2">
        <div className="bg-muted h-4 w-3/4 rounded" />
        <div className="bg-muted h-4 w-1/2 rounded" />
      </div>
    </div>
  );
}
```

### Legacy

Use simple loading indicators:
- Spinning indicator
- "Loading..." text
- Disabled buttons during requests

---

## Toast Notifications

### React (Sonner)

```tsx
import { toast } from 'sonner';

// Success
toast.success('Recipe saved to favorites');

// Error
toast.error('Failed to load recipe');

// Loading
toast.loading('Saving...');
```

### Legacy

```javascript
// legacy/static/legacy/js/toast.js
var Cookie = Cookie || {};
Cookie.toast = (function() {
    var container = document.getElementById('toast-container');

    function show(message, type) {
        var toast = document.createElement('div');
        toast.className = 'toast toast-' + (type || 'info');
        toast.textContent = message;
        container.appendChild(toast);

        setTimeout(function() {
            toast.classList.add('fade-out');
            setTimeout(function() {
                container.removeChild(toast);
            }, 300);
        }, 3000);
    }

    return {
        success: function(msg) { show(msg, 'success'); },
        error: function(msg) { show(msg, 'error'); },
        info: function(msg) { show(msg, 'info'); }
    };
})();
```

---

## Testing Strategy

### Test Framework

- **pytest** for all tests
- Django test client for API tests
- pytest-asyncio for async tests

### Test Categories

1. **Unit Tests:** Models, services, utilities
2. **Integration Tests:** API endpoints, full flows
3. **Manual Testing:** Both interfaces on target devices

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_profiles.py
├── test_recipes.py
├── test_collections.py
├── test_ai.py
├── test_scraping.py
├── test_search.py
└── test_settings.py
```

### Key Test Cases

```python
# Profiles
def test_create_profile()
def test_select_profile_sets_session()
def test_delete_profile_cascades_data()

# Recipes
def test_scrape_recipe_saves_image_locally()
def test_scrape_same_url_creates_new_recipe()
def test_recipe_deletion_orphans_remixes()

# Collections
def test_favorites_per_profile_isolation()
def test_collection_crud()
def test_remix_visibility_per_profile()

# AI
def test_ai_unavailable_without_key()
def test_remix_creates_new_recipe()
def test_serving_adjustment_hidden_without_servings()
def test_discover_daily_refresh()

# Search
def test_multi_site_search()
def test_source_filtering()
def test_rate_limiting()
```

---

## Cross-Browser Testing

### Modern Browsers (React)
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

### Legacy (iOS 9)
- [ ] iOS 9 iPad (real device or simulator)
- [ ] Test all ES5 code paths
- [ ] Test timers in play mode
- [ ] Test all user flows

### Test Checklist

- [ ] Profile selection and switching
- [ ] Recipe search and import
- [ ] Favorites and collections
- [ ] Recipe detail with all tabs
- [ ] Play mode with timers
- [ ] Settings all tabs
- [ ] Dark/light theme (React only)
- [ ] AI features (with API key)
- [ ] AI features hidden (without API key)
- [ ] Error states and empty states
- [ ] Loading states

---

## Acceptance Criteria

1. Settings screen works on both interfaces
2. All 5 settings tabs functional (General, AI Prompts, Sources, Selectors, Users)
3. API key can be set and tested
4. Error messages are clear and actionable
5. Loading states prevent UI flashing
6. Toast notifications work on both interfaces
7. All unit and integration tests pass
8. App works on iOS 9 iPad
9. App works on modern browsers
10. No console errors in production
11. User management: list profiles with stats, delete with cascade
12. Profile deletion removes all related data including recipe images
13. All 15 search sources operational or replaced with working alternatives

---

## Search Source Health Review (Session E - Task 9.9)

**Purpose:** Audit all recipe search sources, repair broken selectors using AI, and replace sources that cannot be fixed with new working alternatives.

### Background

Over time, recipe sites change their HTML structure, breaking CSS selectors. The `SearchSource` model tracks:
- `consecutive_failures` - incremented when searches return 0 results
- `needs_attention` - set to True after 3+ failures
- `last_tested` - timestamp of last successful/failed test
- `result_selector` - CSS selector for extracting recipe links

### Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Source Health Review                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Generate Health Report                                      │
│     └── List all sources with failure counts, last test date    │
│                                                                 │
│  2. For each FAILED source:                                     │
│     ├── Attempt AI Selector Repair (8B.9)                       │
│     │   ├── If confidence >= 0.8 → Apply fix, test again        │
│     │   └── If confidence < 0.8 → Manual review needed          │
│     │                                                           │
│     └── If AI repair fails:                                     │
│         ├── Try manual selector fix                             │
│         └── If unfixable → Find replacement source              │
│                                                                 │
│  3. Update source configuration                                 │
│     ├── Fix selectors                                           │
│     ├── Add new sources                                         │
│     └── Disable permanently broken sources                      │
│                                                                 │
│  4. Verify all 15 sources return results                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Step 1: Generate Health Report

Run the Source Selectors tab "Test All Sources" or use a script:

```python
# Script to generate source health report
from apps.recipes.models import SearchSource

def source_health_report():
    sources = SearchSource.objects.all().order_by('-consecutive_failures')

    print("=" * 60)
    print("SEARCH SOURCE HEALTH REPORT")
    print("=" * 60)

    healthy = []
    needs_attention = []

    for source in sources:
        status = "🟢 OK" if source.consecutive_failures == 0 else \
                 "🟡 WARN" if source.consecutive_failures < 3 else \
                 "🔴 FAIL"

        if source.consecutive_failures >= 3:
            needs_attention.append(source)
        else:
            healthy.append(source)

        print(f"{status} {source.name}")
        print(f"    Host: {source.host}")
        print(f"    Failures: {source.consecutive_failures}")
        print(f"    Last tested: {source.last_tested or 'Never'}")
        print(f"    Selector: {source.result_selector[:50]}...")
        print()

    print("=" * 60)
    print(f"SUMMARY: {len(healthy)} healthy, {len(needs_attention)} need attention")
    print("=" * 60)

    return needs_attention

# Run: python manage.py shell < scripts/source_health.py
```

### Step 2: AI Selector Repair (8B.9 Integration)

For each failed source, attempt AI repair:

```python
from apps.ai.services.selector import repair_selector
from apps.recipes.models import SearchSource

def attempt_ai_repairs():
    failed_sources = SearchSource.objects.filter(consecutive_failures__gte=3)

    for source in failed_sources:
        print(f"\n{'='*40}")
        print(f"Attempting AI repair for: {source.name}")
        print(f"Current selector: {source.result_selector}")

        try:
            result = repair_selector(source)

            if result['success']:
                print(f"✅ AI repaired selector!")
                print(f"   New selector: {result['new_selector']}")
                print(f"   Confidence: {result['confidence']}")

                # Test the new selector
                test_result = test_source(source)
                if test_result['success']:
                    print(f"   Test passed: {test_result['result_count']} results")
                else:
                    print(f"   ⚠️ Test failed even with new selector")
            else:
                print(f"❌ AI could not repair (confidence too low)")
                print(f"   Best suggestion: {result.get('suggestion', 'None')}")
                print(f"   Confidence: {result.get('confidence', 0)}")

        except Exception as e:
            print(f"❌ AI repair error: {e}")
```

### Step 3: Manual Repair / Replacement

If AI repair fails, manually inspect and either:

**Option A: Manual Selector Fix**
1. Visit the source site in browser
2. Open DevTools, find recipe link elements
3. Identify new CSS selector
4. Update via Settings > Source Selectors tab
5. Test the new selector

**Option B: Replace Source**
1. Find alternative recipe site with similar content
2. Create new `SearchSource` entry
3. Configure selector for new site
4. Disable the broken source

### Replacement Source Candidates

If existing sources cannot be fixed, consider these alternatives:

| Category | Current Source | Potential Replacement |
|----------|---------------|----------------------|
| General | AllRecipes | Food.com, Yummly |
| Healthy | EatingWell | Cooking Light, Skinnytaste |
| Budget | Budget Bytes | $5 Dinners, Good Cheap Eats |
| Quick | Tasty | Delish, Simply Recipes |
| International | Serious Eats | The Woks of Life, RecipeTin Eats |
| Baking | Sally's Baking | King Arthur, Handle the Heat |
| Vegetarian | Cookie and Kate | Minimalist Baker, Oh She Glows |

### Step 4: Verification Checklist

After repairs/replacements, verify:

```
[ ] Source 1:  AllRecipes.com     - Returns results? ___
[ ] Source 2:  Food Network       - Returns results? ___
[ ] Source 3:  Serious Eats       - Returns results? ___
[ ] Source 4:  Epicurious         - Returns results? ___
[ ] Source 5:  Bon Appetit        - Returns results? ___
[ ] Source 6:  Tasty.co           - Returns results? ___
[ ] Source 7:  Delish             - Returns results? ___
[ ] Source 8:  Simply Recipes     - Returns results? ___
[ ] Source 9:  Budget Bytes       - Returns results? ___
[ ] Source 10: Cookie and Kate    - Returns results? ___
[ ] Source 11: Sally's Baking     - Returns results? ___
[ ] Source 12: NYT Cooking        - Returns results? ___
[ ] Source 13: BBC Good Food      - Returns results? ___
[ ] Source 14: Taste of Home      - Returns results? ___
[ ] Source 15: EatingWell         - Returns results? ___
```

### Implementation Notes

**Using AI Selector Repair (8B.9):**

The AI selector repair feature (implemented in Phase 8B.9) can be invoked:

1. **Via API:**
   ```bash
   curl -X POST http://localhost:8000/api/ai/repair-selector/ \
     -H "Content-Type: application/json" \
     -d '{"source_id": 123}'
   ```

2. **Via Settings UI:**
   - Go to Settings > Source Selectors
   - Click "Test" on a failed source
   - If test fails, click "AI Repair" button (if available)

3. **Via Script:**
   ```python
   from apps.ai.services.selector import repair_selector
   source = SearchSource.objects.get(host='example.com')
   result = repair_selector(source)
   ```

**Auto-Repair Consideration:**

For production, consider enabling automatic repair in the search flow:
- When a source returns 0 results, trigger async AI repair
- See `plans/FUTURE-ENHANCEMENTS.md` FE-002 for the full spec

### Session E Deliverables

1. Health report generated for all 15 sources
2. AI repair attempted on all failed sources
3. Manual fixes applied where AI repair insufficient
4. Replacement sources added for unfixable sites
5. All 15 sources verified returning search results
6. Documentation updated with any new sources or selector patterns

### Acceptance Criteria (9.9)

1. All 15 configured search sources return results on test
2. No sources have `needs_attention=True`
3. `consecutive_failures=0` for all active sources
4. Any replaced sources documented in source comments
5. AI selector repair feature tested and working

---

## Browser Fingerprint Spoofer Review (Session G - Task 9.11)

**Purpose:** Review and optimize the browser fingerprint spoofing library used for web scraping to ensure it is configured correctly, using best practices, and maximizing success rates when scraping recipe sites.

### Background

The application uses browser fingerprint spoofing to avoid bot detection when scraping recipe websites. This session involves:
- Auditing the current fingerprint spoofer configuration
- Reviewing how it integrates with the scraping service
- Ensuring optimal settings for recipe site compatibility
- Identifying any missed opportunities or misconfigurations

### Review Areas

#### 1. Library Audit

**Identify Current Implementation:**
- Which fingerprint spoofing library is in use?
- What version is installed?
- Is there a more recent/better maintained alternative?

**Library Options (common ones):**
- `playwright-stealth` / `puppeteer-stealth`
- `undetected-chromedriver`
- `fake-useragent`
- `curl-cffi` (for requests-based scraping)
- Custom header rotation

**Questions to Answer:**
- Is the library actively maintained?
- Does it handle all major fingerprinting vectors?
- Is it compatible with async operations?

#### 2. Configuration Review

**Check Settings For:**

| Setting | Purpose | Optimal Value |
|---------|---------|---------------|
| User-Agent rotation | Avoid same-UA detection | Pool of 20+ modern UAs |
| Accept-Language | Match realistic browser | Weighted by region |
| Accept-Encoding | Content negotiation | gzip, deflate, br |
| Referer | Hide scraper origin | Google search or direct |
| DNT (Do Not Track) | Realistic browser behavior | Random (1/0) |
| Sec-Fetch-* headers | Modern browser markers | Match Chrome/Firefox |
| Connection timing | Avoid bot patterns | Random delays (1-5s) |
| TLS fingerprint | Advanced detection | JA3 spoofing if available |
| WebGL/Canvas | Advanced fingerprinting | Spoof if browser-based |
| Screen resolution | Device fingerprinting | Common resolutions |

**Configuration Checklist:**
```
[ ] User-Agent pool is diverse and current
[ ] Headers match a real browser exactly
[ ] Request timing has realistic randomization
[ ] TLS fingerprint matches browser (if applicable)
[ ] Cookies are handled appropriately
[ ] Proxy rotation configured (if used)
[ ] Session persistence mimics real user
```

#### 3. Integration Review

**How Fingerprinting Integrates with Scraping:**

1. **Search Service** (`apps/recipes/services/search.py`)
   - Review how headers are set for search requests
   - Check if fingerprinting is applied consistently
   - Verify retry logic uses different fingerprints

2. **Scrape Service** (`apps/recipes/services/scrape.py`)
   - Review how recipes are fetched
   - Check if fingerprinting matches search service
   - Verify image downloads use same spoofing

3. **Source Testing** (Source Selectors tab)
   - Ensure test requests use production fingerprinting
   - Results should match real scrape success rates

**Code Review Points:**
```python
# Check for these patterns:

# ❌ Bad: Hardcoded single User-Agent
headers = {'User-Agent': 'Mozilla/5.0 ...'}

# ✅ Good: Rotated from pool
headers = {'User-Agent': get_random_user_agent()}

# ❌ Bad: Missing modern headers
headers = {'User-Agent': ua}

# ✅ Good: Complete header set
headers = {
    'User-Agent': ua,
    'Accept': 'text/html,application/xhtml+xml...',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    ...
}
```

#### 4. Best Practices Checklist

**Request Behavior:**
- [ ] Random delays between requests (not fixed intervals)
- [ ] Delays vary per domain (some sites stricter than others)
- [ ] Session cookies preserved across requests to same domain
- [ ] Referer header set realistically (Google search, direct, etc.)
- [ ] Failed requests retry with different fingerprint

**Header Quality:**
- [ ] User-Agent pool contains only modern, valid UAs
- [ ] Accept headers match User-Agent browser type
- [ ] Sec-Fetch headers present and correct
- [ ] No scraper-identifying headers leaked

**Detection Avoidance:**
- [ ] Request rate respects site's tolerance
- [ ] No predictable request patterns
- [ ] IP reputation maintained (proxy rotation if needed)
- [ ] Handles soft blocks gracefully (CAPTCHA, rate limits)

#### 5. Site-Specific Considerations

Some recipe sites may have stricter bot detection:

| Site | Protection Level | Notes |
|------|-----------------|-------|
| AllRecipes | Low | Basic UA check |
| Food Network | Medium | Cloudflare |
| NYT Cooking | High | Paywall + bot detection |
| Serious Eats | Low | Minimal protection |
| BBC Good Food | Low-Medium | Regional checks |
| Epicurious | Medium | Rate limiting |

**For stricter sites, consider:**
- Longer delays
- Residential proxy IP (if available)
- Browser-based scraping (Playwright) as fallback

#### 6. Testing Methodology

**Manual Testing:**
```bash
# Test single source with verbose output
python manage.py shell
>>> from apps.recipes.services.search import search_recipes
>>> results = search_recipes('chocolate cake', sources=['allrecipes'])
>>> print(f"Found {len(results)} results")

# Check headers being sent
>>> import httpx
>>> # Add request logging to see exact headers
```

**Automated Testing:**
```python
def test_fingerprint_rotation():
    """Verify fingerprints change between requests."""
    fingerprints = set()
    for _ in range(10):
        headers = get_spoofed_headers()
        fingerprints.add(headers['User-Agent'])
    assert len(fingerprints) >= 5, "Should use diverse User-Agents"

def test_headers_complete():
    """Verify all required headers present."""
    headers = get_spoofed_headers()
    required = ['User-Agent', 'Accept', 'Accept-Language', 'Accept-Encoding']
    for key in required:
        assert key in headers, f"Missing header: {key}"

def test_modern_ua():
    """Verify User-Agents are current browser versions."""
    headers = get_spoofed_headers()
    ua = headers['User-Agent']
    # Should be Chrome 100+ or equivalent
    assert 'Chrome/1' in ua or 'Firefox/1' in ua
```

### Implementation Tasks

1. **Audit Current Setup**
   - Locate fingerprint spoofing code
   - Document current configuration
   - List all headers being sent

2. **Identify Gaps**
   - Compare against best practices checklist
   - Note missing headers or outdated UAs
   - Check for inconsistent application

3. **Optimize Configuration**
   - Update User-Agent pool with current browsers
   - Add missing Sec-Fetch headers
   - Implement proper header ordering
   - Add realistic request timing

4. **Test Changes**
   - Test against all 15 sources
   - Verify success rate improves or maintains
   - Check for any regressions

5. **Document Configuration**
   - Add comments explaining each header
   - Document any site-specific handling
   - Note recommended update frequency for UA pool

### Deliverables

1. Audit report of current fingerprint configuration
2. List of improvements/optimizations made
3. Updated configuration with best practices applied
4. Test results showing source compatibility
5. Documentation of fingerprint settings

### Acceptance Criteria (9.11)

1. Fingerprint spoofer code is located and documented
2. Current configuration is audited against best practices
3. User-Agent pool contains only modern, valid browsers
4. All required HTTP headers are present and correctly formatted
5. Request timing includes appropriate randomization
6. All 15 search sources work with updated configuration
7. No regression in scrape success rates
8. Configuration is documented with maintenance notes

---

## Checkpoint (End of Phase)

```
[ ] Settings General tab - profile management, API key, about section
[ ] Settings AI Prompts tab - all 10 prompts editable
[ ] Settings Sources tab - enable/disable 15 sources
[ ] Settings Selectors tab - edit and test CSS selectors
[ ] Settings Users tab - list all profiles with stats
[ ] User deletion - cascade removes all related data
[ ] User deletion - recipe images cleaned up from filesystem
[ ] User deletion - confirmation modal shows data summary
[ ] Settings Danger Zone tab - reset database option visible
[ ] Database reset - two-step confirmation modal works
[ ] Database reset - deletes all profiles, recipes, images, cache
[ ] Database reset - preserves search sources and AI prompts
[ ] Database reset - re-seeds default data after reset
[ ] Database reset - invalidates sessions, redirects to home
[ ] API error - toast notification with clear message
[ ] Loading state - skeleton/spinner shown during fetch
[ ] Toast on success - "Recipe saved" etc. appears
[ ] pytest - ALL tests pass (unit + integration)
[ ] Chrome/Firefox/Safari/Edge - React interface works
[ ] iOS 9 iPad - Legacy interface fully functional
[ ] Browser console - no errors in production
[ ] Source health - all 15 sources audited
[ ] Source health - AI repair attempted on failed sources
[ ] Source health - all sources returning results or replaced
[ ] Source health - no sources with needs_attention=True
[ ] Fingerprint spoofer - code located and documented
[ ] Fingerprint spoofer - configuration audited against best practices
[ ] Fingerprint spoofer - User-Agent pool is modern and diverse
[ ] Fingerprint spoofer - all required HTTP headers present
[ ] Fingerprint spoofer - request timing has randomization
[ ] Fingerprint spoofer - all sources work with updated config
```

---

## Final Checklist

- [ ] All phases complete
- [ ] All tests passing
- [ ] No console errors
- [ ] All 15 sources have working selectors (audited & repaired/replaced)
- [ ] AI features work with valid API key
- [ ] AI features hidden without API key
- [ ] AI selector repair tested and functional
- [ ] iOS 9 iPad fully functional
- [ ] Dark mode works (React)
- [ ] Light-only theme works (Legacy)
- [ ] Images stored locally
- [ ] Timers work in play mode
- [ ] Data properly isolated per profile
- [ ] User management works on both interfaces
- [ ] Profile deletion cascades all data including images
- [ ] Danger Zone tab with database reset works on both interfaces
- [ ] Database reset performs complete factory reset with confirmation
- [ ] Fingerprint spoofer reviewed and optimized for best practices
- [ ] All scraping headers modern and properly configured

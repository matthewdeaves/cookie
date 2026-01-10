# QA-059: Phase 10 CI/CD Code Review Items

## Status
**RESOLVED** - All 6 items implemented

## Phase
Phase 10 (GitHub Actions CI/CD)

## Issue

Code review of Phase 10 implementation identified several items that should be addressed before or shortly after initial deployment.

---

## Items

### 1. STATICFILES_DIRS Missing Directory Check

**File:** `cookie/settings.py:108-110`

**Problem:** `STATICFILES_DIRS` includes `frontend/dist` which won't exist in development unless the frontend has been built. This causes `collectstatic` to fail in dev environments.

```python
STATICFILES_DIRS = [
    BASE_DIR / 'frontend' / 'dist',
]
```

**Fix:**
```python
_frontend_dist = BASE_DIR / 'frontend' / 'dist'
STATICFILES_DIRS = [_frontend_dist] if _frontend_dist.exists() else []
```

**Severity:** Medium - Breaks dev workflow for `collectstatic`

---

### 2. STATICFILES_STORAGE Deprecated in Django 4.2+

**File:** `cookie/settings.py:113`

**Problem:** `STATICFILES_STORAGE` was deprecated in Django 4.2 and will be **removed in Django 5.1**. Since we're on Django 5.0, this works but shows deprecation warnings.

```python
# Current (deprecated):
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

**Fix:** Use the new `STORAGES` dict format:
```python
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
```

**Severity:** Low - Works now, but will break on Django 5.1 upgrade

**Reference:** [Django 4.2 Release Notes](https://docs.djangoproject.com/en/5.1/releases/4.2/) | [Migration Guide](https://medium.com/@awaisq/upgrade-django-4-2-to-5-2-key-changes-d6b073709352)

---

### 3. Test Mock Data Duplication

**File:** `frontend/src/test/components.test.tsx:57,74,139`

**Problem:** `mockStats` object is defined identically 3 times in different test cases.

```typescript
const mockStats = { favorites: 0, collections: 0, collection_items: 0, remixes: 0, view_history: 0, scaling_cache: 0, discover_cache: 0 }
```

**Fix:** Extract to a shared constant at the top of the file:
```typescript
const mockStats: ProfileStats = {
  favorites: 0,
  collections: 0,
  collection_items: 0,
  remixes: 0,
  view_history: 0,
  scaling_cache: 0,
  discover_cache: 0,
}
```

**Severity:** Low - Code smell, no functional impact

---

### 4. Test Files in Production Docker Image

**File:** `Dockerfile.prod:59,61-62`

**Problem:** Test files (`tests/`, `pytest.ini`, `conftest.py`) are copied into the production image, adding unnecessary bloat.

```dockerfile
# Line 59 - remove:
COPY --chown=app:app tests/ tests/
# Line 60 - KEEP (required for Django):
COPY --chown=app:app manage.py .
# Lines 61-62 - remove:
COPY --chown=app:app pytest.ini .
COPY --chown=app:app conftest.py .
```

**Fix:** Remove lines 59, 61, and 62. Keep line 60 (`manage.py`). Tests should only run in CI, not in production containers.

**Severity:** Low - ~50KB bloat, no security impact

---

### 5. Volume Mount Permission Handling

**File:** `entrypoint.prod.sh:6`

**Problem:** `mkdir -p "$DATA_DIR/media"` fails if `/app/data` is a volume mounted with different ownership than the container's `app` user.

```bash
mkdir -p "$DATA_DIR/media"
```

**Research:** Docker volume permissions are a common pain point. The UID/GID of the container user must match the volume's owner, or the directory must be pre-created with correct permissions.

**Options:**
1. **Add error handling** (simplest):
   ```bash
   mkdir -p "$DATA_DIR/media" 2>/dev/null || echo "Warning: Could not create media directory"
   ```

2. **Document volume setup** in README:
   ```bash
   # Before first run:
   mkdir -p ./data && chmod 777 ./data
   ```

3. **Use fixuid** or **gosu** to dynamically match host UID (complex)

**Severity:** Medium - Causes container startup failure with some volume configurations

**Reference:** [Docker Volume Permissions Guide](https://mydeveloperplanet.com/2022/10/19/docker-files-and-volumes-permission-denied/) | [MatchHostFsOwner Solution](https://www.joyfulbikeshedding.com/blog/2023-04-20-cure-docker-volume-permission-pains-with-matchhostfsowner.html)

---

### 6. datetime.utcnow() Deprecated in Python 3.12+

**File:** `.github/workflows/coverage.yml:171`

**Problem:** `datetime.utcnow()` is deprecated in Python 3.12 and will be removed in a future version.

```python
'generated_at': datetime.utcnow().isoformat() + 'Z',
```

**Fix:** Use timezone-aware datetime:
```python
from datetime import datetime, timezone
'generated_at': datetime.now(timezone.utc).isoformat(),
```

Note: `.isoformat()` on a timezone-aware datetime already includes the `+00:00` suffix, so no need to append `'Z'`.

**Severity:** Low - Shows deprecation warning, still works in Python 3.12

**Reference:** [Miguel Grinberg's Explanation](https://blog.miguelgrinberg.com/post/it-s-time-for-a-change-datetime-utcnow-is-now-deprecated) | [Simon Willison's Fix Guide](https://til.simonwillison.net/python/utc-warning-fix)

---

## Priority

Low/Medium - None of these block the initial deployment. They should be addressed in a follow-up session.

## Recommendation

1. Fix items #1 and #5 before deployment (Medium severity, affect usability)
2. Fix remaining items in next maintenance session
3. Add Django 5.1 upgrade to future roadmap (item #2 becomes blocking)

## Affected Components

- `cookie/settings.py` - Django configuration
- `frontend/src/test/components.test.tsx` - Frontend tests
- `Dockerfile.prod` - Production container
- `entrypoint.prod.sh` - Container startup script
- `.github/workflows/coverage.yml` - CI coverage workflow

---

## Implementation Plan

**Session scope:** All 6 fixes can be completed in a single session.

### Phase A: Medium Severity Items (Pre-deployment)

#### Step 1: Fix STATICFILES_DIRS directory check
**File:** `cookie/settings.py`

1. Replace lines 107-110:
   ```python
   # Include built frontend assets in static files
   STATICFILES_DIRS = [
       BASE_DIR / 'frontend' / 'dist',
   ]
   ```
   With:
   ```python
   # Include built frontend assets in static files (only if directory exists)
   _frontend_dist = BASE_DIR / 'frontend' / 'dist'
   STATICFILES_DIRS = [_frontend_dist] if _frontend_dist.exists() else []
   ```

2. Verify: Run `python manage.py collectstatic --dry-run` in dev environment without `frontend/dist`

#### Step 2: Fix volume mount permission handling
**File:** `entrypoint.prod.sh`

1. Replace line 6:
   ```bash
   mkdir -p "$DATA_DIR/media"
   ```
   With:
   ```bash
   mkdir -p "$DATA_DIR/media" 2>/dev/null || {
       echo "Warning: Could not create $DATA_DIR/media - ensure volume has correct permissions"
   }
   ```

2. Verify: Test container startup with a read-only volume mount

---

### Phase B: Low Severity Items (Post-deployment)

#### Step 3: Migrate to STORAGES dict format
**File:** `cookie/settings.py`

1. Replace line 113:
   ```python
   STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
   ```
   With:
   ```python
   STORAGES = {
       "default": {
           "BACKEND": "django.core.files.storage.FileSystemStorage",
       },
       "staticfiles": {
           "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
       },
   }
   ```

2. Verify: Run `python manage.py check` and confirm no deprecation warnings

#### Step 4: Extract shared test mock data
**File:** `frontend/src/test/components.test.tsx`

1. Add `ProfileStats` to the import from `../api/client` (if not already imported):
   ```typescript
   import type { ProfileStats } from '../api/client'
   ```

2. Add shared constant after the mock definitions (around line 36):
   ```typescript
   // Shared test fixtures
   const mockStats: ProfileStats = {
     favorites: 0,
     collections: 0,
     collection_items: 0,
     remixes: 0,
     view_history: 0,
     scaling_cache: 0,
     discover_cache: 0,
   }
   ```

3. Remove the duplicate `mockStats` definitions from lines 57, 74, and 139

4. Verify: Run `npm test` in frontend directory

#### Step 5: Remove test files from production Docker image
**File:** `Dockerfile.prod`

1. Remove line 59:
   ```dockerfile
   COPY --chown=app:app tests/ tests/
   ```

2. Remove lines 61-62:
   ```dockerfile
   COPY --chown=app:app pytest.ini .
   COPY --chown=app:app conftest.py .
   ```

3. Keep line 60 (`manage.py` - required for Django)

4. Verify: Build image and confirm it starts correctly

#### Step 6: Fix deprecated datetime.utcnow()
**File:** `.github/workflows/coverage.yml`

1. Find the line `from datetime import datetime` (in the embedded Python script) and change to:
   ```python
   from datetime import datetime, timezone
   ```

2. Find the line containing `datetime.utcnow()` and replace:
   ```python
   # Before:
   'generated_at': datetime.utcnow().isoformat() + 'Z',
   # After:
   'generated_at': datetime.now(timezone.utc).isoformat(),
   ```

3. Verify: Push to branch and confirm coverage workflow runs without warnings

---

### Verification Checklist

After implementation, verify:

- [ ] `python manage.py collectstatic --dry-run` works without `frontend/dist`
- [ ] `python manage.py check` shows no deprecation warnings
- [ ] Docker container starts with volume mount
- [ ] Frontend tests pass (`npm test`)
- [ ] Docker image builds and runs correctly
- [ ] Coverage workflow completes successfully

---

### Rollback Plan

All changes are isolated and low-risk. If issues arise:

1. **Settings changes** (Steps 1, 3): Revert `cookie/settings.py` to previous version
2. **Entrypoint change** (Step 2): Revert `entrypoint.prod.sh` to previous version
3. **Test refactor** (Step 4): No production impact, revert if tests fail
4. **Dockerfile change** (Step 5): Revert `Dockerfile.prod` and rebuild
5. **Workflow change** (Step 6): Revert `.github/workflows/coverage.yml`

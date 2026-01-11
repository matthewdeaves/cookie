# Future Enhancements

> **Purpose:** Log feature ideas and enhancements for future development
> **Status:** Backlog - implement when needed

---

## Enhancement Log

| ID | Summary | Priority | Complexity |
|----|---------|----------|------------|
| FE-001 | Database-driven search URL filters with settings UI | Medium | Medium |
| FE-002 | Automatic selector repair on search failure | Low | Medium |
| FE-003 | OAuth/social login for production deployment mode | High | High |
| FE-004 | Settings page access control (admin-only restriction) | Medium | Medium |
| FE-005 | Migrate from SQLite to MySQL/PostgreSQL | Medium | Medium |
| FE-006 | Multi-selection for AI remix suggestions | Low | Low |
| FE-007 | ~~Add nginx to production container for dev/prod parity~~ | ~~High~~ | ~~Medium~~ |
| FE-008 | ~~Docker Hub: Only maintain latest image, no version history~~ | ~~Low~~ | ~~Low~~ |
| FE-009 | AI-powered meal pairing suggestions | Medium | Medium |
| FE-010 | ~~Investigate GitHub native ARM64 runners for faster CD builds~~ | ~~Low~~ | ~~Low~~ |
| FE-011 | ~~Modern frontend nutrition labels show raw camelCase keys~~ | ~~Low~~ | ~~Low~~ |
| FE-012 | ~~Historical code quality metrics with trend graphs~~ | ~~Low~~ | ~~Medium~~ |
| FE-013 | Linked recipe navigation (original ↔ remix toggle) | Low | Low |
| FE-014 | Legacy frontend discover suggestions grid layout | Low | Low |

---

## FE-001: Database-Driven Search URL Filters

**Status:** Backlog

### Problem

Search result URL filtering patterns are currently hardcoded in `apps/recipes/services/search.py`. Adding new patterns requires code changes and deployment.

### Current Implementation

- Patterns defined in `_looks_like_recipe_url()` method
- Includes ~40 exclusion patterns for articles, videos, index pages
- No way to add/edit/delete patterns without code changes

### Proposed Solution

1. **New Model:** `SearchUrlFilter`
   - `pattern` - regex pattern to match
   - `filter_type` - include/exclude
   - `category` - article, video, index, etc.
   - `enabled` - toggle on/off
   - `notes` - description of what it catches

2. **Settings Page:**
   - List all filters with enable/disable toggle
   - Add new filter with pattern validation
   - Edit existing filters
   - Delete filters
   - Test pattern against sample URLs

3. **Migration:**
   - Seed database with current hardcoded patterns
   - Update `_looks_like_recipe_url()` to query database

### Benefits

- Non-developers can manage filters
- No deployment needed for new patterns
- Can quickly disable problematic patterns
- Audit trail of filter changes

### Files to Change

- `apps/recipes/models.py` - Add `SearchUrlFilter` model
- `apps/recipes/services/search.py` - Query filters from database
- `apps/legacy/views.py` - Settings page view
- `apps/legacy/templates/legacy/settings.html` - Filter management UI
- New migration to seed existing patterns

### Notes

- Cache filter queries to avoid DB hit on every search
- Invalidate cache when filters are modified
- Consider regex validation on save to prevent invalid patterns

---

## FE-002: Automatic Selector Repair on Search Failure

**Status:** Backlog

### Problem

When a search source's CSS selector breaks (site redesign), the source returns 0 results. Currently, broken selectors require manual admin intervention to repair.

### Current Implementation

- `search.py` tracks `consecutive_failures` and sets `needs_attention=True` after 3 failures
- `apps/ai/services/selector.py` provides `repair_selector()` function
- API endpoint `POST /api/ai/repair-selector` for manual repair
- Admin must manually trigger repair via API

### Proposed Solution

Add automatic inline integration to the search flow:

1. **Detect failure:** When 0 results are returned AND we have the HTML response
2. **Trigger async repair:** Fire-and-forget background task (non-blocking)
3. **AI analysis:** Repair runs in background, calls AI to suggest new selector
4. **Auto-update:** If confidence >= threshold, update the source's selector
5. **Next search:** Uses the repaired selector automatically

### Implementation Details

```python
# In search.py _search_source()
if not results and html_response:
    # Fire-and-forget async repair
    from apps.ai.services.selector import repair_selector
    import threading
    threading.Thread(
        target=repair_selector,
        args=(source, html_response),
        kwargs={'auto_update': True},
        daemon=True
    ).start()
```

### Benefits

- Self-healing search sources
- No admin intervention needed for common selector breakage
- Repairs happen transparently in background
- Next user search benefits from repaired selector

### Considerations

- Don't spam AI with repair attempts (rate limit per source)
- Log all auto-repairs for admin review
- Consider retry backoff if repair fails multiple times
- May want confidence threshold higher for auto-repair (0.9 vs 0.8)

---

## FE-003: OAuth/Social Login for Production Deployment

**Status:** Backlog

### Problem

Cookie currently uses a simple profile-based system with no authentication. For production deployment as a public service, proper user authentication is required to:
- Secure user data
- Enable multi-device access
- Prevent unauthorized access
- Meet user expectations for a modern web app

### Current Implementation

- Profiles are created locally with just a name
- No password, no email verification
- Anyone with access to the URL can create/switch profiles
- Session-based profile tracking only

### Proposed Solution

Add a "production mode" configuration that requires OAuth authentication:

1. **OAuth Providers:**
   - Google (most common, broad user base)
   - GitHub (developer-friendly)
   - Apple ID (required for iOS apps, privacy-focused)
   - LinkedIn (optional, professional network)

2. **Configuration:**
   ```python
   # settings.py or AppSettings
   AUTHENTICATION_MODE = 'local'  # or 'oauth'
   OAUTH_PROVIDERS = ['google', 'github', 'apple']
   OAUTH_REQUIRED = True  # False allows local + oauth
   ```

3. **User Model Changes:**
   - Add `User` model (or use Django's built-in)
   - Link `Profile` to `User` (one user can have multiple profiles/households)
   - Store OAuth provider + provider user ID

4. **Flow:**
   - Landing page shows "Sign in with Google/GitHub/Apple"
   - OAuth callback creates/retrieves user
   - User selects or creates profile
   - Session tied to authenticated user

### Django Libraries

| Provider | Library | Notes |
|----------|---------|-------|
| All | `django-allauth` | Most comprehensive, supports all providers |
| All | `python-social-auth` | Alternative, also well-maintained |
| Google | `google-auth` | Direct Google integration |
| Apple | Requires special handling | JWT-based, needs Apple Developer account |

**Recommended:** `django-allauth` - handles all providers with consistent API

### Implementation Phases

**Phase 1: Infrastructure**
- Install `django-allauth`
- Configure User model
- Link Profile to User (nullable for migration)
- Add OAuth provider credentials (env vars)

**Phase 2: Google + GitHub**
- Implement Google OAuth
- Implement GitHub OAuth
- Update login/profile selection flow
- Migrate existing profiles (optional user linking)

**Phase 3: Apple ID**
- Apple Developer account setup
- Implement Sign in with Apple
- Handle Apple's privacy features (hidden email)

**Phase 4: Production Hardening**
- Email verification (optional)
- Account linking (connect multiple providers)
- Account deletion (GDPR compliance)
- Rate limiting on auth endpoints

### Files to Change

- `settings.py` - allauth configuration
- `apps/profiles/models.py` - Add User FK to Profile
- `apps/profiles/views.py` - OAuth callback handling
- `apps/legacy/templates/legacy/login.html` - OAuth buttons
- `frontend/src/screens/Login.tsx` - OAuth buttons
- New migration for User-Profile relationship

### Environment Variables

```bash
# Google
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# GitHub
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=

# Apple
APPLE_CLIENT_ID=
APPLE_TEAM_ID=
APPLE_KEY_ID=
APPLE_PRIVATE_KEY=

# LinkedIn (optional)
LINKEDIN_CLIENT_ID=
LINKEDIN_CLIENT_SECRET=
```

### Deployment Considerations

- OAuth requires HTTPS (use Let's Encrypt)
- Callback URLs must be registered with each provider
- Apple requires paid developer account ($99/year)
- LinkedIn API has stricter approval process

### Migration Path

1. Deploy with `AUTHENTICATION_MODE='local'` (current behavior)
2. Configure OAuth providers
3. Switch to `AUTHENTICATION_MODE='oauth'`
4. Existing local profiles become "unclaimed"
5. Users can optionally link existing profiles to their OAuth account

### Security Notes

- Store OAuth tokens securely (encrypted at rest)
- Implement CSRF protection on OAuth flows
- Validate OAuth state parameter
- Consider refresh token rotation
- Log all authentication events

---

## FE-004: Settings Page Access Control

**Status:** Backlog (Requires Research)

### Problem

The Settings page provides access to sensitive configuration:
- API keys (OpenRouter)
- AI prompt customization
- Search source management
- User/profile deletion
- **Database reset (Danger Zone)** - complete factory reset capability

In a production multi-user environment, these settings should be restricted to administrators only, not all users. The database reset feature in particular is extremely destructive and should never be accessible to regular users.

### Current Implementation

- Settings page accessible to anyone with a profile
- No concept of admin vs regular user
- No permission checks on settings endpoints

### Desired Behavior

- Regular users: Can access General tab (theme, own profile settings)
- Admins only: AI Prompts, Sources, Source Selectors, Users tabs
- API endpoints should enforce same restrictions

### Research Required

The implementation approach depends on the authentication model chosen:

**If using FE-003 (OAuth):**
- User groups/roles via Django's built-in permission system
- Admin flag on User model
- OAuth provider admin groups (e.g., GitHub org membership)

**If staying local (profiles only):**
- Admin PIN/password for settings access
- Designated "admin profile" concept
- Environment variable whitelist of admin profile names

**Alternative approaches to evaluate:**
- Django's `@permission_required` decorator
- Custom middleware for settings routes
- Frontend-only hiding (not secure, but simple)
- Separate admin interface entirely (Django admin?)

### Possible Implementation Options

| Option | Pros | Cons |
|--------|------|------|
| Django User groups | Standard, well-documented | Requires User model (FE-003) |
| Admin profile flag | Simple, works with current model | No real security without auth |
| Settings PIN | Works without full auth | Extra friction, PIN management |
| Django admin site | Already exists, powerful | Different UI, not mobile-friendly |
| Environment whitelist | Simple config | Hardcoded, no runtime changes |

### Dependencies

- May depend on FE-003 (OAuth) for proper implementation
- Could be implemented partially without OAuth using PIN approach

### Notes

- Research should evaluate Django's permission framework
- Consider whether Django's built-in admin site is sufficient
- If implementing custom, ensure API endpoints are also protected
- Mobile/tablet UX matters - Django admin is not touch-friendly

---

## FE-005: Migrate from SQLite to MySQL/PostgreSQL

**Status:** Backlog

### Problem

SQLite has concurrency limitations that cause issues in production and testing:
- Table-level locking prevents concurrent writes
- In-memory databases have isolation issues with background threads
- CI tests fail intermittently due to "database table is locked" errors
- Background tasks (e.g., AI tip generation) conflict with request handling

### Current Implementation

- SQLite for development and production
- In-memory SQLite for CI tests (`file:memorydb_default?mode=memory&cache=shared`)
- Background threads using daemon threads for fire-and-forget tasks
- Race conditions between test teardown and background DB access

### Observed Issues

1. **CI Test Flakiness:** `test_scrape_same_url_twice_creates_two_records` fails intermittently
   - Background tip generation thread locks `core_appsettings` table
   - pytest teardown can't flush database while thread holds lock
   - Workaround: Mock threading module in affected tests

2. **Concurrent Request Handling:** Multiple simultaneous requests may conflict
   - Recipe scraping + tip generation + user requests
   - SQLite serializes all writes

### Proposed Solution

Migrate to MySQL or PostgreSQL for better concurrency:

**Option A: MySQL**
- Widely used, good Django support
- Row-level locking (InnoDB)
- Good performance for read-heavy workloads
- `mysqlclient` or `PyMySQL` driver

**Option B: PostgreSQL**
- More advanced features (JSONB, full-text search)
- Excellent concurrency (MVCC)
- Better for complex queries
- `psycopg2` or `psycopg3` driver

### Implementation Steps

1. **Docker Setup:**
   - Add MySQL/PostgreSQL service to `docker-compose.yml`
   - Configure persistent volume for data
   - Health check for container readiness

2. **Django Configuration:**
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.mysql',  # or postgresql
           'NAME': os.environ.get('DB_NAME', 'cookie'),
           'USER': os.environ.get('DB_USER', 'cookie'),
           'PASSWORD': os.environ.get('DB_PASSWORD'),
           'HOST': os.environ.get('DB_HOST', 'db'),
           'PORT': os.environ.get('DB_PORT', '3306'),
       }
   }
   ```

3. **CI Updates:**
   - Add database service to GitHub Actions workflow
   - Use real database instead of in-memory SQLite
   - Remove threading mocks from tests (no longer needed)

4. **Migration:**
   - Export existing SQLite data
   - Import to new database
   - Test all functionality

### Files to Change

- `docker-compose.yml` - Add database service
- `cookie/settings.py` - Database configuration
- `.github/workflows/ci.yml` - CI database service
- `requirements.txt` - Add database driver
- `tests/test_recipes_api.py` - Remove threading workarounds

### Benefits

- Eliminates "database table is locked" errors
- Better concurrent request handling
- Production-ready database
- Enables future scaling (connection pooling, read replicas)
- Removes need for test workarounds

### Considerations

- Local development requires running database container
- Slightly more complex setup for new developers
- Need to decide between MySQL and PostgreSQL
- Data migration from existing SQLite databases

---

## FE-006: Multi-Selection for AI Remix Suggestions

**Status:** Backlog

### Problem

When creating a recipe remix, the AI generates several variation suggestions (e.g., "Make it spicier", "Add Mediterranean flavors", "Make it vegetarian"). Currently, users can only select one suggestion at a time.

### Current Implementation

- Remix modal displays AI-generated suggestions as selectable options
- User picks a single suggestion or enters custom text
- AI generates the remixed recipe based on that one instruction

### Proposed Solution

Allow users to select multiple AI suggestions to combine into a single remix:

1. **Multi-select UI:** Change suggestion selection from radio buttons to checkboxes
2. **Combined prompt:** When multiple suggestions are selected, combine them into the remix prompt (e.g., "Make it spicier AND vegetarian")
3. **Visual feedback:** Show selected count and allow deselection
4. **Optional limit:** May want to cap at 3-4 selections to keep remixes coherent

### Benefits

- More creative remix possibilities
- Better matches user intent when they want multiple modifications
- More efficient than creating multiple sequential remixes

### Handling Conflicting Selections

Users may select suggestions that conflict (e.g., "Make it vegan" + "Add Italian salami"). Rather than complex conflict detection rules, let the AI handle it:

**Approach: AI-Driven Conflict Resolution**

1. Pass all selected suggestions to the AI
2. Include instruction: "If any suggestions conflict, create separate recipe variations"
3. AI returns either:
   - **Single recipe** - when selections are compatible
   - **Multiple recipes** - when conflicts exist (one per conflicting path)

**Example prompt addition:**
```
Apply the following modifications: [list of selections]

If any modifications conflict (e.g., vegan + meat-based), create separate
recipe variations - one for each conflicting approach. Label each variation
clearly (e.g., "Vegan Version", "Salami Version").
```

**UI Considerations:**
- Display multiple results in a carousel or tabs if AI returns variations
- Let user pick which variation to save (or save all as separate remixes)
- Show a subtle indicator when AI detected conflicts: "We created 2 versions based on your selections"

**Why this approach:**
- No hardcoded conflict rules to maintain
- AI understands nuanced conflicts (dietary, cuisine style, technique)
- Simple implementation - just prompt engineering
- Gives user more value (multiple recipes) rather than error messages

### Files to Change

- `frontend/src/components/RemixModal.tsx` - Multi-select UI, handle multiple results
- `apps/ai/services/remix.py` - Updated prompt with conflict handling instruction
- `frontend/src/types/` - May need type for multi-recipe response

### Related

- **FE-013** - Linked recipe navigation for viewing original ↔ remix relationships

---

## FE-007: Add Nginx to Production Container

**Status:** ✅ Implemented
**Priority:** High (currently production container doesn't serve frontend properly)

### Problem

The production container only runs gunicorn serving Django directly. This causes:
1. **No frontend at `/`** - Modern browsers get 404 at root URL
2. **No browser detection** - Legacy browsers (iOS < 11, IE, Edge Legacy) aren't redirected to `/legacy/`
3. **Dev/prod disparity** - Development uses nginx for routing, production doesn't

### Current Implementation

**Development (`docker-compose.yml`):**
- 3 containers: nginx, Django (web), Vite dev server (frontend)
- nginx handles all routing via `nginx/nginx.conf`:
  - `/api/`, `/legacy/`, `/admin/` → Django
  - `/` with browser detection → Vite (modern) or redirect to `/legacy/` (old browsers)
  - Static files, media, Vite HMR

**Production (`docker-compose.prod.yml` + `Dockerfile.prod`):**
- Single container running gunicorn only
- Frontend built and copied to `/app/frontend/dist`
- Static files collected to `/app/staticfiles`
- No nginx, no browser detection, no frontend routing
- `entrypoint.prod.sh` starts only gunicorn

### Proposed Solution

Add nginx to the production container, running alongside gunicorn:

1. **Install nginx in Dockerfile.prod**
2. **Create production nginx config** (`nginx/nginx.prod.conf`)
3. **Update entrypoint** to start both nginx and gunicorn
4. **Expose port 80** (nginx) instead of 8000 (gunicorn)

### Implementation Details

#### 1. Dockerfile.prod Changes

```dockerfile
# Add nginx to the production image
FROM python:3.12-slim AS production

RUN apt-get update && apt-get install -y --no-install-recommends \
    libffi8 \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Copy nginx config
COPY nginx/nginx.prod.conf /etc/nginx/nginx.conf

# Expose nginx port
EXPOSE 80
```

#### 2. Production Nginx Config (`nginx/nginx.prod.conf`)

```nginx
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    upstream django {
        server 127.0.0.1:8000;  # Local gunicorn
    }

    server {
        listen 80;
        server_name _;

        # API requests -> Django
        location /api/ {
            proxy_pass http://django;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Legacy frontend -> Django
        location /legacy/ {
            proxy_pass http://django;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            add_header Cache-Control "no-cache, no-store, must-revalidate";
        }

        # Static files (Django collected)
        location /static/ {
            alias /app/staticfiles/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # Media files
        location /media/ {
            alias /app/data/media/;
        }

        # Modern frontend with legacy browser detection
        location / {
            # Same browser detection as dev nginx.conf
            set $legacy_browser 0;

            if ($http_user_agent ~* "(?:iPhone|iPad|iPod).*OS [1-9]_") {
                set $legacy_browser 1;
            }
            if ($http_user_agent ~* "(?:iPhone|iPad|iPod).*OS 10_") {
                set $legacy_browser 1;
            }
            if ($http_user_agent ~* "MSIE |Trident/") {
                set $legacy_browser 1;
            }
            if ($http_user_agent ~* "Edge/[0-9]") {
                set $legacy_browser 1;
            }

            if ($legacy_browser = 1) {
                return 302 /legacy/;
            }

            # Serve built frontend
            root /app/frontend/dist;
            try_files $uri $uri/ /index.html;
        }
    }
}
```

#### 3. Entrypoint Changes (`entrypoint.prod.sh`)

```bash
# Start gunicorn in background
echo "Starting Gunicorn on 127.0.0.1:8000..."
gunicorn \
    --bind 127.0.0.1:8000 \
    --workers ${GUNICORN_WORKERS:-2} \
    --threads ${GUNICORN_THREADS:-4} \
    --worker-class gthread \
    --worker-tmp-dir /dev/shm \
    --access-logfile - \
    --error-logfile - \
    cookie.wsgi:application &

# Start nginx in foreground
echo "Starting Nginx on 0.0.0.0:80..."
exec nginx -g 'daemon off;'
```

#### 4. docker-compose.prod.yml Changes

```yaml
services:
  web:
    image: mndeaves/cookie:latest
    container_name: cookie-prod
    ports:
      - "80:80"  # Changed from 8000
    # ... rest unchanged
```

### Files to Change

| File | Change |
|------|--------|
| `Dockerfile.prod` | Install nginx, copy config, expose port 80 |
| `nginx/nginx.prod.conf` | New file - production nginx config |
| `entrypoint.prod.sh` | Start both gunicorn and nginx |
| `docker-compose.prod.yml` | Map port 80:80 instead of 80:8000, update healthcheck |

### Benefits

- **Dev/prod parity** - Same nginx routing logic in both environments
- **Single source of truth** - Browser detection rules in nginx configs only
- **Efficient static serving** - nginx serves frontend assets directly
- **Proper SPA routing** - `try_files` handles client-side routes
- **Single container** - No orchestration complexity

### Considerations

- **Two processes in one container** - nginx (foreground) + gunicorn (background)
  - Alternative: Use supervisord or s6-overlay for proper process management
  - Simple approach: nginx foreground, gunicorn background works for this use case
- **Container size** - nginx adds ~10MB to image
- **Healthcheck update** - Should check nginx (port 80) not gunicorn (port 8000)
- **Config duplication** - Some overlap between `nginx.conf` and `nginx.prod.conf`
  - Could use templating or shared includes to reduce duplication

### Alternative Approaches Considered

| Approach | Pros | Cons |
|----------|------|------|
| Django middleware for browser detection | No nginx needed | Slower, Django handles all requests |
| Separate nginx container in prod | Clean separation | Requires docker-compose in prod |
| Whitenoise for everything | Simple | No browser detection, less efficient |
| **Nginx in same container** | Dev/prod parity, efficient | Two processes |

### Testing Checklist

- [ ] Modern browser (Firefox, Chrome) → serves React frontend at `/`
- [ ] Legacy browser (iOS 9 iPad) → redirects to `/legacy/`
- [ ] API calls (`/api/*`) → proxied to Django
- [ ] Static files → served with cache headers
- [ ] SPA client-side routing → works (e.g., `/recipe/123`)
- [ ] Healthcheck passes
- [ ] Container starts cleanly with both processes

---

## FE-008: Docker Hub - Only Maintain Latest Image

**Status:** ✅ Implemented
**Priority:** Low (storage optimization)

### Problem

The current CD workflow (`.github/workflows/cd.yml`) creates multiple Docker image tags on each release:
- `latest`
- `1.2.3` (full semver)
- `1.2` (major.minor)
- `1` (major only)

Over time, Docker Hub accumulates many image versions. For a self-hosted personal app, only `latest` is needed on Docker Hub. Version history is preserved in git tags.

### Clarification: Git Tags vs Docker Hub Tags

| Location | What's Stored | Keep History? |
|----------|---------------|---------------|
| **Git repo** | Code versions (v1.0.0, v1.1.0, etc.) | ✅ Yes - full tag history |
| **Docker Hub** | Built container images | ❌ No - only `latest` needed |

Users who need a specific version can:
1. Check out the git tag
2. Build locally with `bin/prod build`

### Current Implementation

```yaml
# cd.yml - Extract metadata step
tags: |
  type=semver,pattern={{version}}
  type=semver,pattern={{major}}.{{minor}}
  type=semver,pattern={{major}},enable=${{ !startsWith(github.ref, 'refs/tags/v0.') }}
  type=raw,value=latest,enable=${{ !contains(github.ref, '-') }}
```

### Proposed Solution

#### Step 1: Only Push `latest` Tag

Simplify the metadata step:

```yaml
- name: Extract metadata
  id: meta
  uses: docker/metadata-action@v5
  with:
    images: ${{ env.IMAGE_NAME }}
    tags: |
      type=raw,value=latest
```

#### Step 2: One-Time Cleanup of Existing Tags

Delete old versioned tags from Docker Hub (one-time manual task):

**Option A: Docker Hub UI**
- Go to https://hub.docker.com/repository/docker/mndeaves/cookie/tags
- Delete all tags except `latest`

**Option B: Docker Hub API**
```bash
# Get auth token
TOKEN=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"username": "USERNAME", "password": "TOKEN"}' \
  https://hub.docker.com/v2/users/login/ | jq -r .token)

# List and delete old tags
curl -s -H "Authorization: JWT $TOKEN" \
  "https://hub.docker.com/v2/repositories/mndeaves/cookie/tags?page_size=100" \
  | jq -r '.results[].name | select(. != "latest")' \
  | xargs -I {} curl -X DELETE \
    -H "Authorization: JWT $TOKEN" \
    "https://hub.docker.com/v2/repositories/mndeaves/cookie/tags/{}/"
```

### Implementation Steps

1. Update `.github/workflows/cd.yml` - change tags to only `latest`
2. Manually delete old tags from Docker Hub (one-time)

### Files to Change

- `.github/workflows/cd.yml` - Simplify tag metadata

### Benefits

- Single image to maintain on Docker Hub
- No confusion about versions - always use `latest`
- Git tags preserve full version history for code
- Users can build any version locally from git tags

---

## FE-009: AI-Powered Meal Pairing Suggestions

**Status:** Backlog

### Problem

When viewing a recipe, users often want to plan a complete meal around it. Finding complementary dishes that pair well together requires culinary knowledge and additional searching. Currently, users must manually search for starters, sides, or desserts that would work with their chosen recipe.

### Proposed Solution

Add an AI-powered "Complete Your Meal" feature that suggests complementary courses based on the recipe being viewed:

1. **AI Analysis:** When viewing a recipe, AI understands the dish type, cuisine, flavours, and meal context
2. **Course Suggestions:** Generate suggestions for missing courses to create a 3-4 course meal
3. **Discovery-Style Links:** Each suggestion is a search link (reusing existing Discover infrastructure)
4. **Smart Context:** Suggestions adapt based on what the current recipe is:
   - Viewing a **beef wellington** → suggest a starter and dessert
   - Viewing an **ice cream** → suggest a starter and main course
   - Viewing a **soup** → suggest a main and dessert

### User Experience

1. User views a recipe (e.g., "Beef Wellington")
2. A "Complete Your Meal" section appears with AI-generated suggestions:
   - **Starter:** "French Onion Soup" → links to search
   - **Dessert:** "Chocolate Fondant" → links to search
3. Tapping a suggestion opens search results (same as Discover items)
4. User can browse results and save recipes to build their complete meal

### Implementation Details

**Reuse Existing Infrastructure:**
- Same search link format as Discover suggestions
- Same UI pattern for displaying clickable search suggestions
- Same backend search flow when user taps a suggestion

**AI Prompt Design:**
```
Given this recipe: [recipe title, ingredients, cuisine]
Suggest complementary dishes for a complete meal.
Consider: cuisine pairing, flavour balance, dietary consistency.
Return: course type + search terms (e.g., "Starter: French onion soup")
```

**Course Logic:**
- Detect current recipe's likely course (starter, main, dessert, side)
- Suggest the missing courses for a balanced meal
- Prioritise cuisine-appropriate pairings

### Files to Change

- `apps/ai/services/` - New meal pairing service
- `apps/recipes/views.py` or API endpoint - Serve suggestions
- `frontend/src/screens/Recipe.tsx` - Display suggestions section
- Reuse `frontend/src/components/Discover*` components for suggestion UI

### Benefits

- Helps users plan complete meals, not just individual dishes
- Leverages AI for culinary knowledge (what pairs with what)
- Reuses existing Discover/search infrastructure
- Encourages exploration of more recipes
- Natural extension of the AI features already in the app

### Considerations

- Cache suggestions per recipe to avoid repeated AI calls
- Consider showing suggestions only after recipe is saved (engagement signal)
- May want to limit to 2-3 suggestions to avoid overwhelming the UI
- Ensure suggestions respect any dietary preferences if implemented

---

## FE-010: Investigate GitHub Native ARM64 Runners

**Status:** Backlog

### Problem

The CD workflow builds multi-platform Docker images (linux/amd64 + linux/arm64) using QEMU emulation on x86 GitHub runners. This is extremely slow - ARM64 builds can take 30-60+ minutes due to CPU instruction emulation, particularly during npm and pip install steps.

### Current Implementation

- `cd.yml` uses `docker/build-push-action@v5` with `platforms: linux/amd64,linux/arm64`
- QEMU emulates ARM64 instructions on amd64 runners
- Single job builds both platforms sequentially
- Total build time: 30-60+ minutes

### Proposed Investigation

GitHub now offers native ARM64 runners. Investigate:

1. **Availability:** `ubuntu-24.04-arm64` runner availability
2. **Pricing:** Cost difference vs standard x86 runners
3. **Build matrix:** Run amd64 and arm64 builds in parallel on native runners
4. **Merge manifests:** Combine platform-specific images into multi-arch manifest

### Potential Implementation

```yaml
jobs:
  build:
    strategy:
      matrix:
        include:
          - platform: linux/amd64
            runner: ubuntu-latest
          - platform: linux/arm64
            runner: ubuntu-24.04-arm64
    runs-on: ${{ matrix.runner }}
    steps:
      - name: Build and push (single platform)
        uses: docker/build-push-action@v5
        with:
          platforms: ${{ matrix.platform }}
          # ...

  merge:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Create multi-arch manifest
        # Merge platform images into single manifest
```

### Benefits

- **Much faster builds:** Native ARM64 vs QEMU emulation (minutes vs hour+)
- **Parallel execution:** Both platforms build simultaneously
- **More reliable:** No emulation quirks or timeouts

### Considerations

- **Cost:** ARM64 runners may have different pricing tier
- **Availability:** Check if ARM64 runners are available for public repos / free tier
- **Complexity:** Build matrix + manifest merge is more complex than single job
- **Cache strategy:** May need separate caches per platform

### Research Links

- https://github.blog/changelog/2024-06-03-actions-arm-based-linux-and-windows-runners-are-now-in-public-preview/
- https://docs.github.com/en/actions/using-github-hosted-runners/about-larger-runners

---

## FE-011: Modern Frontend Nutrition Labels Show Raw camelCase Keys

**Status:** Complete

### Problem

On the recipe view page nutrition tab, the modern React frontend displays raw camelCase keys from the API instead of human-readable labels:

- `carbohydrateContent` instead of "Carbohydrate"
- `cholesterolContent` instead of "Cholesterol"
- `saturatedFatContent` instead of "Saturated Fat"

The legacy frontend displays these correctly using a Django template filter.

### Current Implementation

**Modern Frontend** (`frontend/src/screens/RecipeDetail.tsx`, lines 598-630):

```typescript
{nutritionEntries.map(([key, value]) => (
  <div key={key} className="rounded-lg bg-muted/50 p-3">
    <span className="block text-sm capitalize text-muted-foreground">
      {key.replace(/_/g, ' ')}  {/* Only handles snake_case! */}
    </span>
    <span className="text-lg font-medium text-foreground">{value}</span>
  </div>
))}
```

**Legacy Frontend** (`apps/legacy/templatetags/legacy_tags.py`, lines 32-53):

```python
@register.filter
def format_nutrition_key(key):
    # Remove common suffixes
    key = re.sub(r'Content$', '', key)

    # Handle snake_case
    if '_' in key:
        return key.replace('_', ' ').title()

    # Handle CamelCase (insert space before capitals)
    spaced = re.sub(r'([a-z])([A-Z])', r'\1 \2', key)
    return spaced.capitalize() if spaced else ''
```

### Root Cause

The `recipe-scrapers` library returns nutrition data in schema.org format with camelCase keys (e.g., `carbohydrateContent`, `proteinContent`). The legacy frontend has proper formatting logic, but the modern frontend only does `key.replace(/_/g, ' ')` which doesn't handle camelCase.

### Proposed Fix

Add a `formatNutritionKey` utility function to the modern frontend:

```typescript
// frontend/src/utils/formatters.ts
export function formatNutritionKey(key: string): string {
  if (!key) return '';

  // Remove "Content" suffix
  let formatted = key.replace(/Content$/, '');

  // Handle snake_case
  if (formatted.includes('_')) {
    return formatted.split('_').map(w =>
      w.charAt(0).toUpperCase() + w.slice(1)
    ).join(' ');
  }

  // Handle camelCase - insert space before capitals
  formatted = formatted.replace(/([a-z])([A-Z])/g, '$1 $2');

  // Capitalize first letter
  return formatted.charAt(0).toUpperCase() + formatted.slice(1);
}
```

Then update `RecipeDetail.tsx`:

```typescript
import { formatNutritionKey } from '@/utils/formatters';

// In NutritionTab:
<span className="block text-sm text-muted-foreground">
  {formatNutritionKey(key)}
</span>
```

### Files to Modify

1. Create or update: `frontend/src/utils/formatters.ts`
2. Update: `frontend/src/screens/RecipeDetail.tsx` (NutritionTab component)

### Comparison

| Input | Modern (Current) | Legacy | Modern (Fixed) |
|-------|------------------|--------|----------------|
| `carbohydrateContent` | carbohydrateContent | Carbohydrate | Carbohydrate |
| `cholesterolContent` | cholesterolContent | Cholesterol | Cholesterol |
| `saturatedFatContent` | saturatedFatContent | Saturated Fat | Saturated Fat |
| `calories` | calories | Calories | Calories |
| `saturated_fat` | saturated fat | Saturated Fat | Saturated Fat |

---

## FE-012: Historical Code Quality Metrics with Trend Graphs

**Status:** Complete

### Problem

The current GitHub Pages metrics dashboard only shows the latest snapshot. Each CI run overwrites previous data (`keep_files: false`), so there's no way to visualize code quality trends over time (e.g., coverage improving, complexity decreasing).

The gh-pages branch has commit history, but each commit contains only that run's data - no accumulated historical records.

### Current Behavior

```yaml
# .github/workflows/coverage.yml
- name: Deploy to GitHub Pages
  uses: peaceiris/actions-gh-pages@v4
  with:
    keep_files: false  # Wipes all previous content
```

- `metrics.json` contains only current values with `generated_at` timestamp
- No historical data preserved
- Cannot graph progress over time

### Proposed Solution

#### 1. Preserve Historical Data

Change deployment to keep existing files:

```yaml
- name: Deploy to GitHub Pages
  uses: peaceiris/actions-gh-pages@v4
  with:
    keep_files: true  # Preserve history directory
```

#### 2. Store Timestamped Metrics

Add step to append metrics to history:

```bash
# Create history directory if not exists
mkdir -p site/coverage/history

# Save timestamped snapshot
DATE=$(date +%Y-%m-%d)
cp site/coverage/api/metrics.json "site/coverage/history/${DATE}.json"

# Append to consolidated history file
python3 << 'EOF'
import json
import os
from datetime import datetime

history_file = 'site/coverage/history/all.json'
current_file = 'site/coverage/api/metrics.json'

# Load existing history or start fresh
if os.path.exists(history_file):
    with open(history_file) as f:
        history = json.load(f)
else:
    history = {'entries': []}

# Load current metrics
with open(current_file) as f:
    current = json.load(f)

# Add entry with date key
date = datetime.now().strftime('%Y-%m-%d')
entry = {
    'date': date,
    'frontend_coverage': current['coverage']['frontend']['percentage'],
    'backend_coverage': current['coverage']['backend']['percentage'],
    'frontend_complexity': current['complexity']['frontend']['complexity_warnings'],
    'backend_complexity': current['complexity']['backend']['cyclomatic_complexity'],
    'bundle_size_kb': current['bundle']['size_kb'],
    'frontend_duplication': current['duplication']['frontend']['percentage'],
    'backend_duplication': current['duplication']['backend']['percentage'],
}

# Avoid duplicates for same date (keep latest)
history['entries'] = [e for e in history['entries'] if e['date'] != date]
history['entries'].append(entry)

# Sort by date
history['entries'].sort(key=lambda x: x['date'])

# Keep last 90 days
history['entries'] = history['entries'][-90:]

with open(history_file, 'w') as f:
    json.dump(history, f, indent=2)
EOF
```

#### 3. Add Trend Charts to Dashboard

Add Chart.js or similar to visualize trends:

```html
<canvas id="coverageChart"></canvas>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
fetch('history/all.json')
  .then(r => r.json())
  .then(data => {
    new Chart(document.getElementById('coverageChart'), {
      type: 'line',
      data: {
        labels: data.entries.map(e => e.date),
        datasets: [{
          label: 'Frontend Coverage %',
          data: data.entries.map(e => e.frontend_coverage),
          borderColor: '#3b82f6'
        }, {
          label: 'Backend Coverage %',
          data: data.entries.map(e => e.backend_coverage),
          borderColor: '#10b981'
        }]
      }
    });
  });
</script>
```

### Files to Modify

1. `.github/workflows/coverage.yml` - Add history preservation logic
2. Dashboard HTML generation - Add chart section

### Data Structure

**history/all.json:**
```json
{
  "entries": [
    {
      "date": "2026-01-10",
      "frontend_coverage": 78.5,
      "backend_coverage": 85.2,
      "frontend_complexity": 0,
      "backend_complexity": 2.1,
      "bundle_size_kb": 245,
      "frontend_duplication": 1.2,
      "backend_duplication": 0.8
    },
    {
      "date": "2026-01-11",
      "frontend_coverage": 79.1,
      "backend_coverage": 85.2,
      ...
    }
  ]
}
```

### Benefits

- Visualize coverage trends over time
- Track complexity reduction efforts
- Monitor bundle size growth
- Celebrate progress milestones
- Identify regressions quickly

### Considerations

- Keep last 90 days to limit file size
- One entry per day (latest wins if multiple runs)
- Chart.js adds ~60KB but loads from CDN
- Need to handle first run (no existing history)

### Additional Metrics to Track

Beyond the core quality metrics, the following could provide valuable trend data:

#### Already Available in CI (just needs extraction)

| Metric | Source | Trend Value |
|--------|--------|-------------|
| **Lines of Code** | radon raw metrics (`complexity/raw.json`) | Track codebase growth |
| **JS Bundle Size** | bundle summary (`js_size_kb`) | Monitor JS-specific bloat |
| **CSS Bundle Size** | bundle summary (`css_size_kb`) | Monitor styling overhead |
| **Clone Count** | duplication summary (`clones_count`) | Track copy-paste instances |
| **Files Analyzed** | complexity summary | Track codebase file count |
| **Functions Analyzed** | complexity summary | Track function proliferation |
| **Legacy Errors** | legacy lint summary | Track legacy code health |

#### New Metrics (require CI changes)

| Metric | Implementation | Trend Value |
|--------|----------------|-------------|
| **Test Count (Backend)** | Parse pytest output: `294 tests` currently | Track test suite growth |
| **Test Count (Frontend)** | Parse vitest output: `81 tests` currently | Track frontend test coverage |
| **Dependency Count (npm)** | Count `package.json` deps: `10 prod + 17 dev` | Monitor dependency bloat |
| **Dependency Count (pip)** | Count `requirements.txt` lines: `15` | Monitor Python dependencies |
| **API Endpoint Count** | Grep `@router.` decorators: `39` currently | Track API surface growth |
| **Component Count** | Count `.tsx` in `components/`: `6` currently | Track UI component count |
| **Build Time** | CI job duration from GitHub API | Monitor CI performance |
| **Test Execution Time** | pytest/vitest timing output | Track test suite speed |
| **TypeScript Errors** | Parse `tsc --noEmit` output | Track type safety |

#### Suggested Chart Groupings

**Quality Trends (primary):**
- Coverage (frontend + backend) - line chart
- Complexity (frontend + backend) - line chart
- Duplication (frontend + backend) - line chart

**Size Trends:**
- Bundle size (JS + CSS stacked) - area chart
- Lines of code (frontend + backend) - area chart
- Dependency count (npm + pip) - bar chart

**Health Indicators:**
- Security vulnerabilities - line chart (should stay at 0)
- Test count growth - line chart (should increase)
- API endpoint count - step chart

#### Updated History Entry Structure

```json
{
  "date": "2026-01-11",
  "coverage": {
    "frontend": 78.5,
    "backend": 85.2
  },
  "complexity": {
    "frontend_warnings": 0,
    "backend_cc": 2.1,
    "backend_mi": 85.4
  },
  "duplication": {
    "frontend": 1.2,
    "backend": 0.8,
    "frontend_clones": 3,
    "backend_clones": 2
  },
  "bundle": {
    "total_kb": 245,
    "js_kb": 210,
    "css_kb": 35
  },
  "codebase": {
    "frontend_loc": 7273,
    "backend_files": 50,
    "backend_functions": 156
  },
  "tests": {
    "frontend_count": 81,
    "backend_count": 294
  },
  "dependencies": {
    "npm_prod": 10,
    "npm_dev": 17,
    "pip": 15
  },
  "security": {
    "frontend_vulns": 0,
    "backend_vulns": 0
  },
  "legacy": {
    "errors": 0,
    "warnings": 5,
    "duplication": 2.1
  }
}
```

---

## FE-013: Linked Recipe Navigation (Original ↔ Remix Toggle)

**Status:** Backlog

### Problem

When a recipe is remixed (especially with FE-006's multi-selection creating multiple variations), there's no way to see the relationship between recipes or quickly switch between the original and its remixes.

Users may want to:
- Compare the original recipe with a remix
- See all variations created from one base recipe
- Navigate back to the original after viewing a remix
- Understand which recipe was the "parent"

### Current Implementation

- Recipes have a `remixed_from` field linking to the parent recipe
- No UI exposes this relationship
- No way to discover remixes of a recipe you're viewing

### Proposed Solution

Add a linked recipe indicator and quick-toggle on the recipe view screen:

#### 1. Visual Indicator

When viewing a recipe that has linked recipes (parent or children), show a subtle indicator:

```
┌─────────────────────────────────────┐
│  Beef Wellington                    │
│  ⟳ 2 linked recipes                 │  ← Clickable indicator
│                                     │
│  [Ingredients] [Steps] [Nutrition]  │
└─────────────────────────────────────┘
```

#### 2. Quick Toggle UI

Tapping the indicator reveals a compact switcher:

```
┌─────────────────────────────────────┐
│  Linked Recipes                     │
│                                     │
│  ○ Beef Wellington (Original)       │
│  ● Beef Wellington - Vegan Version  │  ← Currently viewing
│  ○ Beef Wellington - Spicy Version  │
│                                     │
│  [Close]                            │
└─────────────────────────────────────┘
```

#### 3. Data Model

The existing `remixed_from` foreign key is sufficient:

```python
# Already exists in Recipe model
remixed_from = models.ForeignKey('self', null=True, on_delete=models.SET_NULL)
```

To get linked recipes:
- **Parent:** `recipe.remixed_from`
- **Children:** `Recipe.objects.filter(remixed_from=recipe)`
- **Siblings:** `Recipe.objects.filter(remixed_from=recipe.remixed_from)`

#### 4. API Addition

New endpoint or extend existing recipe detail:

```python
# Option A: Extend recipe detail response
{
  "id": 123,
  "title": "Beef Wellington - Vegan Version",
  "remixed_from": 100,
  "linked_recipes": [
    {"id": 100, "title": "Beef Wellington", "relationship": "original"},
    {"id": 124, "title": "Beef Wellington - Spicy Version", "relationship": "sibling"}
  ],
  ...
}

# Option B: Separate endpoint
GET /api/recipes/123/linked/
```

### UI Placement Options

| Option | Pros | Cons |
|--------|------|------|
| **Header badge** | Always visible, non-intrusive | Takes header space |
| **Tab addition** | Consistent with other tabs | Hidden until clicked |
| **Floating pill** | Prominent, easy to tap | May obscure content |
| **Info section** | Groups with other metadata | Below the fold |

**Recommendation:** Header badge (subtle) that expands to overlay/modal on tap.

### Files to Change

- `apps/recipes/models.py` - Add helper methods for linked recipe queries
- `apps/recipes/views.py` - Include linked recipes in detail response
- `frontend/src/screens/RecipeDetail.tsx` - Add indicator and toggle UI
- `frontend/src/components/LinkedRecipeSwitcher.tsx` - New component for the toggle

### Benefits

- Discover recipe variations easily
- Compare original vs remix without searching
- Navigate recipe "family tree"
- Better UX when FE-006 creates multiple conflict variations

### Considerations

- Keep indicator subtle - many recipes won't have links
- Preload linked recipe titles to avoid loading delay on toggle
- Consider showing relationship type (original, remix, sibling)
- Mobile-friendly tap targets for the switcher

### Related

- **FE-006** - Multi-selection remix (may create multiple linked recipes from conflicts)

---

## FE-014: Legacy Frontend Discover Suggestions Grid Layout

**Status:** Backlog

### Problem

On the Legacy frontend, the Discover suggestions render as a single column with each item at full width on iPad. This is because the current CSS uses CSS Grid which is **not supported on iOS 9 Safari**.

### Root Cause

**File:** `apps/legacy/static/legacy/css/components.css` (Lines 340-357)

The current implementation uses CSS Grid:

```css
/* Current code - BROKEN on iOS 9 */
.discover-grid {
    display: grid;                        /* Not supported iOS 9 */
    grid-template-columns: 1fr;           /* Not supported iOS 9 */
    gap: 1rem;                            /* Not supported iOS 9 */
}

@media (min-width: 640px) {
    .discover-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (min-width: 1024px) {
    .discover-grid {
        grid-template-columns: repeat(3, 1fr);
    }
}
```

**iOS 9 Safari CSS Grid Support:** None. CSS Grid was introduced in iOS 10.3 with partial support, full support in iOS 12+.

On iOS 9, `display: grid` is ignored and the container falls back to `display: block`, causing all cards to stack vertically at full width.

### Current Code Structure

**Template:** `apps/legacy/templates/legacy/home.html` (Line 149)
```html
<div id="discover-suggestions" class="discover-grid">
    <!-- Cards rendered by JS -->
</div>
```

**JavaScript:** `apps/legacy/static/legacy/js/pages/home.js`
- `renderSuggestions()` (Lines 202-213) - Renders cards into `#discover-suggestions`
- `createSuggestionCard()` (Lines 218-252) - Creates `<button class="discover-card">` elements

**Card CSS:** The individual `.discover-card` elements already use flexbox with `-webkit-` prefixes (Lines 360-432), so they render correctly. Only the grid container is broken.

### Proposed Fix

Replace CSS Grid with flexbox for the `.discover-grid` container:

```css
/* iOS 9 compatible flexbox layout */
.discover-grid {
    display: -webkit-flex;
    display: flex;
    -webkit-flex-wrap: wrap;
    flex-wrap: wrap;
    margin: -0.5rem;  /* Negative margin to offset card margins */
}

.discover-card {
    /* Add to existing .discover-card styles */
    width: 100%;
    margin: 0.5rem;
    box-sizing: border-box;
}

/* Tablet - 2 columns */
@media (min-width: 640px) {
    .discover-card {
        width: calc(50% - 1rem);
    }
}

/* Desktop - 3 columns */
@media (min-width: 1024px) {
    .discover-card {
        width: calc(33.333% - 1rem);
    }
}
```

### Implementation Notes

1. **No template changes needed** - HTML structure stays the same
2. **Only CSS changes** - Replace grid with flexbox in `components.css`
3. **Follows existing patterns** - The `.recipe-grid` class in `layout.css:256-267` already uses this flexbox approach
4. **Preserve gap equivalent** - Use margin on cards + negative margin on container (same as recipe grid)

### Files to Change

| File | Lines | Change |
|------|-------|--------|
| `apps/legacy/static/legacy/css/components.css` | 340-357 | Replace CSS Grid with flexbox |
| `apps/legacy/static/legacy/css/components.css` | 360-373 | Add width/margin to `.discover-card` |

### Testing

- [ ] iOS 9 iPad - Verify 2-column layout on tablet width
- [ ] iOS 9 iPhone - Verify single column on mobile
- [ ] Modern browsers - Verify layout still works (flexbox is universal)
- [ ] Card spacing consistent with recipe grid

### Benefits

- Discover suggestions display in responsive grid on iOS 9 iPads
- Consistent with existing `.recipe-grid` flexbox pattern
- No JavaScript changes required
- Backwards compatible with all browsers

### Priority

Low - Cosmetic/UX improvement, functionality works correctly

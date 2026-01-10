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

### Files to Change

- `frontend/src/components/RemixModal.tsx` - Multi-select UI
- `apps/ai/services/remix.py` - Handle combined suggestions in prompt

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

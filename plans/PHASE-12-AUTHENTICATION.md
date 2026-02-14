# Phase 12: FE-003 Dual-Mode Authentication System

> **Status:** [OPEN]
> **Depends on:** Phase 10 (CI/CD) [DONE]

---

## Session Scope

| Session | Status | Implementation Phases | Tasks | Verify |
|---------|--------|----------------------|-------|--------|
| A | [DONE] | 1 (Database) | 1.1-1.4, model tests | `makemigrations` + `migrate` succeeds, `pytest tests/test_auth.py::TestModels` |
| B | [DONE] | 2 (Backend Auth Logic) | 2.1-2.4, auth API tests | `pytest tests/test_auth.py::TestAuthAPI` |
| C | [DONE] | 3 (Login/Register Views) | 3.1-3.4, view tests | `pytest tests/test_auth.py::TestViews` |
| D | [DONE] | 4 (Legacy Templates) | 4.1-4.2, template tests | `pytest tests/test_auth.py::TestTemplates` + Manual: iOS 9 Safari login/register forms work |
| E | [DONE] | 5 (React Frontend) | 5.1-5.7, component tests | `npm test -- Login.test.tsx Register.test.tsx AuthContext.test.tsx` + Manual: Chrome/Safari auth flow |
| F | [DONE] | 6 (Settings UI) | 6.1-6.2 | `pytest tests/test_auth.py::TestSettingsAPI` + Manual: toggle deployment mode, verify env var override display |
| G | [DONE] | 7 (CSRF) | 7.1-7.5, CSRF tests | `pytest tests/test_csrf.py` + manual AJAX POST test (both frontends) |
| H | [DONE] | 8 (Admin Authorization) | 8.1-8.6, admin tests | `pytest tests/test_auth.py::TestAdminAuthorization` + Manual: non-admin blocked from Settings |

**Coverage target:** Maintain or improve existing test coverage (currently ~85% backend, ~80% frontend). New auth code should have ≥90% coverage.

---

## Goal
Add authentication that works for two deployment scenarios:
1. **Home Server** (default): Current behavior - simple profile selection, anyone can create profiles, no passwords
2. **Public Hosting**: Username + password only (no email collection)

Both modes must work on iOS 9 Safari (no OAuth, ES5 JavaScript only).

---

## Design Decisions

### Home Mode (unchanged from current)
- Profile selector shows all profiles
- Anyone can create a new profile (just enter name, pick color)
- No passwords, no authentication barrier
- Perfect for family use on home network

### Public Mode
- Username + password registration
- **Usernames must be unique** (enforced by Django User model)
- **No email field** - we do not collect or store emails
- Simple login form
- Admin can disable new registrations
- **Admin-only access to Settings page** (see Admin Authorization section)

### How to Configure Deployment Mode

**Two-tier configuration** (environment variable overrides database):

1. **Environment Variable** (recommended for production):
   ```bash
   COOKIE_DEPLOYMENT_MODE=public  # or "home" (default)
   ```
   - Set in docker-compose.yml or .env file
   - Cannot be changed via UI when set
   - Best for fixed deployments

2. **Database Setting** (via Settings UI):
   - Only used if environment variable is NOT set
   - Can be changed at runtime via Settings page
   - Good for testing/experimentation

**Priority:** `ENV_VAR` > `database` > `default (home)`

**Example docker-compose.prod.yml for public hosting:**
```yaml
services:
  web:
    environment:
      - COOKIE_DEPLOYMENT_MODE=public
      - COOKIE_ALLOW_REGISTRATION=true
      - COOKIE_INSTANCE_NAME=My Recipe Site
      - COOKIE_ADMIN_USERNAME=admin  # Required for public mode
```

### Admin Authorization (Public Mode Only)

In public mode, the Settings page contains sensitive operations that must be restricted:
- OpenRouter API key management
- AI prompt configuration
- User profile deletion (any user)
- Database reset

**Admin designation via environment variable:**
```bash
COOKIE_ADMIN_USERNAME=admin  # Username that gets admin privileges
```

**Access control rules:**

| Feature | Home Mode | Public Mode (Admin) | Public Mode (User) |
|---------|-----------|---------------------|-------------------|
| Settings page access | ✅ All | ✅ Yes | ❌ 403 Forbidden |
| View own profile | ✅ All | ✅ Yes | ✅ Yes |
| Edit own profile | ✅ All | ✅ Yes | ✅ Yes |
| Delete own profile | ✅ All | ✅ Yes | ✅ Yes |
| View other profiles | ✅ All | ✅ Yes | ❌ No |
| Delete other profiles | ✅ All | ✅ Yes | ❌ No |
| API key management | ✅ All | ✅ Yes | ❌ No |
| Reset database | ✅ All | ✅ Yes | ❌ No |
| Change deployment mode | ✅ All | ✅ Yes | ❌ No |

**Why env var instead of database flag?**
- Prevents privilege escalation through database manipulation
- Admin is set at deployment time, not runtime
- Clear separation: infrastructure config (env) vs user data (db)
- If admin forgets credentials, redeploy with new COOKIE_ADMIN_USERNAME

### User Model Approach
- Use Django's built-in `django.contrib.auth.User` model
- Link Profile to User via OneToOne (nullable for home mode)
- Home mode: Profiles exist without User accounts (current behavior)
- Public mode: Each User has exactly one Profile (created on registration)
- Username is the only identifier (no email stored)

---

## Implementation Phase 1: Database Changes

### 1.1 Add Django Auth to Settings
**File:** `cookie/settings.py`

```python
INSTALLED_APPS = [
    "django.contrib.auth",           # ADD
    "django.contrib.contenttypes",   # ADD (required by auth)
    # ... existing apps
]

MIDDLEWARE = [
    # ... existing middleware
    "django.contrib.auth.middleware.AuthenticationMiddleware",  # ADD after sessions
]
```

### 1.2 Extend Profile Model
**File:** `apps/profiles/models.py`

Add field:
```python
user = models.OneToOneField(
    'auth.User', on_delete=models.CASCADE,
    null=True, blank=True, related_name='profile'
)
```

### 1.3 Extend AppSettings Model
**File:** `apps/core/models.py`

Add fields:
```python
deployment_mode = models.CharField(
    max_length=10, choices=[('home', 'Home Server'), ('public', 'Public Hosting')],
    default='home'
)
allow_registration = models.BooleanField(default=True)
instance_name = models.CharField(max_length=100, default='Cookie')

def get_deployment_mode(self):
    """Get deployment mode - env var takes precedence over database."""
    import os
    env_mode = os.environ.get('COOKIE_DEPLOYMENT_MODE', '').lower()
    if env_mode in ('home', 'public'):
        return env_mode
    return self.deployment_mode

def get_allow_registration(self):
    """Get registration setting - env var takes precedence."""
    import os
    env_val = os.environ.get('COOKIE_ALLOW_REGISTRATION', '').lower()
    if env_val in ('true', 'false'):
        return env_val == 'true'
    return self.allow_registration

def get_instance_name(self):
    """Get instance name - env var takes precedence."""
    import os
    return os.environ.get('COOKIE_INSTANCE_NAME', '') or self.instance_name
```

### 1.4 Create Migrations
```bash
docker compose exec web python manage.py makemigrations profiles core
docker compose exec web python manage.py migrate
```

### 1.5 Add Model Tests
**File:** `tests/test_auth.py`

```python
class TestModels:
    """Tests for Session A - Database Changes"""

    def test_profile_user_field_nullable(self):
        """Profile can exist without User (home mode)"""

    def test_profile_links_to_user(self):
        """Profile can link to User (public mode)"""

    def test_appsettings_deployment_mode_default(self):
        """Deployment mode defaults to 'home'"""

    def test_appsettings_get_deployment_mode_env_override(self, monkeypatch):
        """Environment variable overrides database setting"""

    def test_appsettings_get_allow_registration_env_override(self, monkeypatch):
        """COOKIE_ALLOW_REGISTRATION env var overrides database"""

    def test_appsettings_get_instance_name_env_override(self, monkeypatch):
        """COOKIE_INSTANCE_NAME env var overrides database"""
```

**Verify:** `docker compose exec web python -m pytest tests/test_auth.py::TestModels -v`

---

## Implementation Phase 2: Backend Authentication Logic

### 2.1 Update Profile Selection Endpoint
**File:** `apps/profiles/api.py`

Modify `POST /api/profiles/{id}/select/`:
- Home mode: Allow selection (current behavior)
- Public mode: Verify request.user is authenticated and owns this profile
- Return 401 if unauthorized in public mode

### 2.2 Update get_current_profile Utility
**File:** `apps/profiles/utils.py`

Make deployment-mode aware:
- Home mode: Use session['profile_id'] (existing behavior)
- Public mode: Use request.user.profile

### 2.3 Update require_profile Decorator
**File:** `apps/legacy/views.py`

Make deployment-mode aware:
- Home mode: Redirect to profile_selector if no session (current behavior)
- Public mode: Redirect to login if not authenticated

### 2.4 Add Auth Settings API
**File:** `apps/core/api.py`

Add endpoint for frontend to check deployment mode:
```
GET /api/system/auth-settings/
Returns: { deployment_mode, allow_registration, instance_name }
```

### 2.5 Add Auth API Tests
**File:** `tests/test_auth.py`

```python
class TestAuthAPI:
    """Tests for Session B - Backend Auth Logic"""

    def test_profile_select_home_mode_no_auth_required(self):
        """Home mode: any user can select any profile"""

    def test_profile_select_public_mode_requires_auth(self):
        """Public mode: 401 if not authenticated"""

    def test_profile_select_public_mode_wrong_user(self):
        """Public mode: 403 if user doesn't own profile"""

    def test_profile_select_public_mode_own_profile(self):
        """Public mode: success when user owns profile"""

    def test_get_current_profile_home_mode_uses_session(self):
        """Home mode: profile from session['profile_id']"""

    def test_get_current_profile_public_mode_uses_user(self):
        """Public mode: profile from request.user.profile"""

    def test_auth_settings_endpoint_returns_config(self):
        """GET /api/system/auth-settings/ returns deployment config"""
```

**Verify:** `docker compose exec web python -m pytest tests/test_auth.py::TestAuthAPI -v`

---

## Implementation Phase 3: Login/Register Views (Public Mode)

### 3.1 Add Login View
**File:** `apps/legacy/views.py`

```python
def login_view(request):
    # If home mode, redirect to profile selector
    # POST: authenticate user, login, set session, redirect to home
    # GET: render login form

    # SECURITY: Use same error message for all failures (prevents username enumeration)
    # SECURITY: Log failed attempts for monitoring
    if not authenticated:
        logger.warning(
            f"Failed login attempt for username={username} ip={get_client_ip(request)}"
        )
        return render(request, 'legacy/login.html', {
            'error': 'Invalid username or password'  # Same message always!
        })
```

### 3.2 Add Register View
**File:** `apps/legacy/views.py`

```python
def register_view(request):
    # If home mode or registration disabled, redirect
    # POST: validate username/password, create User + Profile, login, redirect
    # GET: render registration form
```

Validation:
- Username: 3-30 characters, **must be unique**, alphanumeric + underscore only
- Password: 8+ characters
- **No email field** - registration form does not include email input

### 3.3 Add Logout View
**File:** `apps/legacy/views.py`

```python
def logout_view(request):
    # Clear Django auth + session['profile_id']
    # Redirect based on deployment mode
```

### 3.4 Add URL Routes
**File:** `apps/legacy/urls.py`

```python
path("login/", views.login_view, name="login"),
path("register/", views.register_view, name="register"),
path("logout/", views.logout_view, name="logout"),
```

### 3.5 Add View Tests
**File:** `tests/test_auth.py`

```python
class TestViews:
    """Tests for Session C - Login/Register Views"""

    # Login view
    def test_login_get_renders_form(self):
        """GET /legacy/login/ renders login template"""

    def test_login_home_mode_redirects_to_selector(self):
        """Login view redirects to profile selector in home mode"""

    def test_login_success_redirects_to_home(self):
        """Valid credentials redirect to home page"""

    def test_login_invalid_credentials_generic_error(self):
        """Invalid credentials show generic error (prevents username enumeration)"""

    def test_login_same_error_for_wrong_password_and_nonexistent_user(self):
        """Login shows identical error for wrong password and nonexistent user"""

    def test_session_id_regenerated_on_login(self):
        """Session ID changes after login (prevents session fixation)"""

    # Register view
    def test_register_get_renders_form(self):
        """GET /legacy/register/ renders register template"""

    def test_register_home_mode_redirects(self):
        """Register view redirects in home mode"""

    def test_register_disabled_redirects(self):
        """Register view redirects when registration disabled"""

    def test_register_success_creates_user_and_profile(self):
        """Valid registration creates User and Profile"""

    def test_register_duplicate_username_shows_error(self):
        """Duplicate username shows error message"""

    def test_register_password_mismatch_shows_error(self):
        """Password confirmation mismatch shows error"""

    def test_register_short_password_shows_error(self):
        """Password under 8 chars shows error"""

    def test_register_invalid_username_shows_error(self):
        """Username with invalid chars shows error"""

    # Logout view
    def test_logout_clears_session(self):
        """Logout clears Django auth and session profile_id"""

    def test_logout_public_mode_redirects_to_login(self):
        """Public mode: logout redirects to login"""

    def test_logout_home_mode_redirects_to_selector(self):
        """Home mode: logout redirects to profile selector"""
```

**Verify:** `docker compose exec web python -m pytest tests/test_auth.py::TestViews -v`

---

## Implementation Phase 4: Legacy Frontend Templates (ES5/iOS 9)

### 4.1 Create Login Template
**New file:** `apps/legacy/templates/legacy/login.html`

Simple HTML form:
- Username field
- Password field
- Submit button
- Link to register (if allowed)
- Error message display
- Instance name as page title

### 4.2 Create Register Template
**New file:** `apps/legacy/templates/legacy/register.html`

Simple HTML form:
- Username field (3+ chars)
- Password field (8+ chars)
- Confirm password field
- Avatar color picker (ES5 inline script)
- Submit button
- Link to login

### 4.3 Profile Selector Unchanged
No changes needed - home mode keeps current behavior.

### 4.4 Add Template Rendering Tests
**File:** `tests/test_auth.py`

```python
class TestTemplates:
    """Tests for Session D - Template Rendering"""

    def test_login_template_renders(self, client):
        """GET /legacy/login/ returns 200 and contains form elements"""
        response = client.get('/legacy/login/')
        assert response.status_code == 200
        assert b'<form' in response.content
        assert b'username' in response.content.lower()
        assert b'password' in response.content.lower()

    def test_register_template_renders(self, client, settings):
        """GET /legacy/register/ returns 200 and contains form elements"""
        # Enable public mode and registration
        response = client.get('/legacy/register/')
        assert response.status_code == 200
        assert b'<form' in response.content
        assert b'username' in response.content.lower()
        assert b'password' in response.content.lower()

    def test_login_template_shows_instance_name(self, client):
        """Login page displays configured instance name"""

    def test_register_template_has_color_picker(self, client):
        """Register page includes avatar color picker"""

    def test_login_template_no_es6_syntax(self, client):
        """Login page inline scripts are ES5 compliant"""

    def test_register_template_no_es6_syntax(self, client):
        """Register page inline scripts are ES5 compliant"""
```

**Verify:** `docker compose exec web python -m pytest tests/test_auth.py::TestTemplates -v`

### 4.5 Legacy Template Verification
**Test device:** iPad 2/3/4 or iPad Mini 1 running iOS 9.3.6

**Manual testing checklist for Session D:**

- [ ] **Login form (iOS 9 Safari)**
  - [ ] Form renders without JavaScript errors
  - [ ] Username field accepts input
  - [ ] Password field masks characters
  - [ ] Submit button POSTs form (no JS required)
  - [ ] Error message displays for invalid login
  - [ ] "Register" link navigates correctly (if registration enabled)
  - [ ] Instance name displays in page title

- [ ] **Register form (iOS 9 Safari)**
  - [ ] Form renders without JavaScript errors
  - [ ] Username field accepts input (shows validation on blur)
  - [ ] Password fields mask characters
  - [ ] Confirm password field present
  - [ ] Avatar color picker works (ES5 inline script)
  - [ ] Submit button POSTs form
  - [ ] Error messages display for validation failures
  - [ ] "Login" link navigates correctly

---

## Implementation Phase 5: React Frontend

### 5.1 Add Auth Context
**New file:** `frontend/src/contexts/AuthContext.tsx`

- Fetch auth settings on mount
- Provide `isPublicMode`, `isAuthenticated`, `settings`
- Expose `login(username, password)` - calls API, updates state
- Expose `logout()` - calls API, clears state, redirects based on mode:
  - Public mode: Redirect to `/login`
  - Home mode: Redirect to `/` (profile selector)

### 5.2 Add Login Screen
**New file:** `frontend/src/screens/Login.tsx`

- Form with username/password
- Call login API, redirect on success

### 5.3 Add Register Screen
**New file:** `frontend/src/screens/Register.tsx`

- Form with username, password, confirm, color picker
- Call register API, redirect on success

### 5.4 Update Router
**File:** `frontend/src/router.tsx`

- Add `/login` and `/register` routes (as PublicRoute children)
- Update ProtectedRoute to check deployment mode:
  - Home mode: Redirect to `/` if no profile (current behavior)
  - Public mode: Redirect to `/login` if not authenticated
- Update PublicRoute to check deployment mode:
  - Home mode: Redirect to `/home` if profile exists (current behavior)
  - Public mode: Redirect to `/home` if authenticated

### 5.5 Add API Endpoints
**File:** `frontend/src/api/client.ts`

```typescript
auth: {
  login: (username: string, password: string) => Promise<Profile>,
  register: (username: string, password: string, avatarColor: string) => Promise<Profile>,
  logout: () => Promise<void>,
  getSettings: () => Promise<AuthSettings>,
}
```

### 5.6 Add Frontend Tests
**Files:**
- `frontend/src/test/Login.test.tsx`
- `frontend/src/test/Register.test.tsx`
- `frontend/src/test/AuthContext.test.tsx`

```typescript
// Login.test.tsx
describe('Login', () => {
  it('renders username and password fields')
  it('submits form and redirects on success')
  it('displays error message on login failure')
  it('shows link to register when registration enabled')
  it('hides register link when registration disabled')
  it('redirects to profile selector if home mode')
})

// Register.test.tsx
describe('Register', () => {
  it('renders username, password, confirm, color picker')
  it('validates password confirmation matches')
  it('validates username format (alphanumeric + underscore)')
  it('validates minimum password length')
  it('submits and redirects on success')
  it('displays error for duplicate username')
  it('redirects if registration disabled')
})

// AuthContext.test.tsx
describe('AuthContext', () => {
  it('fetches auth settings on mount')
  it('provides isPublicMode based on settings')
  it('provides isAuthenticated state')
  it('updates state after login')
  it('clears state after logout')
})
```

**Verify:** `docker compose exec frontend npm test -- Login.test.tsx Register.test.tsx AuthContext.test.tsx`

### 5.7 React Frontend Verification
**Test browsers:** Chrome (latest), Safari (latest)

**Manual testing checklist for Session E:**

- [ ] **Login screen (Chrome/Safari)**
  - [ ] Form renders with username/password fields
  - [ ] Submit shows loading state
  - [ ] Error message displays for invalid credentials
  - [ ] Success redirects to /home
  - [ ] "Register" link visible when registration enabled
  - [ ] "Register" link hidden when registration disabled
  - [ ] Redirects to / (profile selector) if home mode

- [ ] **Register screen (Chrome/Safari)**
  - [ ] Form renders all fields (username, password, confirm, color)
  - [ ] Client-side validation shows errors
  - [ ] Color picker allows selection
  - [ ] Success creates account and redirects
  - [ ] Duplicate username shows error
  - [ ] Redirects if registration disabled

- [ ] **Auth flow**
  - [ ] Protected routes redirect to /login in public mode
  - [ ] Logout clears session and redirects to /login
  - [ ] Refresh preserves authentication state

---

## Implementation Phase 6: Settings UI

### 6.1 Add Authentication Section to Settings
**Files:**
- `apps/legacy/templates/legacy/settings.html`
- `apps/legacy/static/legacy/js/pages/settings.js`

Add "Deployment" card with:
- Deployment mode radio buttons (Home / Public)
- Allow registration toggle (public mode only)
- Instance name input (public mode only)
- Save button

**Important behaviors:**
- If `COOKIE_DEPLOYMENT_MODE` env var is set, show mode as **read-only** with message "Set via environment variable"
- Same for other env-var-controlled settings
- Show confirmation when switching to public mode ("Users will need to create accounts to access")

### 6.2 Add Settings API Endpoint
**File:** `apps/core/api.py`

```
PUT /api/system/auth-settings/
Body: { deployment_mode, allow_registration, instance_name }
```

### 6.3 Add Settings API Tests
**File:** `tests/test_auth.py`

```python
class TestSettingsAPI:
    """Tests for Session F - Settings API"""

    def test_put_auth_settings_updates_deployment_mode(self, client, admin_user):
        """PUT /api/system/auth-settings/ updates deployment mode"""

    def test_put_auth_settings_updates_allow_registration(self, client, admin_user):
        """PUT /api/system/auth-settings/ updates allow_registration"""

    def test_put_auth_settings_updates_instance_name(self, client, admin_user):
        """PUT /api/system/auth-settings/ updates instance_name"""

    def test_put_auth_settings_respects_env_override(self, client, admin_user, monkeypatch):
        """Cannot change deployment_mode via API when env var is set"""
        monkeypatch.setenv('COOKIE_DEPLOYMENT_MODE', 'public')
        # API should return error or ignore the field

    def test_get_auth_settings_shows_env_override_status(self, client, monkeypatch):
        """GET response indicates which settings are env-controlled"""
```

**Verify:** `docker compose exec web python -m pytest tests/test_auth.py::TestSettingsAPI -v`

### 6.4 React Settings Scope
**Note:** Deployment settings UI is implemented in **Legacy only** for this phase. React Settings page already exists but does not need deployment controls because:
1. Public mode users will primarily use the legacy frontend (iOS 9 compatibility)
2. Admin configuration is a low-frequency operation
3. Keeps Phase 12 scope focused

If React deployment settings are needed later, add to `FUTURE-ENHANCEMENTS.md`.

### 6.5 Settings UI Verification
**Test devices:** iOS 9 Safari (iPad 2/3/4 or iPad Mini 1), Chrome (latest)

**Manual testing checklist for Session F:**

- [ ] **Legacy Settings Page**
  - [ ] "Deployment" card appears in settings
  - [ ] Home/Public radio buttons toggle mode
  - [ ] "Allow Registration" toggle appears in public mode only
  - [ ] "Instance Name" input appears in public mode only
  - [ ] When env var set: mode shows as read-only with "Set via environment variable" message
  - [ ] Confirmation dialog appears when switching to public mode
  - [ ] Save button persists changes

- [ ] **React Settings (if applicable)**
  - [ ] Same behavior as legacy settings
  - [ ] Form state updates correctly on toggle

---

## Implementation Phase 7: CSRF Protection

### 7.1 Enable CSRF Middleware
**File:** `cookie/settings.py`

```python
MIDDLEWARE = [
    # ... existing
    "django.middleware.csrf.CsrfViewMiddleware",  # ADD
]
```

### 7.2 Update AJAX Helper (ES5)
**File:** `apps/legacy/static/legacy/js/ajax.js`

Add CSRF token to mutating requests:
```javascript
function getCSRFToken() {
    var value = "; " + document.cookie;
    var parts = value.split("; csrftoken=");
    if (parts.length === 2) return parts.pop().split(";").shift();
    return "";
}
// Add header: xhr.setRequestHeader('X-CSRFToken', getCSRFToken());
```

### 7.3 Enable CSRF in Django Ninja
**File:** `cookie/urls.py`

```python
api = NinjaAPI(csrf=True)
```

### 7.4 Update React API Client for CSRF
**File:** `frontend/src/api/client.ts`

Add CSRF token extraction and include in mutating requests:
```typescript
function getCSRFToken(): string {
  const match = document.cookie.match(/csrftoken=([^;]+)/)
  return match ? match[1] : ''
}

// Update fetch wrapper to include CSRF for POST/PUT/DELETE:
const response = await fetch(url, {
  method,
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCSRFToken(),
  },
  body: JSON.stringify(data),
})
```

### 7.5 Add CSRF Tests
**File:** `tests/test_csrf.py`

```python
class TestCSRF:
    """Tests for Session G - CSRF Protection"""

    def test_login_requires_csrf_token(self):
        """POST to login without CSRF token returns 403"""

    def test_register_requires_csrf_token(self):
        """POST to register without CSRF token returns 403"""

    def test_api_post_requires_csrf_token(self):
        """POST to Django Ninja API without CSRF returns 403"""

    def test_api_post_with_csrf_token_succeeds(self):
        """POST to Django Ninja API with valid CSRF succeeds"""

    def test_csrf_token_in_cookie(self):
        """CSRF token is set in cookie after GET request"""
```

**Verify:** `docker compose exec web python -m pytest tests/test_csrf.py -v`

---

## Implementation Phase 8: Admin Authorization

### 8.1 Add Admin Check Utility
**File:** `apps/core/utils.py`

```python
import os

def get_admin_username():
    """Get the admin username from environment variable."""
    return os.environ.get('COOKIE_ADMIN_USERNAME', '')

def is_admin(user):
    """Check if user has admin privileges."""
    from apps.core.models import AppSettings
    settings = AppSettings.get_solo()

    # Home mode: everyone is effectively admin
    if settings.get_deployment_mode() == 'home':
        return True

    # Public mode: check username against env var
    admin_username = get_admin_username()
    if not admin_username:
        # No admin configured = no admin access (secure default)
        return False

    return user.is_authenticated and user.username == admin_username
```

### 8.2 Add require_admin Decorator
**File:** `apps/core/decorators.py`

```python
from functools import wraps
from django.http import HttpResponseForbidden
from apps.core.utils import is_admin

def require_admin(view_func):
    """Decorator to restrict view to admin users only."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not is_admin(request.user):
            return HttpResponseForbidden("Admin access required")
        return view_func(request, *args, **kwargs)
    return wrapper
```

### 8.3 Protect Settings View
**File:** `apps/legacy/views.py`

```python
from apps.core.decorators import require_admin

@require_admin
def settings_view(request):
    # ... existing implementation
```

### 8.4 Protect Admin-Only API Endpoints
**File:** `apps/core/api.py`, `apps/ai/api.py`, `apps/profiles/api.py`

Add admin checks to these endpoints:
- `PUT /api/system/auth-settings/` - deployment mode changes
- `POST /api/system/reset/` - database reset
- `PUT /api/ai/key/` - API key management
- `PUT /api/ai/prompts/{type}/` - prompt editing
- `DELETE /api/profiles/{id}/` - deleting OTHER users' profiles
- `GET /api/profiles/` - listing all profiles (admin can see all, user sees only own)

```python
from apps.core.utils import is_admin

@api.put("/system/auth-settings/")
def update_auth_settings(request, data: AuthSettingsSchema):
    if not is_admin(request.user):
        return api.create_response(request, {"error": "Admin access required"}, status=403)
    # ... existing implementation
```

### 8.5 Add isAdmin to Auth Context (React)
**File:** `frontend/src/contexts/AuthContext.tsx`

```typescript
interface AuthContextType {
  // ... existing
  isAdmin: boolean
}

// Fetch from /api/system/auth-settings/ which should include is_admin flag
```

**File:** `apps/core/api.py`

Update GET endpoint to include admin status:
```python
@api.get("/system/auth-settings/")
def get_auth_settings(request):
    return {
        "deployment_mode": settings.get_deployment_mode(),
        "allow_registration": settings.get_allow_registration(),
        "instance_name": settings.get_instance_name(),
        "is_admin": is_admin(request.user),  # ADD
        "env_overrides": {
            "deployment_mode": bool(os.environ.get('COOKIE_DEPLOYMENT_MODE')),
            "allow_registration": bool(os.environ.get('COOKIE_ALLOW_REGISTRATION')),
            "instance_name": bool(os.environ.get('COOKIE_INSTANCE_NAME')),
        }
    }
```

### 8.6 Hide Settings Link for Non-Admins
**Files:**
- `apps/legacy/templates/legacy/partials/nav_header.html`
- `frontend/src/components/NavHeader.tsx`

Only show Settings navigation link if user is admin:

**Legacy (Django template):**
```django
{% if is_admin %}
<a href="{% url 'legacy:settings' %}" class="nav-link">Settings</a>
{% endif %}
```

**React:**
```typescript
{isAdmin && <Link to="/settings">Settings</Link>}
```

### 8.7 Add Admin Authorization Tests
**File:** `tests/test_auth.py`

```python
class TestAdminAuthorization:
    """Tests for Session H - Admin Authorization"""

    def test_is_admin_home_mode_returns_true(self):
        """Home mode: all users are effectively admin"""

    def test_is_admin_public_mode_no_env_var(self):
        """Public mode without COOKIE_ADMIN_USERNAME: no one is admin"""

    def test_is_admin_public_mode_matching_username(self, monkeypatch):
        """Public mode: user matching env var is admin"""

    def test_is_admin_public_mode_non_matching_username(self, monkeypatch):
        """Public mode: user not matching env var is not admin"""

    def test_settings_view_home_mode_accessible(self):
        """Home mode: settings accessible without auth"""

    def test_settings_view_public_mode_admin_accessible(self, monkeypatch):
        """Public mode: settings accessible to admin"""

    def test_settings_view_public_mode_user_forbidden(self, monkeypatch):
        """Public mode: settings returns 403 for non-admin"""

    def test_api_reset_public_mode_user_forbidden(self, monkeypatch):
        """Public mode: reset endpoint returns 403 for non-admin"""

    def test_api_delete_own_profile_allowed(self):
        """Any user can delete their own profile"""

    def test_api_delete_other_profile_admin_only(self, monkeypatch):
        """Only admin can delete other users' profiles"""

    def test_settings_nav_hidden_for_non_admin(self):
        """Settings link not shown in nav for non-admin users"""
```

**Verify:** `docker compose exec web python -m pytest tests/test_auth.py::TestAdminAuthorization -v`

### 8.8 Admin Authorization Manual Testing
**Test devices:** iOS 9 Safari (iPad 2/3/4 or iPad Mini 1), Chrome (latest)

**Manual testing checklist for Session H:**

- [ ] **Home mode (no restrictions)**
  - [ ] Any profile can access Settings page
  - [ ] Settings link visible in navigation
  - [ ] All admin operations work (API key, prompts, etc.)

- [ ] **Public mode as admin**
  - [ ] Login as COOKIE_ADMIN_USERNAME user
  - [ ] Settings link visible in navigation
  - [ ] Settings page accessible
  - [ ] Can delete other users' profiles
  - [ ] Can reset database

- [ ] **Public mode as regular user**
  - [ ] Login as non-admin user
  - [ ] Settings link NOT visible in navigation
  - [ ] Direct URL to /settings returns 403
  - [ ] API calls to admin endpoints return 403
  - [ ] CAN delete own profile
  - [ ] CANNOT see other users in Users list

- [ ] **Public mode with no admin configured**
  - [ ] COOKIE_ADMIN_USERNAME not set
  - [ ] No one can access Settings (secure default)
  - [ ] Warning logged on startup: "No admin user configured"

---

## Files Summary

### Create (12 files)
1. `apps/legacy/templates/legacy/login.html`
2. `apps/legacy/templates/legacy/register.html`
3. `apps/core/utils.py` - Admin check utilities (get_admin_username, is_admin)
4. `apps/core/decorators.py` - require_admin decorator
5. `frontend/src/contexts/AuthContext.tsx`
6. `frontend/src/screens/Login.tsx`
7. `frontend/src/screens/Register.tsx`
8. `tests/test_auth.py` - Backend auth tests (TestModels, TestAuthAPI, TestViews, TestTemplates, TestSettingsAPI, TestAdminAuthorization)
9. `tests/test_csrf.py` - CSRF protection tests
10. `frontend/src/test/Login.test.tsx`
11. `frontend/src/test/Register.test.tsx`
12. `frontend/src/test/AuthContext.test.tsx`
13. Migrations for profiles and core apps

### Modify (14 files)
1. `cookie/settings.py` - Add auth app, middleware, CSRF
2. `apps/profiles/models.py` - Add user field
3. `apps/core/models.py` - Add deployment_mode, allow_registration, instance_name
4. `apps/core/api.py` - Auth settings endpoints, admin checks
5. `apps/ai/api.py` - Admin checks on API key and prompt endpoints
6. `apps/profiles/api.py` - Mode-aware profile selection, admin checks on delete
7. `apps/profiles/utils.py` - Mode-aware get_current_profile
8. `apps/legacy/views.py` - Login/register/logout views, require_admin on settings
9. `apps/legacy/urls.py` - Add auth routes
10. `apps/legacy/static/legacy/js/ajax.js` - CSRF token (ES5)
11. `apps/legacy/templates/legacy/settings.html` - Deployment settings UI
12. `apps/legacy/templates/legacy/partials/nav_header.html` - Hide Settings for non-admin
13. `frontend/src/router.tsx` - Auth routes, update ProtectedRoute and PublicRoute
14. `frontend/src/api/client.ts` - CSRF token handling
15. `frontend/src/components/NavHeader.tsx` - Hide Settings for non-admin

---

## Mode Comparison

| Feature | Home Mode | Public Mode |
|---------|-----------|-------------|
| Profile creation | Anyone, no password | Registration required |
| Login required | No | Yes |
| Username | Display name only | **Unique**, used for login |
| Password | None | Required (8+ chars) |
| Email collected | **No** | **No** |
| Who can access | Anyone on network | Registered users only |
| Registration | Always open | Can be disabled by admin |
| Settings access | **All users** | **Admin only** (via COOKIE_ADMIN_USERNAME) |
| Admin designation | N/A (all have access) | Environment variable |
| Configure via | Settings UI or env var | Settings UI or env var (admin only) |

---

## Security Configuration

### Password Security (Django Defaults)
Django uses PBKDF2 with SHA256 by default. Add password validators to enforce strength:

**File:** `cookie/settings.py`

```python
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
]
```

### Session Security
**File:** `cookie/settings.py`

```python
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
# For production with HTTPS:
# SESSION_COOKIE_SECURE = True
```

**Session fixation protection:** Django automatically regenerates the session ID on login when using `django.contrib.auth.login()`. Ensure all login paths use this function.

### Django Admin Site

The Django admin site (`/admin/`) is **not enabled**. All administrative functions are handled through Cookie's Settings UI, which has proper authorization checks.

**Do not add to settings.py:**
```python
# "django.contrib.admin",  # Not used - Cookie has custom Settings UI
```

**Do not add to urls.py:**
```python
# path('admin/', admin.site.urls),  # Disabled - no Django admin
```

**Why:** The Django admin site creates unnecessary attack surface. Cookie's Settings page provides all needed admin functionality with proper mode-aware authorization.

### Admin Configuration (Public Mode)

**Required for public deployments:**
```bash
COOKIE_ADMIN_USERNAME=admin  # Username that gets admin privileges
```

**Security considerations:**
- Admin is determined by username match, not a database flag (prevents privilege escalation)
- If `COOKIE_ADMIN_USERNAME` is not set in public mode, NO ONE can access Settings (secure default)
- The admin user must register like any other user (same registration flow)
- To change admin: update environment variable and restart container
- No "superuser" or Django admin site - all admin access through Cookie's Settings UI

**Startup validation:**
```python
# In apps/core/apps.py ready() method
if settings.get_deployment_mode() == 'public':
    admin_username = os.environ.get('COOKIE_ADMIN_USERNAME')
    if not admin_username:
        logger.warning(
            "COOKIE_ADMIN_USERNAME not set in public mode. "
            "No user will have admin access to Settings."
        )
```

### Rate Limiting (Cloudflare)
Rate limiting is handled at the edge by Cloudflare, not in the application:

1. **Cloudflare Dashboard** → Security → WAF → Rate Limiting Rules
2. Create rule targeting `/legacy/login/` and `/legacy/register/`
3. Example: 10 requests per minute per IP, then challenge/block

Benefits over application-level rate limiting:
- Blocks malicious traffic before it hits the server
- No additional Django dependencies
- Centralized with other security rules
- DDoS protection included

---

## Verification

### Manual Testing
1. **Home mode (default)**:
   - Profile selector shows all profiles (unchanged)
   - Can create new profile without password
   - Selecting profile works as before

2. **Public mode**:
   - `/legacy/` redirects to `/legacy/login/`
   - Can register with username/password (no email)
   - Can login with username/password
   - Logout returns to login page
   - Registration can be disabled in settings

3. **iOS 9 Safari**:
   - Login form works (standard POST)
   - Register form works (standard POST)
   - Color picker works (ES5)
   - No JavaScript errors

4. **Mode switching**:
   - Can change mode in settings
   - Warning shown before switching to public
   - Existing home-mode profiles still work

### Automated Tests
```bash
# Backend - all auth tests
docker compose exec web python -m pytest tests/test_auth.py tests/test_csrf.py -v

# Frontend - auth components
docker compose exec frontend npm test -- Login.test.tsx Register.test.tsx AuthContext.test.tsx
```

---

---

## Security Checklist

Before marking Phase 12 complete, verify:

- [ ] **Authentication**
  - [ ] `django.contrib.auth.login()` used (regenerates session ID)
  - [ ] Same error message for all login failures (no username enumeration)
  - [ ] Failed login attempts logged with IP address
  - [ ] Password validators enabled (MinimumLength, CommonPassword)

- [ ] **Authorization**
  - [ ] Settings page protected by `@require_admin`
  - [ ] Admin-only API endpoints check `is_admin()`
  - [ ] Profile deletion checks ownership OR admin status
  - [ ] `is_admin` flag returned in `/api/system/auth-settings/`

- [ ] **CSRF**
  - [ ] `CsrfViewMiddleware` enabled
  - [ ] `{% csrf_token %}` in all POST forms
  - [ ] `X-CSRFToken` header in AJAX requests (both frontends)
  - [ ] `NinjaAPI(csrf=True)` set

- [ ] **Session**
  - [ ] `SESSION_COOKIE_HTTPONLY = True`
  - [ ] `SESSION_COOKIE_SAMESITE = 'Lax'`
  - [ ] `SESSION_COOKIE_SECURE = True` (production with HTTPS)

- [ ] **Configuration**
  - [ ] Django admin site NOT enabled (`django.contrib.admin` not in INSTALLED_APPS)
  - [ ] `COOKIE_ADMIN_USERNAME` documented in deployment docs
  - [ ] Startup warning logged if admin not configured in public mode

- [ ] **Tests**
  - [ ] Username enumeration prevention test passes
  - [ ] Session fixation prevention test passes
  - [ ] All admin authorization tests pass
  - [ ] CSRF rejection tests pass

---

## Future Enhancements (Not in Scope)
- Password reset (admin-only for now since no email)
- Remember me / longer sessions
- Account lockout after failed attempts (consider Cloudflare's bot management)

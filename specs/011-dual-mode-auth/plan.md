# Implementation Plan: Dual-Mode Authentication & Production Deployment

**Feature**: 011-dual-mode-auth
**Branch**: `feature/011-dual-mode-auth`
**Created**: 2026-03-24

---

## Technical Context

### Current Stack
- **Backend**: Python 3.12, Django 5.0, Django Ninja 1.0+, Gunicorn, WhiteNoise
- **Frontend**: React 19, TypeScript 5.9, Vite 7, React Router
- **Legacy Frontend**: ES5 JavaScript, Django templates
- **Database**: PostgreSQL 18 (via dj-database-url)
- **Infrastructure**: Docker Compose (dev + prod), nginx reverse proxy
- **Auth (current)**: Profile-based sessions only — no Django auth, no User model

### New Dependencies
- `django.contrib.auth` (built into Django — no pip install)
- `django-ses` (AWS SES email backend)
- No new frontend dependencies

### Key Integration Points
- `apps/core/auth.py` — SessionAuth class (must become mode-aware)
- `cookie/settings.py` — Conditional INSTALLED_APPS and MIDDLEWARE
- `apps/profiles/models.py` — Add optional User FK
- `cookie/urls.py` — Conditional auth router mount
- `frontend/src/App.tsx` — Mode detection, conditional rendering
- `frontend/src/contexts/ProfileContext.tsx` — Auth-aware session restoration
- 12+ API endpoints need admin-only enforcement (see contracts/permission-map.md)

---

## Constitution Check

No `.specify/memory/constitution.md` exists. Key principles from spec:

| Principle | Status | Notes |
|-----------|--------|-------|
| Zero email storage | ✅ Compliant | Email never written to DB, log, or disk |
| Home mode regression-free | ✅ Compliant | Conditional loading, all existing tests pass unchanged |
| ES5 legacy parity | ✅ Compliant | Legacy frontend gets matching auth screens |
| Docker-only commands | ✅ Compliant | All backend work via docker compose exec |
| Code quality limits | ✅ Planned | Functions <100 lines, complexity <15, files <500 lines |

---

## Implementation Phases

### Phase 1: Backend Auth Foundation

**Goal**: Django auth integrated, mode switching works, auth endpoints functional.

#### 1.1 Settings & Mode Configuration
**Files**: `cookie/settings.py`

- Add `AUTH_MODE = os.environ.get("AUTH_MODE", "home")` setting
- Conditionally add to INSTALLED_APPS when `AUTH_MODE == "public"`:
  - `django.contrib.auth`
  - `django.contrib.contenttypes` (already present)
- Conditionally add to MIDDLEWARE when `AUTH_MODE == "public"`:
  - `django.contrib.auth.middleware.AuthenticationMiddleware` (after SessionMiddleware)
- Add email configuration:
  - `EMAIL_BACKEND` (default: console in dev, configurable for SES)
  - `DEFAULT_FROM_EMAIL`
  - `AWS_SES_REGION_NAME` (for SES backend)
- Add `AUTH_PASSWORD_VALIDATORS` (standard Django validators)

#### 1.2 Profile Model Migration
**Files**: `apps/profiles/models.py`, new migration

- Add `user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE, related_name="profile")`
- Migration must be safe: nullable FK, no data migration needed
- Works in both modes: null in home mode, populated in public mode

#### 1.3 SessionAuth Mode-Aware Refactor
**Files**: `apps/core/auth.py`

- Refactor `SessionAuth.authenticate()`:
  - Home mode: check `session["profile_id"]` → Profile (unchanged)
  - Public mode: check `request.user.is_authenticated` → `request.user.profile`
- Add `AdminAuth(SessionAuth)`:
  - Home mode: same as SessionAuth (no admin distinction)
  - Public mode: additionally check `request.user.is_staff`

#### 1.4 Auth API Endpoints
**Files**: New `apps/core/auth_api.py`

- `POST /api/auth/register/` — Create user, send verification email, discard email
- `POST /api/auth/login/` — Authenticate, set session, return user+profile
- `POST /api/auth/logout/` — Flush session
- `GET /api/auth/verify-email/` — Validate signed token, activate user, redirect
- `GET /api/auth/me/` — Return current user+profile
- `POST /api/auth/change-password/` — Validate current, set new
- Rate limiting on all endpoints (per contracts/auth-api.md)

#### 1.5 Email Verification Service
**Files**: New `apps/core/email_service.py`

- `send_verification_email(user_id, email)` — takes email as parameter (transient)
  - Generates signed token via `TimestampSigner`
  - Builds verification URL
  - Sends email via Django's `send_mail()`
  - Email parameter is NOT stored — function receives it, uses it, discards it
- Email template: simple HTML + plain text alternative
- Verification URL: `{SITE_URL}/api/auth/verify-email/?token={signed_token}`

#### 1.6 Mode Endpoint
**Files**: `apps/core/api.py`

- Add `GET /api/system/mode/` — returns `{"mode": "home"}` or `{"mode": "public"}`

#### 1.7 Conditional URL Mounting
**Files**: `cookie/urls.py`

- Import auth router conditionally: `if settings.AUTH_MODE == "public": api.add_router("/auth", auth_router)`
- In home mode, `/api/auth/*` returns 404 (router not mounted)

#### 1.8 Admin-Only Endpoint Enforcement
**Files**: `apps/core/api.py`, `apps/ai/api.py`, `apps/recipes/sources_api.py`

- Replace `auth=SessionAuth()` with `auth=AdminAuth()` on all admin-only endpoints (see contracts/permission-map.md)
- In home mode, AdminAuth behaves identically to SessionAuth (no change)
- In public mode, AdminAuth additionally checks `is_staff`

#### 1.9 Profile Endpoint Behavior Changes (Public Mode)
**Files**: `apps/profiles/api.py`

- `GET /api/profiles/` — In public mode: return only current user's profile (admin sees all)
- `POST /api/profiles/` — In public mode: return 404 (profiles created via /auth/register)
- `POST /api/profiles/{id}/select/` — In public mode: return 404 (no profile switching)
- `DELETE /api/profiles/{id}/` — In public mode: cascade deletes User too

---

### Phase 2: Admin CLI & Management

**Goal**: Site administrators can manage users via command line.

#### 2.1 Management Command
**Files**: New `apps/core/management/commands/cookie_admin.py`

- Subcommands: `list-users`, `promote`, `demote`, `reset-password`, `activate`, `deactivate`, `cleanup-unverified`
- Per contracts/admin-cli.md
- Validates mode is "public" before executing
- Safety check: cannot demote last admin

#### 2.2 Auto-Admin First User
**Files**: `apps/core/auth_api.py` (register endpoint)

- On registration: check if any active users exist
- If no active users → set `is_staff=True` on this user
- Log this event for auditability

#### 2.3 Stale Registration Cleanup
**Files**: `apps/core/management/commands/cookie_admin.py`

- `cleanup-unverified` subcommand
- Deletes User + Profile where `is_active=False` and `date_joined` > 24 hours ago
- Add to entrypoint scripts (run on container start)

---

### Phase 3: Frontend — React Auth Screens

**Goal**: Modern frontend supports login, registration, and mode-aware routing.

#### 3.1 Mode Detection
**Files**: `frontend/src/App.tsx`, new `frontend/src/contexts/AuthContext.tsx`

- On app load, call `GET /api/system/mode/`
- If "home" → render existing app (ProfileSelector, etc.)
- If "public" → render AuthContext-wrapped app (Login, Register, etc.)

#### 3.2 Auth Context
**Files**: New `frontend/src/contexts/AuthContext.tsx`

- State: `user`, `profile`, `isAdmin`, `isLoading`
- Methods: `login(username, password)`, `logout()`, `register(...)`, `changePassword(...)`
- Session restoration: calls `GET /api/auth/me/` on mount
- Wraps ProfileContext (profile comes from auth, not direct selection)

#### 3.3 Login Screen
**Files**: New `frontend/src/screens/Login.tsx`

- Username + password form
- "Forgot password?" → text explaining to contact admin
- Link to registration
- Error display (invalid credentials, rate limited, unverified)
- Success message when redirected from email verification (`?verified=true`)

#### 3.4 Registration Screen
**Files**: New `frontend/src/screens/Register.tsx`

- Username, password, password confirmation, email, privacy checkbox
- Link to privacy policy (opens in new tab)
- Client-side validation (matching passwords, email format, username rules)
- Success: show "check your email" message
- Error: display server-side validation errors

#### 3.5 Router Updates
**Files**: `frontend/src/router.tsx`

- Public mode routes:
  - `/login` → Login (public)
  - `/register` → Register (public)
  - `/privacy` → redirect to `/privacy/` (Django-served)
  - All other routes → require authentication (redirect to /login)
- Home mode routes: unchanged

#### 3.6 Settings Page Segmentation
**Files**: `frontend/src/screens/Settings.tsx`, all `frontend/src/components/settings/*.tsx`

- Settings component checks `useAuth().isAdmin`
- Admin-only tabs (Prompts, Sources, Selectors, Users, Danger) hidden for non-admins
- Add "Account" section for public mode: change password, delete account
- API key section in General tab: hidden for non-admins

---

### Phase 4: Frontend — Legacy Auth Screens

**Goal**: Legacy ES5 frontend supports login, registration, and mode-aware routing.

#### 4.1 Legacy Login Template
**Files**: New `apps/legacy/templates/legacy/login.html`

- ES5-only JavaScript
- Form: username, password
- "Forgot password?" text → contact admin
- Link to register
- Error/success messages

#### 4.2 Legacy Registration Template
**Files**: New `apps/legacy/templates/legacy/register.html`

- ES5-only JavaScript
- Form: username, password, password confirmation, email, privacy checkbox
- Link to privacy policy
- Client-side validation (ES5 compatible)
- Success/error messages

#### 4.3 Legacy Views & Routing
**Files**: `apps/legacy/views.py`, `apps/legacy/urls.py`

- New views: `login_view`, `register_view`
- In public mode: root URL (`""`) → login (not profile_selector)
- `@require_profile` decorator updated: in public mode, redirects to login instead of profile_selector
- Add `@require_admin` decorator for admin-only legacy views (settings sub-pages)

#### 4.4 Legacy Settings Segmentation
**Files**: Legacy settings JS files, legacy settings template

- Conditionally render admin sections based on profile data
- API responses include `is_admin` flag
- Hide admin tabs (Prompts, Sources, Selectors, Users, Danger) for non-admins

---

### Phase 5: Privacy Policy

**Goal**: UK GDPR-compliant privacy policy accessible from both frontends.

#### 5.1 Privacy Policy Template
**Files**: New `apps/core/templates/core/privacy_policy.html`

- Standalone HTML page (no JavaScript dependency)
- Covers all UK GDPR requirements per spec
- Responsive design (works on mobile, legacy browsers)
- Served at `/privacy/`

#### 5.2 Privacy Policy View & URL
**Files**: `apps/core/views.py`, `cookie/urls.py`

- Simple TemplateView at `/privacy/`
- No authentication required
- Available in both modes (but primarily relevant in public mode)

---

### Phase 6: Production Infrastructure

**Goal**: Cookie deployed on a cloud VPS, secure and automated.

#### 6.1 Email Service Configuration
**Files**: `requirements.txt`, `cookie/settings.py`, new `docs/EMAIL-SETUP.md`

- Add `django-ses` to requirements (optional — SMTP also supported)
- Settings: email backend configuration (SES or SMTP via env vars)
- Documentation: SES setup (domain verification, DKIM, SPF, sandbox exit)
- Documentation: Generic SMTP setup as alternative

#### 6.2 Nginx Cloudflare Origin Certificate
**Files**: `nginx/nginx.prod.conf`, new `docs/CLOUDFLARE-SETUP.md`

- Update nginx to terminate HTTPS with Cloudflare Origin Certificate
- Listen on 443 with SSL
- Redirect 80 → 443
- Documentation: generating Origin Certificate, installing it, Cloudflare SSL mode

#### 6.3 Database Backup Script
**Files**: New `bin/backup-db`, new `docs/BACKUP-RESTORE.md`

- Shell script: `pg_dump | gzip` + configurable upload target (S3, local, rsync, etc.)
- Configurable retention
- Runs via cron (daily)
- Documentation: storage setup, restore procedure

#### 6.4 Production Docker Compose Updates
**Files**: `docker-compose.prod.yml`

- Add `AUTH_MODE` environment variable
- Add `SITE_URL` environment variable (for verification email links)
- Add email-related environment variables
- Add logging-related environment variables (LOG_FORMAT, LOG_LEVEL)
- Document all new environment variables

#### 6.5 VPS Deployment Guide
**Files**: New `docs/DEPLOYMENT.md` (update existing)

- VPS setup (any provider: Hetzner, AWS EC2, DigitalOcean, etc.)
- Firewall configuration (SSH from admin IP, HTTP/HTTPS from Cloudflare IPs)
- Docker + Docker Compose installation
- Docker Compose deployment
- Cron setup for backups
- Monitoring (health endpoint)

#### 6.6 Cloudflare Configuration Guide
**Files**: New `docs/CLOUDFLARE-SETUP.md` (merged with 6.2)

- DNS A record → server IP
- SSL mode: Full (Strict)
- Origin Certificate generation
- Cache rules (static assets only)
- Security settings (WAF basics)

---

### Phase 7: Testing

**Goal**: Comprehensive test coverage proving both modes work correctly and securely. Tests are written alongside each phase (not deferred to the end), with a final integration pass here.

#### 7.1 Backend Auth Tests
**Files**: New `tests/test_auth.py`

Registration:
- Successful registration creates inactive user with empty email field
- Registration with taken username returns 400
- Registration with weak password returns 400 (too short, all numeric, common)
- Registration with mismatched passwords returns 400
- Registration with `privacy_accepted=false` returns 400
- Registration with invalid email format returns 400
- Rate limiting: 6th registration attempt from same IP returns 429
- **Security: After registration, `User.objects.get(username=x).email == ""`** (proves email not stored)
- **Security: Database query for registered email returns zero results** (grep all columns)

Email verification:
- Valid token activates user (`is_active` changes from False to True)
- Expired token (>2 hours) returns error page with helpful message
- Tampered token (modified signature) returns error
- Already-used token (user already active) redirects to login (idempotent)
- Token for nonexistent user returns error
- Token works across different browser sessions (stateless)

Login:
- Correct credentials returns 200 with user+profile data
- Wrong password returns 401 with generic message (doesn't reveal if username exists)
- Nonexistent username returns 401 with same generic message
- Unverified account returns 403
- Deactivated account returns 403
- Rate limiting: 11th failed attempt from same IP returns 429
- **Security: Successful login sets both Django session and profile_id in session**
- **Security: Session cookie has Secure, HttpOnly, SameSite=Lax flags**

Logout:
- Successful logout clears session
- Subsequent API calls return 401
- Double-logout is idempotent (200)

Change password:
- Correct current password + valid new password succeeds
- Wrong current password returns 400
- Weak new password returns 400
- Rate limited per user

#### 7.2 Permission Tests (Security-Critical)
**Files**: New `tests/test_permissions.py`

**Admin-only endpoints (all 9 must return 403 for non-admin):**
- `POST /api/system/reset/` — non-admin → 403
- `GET /api/system/reset-preview/` — non-admin → 403
- `POST /api/ai/save-api-key` — non-admin → 403
- `PUT /api/ai/prompts/{type}` — non-admin → 403
- `POST /api/ai/repair-selector` — non-admin → 403
- `POST /api/sources/{id}/toggle/` — non-admin → 403
- `POST /api/sources/bulk-toggle/` — non-admin → 403
- `PUT /api/sources/{id}/selector/` — non-admin → 403
- `POST /api/sources/test-all/` — non-admin → 403

**Admin access (all 9 must succeed for admin):**
- Same endpoints with admin user → 200/success

**Profile ownership enforcement:**
- User A cannot GET User B's recipes → 404
- User A cannot DELETE User B's recipes → 404
- User A cannot see User B's favorites → returns empty (scoped to own profile)
- User A cannot see User B's collections → returns empty
- Admin CAN see all profiles via GET /api/profiles/

**Unauthenticated access:**
- All profile-scoped endpoints return 401 without session
- Public endpoints (health, search, mode) return 200 without session

#### 7.3 Email Privacy Tests (Security-Critical)
**Files**: New `tests/test_email_privacy.py`

- **After registration, query every column of auth_user table — email field is empty string**
- **After registration, search django_session table for email string — not found**
- **After registration, search django_cache table for email string — not found**
- **Mock email backend captures sent email — verify it was sent correctly**
- **After send, verify email parameter is not retained in any object attribute**
- **Log output during registration does NOT contain the email address** (capture log output and search)

#### 7.4 Mode Switching Tests
**Files**: New `tests/test_mode.py`

- `AUTH_MODE=home`: `/api/auth/*` returns 404 (router not mounted)
- `AUTH_MODE=home`: `/api/profiles/` returns all profiles (no auth filtering)
- `AUTH_MODE=home`: `/api/profiles/` POST works (create profile without registration)
- `AUTH_MODE=public`: `/api/profiles/` POST returns 404 (must register instead)
- `AUTH_MODE=public`: `/api/profiles/{id}/select/` returns 404 (no profile switching)
- `AUTH_MODE=public`: `/api/system/mode/` returns `{"mode": "public"}`
- `AUTH_MODE=home`: `/api/system/mode/` returns `{"mode": "home"}`
- **AdminAuth in home mode behaves as SessionAuth** (no admin check)

#### 7.5 Admin CLI Tests
**Files**: New `tests/test_admin_cli.py`

- `list-users` shows all users with correct flags
- `promote <user>` sets `is_staff=True`
- `demote <user>` sets `is_staff=False`
- `demote` last admin → error (refuses)
- `reset-password <user> --generate` changes password and prints new one
- `deactivate <user>` sets `is_active=False`
- `activate <user>` sets `is_active=True`
- `cleanup-unverified` deletes only inactive users older than threshold
- `cleanup-unverified --dry-run` shows count without deleting
- All commands in home mode → error exit code 2
- Nonexistent username → error exit code 1

#### 7.6 Auto-Admin First User Tests
**Files**: `tests/test_auth.py` (additional)

- First registration on empty database → user gets `is_staff=True`
- Second registration → user gets `is_staff=False`
- If first user is deleted, next registration does NOT get auto-admin (must use CLI)

#### 7.7 Frontend Tests
**Files**: New frontend test files

- AuthContext: login sets user+profile state, logout clears it
- AuthContext: session restoration via /api/auth/me/ on mount
- Login screen: renders form, submits credentials, handles errors
- Register screen: renders form with privacy link, validates client-side, handles server errors
- Settings: admin user sees all tabs, non-admin sees only General + Account
- Router: unauthenticated user redirected to /login in public mode
- Router: authenticated user can access all protected routes
- Mode detection: home mode renders ProfileSelector, public mode renders Login

#### 7.8 Existing Test Regression
**Files**: All existing test files

- **Full test suite passes with `AUTH_MODE=home` (default) — zero modifications to existing tests**
- CI runs tests in home mode by default
- CI additionally runs auth-specific tests with `AUTH_MODE=public`

#### 7.9 Rate Limiting Tests
**Files**: New `tests/test_auth_ratelimit.py`

- Registration: 5/hour per IP enforced
- Login: 10/hour per IP enforced
- Change password: 5/hour per user enforced
- Rate limit resets correctly after window expires
- Rate limit response includes `Retry-After` header

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Django auth migration breaks existing sessions | High | Migration is additive (new tables only). Existing sessions use profile_id, not user_id |
| Email accidentally logged | High | Audit all log statements. Disable email in Django's default logging. Test by searching logs |
| Home mode regression | High | All existing tests run in home mode. Conditional loading ensures zero auth code executes |
| SES sandbox limits | Medium | Document sandbox exit process. Use console backend until approved |
| Token replay attack | Low | Single-use enforced via is_active check. 2-hour window limits exposure |
| Username enumeration via registration | Low | Rate limiting. Accepted trade-off (usernames are semi-public anyway) |

## Dependency Order

```
Phase 1 (Backend Auth Foundation)
    ↓
Phase 2 (Admin CLI) — depends on User model from Phase 1
    ↓
Phase 3 (React Frontend) — depends on auth API from Phase 1
Phase 4 (Legacy Frontend) — depends on auth API from Phase 1
    ↓ (Phase 3 & 4 can run in parallel)
Phase 5 (Privacy Policy) — independent, can run any time after Phase 1
    ↓
Phase 6 (Infrastructure) — independent of code, can run in parallel
    ↓
Phase 7 (Testing) — runs throughout, final pass after all phases
```

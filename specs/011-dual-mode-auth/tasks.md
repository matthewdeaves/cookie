# Tasks: Dual-Mode Authentication & Production Deployment

**Feature**: 011-dual-mode-auth
**Branch**: `feature/011-dual-mode-auth`
**Generated**: 2026-03-24

---

## User Story Mapping

| Story | Spec Scenario | Priority | Summary |
|-------|--------------|----------|---------|
| US1 | Scenario 1 | P1 | Mode configuration & home mode zero-regression |
| US2 | Scenarios 2, 3 | P1 | Registration & transient email verification |
| US3 | Scenario 4 | P1 | Login, session management & auth-aware SessionAuth |
| US4 | Scenarios 5, 6 | P1 | Admin permissions, CLI tool & settings segmentation |
| US5 | Scenario 7 | P2 | Account management (deletion, password change) |
| US6 | Scenario 8 | P2 | Privacy policy (UK GDPR) |
| US7 | Scenario 10 | P2 | Legacy frontend auth screens (ES5) |
| US8 | Scenario 9 | P3 | Production infrastructure (AWS, Cloudflare, backups) |

---

## Phase 1: Setup

- [ ] T001 Add `django.contrib.auth` conditionally to INSTALLED_APPS based on AUTH_MODE env var in `cookie/settings.py`
- [ ] T002 Add `AuthenticationMiddleware` conditionally to MIDDLEWARE when AUTH_MODE=public in `cookie/settings.py`
- [ ] T003 Add email backend configuration (EMAIL_BACKEND, DEFAULT_FROM_EMAIL, AWS_SES_REGION_NAME, SITE_URL) to `cookie/settings.py`
- [ ] T004 Add AUTH_PASSWORD_VALIDATORS (min length 8, common password, numeric-only checks) to `cookie/settings.py`
- [ ] T005 [P] Add `django-ses` to `requirements.txt`
- [ ] T006 [P] Add AUTH_MODE environment variable to `docker-compose.yml` and `docker-compose.prod.yml`

---

## Phase 2: Foundation (Blocking — Must Complete Before User Stories)

- [ ] T007 Add nullable `user` OneToOneField(settings.AUTH_USER_MODEL) to Profile model in `apps/profiles/models.py`
- [ ] T008 Generate and verify migration for Profile.user field in `apps/profiles/migrations/`
- [ ] T009 Refactor SessionAuth to be mode-aware (home: profile_id session lookup, public: request.user→profile) in `apps/core/auth.py`
- [ ] T010 Add AdminAuth subclass of SessionAuth (home: same as SessionAuth, public: additionally checks is_staff) in `apps/core/auth.py`
- [ ] T011 Add GET /api/system/mode/ endpoint returning {"mode": "home"|"public"} in `apps/core/api.py`
- [ ] T012 Create email verification service with send_verification_email(user_id, email) using TimestampSigner in `apps/core/email_service.py`
- [ ] T013 Create verification token generation and validation helpers (sign, unsign with 2h max_age) in `apps/core/email_service.py`
- [ ] T014 Create email templates (HTML + plaintext) for verification email in `apps/core/templates/core/verification_email.html` and `apps/core/templates/core/verification_email.txt`
- [ ] T015 Create verification failed HTML template in `apps/core/templates/core/verification_failed.html`

### Foundation Tests

- [ ] T016 Write tests for mode-aware SessionAuth (home mode: profile_id lookup unchanged, public mode: request.user→profile) in `tests/test_auth.py`
- [ ] T017 Write tests for AdminAuth (home mode: same as SessionAuth, public mode: checks is_staff) in `tests/test_auth.py`
- [ ] T018 Write test for GET /api/system/mode/ returning correct mode in `tests/test_mode.py`
- [ ] T019 Write tests for token generation/validation (valid, expired, tampered, already-used) in `tests/test_auth.py`

---

## Phase 3: US1 — Mode Configuration & Home Mode Regression

**Goal**: AUTH_MODE=home (default) runs identically to current behavior. Zero auth code executes.

**Independent test criteria**: All existing tests pass with AUTH_MODE=home. Auth endpoints return 404 in home mode.

### US1 Tests

- [ ] T020 [US1] Write test: home mode is default when AUTH_MODE not set, django.contrib.auth NOT in INSTALLED_APPS, AuthenticationMiddleware NOT in MIDDLEWARE in `tests/test_mode.py`
- [ ] T021 [US1] Write test: AUTH_MODE=home, /api/auth/* returns 404 (router not mounted) in `tests/test_mode.py`
- [ ] T022 [US1] Write test: AUTH_MODE=home, /api/profiles/ GET returns all profiles (no auth filtering) in `tests/test_mode.py`
- [ ] T023 [US1] Write test: AUTH_MODE=home, /api/profiles/ POST creates profile without registration in `tests/test_mode.py`
- [ ] T024 [US1] Write test: AUTH_MODE=home, AdminAuth behaves identically to SessionAuth (no admin check) in `tests/test_mode.py`
- [ ] T025 [US1] Run full existing test suite with AUTH_MODE=home — verify zero failures in `tests/`

---

## Phase 4: US2 — Registration & Email Verification

**Goal**: Users can register with username/password/email, receive verification email, and activate their account. Email is never stored.

**Independent test criteria**: Register → receive email → click link → account active. User.email is always empty string.

- [ ] T028 [US2] Create auth API router with Django Ninja in `apps/core/auth_api.py`
- [ ] T029 [US2] Implement POST /api/auth/register/ endpoint (create User with is_active=False, auto-create Profile, send verification email, discard email) in `apps/core/auth_api.py`
- [ ] T030 [US2] Add username validation (3-30 chars, ^[a-zA-Z0-9_]+$, case-insensitive uniqueness) to register endpoint in `apps/core/auth_api.py`
- [ ] T031 [US2] Add password validation using Django's AUTH_PASSWORD_VALIDATORS in register endpoint in `apps/core/auth_api.py`
- [ ] T032 [US2] Add stale registration replacement (if username exists, is_active=False, date_joined >2h ago → replace) in `apps/core/auth_api.py`
- [ ] T033 [US2] Implement auto-admin first user logic (if no active users exist, set is_staff=True) in `apps/core/auth_api.py`
- [ ] T034 [US2] Implement GET /api/auth/verify-email/?token= endpoint (unsign token, activate user, redirect to login) in `apps/core/auth_api.py`
- [ ] T035 [US2] Add rate limiting to register endpoint (5/hour per IP) in `apps/core/auth_api.py`
- [ ] T036 [US2] Conditionally mount auth router only when AUTH_MODE=public in `cookie/urls.py`
- [ ] T036b [US2] Add cleanup-unverified management command (delete inactive users older than 24h, --dry-run) in `apps/core/management/commands/cleanup_unverified.py`
- [ ] T036c [US2] Add cleanup-unverified to entrypoint scripts (only when AUTH_MODE=public) in `entrypoint.sh` and `entrypoint.prod.sh`

### US2 Tests

- [ ] T037 [US2] Write test: successful registration creates inactive user with empty email field in `tests/test_auth.py`
- [ ] T038 [US2] Write test: after registration, User.email == "" (proves email not stored) in `tests/test_auth.py`
- [ ] T039 [US2] Write test: registration with taken username returns 400 in `tests/test_auth.py`
- [ ] T040 [US2] Write test: registration with weak password returns 400 in `tests/test_auth.py`
- [ ] T041 [US2] Write test: registration with mismatched passwords returns 400 in `tests/test_auth.py`
- [ ] T042 [US2] Write test: registration with privacy_accepted=false returns 400 in `tests/test_auth.py`
- [ ] T043 [US2] Write test: registration with invalid email returns 400 in `tests/test_auth.py`
- [ ] T044 [US2] Write test: valid verification token activates user in `tests/test_auth.py`
- [ ] T045 [US2] Write test: expired verification token (>2h) returns error in `tests/test_auth.py`
- [ ] T046 [US2] Write test: tampered verification token returns error in `tests/test_auth.py`
- [ ] T047 [US2] Write test: already-used token (user already active) redirects to login in `tests/test_auth.py`
- [ ] T048 [US2] Write test: first registration auto-promotes to admin (is_staff=True) in `tests/test_auth.py`
- [ ] T049 [US2] Write test: second registration does NOT get auto-admin in `tests/test_auth.py`
- [ ] T050 [US2] Write test: stale inactive registration replaced when re-registering same username in `tests/test_auth.py`

### US2 Email Privacy Tests (Security-Critical)

- [ ] T051 [US2] Write test: after registration, search all auth_user columns — email field is empty string in `tests/test_email_privacy.py`
- [ ] T052 [US2] Write test: after registration, search django_session table for email string — not found in `tests/test_email_privacy.py`
- [ ] T053 [US2] Write test: mock email backend captures sent email — verify it was sent correctly in `tests/test_email_privacy.py`
- [ ] T054 [US2] Write test: log output during registration does NOT contain the email address in `tests/test_email_privacy.py`

### US2 Rate Limiting Tests

- [ ] T055 [US2] Write test: 6th registration attempt from same IP returns 429 in `tests/test_auth_ratelimit.py`

---

## Phase 5: US3 — Login, Session & Auth-Aware API

**Goal**: Verified users can log in, get a session, and access profile-scoped endpoints. Unverified/deactivated users cannot.

**Independent test criteria**: Login with valid credentials → session established → profile-scoped endpoints return user's data.

- [ ] T056 [US3] Implement POST /api/auth/login/ endpoint (authenticate, set Django session + profile_id, return user+profile) in `apps/core/auth_api.py`
- [ ] T057 [US3] Implement POST /api/auth/logout/ endpoint (flush session) in `apps/core/auth_api.py`
- [ ] T058 [US3] Implement GET /api/auth/me/ endpoint (return current user+profile for session restoration) in `apps/core/auth_api.py`
- [ ] T059 [US3] Add rate limiting to login endpoint (10/hour per IP) in `apps/core/auth_api.py`
- [ ] T060 [US3] Update profile list endpoint: in public mode return only current user's profile (admin sees all) in `apps/profiles/api.py`
- [ ] T061 [US3] Disable profile creation endpoint in public mode (profiles created via /auth/register) in `apps/profiles/api.py`
- [ ] T062 [US3] Disable profile select endpoint in public mode (no profile switching) in `apps/profiles/api.py`

### US3 Tests

- [ ] T062b [US3] Write test: SESSION_COOKIE_AGE remains 43200 (12 hours) in both modes in `tests/test_mode.py`
- [ ] T063 [US3] Write test: correct credentials returns 200 with user+profile data in `tests/test_auth.py`
- [ ] T064 [US3] Write test: wrong password returns 401 with generic message in `tests/test_auth.py`
- [ ] T065 [US3] Write test: nonexistent username returns 401 with same generic message in `tests/test_auth.py`
- [ ] T066 [US3] Write test: unverified account returns 403 in `tests/test_auth.py`
- [ ] T067 [US3] Write test: deactivated account returns 403 in `tests/test_auth.py`
- [ ] T068 [US3] Write test: successful logout clears session in `tests/test_auth.py`
- [ ] T069 [US3] Write test: GET /api/auth/me/ returns current user after login in `tests/test_auth.py`
- [ ] T070 [US3] Write test: GET /api/auth/me/ returns 401 when not logged in in `tests/test_auth.py`
- [ ] T071 [US3] Write test: /api/profiles/ in public mode returns only own profile in `tests/test_permissions.py`
- [ ] T072 [US3] Write test: /api/profiles/ POST returns 404 in public mode in `tests/test_permissions.py`
- [ ] T073 [US3] Write test: /api/profiles/{id}/select/ returns 404 in public mode in `tests/test_permissions.py`

### US3 Rate Limiting Tests

- [ ] T074 [US3] Write test: 11th failed login attempt from same IP returns 429 in `tests/test_auth_ratelimit.py`

---

## Phase 6: US4 — Admin Permissions, CLI & Settings Segmentation

**Goal**: Admin-only endpoints return 403 for non-admins. CLI tool manages users. Settings UI hides admin sections.

**Independent test criteria**: Non-admin → 403 on all 9 admin endpoints. CLI promote/demote/reset-password work. Settings API returns is_admin flag.

- [ ] T075 [US4] Replace auth=SessionAuth() with auth=AdminAuth() on system reset endpoints in `apps/core/api.py`
- [ ] T076 [US4] Replace auth=SessionAuth() with auth=AdminAuth() on AI admin endpoints (test-api-key, save-api-key, prompts PUT, repair-selector) in `apps/ai/api.py`
- [ ] T077 [US4] Replace auth=SessionAuth() with auth=AdminAuth() on source admin endpoints (toggle, bulk-toggle, selector PUT, test-all) in `apps/recipes/sources_api.py`
- [ ] T078 [P] [US4] Add sources-needing-attention and test endpoints to AdminAuth in `apps/ai/api.py` and `apps/recipes/sources_api.py`
- [ ] T079 [P] [US4] Add cache/health endpoint to AdminAuth in `apps/recipes/api.py`
- [ ] T080 [US4] Create cookie_admin management command with subcommand dispatch in `apps/core/management/commands/cookie_admin.py`
- [ ] T081 [US4] Implement list-users subcommand (table format, --active-only, --admins-only, --json) in `apps/core/management/commands/cookie_admin.py`
- [ ] T082 [US4] Implement promote subcommand (set is_staff=True, handle already-admin) in `apps/core/management/commands/cookie_admin.py`
- [ ] T083 [US4] Implement demote subcommand (set is_staff=False, refuse if last admin) in `apps/core/management/commands/cookie_admin.py`
- [ ] T084 [US4] Implement reset-password subcommand (interactive, --password, --generate) in `apps/core/management/commands/cookie_admin.py`
- [ ] T085 [US4] Implement activate and deactivate subcommands in `apps/core/management/commands/cookie_admin.py`
- [ ] T086 [US4] Add cleanup-unverified as a cookie_admin subcommand alias (delegates to cleanup_unverified command) in `apps/core/management/commands/cookie_admin.py`
- [ ] T087 [US4] Add mode validation to all cookie_admin subcommands (exit code 2 if home mode) in `apps/core/management/commands/cookie_admin.py`
- [ ] T089 [US4] Include is_admin flag in profile API responses (GET /api/profiles/ and /api/auth/me/) in `apps/profiles/api.py` and `apps/core/auth_api.py`
- [ ] T090 [US4] Update Settings.tsx to show admin-only tabs (Prompts, Sources, Selectors, Users, Danger) only when is_admin=true in `frontend/src/screens/Settings.tsx`
- [ ] T091 [US4] Add Account settings section for public mode (change password, delete account) in `frontend/src/components/settings/SettingsAccount.tsx`
- [ ] T092 [US4] Hide API key section in SettingsGeneral for non-admins in public mode in `frontend/src/components/settings/SettingsGeneral.tsx`

### US4 Permission Tests (Security-Critical)

- [ ] T093 [US4] Write test: POST /api/system/reset/ returns 403 for non-admin in `tests/test_permissions.py`
- [ ] T094 [US4] Write test: GET /api/system/reset-preview/ returns 403 for non-admin in `tests/test_permissions.py`
- [ ] T095 [US4] Write test: POST /api/ai/save-api-key returns 403 for non-admin in `tests/test_permissions.py`
- [ ] T096 [US4] Write test: PUT /api/ai/prompts/{type} returns 403 for non-admin in `tests/test_permissions.py`
- [ ] T097 [US4] Write test: POST /api/ai/repair-selector returns 403 for non-admin in `tests/test_permissions.py`
- [ ] T098 [US4] Write test: POST /api/sources/{id}/toggle/ returns 403 for non-admin in `tests/test_permissions.py`
- [ ] T099 [US4] Write test: POST /api/sources/bulk-toggle/ returns 403 for non-admin in `tests/test_permissions.py`
- [ ] T100 [US4] Write test: PUT /api/sources/{id}/selector/ returns 403 for non-admin in `tests/test_permissions.py`
- [ ] T101 [US4] Write test: POST /api/sources/test-all/ returns 403 for non-admin in `tests/test_permissions.py`
- [ ] T102 [US4] Write test: all 9 admin endpoints return 200/success for admin user in `tests/test_permissions.py`
- [ ] T103 [US4] Write test: User A cannot access User B's recipes/favorites/collections in `tests/test_permissions.py`
- [ ] T104 [US4] Write test: admin can see all profiles via GET /api/profiles/ in `tests/test_permissions.py`
- [ ] T105 [US4] Write test: unauthenticated access to profile-scoped endpoints returns 401 in `tests/test_permissions.py`

### US4 CLI Tests

- [ ] T106 [US4] Write test: list-users shows correct user flags in `tests/test_admin_cli.py`
- [ ] T107 [US4] Write test: promote sets is_staff=True in `tests/test_admin_cli.py`
- [ ] T108 [US4] Write test: demote sets is_staff=False in `tests/test_admin_cli.py`
- [ ] T109 [US4] Write test: demote last admin is refused in `tests/test_admin_cli.py`
- [ ] T110 [US4] Write test: reset-password --generate changes password in `tests/test_admin_cli.py`
- [ ] T111 [US4] Write test: deactivate/activate toggle is_active in `tests/test_admin_cli.py`
- [ ] T112 [US4] Write test: cleanup-unverified deletes only old inactive users in `tests/test_admin_cli.py`
- [ ] T113 [US4] Write test: cleanup-unverified --dry-run shows count without deleting in `tests/test_admin_cli.py`
- [ ] T114 [US4] Write test: all subcommands in home mode exit with code 2 in `tests/test_admin_cli.py`

---

## Phase 7: US5 — Account Management

**Goal**: Users can change password and delete their account. Account deletion is comprehensive (CASCADE).

**Independent test criteria**: Password change works. Account deletion removes User + Profile + all scoped data.

- [ ] T115 [US5] Implement POST /api/auth/change-password/ endpoint in `apps/core/auth_api.py`
- [ ] T116 [US5] Add rate limiting to change-password endpoint (5/hour per user) in `apps/core/auth_api.py`
- [ ] T117 [US5] Update profile DELETE endpoint to cascade delete User in public mode, require confirmation_text="DELETE" in request body in `apps/profiles/api.py`
- [ ] T118 [US5] Invalidate session immediately after account deletion in `apps/profiles/api.py`

### US5 Tests

- [ ] T119 [US5] Write test: change password with correct current password succeeds in `tests/test_auth.py`
- [ ] T120 [US5] Write test: change password with wrong current password returns 400 in `tests/test_auth.py`
- [ ] T121 [US5] Write test: change password with weak new password returns 400 in `tests/test_auth.py`
- [ ] T122 [US5] Write test: account deletion removes User, Profile, recipes, favorites, collections in `tests/test_auth.py`
- [ ] T123 [US5] Write test: session is invalidated after account deletion in `tests/test_auth.py`
- [ ] T124 [US5] Write test: change-password rate limit (6th attempt returns 429) in `tests/test_auth_ratelimit.py`

---

## Phase 8: US6 — Privacy Policy

**Goal**: UK GDPR-compliant privacy policy page accessible at /privacy/ without authentication.

**Independent test criteria**: GET /privacy/ returns 200 with privacy content. Page is accessible without auth.

- [ ] T125 [P] [US6] Create privacy policy HTML template (standalone, no JS dependency) in `apps/core/templates/core/privacy_policy.html`
- [ ] T126 [US6] Write privacy policy content covering: data collected, data NOT collected, legal basis, retention, deletion rights, cookies, contact in `apps/core/templates/core/privacy_policy.html`
- [ ] T127 [US6] Create privacy policy view (TemplateView, no auth required) in `apps/core/views.py`
- [ ] T128 [US6] Add /privacy/ URL route in `cookie/urls.py`

### US6 Tests

- [ ] T129 [US6] Write test: GET /privacy/ returns 200 without authentication in `tests/test_auth.py`
- [ ] T130 [US6] Write test: privacy page contains required UK GDPR elements in `tests/test_auth.py`

---

## Phase 9: US7 — Legacy Frontend Auth Screens

**Goal**: Legacy ES5 frontend has login, registration, and mode-aware routing. All auth flows work on iOS 9 Safari.

**Independent test criteria**: Legacy login/register templates render. Forms submit to same API endpoints. ES5 only (no const/let/arrow).

- [ ] T131 [P] [US7] Create legacy login template (ES5 JS, form, error/success messages) in `apps/legacy/templates/legacy/login.html`
- [ ] T132 [P] [US7] Create legacy registration template (ES5 JS, form with privacy link+checkbox, validation) in `apps/legacy/templates/legacy/register.html`
- [ ] T133 [US7] Create login_view and register_view in `apps/legacy/views.py`
- [ ] T134 [US7] Update legacy URL routing: in public mode root URL → login (not profile_selector) in `apps/legacy/urls.py`
- [ ] T135 [US7] Update @require_profile decorator: in public mode redirect to login instead of profile_selector in `apps/legacy/views.py`
- [ ] T136 [US7] Add @require_admin decorator for admin-only legacy settings pages in `apps/legacy/views.py`
- [ ] T137 [US7] Update legacy settings template/JS to hide admin tabs for non-admins in `apps/legacy/templates/legacy/settings.html` and `apps/legacy/static/legacy/js/pages/settings-init.js`
- [ ] T138 [US7] Add is_admin to legacy template context in legacy views in `apps/legacy/views.py`

---

## Phase 10: US8 — React Frontend Auth Screens

**Goal**: React frontend has login, registration, AuthContext, and mode-aware routing.

**Independent test criteria**: Mode detection renders Login (public) or ProfileSelector (home). Auth flows complete end-to-end.

- [ ] T139 [US8] Create AuthContext with user/profile/isAdmin state and login/logout/register methods in `frontend/src/contexts/AuthContext.tsx`
- [ ] T140 [US8] Add mode detection in App.tsx (call /api/system/mode/, render AuthContext or ProfileContext) in `frontend/src/App.tsx`
- [ ] T141 [P] [US8] Create Login screen (username/password form, forgot password text, link to register, error display, ?verified=true message) in `frontend/src/screens/Login.tsx`
- [ ] T142 [P] [US8] Create Register screen (form with privacy link+checkbox, client-side validation, success/error states) in `frontend/src/screens/Register.tsx`
- [ ] T143 [US8] Update router: public mode routes (/login, /register) and auth-required redirects in `frontend/src/router.tsx`
- [ ] T144 [US8] Add /api/auth/* methods to API client in `frontend/src/api/client.ts`
- [ ] T145 [US8] Add auth types (AuthUser, LoginRequest, RegisterRequest, etc.) in `frontend/src/api/types.ts`

### US8 Frontend Tests

- [ ] T146 [US8] Write test: AuthContext login sets user+profile state in `frontend/src/test/contexts.test.tsx`
- [ ] T147 [US8] Write test: AuthContext logout clears state in `frontend/src/test/contexts.test.tsx`
- [ ] T148 [US8] Write test: AuthContext session restoration via /api/auth/me/ on mount in `frontend/src/test/contexts.test.tsx`
- [ ] T149 [US8] Write test: Login screen renders form and handles errors in `frontend/src/test/Login.test.tsx`
- [ ] T150 [US8] Write test: Register screen renders form with privacy link in `frontend/src/test/Register.test.tsx`
- [ ] T151 [US8] Write test: Settings shows admin tabs only for admin user in `frontend/src/test/Settings.test.tsx`
- [ ] T152 [US8] Write test: Router redirects unauthenticated user to /login in public mode in `frontend/src/test/contexts.test.tsx`
- [ ] T153 [US8] Write test: Mode detection renders ProfileSelector in home mode in `frontend/src/test/contexts.test.tsx`

---

## Phase 11: Production Infrastructure (US9)

**Goal**: Cookie deployed on a cloud VPS with Cloudflare, email service, and automated backups.

**Independent test criteria**: docker-compose.prod.yml includes all new env vars. Backup script runs. Nginx config supports HTTPS.

- [ ] T154 [P] Update docker-compose.prod.yml with AUTH_MODE, SITE_URL, email, and logging environment variables in `docker-compose.prod.yml`
- [ ] T155 [P] Update nginx prod config: add SSL with Cloudflare Origin Certificate, redirect HTTP→HTTPS in `nginx/nginx.prod.conf`
- [ ] T156 [P] Create database backup script (pg_dump | gzip + configurable upload target) in `bin/backup-db`
- [ ] T157 [P] Create VPS deployment guide (provider-agnostic: server setup, firewall, Docker install) in `docs/DEPLOYMENT.md`
- [ ] T158 [P] Create Cloudflare setup guide (DNS, Origin Cert, SSL mode, cache rules) in `docs/CLOUDFLARE-SETUP.md`
- [ ] T159 [P] Create email service setup guide (SES + generic SMTP instructions) in `docs/EMAIL-SETUP.md`
- [ ] T160 [P] Create backup/restore documentation (storage options, retention, restore procedure) in `docs/BACKUP-RESTORE.md`

---

## Phase 12: Logging & Monitoring

**Goal**: Structured JSON logging in production, CloudWatch integration, email scrubbing guaranteed.

- [ ] T161 Add LOG_FORMAT and LOG_LEVEL environment variables to `cookie/settings.py`
- [ ] T162 Create JSON log formatter class for production (timestamp, level, logger, message, extra fields) in `apps/core/logging.py`
- [ ] T163 Update LOGGING dict: use JSON formatter when LOG_FORMAT=json (include request_id from middleware), text formatter when LOG_FORMAT=text in `cookie/settings.py`
- [ ] T164 Add security event logging for auth events (login success/failure, registration, verification, rate limits) in `apps/core/auth_api.py`
- [ ] T165 Set django.core.mail logger to CRITICAL to prevent email content leaking into logs in `cookie/settings.py`
- [ ] T166 Add request_id middleware to attach unique ID to each request for log correlation in `apps/core/middleware.py`
- [ ] T167 Update nginx prod config: add JSON access log format, output to /dev/stdout in `nginx/nginx.prod.conf`
- [ ] T168 Add awslogs logging driver configuration to docker-compose.prod.yml (log groups: /cookie/web, /cookie/db) in `docker-compose.prod.yml`
- [ ] T169 Add CloudWatch Logs IAM permissions to deployment guide in `docs/AWS-DEPLOYMENT.md`
- [ ] T170 [P] Document CloudWatch Logs Insights queries (failed logins, error rate, registration) in `docs/MONITORING.md`
- [ ] T171 [P] Document CloudWatch Alarms setup (high error rate, login spikes) in `docs/MONITORING.md`

### Logging Tests

- [ ] T172 Write test: failed login log does NOT contain username (prevents enumeration) in `tests/test_email_privacy.py`
- [ ] T174 Write test: JSON formatter produces valid JSON with required fields in `tests/test_logging.py`
- [ ] T175 Write test: security events are logged at correct levels in `tests/test_logging.py`

---

## Phase 13: Polish & Cross-Cutting

- [ ] T176 Audit all log statements to ensure email addresses are never logged — grep all files in `apps/`
- [ ] T177 Add CI configuration: run tests with AUTH_MODE=home (default) AND AUTH_MODE=public in `.github/workflows/ci.yml`
- [ ] T178 Update CLAUDE.md with new AUTH_MODE configuration, logging, and auth-related commands
- [ ] T179 Run ruff and eslint to verify code quality limits (functions <100 lines, complexity <15, files <500 lines) across all modified files

---

## Dependency Graph

```
Phase 1 (Setup: T001-T006)
    ↓
Phase 2 (Foundation: T007-T019)
    ↓
Phase 3 (US1 Mode Config: T020-T027) ←── validates home mode before proceeding
    ↓
Phase 4 (US2 Registration: T028-T055) ←── needs auth foundation
    ↓
Phase 5 (US3 Login: T056-T074) ←── needs register endpoint
    ↓
Phase 6 (US4 Admin: T075-T114) ←── needs login + user model
    │
    ├── Phase 7 (US5 Account Mgmt: T115-T124) ←── needs auth endpoints
    ├── Phase 8 (US6 Privacy: T125-T130) ←── independent, can run any time
    ├── Phase 9 (US7 Legacy FE: T131-T138) ←── needs auth API
    └── Phase 10 (US8 React FE: T139-T153) ←── needs auth API

Phase 11 (Infrastructure: T154-T160) ←── independent, can run in parallel with Phases 3-10

Phase 12 (Logging/Monitoring: T161-T175) ←── after Phase 2, parallel with Phases 3-10
    ↓
Phase 13 (Polish: T176-T179) ←── after all other phases
```

## Parallel Execution Opportunities

| Phase | Parallelizable Tasks | Why |
|-------|---------------------|-----|
| Phase 1 | T005, T006 | Different files (requirements.txt vs docker-compose) |
| Phase 2 | T014, T015 | Template files, no code dependencies |
| Phase 6 | T075-T079 | Different API files, same AdminAuth pattern |
| Phase 6 | T078, T079 | Different API files |
| Phase 8 | T125 | Template only, no Python dependencies |
| Phase 9 | T131, T132 | Separate templates |
| Phase 10 | T141, T142 | Separate React screen components |
| Phase 11 | T154-T160 | All infrastructure tasks are independent files |

## Implementation Strategy

**MVP (Minimum Viable)**: Phases 1-5 (T001-T074)
- Mode switching works
- Registration + email verification + login functional
- Backend fully auth-aware
- Can test end-to-end with console email backend

**Full Feature**: Add Phases 6-10 (T075-T153)
- Admin permissions enforced
- CLI tool for admin operations
- Both frontends have auth screens
- Privacy policy in place

**Production Ready**: Add Phases 11-13 (T154-T179)
- AWS infrastructure configured
- Cloudflare + SES operational
- Automated backups
- Structured logging + CloudWatch
- CI pipeline updated

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 179 |
| **Setup + Foundation** | 19 tasks |
| **US1 (Mode Config)** | 8 tasks |
| **US2 (Registration)** | 28 tasks |
| **US3 (Login)** | 19 tasks |
| **US4 (Admin/Permissions)** | 40 tasks |
| **US5 (Account Mgmt)** | 10 tasks |
| **US6 (Privacy Policy)** | 6 tasks |
| **US7 (Legacy FE)** | 8 tasks |
| **US8 (React FE)** | 15 tasks |
| **Infrastructure** | 7 tasks |
| **Logging/Monitoring** | 15 tasks |
| **Polish** | 4 tasks |
| **Test tasks** | 83 (46% of total) |
| **Parallel opportunities** | 20 tasks across 9 groups |

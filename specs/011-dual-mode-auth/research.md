# Research: Dual-Mode Authentication & Production Deployment

## Decision 1: User Model Strategy

**Decision**: Add Django's built-in `auth.User` model alongside the existing `Profile` model. Link them with an optional `OneToOneField` on Profile.

**Rationale**:
- Profile stays unchanged — home mode is completely unaffected
- Django's User model provides battle-tested password hashing (PBKDF2 by default), username validation, and `is_active` / `is_staff` / `is_superuser` flags
- The `is_active` flag maps directly to email verification (inactive until verified)
- The `is_staff` flag maps to admin status
- No need to reinvent password hashing, session authentication, or user management
- Profile keeps all recipe/preference data; User is purely for authentication

**Alternatives considered**:
- Custom User model extending AbstractUser — unnecessary complexity, Django's built-in User has everything needed
- Replacing Profile with User — breaks home mode, Profile has recipe-specific fields (avatar_color, theme, unit_preference)
- Adding auth fields directly to Profile — mixes concerns, harder to keep home mode clean

## Decision 2: Conditional Django Auth Loading

**Decision**: Use `AUTH_MODE` environment variable. In `settings.py`, conditionally add `django.contrib.auth` to `INSTALLED_APPS` and `AuthenticationMiddleware` to `MIDDLEWARE` only when `AUTH_MODE=public`.

**Rationale**:
- Spec requires "zero authentication code executes in home mode"
- Django doesn't query auth tables if `django.contrib.auth` is not in INSTALLED_APPS
- Conditional INSTALLED_APPS is a well-supported Django pattern
- Both modes use the same database schema (auth tables exist but are unused in home mode)

**Alternatives considered**:
- Always load auth, just don't enforce it — violates spec requirement for zero auth code in home mode
- Separate settings files — more files to maintain, easy to get out of sync
- Feature flag in middleware — still loads auth, just bypasses it

## Decision 3: SessionAuth Adapter for Dual Mode

**Decision**: Modify `SessionAuth` to work in both modes. In home mode, it checks `profile_id` in session (current behavior). In public mode, it checks Django's `request.user` and resolves the linked Profile.

**Rationale**:
- Single auth class used by all endpoints
- Endpoints don't need to know which mode they're running in
- The `AdminAuth` subclass adds `is_staff` check on top
- Clean separation: SessionAuth resolves profile, AdminAuth additionally checks admin

**Implementation sketch**:
- Home mode: `session["profile_id"]` → Profile lookup (unchanged)
- Public mode: `request.user.is_authenticated` → `request.user.profile` (OneToOne)

## Decision 4: Email Verification via Signed Tokens

**Decision**: Use `django.core.signing.TimestampSigner` with the user's `pk` encoded. Token is URL-safe, signed with SECRET_KEY, expires in 2 hours. Stateless — no database table for tokens.

**Rationale**:
- No database storage needed for tokens (no cleanup jobs)
- SECRET_KEY rotation invalidates all outstanding tokens (acceptable for 2-hour window)
- `TimestampSigner` includes timestamp in the signature, so expiry is verified on validation
- Single-use enforcement: check `user.is_active`; if already True, token was already used

**Token format**: `base64(user_pk):timestamp:signature`

**Alternatives considered**:
- Database-stored tokens — unnecessary complexity, requires cleanup
- JWT — overkill, adds dependency, same capability as Django signing
- UUID tokens in database — requires table, expiry cron, etc.

## Decision 5: Admin CLI via Django Management Commands

**Decision**: Implement admin operations as Django management commands (`manage.py cookie_admin`), invocable via `docker compose exec web python manage.py cookie_admin <subcommand>`.

**Rationale**:
- Django management commands are the standard pattern for admin CLI operations
- Already runs inside Docker (consistent with project rules)
- Remote execution: `ssh user@server docker compose exec web python manage.py cookie_admin promote username`
- Sub-commands: `promote`, `demote`, `reset-password`, `list-users`, `deactivate`
- No additional authentication needed — if you have server access, you're authorized

**Alternatives considered**:
- Separate HTTP API for admin — adds attack surface, needs its own auth
- Django admin panel — too much UI complexity for 5 operations
- Standalone script — less integrated, harder to share Django ORM context

## Decision 6: Email Backend Configuration

**Decision**: Use Django's built-in email framework with `EMAIL_BACKEND` configurable via environment variable. Default to console backend in development.

**Rationale**:
- Django has native support for SMTP, console, file, and in-memory email backends
- `django-ses` package adds AWS SES support as a drop-in backend
- Console backend shows emails in Docker logs during development — zero config needed
- Production: set `EMAIL_BACKEND=django_ses.SESBackend` + IAM role on EC2

**Environment variables**:
- `EMAIL_BACKEND` (default: `django.core.mail.backends.console.EmailBackend`)
- `DEFAULT_FROM_EMAIL` (default: `noreply@cookie.matthewdeaves.com`)
- `AWS_SES_REGION_NAME` (only for SES, default: `eu-west-2` for UK)

## Decision 7: Frontend Auth Flow

**Decision**: In public mode, the React router replaces `ProfileSelector` with `Login` and `Register` screens. A new `AuthContext` wraps `ProfileContext`, providing `user`, `isAdmin`, `login()`, `logout()`, `register()`.

**Rationale**:
- `ProfileContext` continues to work — it just gets its profile from the User→Profile link instead of direct selection
- `AuthContext` is only rendered in public mode (conditional in App.tsx based on `/api/system/mode` endpoint)
- Legacy frontend: login/register templates replace profile_selector template
- Both frontends call the same `/api/auth/*` endpoints

## Decision 8: Privacy Policy Implementation

**Decision**: Static HTML page served by Django template (not React SPA). Available at `/privacy/` (both frontends). No JavaScript required.

**Rationale**:
- Must be accessible without JavaScript (accessibility, legal requirement)
- Static content — no API calls, no dynamic data
- Django template ensures it works for both modern and legacy browsers
- Linked from registration form and footer

## Decision 9: Production Infrastructure

**Decision**: EC2 t4g.small running existing `docker-compose.prod.yml` with Cloudflare Origin Certificate and AWS SES via IAM role.

**Rationale**:
- Reuses existing production container exactly as-is
- t4g.small (2GB RAM) fits Cookie + PostgreSQL comfortably (~$13.70/mo, ~$8.76 with RI)
- Cloudflare handles SSL, CDN, DDoS — free plan sufficient
- SES is free from EC2 (62,000 emails/month)
- S3 for backups is effectively free at this scale
- Same architecture supports additional sites via nginx virtual hosts

**New infrastructure components**:
- Cron job: `pg_dump | gzip | aws s3 cp` (daily backup)
- IAM role: SES SendEmail + S3 PutObject to backup bucket
- Security group: SSH from admin IP, HTTP/HTTPS from Cloudflare IPs only
- Cloudflare Origin Certificate installed in nginx

## Decision 10: Mode Detection API

**Decision**: Add `GET /api/system/mode/` endpoint (public, no auth) returning `{"mode": "home"}` or `{"mode": "public"}`. Frontend uses this to determine which screens to render.

**Rationale**:
- Frontend needs to know the mode before rendering login vs profile selector
- Single source of truth (backend setting)
- Cacheable (mode doesn't change without restart)
- Also useful for health monitoring and debugging

## Decision 11: Profile Listing in Public Mode

**Decision**: In public mode, `GET /api/profiles/` returns only the current user's profile (not all profiles). Admin can see all profiles.

**Rationale**:
- Current behavior (list all profiles) is designed for household use where everyone sees everyone
- In public mode, users should not see other users' profiles
- Admin needs to see all for user management
- This is a behavioral change scoped to public mode only

## Decision 12: Verification Endpoint Routing

**Decision**: Verification link points to `/api/auth/verify-email/?token=xxx` which validates the token, activates the user, then redirects to the frontend login page with a success query parameter.

**Rationale**:
- Backend handles all token validation (no frontend JavaScript needed to verify)
- Redirect to frontend login page provides good UX
- Works in any browser (even email client web views)
- Legacy browsers get redirected to `/legacy/` login after verification via the existing device detection

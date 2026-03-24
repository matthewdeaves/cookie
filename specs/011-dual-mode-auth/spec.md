# Feature Specification: Dual-Mode Authentication & Production Deployment

**Feature ID**: 011-dual-mode-auth
**Created**: 2026-03-24
**Status**: Ready for Planning

---

## Problem Statement

Cookie is a self-hosted recipe manager designed for household use, where anyone on the local network can create and manage profiles without credentials. To make Cookie available on the public internet (e.g., at `cookie.matthewdeaves.com`), the application needs a second operating mode that provides proper user authentication, role-based access control, and privacy-respecting email verification — while preserving the existing frictionless experience for home/self-hosted deployments.

Additionally, Cookie currently has no production hosting infrastructure. A secure, cost-effective deployment strategy is needed to host Cookie publicly, with the ability to support additional sites on the same infrastructure in the future.

## Goals

1. **Dual-mode operation**: Cookie runs in either "home" mode (current profile-only behavior) or "public" mode (full authentication with username/password accounts)
2. **Privacy-first email verification**: Confirm new accounts are created by real humans with valid email addresses, without ever storing the email address — not even as a hash — in the database or on disk
3. **Role-based access control**: In public mode, restrict site-wide administrative operations (API keys, search sources, AI prompts, database reset) to designated administrators
4. **UK GDPR compliance**: Provide a clear, accurate privacy policy accessible from the registration page, fully compliant with UK data protection law
5. **Secure, affordable production hosting**: Deploy Cookie on AWS infrastructure at minimal cost (~$10-15/month), with proper SSL, DDoS protection, and automated backups
6. **Multi-site readiness**: Infrastructure should support hosting additional small web applications alongside Cookie in the future

## Non-Goals

- Social features (user-to-user sharing, public recipe pages, following)
- OAuth/social login (Google, Facebook, etc.) — may be added later but not in scope
- Multi-tenancy (multiple independent Cookie instances per deployment)
- Custom domain per user or white-labeling
- Paid subscription tiers or monetization features
- Mobile app packaging (PWA or native)
- Automated horizontal scaling or load balancing

## User Personas

### Home User (Existing)
A household member using Cookie on a local network or private server. They select a profile by name, no credentials needed. Everyone in the household trusts each other. All settings are accessible to everyone.

### Public User (New)
An individual who discovers Cookie online, creates an account with a username and password, verifies their email, and uses the app to manage their own recipes. They can only see and modify their own data. They cannot access site-wide settings.

### Site Administrator (New — Public Mode Only)
The person who hosts Cookie publicly. They have full access to all settings: API keys, AI prompt configuration, search source management, and the database reset function. They can also view and manage all user accounts.

## User Scenarios & Testing

### Scenario 1: Home Mode — Unchanged Behavior
**Given** Cookie is running in home mode
**When** a person visits the application
**Then** they see the profile selector (no login screen)
**And** they can create a new profile with just a name and color
**And** all settings pages are fully accessible
**And** no registration, login, or email verification flows exist

**Acceptance Criteria:**
- Home mode is the default when no mode is explicitly configured
- Zero authentication code executes in home mode (no Django auth middleware, no User model queries)
- All existing tests continue to pass without modification
- No visible UI changes compared to current behavior

### Scenario 2: Public Mode — New User Registration
**Given** Cookie is running in public mode
**When** a new visitor arrives at the application
**Then** they see a login screen (not the profile selector)
**And** they can navigate to a registration form
**And** the registration form requires: username, password, password confirmation, email address
**And** the registration form displays a link to the privacy policy
**And** the registration form includes a checkbox to acknowledge the privacy policy
**When** they submit valid registration details
**Then** they see a message: "Check your email to verify your account"
**And** the email address is used to send a verification link and is then immediately discarded (not written to any database table, file, log, or hash)
**And** their account is created but inactive (cannot log in yet)

**Acceptance Criteria:**
- Email address appears in zero database columns, zero log files, zero temporary files on disk — not even as a hash
- No email-derived data of any kind is persisted
- Password meets minimum security requirements (at least 8 characters, not entirely numeric, not a common password)
- Username is unique, case-insensitive, alphanumeric with underscores (3-30 characters)
- Registration is rate-limited to prevent abuse (same email can register multiple accounts — accepted trade-off for absolute privacy)

### Scenario 3: Public Mode — Email Verification
**Given** a user has just registered
**When** they click the verification link in their email
**Then** their account becomes active
**And** they are redirected to the login page with a success message
**And** the verification link expires after a set time period
**And** an expired or already-used link shows a clear error message

**Acceptance Criteria:**
- Verification tokens are cryptographically signed with a 2-hour expiration
- Each token can only be used once
- Expired tokens display a helpful message explaining the user must register again
- Verification works across different devices/browsers (not session-dependent)

### Scenario 4: Public Mode — Login and Session
**Given** a verified user visits Cookie in public mode
**When** they enter their username and password
**Then** they are logged in and see their personal recipe dashboard
**And** a profile is automatically associated with their account (1:1 relationship)
**And** they can only see their own recipes, favorites, collections, and history

**Acceptance Criteria:**
- Login is rate-limited to prevent brute-force attacks
- Failed login attempts are logged (without leaking whether the username exists)
- Session timeout matches current behavior (12 hours)
- "Remember me" is not required for initial implementation

### Scenario 5: Public Mode — Password Reset (Admin-Assisted)
**Given** a user has forgotten their password
**When** they see the login screen
**Then** they see a message directing them to contact the site administrator
**And** no self-service password reset is available (since no email is stored)

**Given** an administrator wants to reset a user's password
**When** they run the admin CLI tool with the target username
**Then** a new temporary password is generated or the user's password is set to a specified value
**And** the user can log in with the new password

**Acceptance Criteria:**
- No self-service password reset exists (impossible without stored email)
- Login screen displays clear instructions for contacting the administrator
- Admin CLI can reset any user's password
- The CLI is usable on the server via `docker compose exec` or remotely via SSH

### Scenario 6: Public Mode — Admin vs Regular User
**Given** a regular user is logged into public mode
**When** they visit the settings page
**Then** they see only their personal settings (theme, unit preference, account management)
**And** they do NOT see: API key configuration, AI prompt editing, search source management, database reset, or other users' profiles

**Given** an administrator is logged into public mode
**When** they visit the settings page
**Then** they see all settings including site-wide configuration
**And** they can manage all user accounts

**Acceptance Criteria:**
- Regular users receive 403 Forbidden when attempting admin-only API endpoints
- Admin status is not self-assignable (must be set via the admin CLI tool)
- The first account created on a fresh public-mode deployment is automatically an administrator
- Subsequent admin promotions/demotions are done exclusively via the CLI (no UI for this)
- Settings UI dynamically shows/hides sections based on user role

### Scenario 7: Public Mode — Account Deletion
**Given** a user wants to delete their account
**When** they request account deletion from their settings
**Then** all their data is permanently removed: user account, profile, recipes, favorites, collections, view history, AI-generated content
**And** no trace of the account remains in the database
**And** the action requires confirmation

**Acceptance Criteria:**
- Deletion is irreversible and comprehensive (CASCADE delete)
- User receives confirmation that deletion is complete
- The deleted user's session is invalidated immediately

### Scenario 8: Privacy Policy Page
**Given** any visitor (logged in or not) in public mode
**When** they navigate to the privacy policy page
**Then** they see a clear, readable privacy policy that explains:
- What data is collected (username, hashed password, recipe data, preferences)
- What is NOT collected (email addresses, tracking data, analytics, advertising data)
- How data is used (solely to provide the recipe management service)
- Data retention and deletion rights
- That only functional session cookies are used (no tracking cookies)
- Contact information for data concerns
- The legal basis for processing (legitimate interest and consent)

**Acceptance Criteria:**
- Privacy policy is accessible without an account
- Privacy policy is linked from the registration page
- Content complies with UK GDPR (UK Data Protection Act 2018) and PECR
- Privacy policy is a static page (no dynamic content that could break)

### Scenario 9: Infrastructure — Production Deployment
**Given** Cookie is deployed on AWS
**When** a user visits `cookie.matthewdeaves.com`
**Then** the connection is encrypted (HTTPS via Cloudflare)
**And** pages load within 3 seconds (p95)
**And** the database is automatically backed up daily
**And** verification emails are delivered reliably via AWS SES

**Acceptance Criteria:**
- Total monthly infrastructure cost is under $15
- SSL/TLS is terminated at Cloudflare (no certificate management on the server)
- SSH access is restricted to the administrator's IP address
- Database backups are stored off-instance (S3) and retained for at least 30 days
- The server can host additional sites alongside Cookie via virtual host routing

### Scenario 10: Dual-Frontend Support
**Given** Cookie runs in public mode
**When** a user accesses Cookie from a modern browser
**Then** they see the React-based login/registration screens

**When** a user accesses Cookie from an older browser (iOS 9 Safari)
**Then** they see the legacy ES5-compatible login/registration screens
**And** all authentication flows work identically

**Acceptance Criteria:**
- Legacy frontend login/registration uses only ES5 JavaScript (no const, let, arrow functions, template literals)
- Both frontends communicate with the same authentication API endpoints
- Browser detection and routing continues to work as currently implemented

## Functional Requirements

### FR-1: Mode Configuration
- The application operating mode is controlled by an environment variable
- Two modes are supported: "home" (default) and "public"
- Mode affects authentication requirements, available UI, and permission enforcement
- Switching modes requires a restart (not hot-swappable)
- In home mode, no authentication-related code is loaded or executed

### FR-2: User Account System (Public Mode)
- User accounts consist of: unique username, hashed password, admin flag, active flag, associated profile, creation timestamp
- No email address or email-derived data is stored in any form
- Each user account has exactly one profile (created automatically at registration)
- Passwords are hashed using a secure, industry-standard algorithm
- Username uniqueness is enforced case-insensitively
- The first user created on a fresh deployment is automatically an administrator

### FR-3: Transient Email Verification
- During registration, the email address is used solely to send a verification link
- The email is held in memory only for the duration of the HTTP request that sends the verification email
- Zero email data is written to the database, log files, or any persistent storage
- The verification token is cryptographically signed with a 2-hour expiration
- The token encodes the user ID and is validated server-side
- After verification, the account becomes active
- If the token expires, the user must register again (no resend mechanism, since the email is not stored)

### FR-4: Admin CLI Tool
- A Django management command for site administration, invoked via `docker compose exec` on the server or remotely via SSH
- Server/SSH access is the authentication mechanism — no additional auth layer needed
- Supports: promoting/demoting users to admin, resetting user passwords, listing users, deactivating accounts
- No self-service password reset exists (since no email is stored)

### FR-5: Permission Enforcement (Public Mode)
- API endpoints are categorized as: public (no auth), authenticated (any logged-in user), or admin-only
- Admin-only endpoints: database reset, API key management, AI prompt editing, search source management, user account management
- Authenticated endpoints enforce profile ownership (users can only access their own data)
- Unauthenticated requests to protected endpoints return 401
- Non-admin requests to admin endpoints return 403

### FR-6: Settings Page Segmentation (Public Mode)
- The settings UI is divided into user-level and admin-level sections
- Regular users see: personal preferences (theme, units), account management (password change, account deletion)
- Administrators additionally see: API key configuration, AI prompts, search sources, source selectors, user management, database reset
- Section visibility is determined by the authenticated user's role

### FR-7: Privacy Policy
- A static privacy policy page is available at a dedicated URL
- The policy covers all UK GDPR requirements for the data Cookie collects
- The registration form links to the policy and requires acknowledgement
- The policy is accessible without authentication

### FR-8: Email Delivery Configuration
- Email sending is configurable via environment variables
- Supported backends: AWS SES (production), SMTP (generic), console (development)
- In development/home mode, no email configuration is required
- Email templates are simple, plain-text with an HTML alternative
- Sender address is configurable via `DEFAULT_FROM_EMAIL`
- Site base URL is configurable via `SITE_URL` environment variable (used to build verification links)

### FR-9: Production Infrastructure
- Application runs on a single cloud VPS (any provider: Hetzner, AWS EC2, DigitalOcean, etc.) with Docker Compose
- Cloudflare (free plan) handles SSL termination, CDN caching, and DDoS protection
- DNS points the custom domain to the server via Cloudflare
- Database backups run automatically on a daily schedule to off-server object storage
- The server's network access is restricted to necessary ports and source IPs (SSH from admin IP only, HTTP/HTTPS from Cloudflare IPs)
- The infrastructure supports virtual-host-based routing for multiple sites via nginx
- Provider choice is deployment-time decision — code is provider-agnostic

### FR-10: Automated Backup
- PostgreSQL database is backed up daily via automated scheduled task
- Backups are compressed and stored in cloud object storage
- Backup retention is at least 30 days
- A restore procedure is documented

### FR-11: Logging & Monitoring
- Application logs are structured (JSON) in production for machine parsing
- Container logs flow to the cloud hosting service's log management (e.g., CloudWatch)
- Email addresses MUST NEVER appear in any log output — enforced by configuration and automated tests
- Security events (login, registration, verification, rate limits, permission denials) are logged at appropriate levels
- Failed login attempts do NOT log the attempted username (prevents enumeration via log access)
- Each request has a unique correlation ID for tracing across log entries
- Log retention is at least 30 days in the cloud log service
- Alerting is configured for error spikes and unusual login failure patterns

## Key Entities

### User (New — Public Mode Only)
- Username (unique, case-insensitive)
- Password (hashed)
- Active flag (set to true after email verification)
- Admin flag (first user is auto-admin)
- Associated Profile (1:1 relationship)
- Date created

### Profile (Existing — Modified)
- All existing fields unchanged
- New optional link to User (populated in public mode, null in home mode)

### Verification Token (Transient)
- Encoded user ID
- Cryptographic signature
- Expiration timestamp
- Not persisted in database (stateless, signed tokens)

## Dependencies

- Email delivery service (AWS SES or equivalent SMTP provider)
- Cloud hosting infrastructure (compute, storage, object storage for backups)
- CDN/proxy service for SSL and DDoS protection (Cloudflare)
- DNS configuration for custom domain

## Assumptions

1. **Single-server deployment**: Cookie does not need horizontal scaling. One server handles all traffic.
2. **Low user volume**: Expected users in the tens or low hundreds, not thousands. This informs rate limiting and infrastructure sizing decisions.
3. **Admin bootstrapping**: The first registered user becomes admin automatically. Additional admins are promoted exclusively via the admin CLI tool.
4. **Absolute email privacy**: No email data of any kind (plaintext, hashed, encrypted, or derived) is ever persisted. The same email can be used for multiple registrations — this is an accepted trade-off for maximum privacy.
5. **No self-service recovery**: Since no email is stored, there is no password reset flow and no "what email did I register with?" feature. Users must remember their username. Admins can reset passwords via CLI.
6. **Session-based auth**: Public mode uses Django's built-in session-based authentication (not JWT). This is consistent with the existing session infrastructure.
7. **Legacy browser parity**: Both React and legacy ES5 frontends support all authentication flows. The legacy frontend is not a second-class citizen.
8. **Cloudflare free tier**: The CDN/proxy service's free plan provides sufficient features (SSL, basic DDoS, DNS).
9. **ARM-based compute**: Using ARM-based cloud instances for ~20% cost savings over x86 equivalents.
10. **Docker Compose in production**: The existing Docker Compose setup is adapted for production deployment rather than introducing container orchestration.

## Constraints

- Email addresses must NEVER be stored in the database, log files, or any persistent storage on the server
- Legacy frontend code must be ES5 compatible (iOS 9.3 Safari)
- All backend commands run inside Docker containers (no host Python/Django)
- Monthly hosting cost must remain under $15
- Privacy policy must comply with UK Data Protection Act 2018 (UK GDPR) and PECR
- Mode switching must not require database migrations (both modes use the same schema)
- Home mode must have zero performance impact from authentication code

## Success Criteria

1. **Mode switching works cleanly**: An operator can switch between home and public mode with a single environment variable change and restart, with no data loss or migration required
2. **Registration-to-login flow completes in under 5 minutes**: A new user can register, receive a verification email, verify their account, and log in within 5 minutes (assuming email delivery within 60 seconds)
3. **Zero stored emails**: A database dump, file system search, and log review of a production deployment reveals zero email addresses or email-derived data in any form
4. **Admin operations are inaccessible to regular users**: Automated tests confirm that every admin-only endpoint returns 403 for non-admin users in public mode
5. **Both frontends fully functional**: All authentication flows (register, verify, login, logout, settings) work on both React and legacy ES5 frontends
6. **Privacy policy passes ICO checklist**: The privacy policy addresses all items on the UK ICO's "Write a privacy notice" checklist
7. **Infrastructure cost under $15/month**: Monthly AWS bill remains under $15 for Cookie running with normal usage
8. **99.5% uptime**: Cookie is accessible at least 99.5% of the time over any 30-day period (allows ~3.6 hours downtime/month for maintenance)
9. **Backup restore verified**: A documented restore procedure can recover the database from backup within 30 minutes
10. **Home mode regression-free**: All existing tests pass without modification when running in home mode

## Resolved Decisions

1. **Verification token expiry**: 2 hours. If expired, user must register again (no resend — email is not stored).
2. **No password reset flow**: Impossible without stored email. Admins reset passwords via CLI tool. Login screen directs users to contact admin.
3. **Admin promotion**: CLI tool only (no UI). Simplest, most secure. Runnable from server or remotely.
4. **No email storage of any kind**: No plaintext, no hash, no encrypted form. Email exists only in memory during the verification request. Same email can register multiple accounts — accepted trade-off for absolute privacy.
5. **Account deletion**: Complete erasure. User account, profile, and all associated data removed. No email-derived data to worry about.

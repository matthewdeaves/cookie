<!--
Sync Impact Report
Version: 1.0.0 → 1.2.0
Changed principles: III renamed "Dual-Mode Operation" → "Multi-Mode Operation", added passkey mode rules
Added: mode-specific endpoint/UI hiding rule, Responsible Development governance section
Follow-up TODOs: none
-->

# Cookie Project Constitution

**Version**: 1.2.0
**Ratified**: 2026-03-24
**Last Amended**: 2026-03-28

## Preamble

Cookie is a self-hosted recipe manager built on the belief that software should
work for everyone — regardless of device age, network access, or technical
sophistication. It pairs a modern React frontend with a legacy ES5 frontend so
that a 2024 iPhone and a 2012 iPad can use the same application with the same
features. AI enhances the experience but is never required. Users own their data.
Privacy is not a setting; it is the architecture.

---

## Principle I: Multi-Generational Device Access

Every feature MUST work on both the modern frontend (React 19, TypeScript,
ES2020+) and the legacy frontend (vanilla ES5, CSS3 with iOS 9.3 Safari
compatibility). Neither frontend is a "fallback" or degraded experience.

**Rules:**
- Legacy frontend code in `apps/legacy/static/legacy/js/` MUST use only ES5
  syntax: `var` (not `const`/`let`), `function` (not arrows), string
  concatenation (not template literals), no destructuring, no classes, no
  `async`/`await`.
- Legacy CSS MUST avoid features unsupported by iOS 9 Safari: no CSS Grid, no
  custom properties (`var(--x)`), no `gap` on flexbox, no `position: sticky`.
  Use `-webkit-` prefixed flexbox.
- Images served to legacy browsers MUST be JPEG or PNG (WebP is not supported
  on iOS 9).
- Touch targets MUST be at least 44x44px per Apple Human Interface Guidelines.
- New features that cannot be implemented in ES5 MUST still have a functional
  (potentially simplified) legacy equivalent — never a blank page or error.
- The legacy frontend is not a second-class citizen. When modifying visual/UI
  elements, both frontends MUST maintain visual coherence.

**Rationale:** Accessibility means literal access. Old iPads persist in
households. Financial constraints and hardware lifecycle mean older devices
outlive their marketing support. Cookie refuses to exclude them.

---

## Principle II: Privacy by Architecture

User privacy MUST be enforced by system design, not policy promises. Data that
is not collected cannot be leaked.

**Rules:**
- Email addresses MUST NEVER be stored in the database, log files, temporary
  files, or any persistent storage — not even as a hash. During registration
  (public mode), email exists only in memory for the duration of the HTTP
  request that sends the verification link.
- No telemetry, analytics, or tracking of any kind. No third-party scripts.
- Only functional session cookies are used. No tracking cookies. No cookie
  consent banner is needed under UK PECR because no non-essential cookies exist.
- All user data (recipes, favorites, collections, history) is scoped to the
  user's profile and deleted completely on account deletion.
- Logs MUST NEVER contain email addresses. Failed login logs MUST NOT contain
  the attempted username (prevents enumeration via log access).
- The privacy policy MUST accurately reflect what is and is not collected,
  comply with UK Data Protection Act 2018 (UK GDPR), and be accessible without
  authentication.

**Rationale:** Users trust Cookie with their recipes and family data. That trust
is maintained by making privacy violations architecturally impossible, not merely
prohibited by policy.

---

## Principle III: Multi-Mode Operation

Cookie MUST support multiple operating modes, controlled by a single environment
variable (`AUTH_MODE`), with clean separation between them.

**Rules:**
- **Home mode** (`AUTH_MODE=home`, default): Profile-only, no credentials
  required. Anyone on the network can create and select profiles. All settings
  are accessible to all users. Zero authentication code executes — no Django
  auth middleware, no User model queries.
- **Public mode** (`AUTH_MODE=public`): Full username/password authentication
  with email verification. Users can only access their own data. Site-wide
  settings (API keys, AI prompts, search sources, database reset) are restricted
  to administrators. Admin promotion is done exclusively via CLI.
- **Passkey mode** (`AUTH_MODE=passkey`): WebAuthn passkey-only authentication.
  No username, email, or password. Users authenticate via biometrics (Face ID,
  Touch ID, Windows Hello). Legacy devices that lack WebAuthn support pair via
  a temporary device authorization code entered on an authenticated modern
  device. Zero personal information is stored — only a random UUID and public
  keys. Admin promotion is done exclusively via CLI.
- Switching modes requires only an environment variable change and restart —
  no database migration, no data loss.
- All existing home-mode functionality MUST remain unchanged when new mode
  code is added. Existing tests MUST pass without modification in home mode.
- Mode-specific endpoints MUST return 404 when accessed in the wrong mode.
  Mode-specific UI MUST be hidden entirely in other modes.

**Rationale:** Cookie serves multiple audiences: families on a home server (where
authentication adds friction without security value), individuals on the public
internet (where traditional authentication is essential), and privacy-conscious
users who want the strongest possible authentication with zero personal data
disclosure. One codebase, multiple modes, zero compromise.

---

## Principle IV: AI as Enhancement, Not Dependency

AI features MUST enhance the user experience without being required for core
functionality. The application MUST be fully usable without any AI configuration.

**Rules:**
- When the OpenRouter API key is not configured or API calls fail, AI-dependent
  UI elements MUST be hidden completely — never shown as disabled, greyed out,
  or with error banners.
- AI prompts are user-customizable via the Settings UI (admin-only in public
  mode). Default prompts are seeded via database migrations.
- Serving adjustment is AI-only because ingredient parsing is genuinely hard
  (ambiguous quantities, non-scalable instructions). Do not attempt frontend
  math fallback.
- AI-generated content (remixes, tips, suggestions) is per-profile, not shared.
- Background AI tasks (selector repair) run asynchronously and never block
  user-facing requests.

**Rationale:** A recipe manager without AI is still a recipe manager. AI
amplifies good UX but does not replace it. Users without API keys should not
feel that they are using an incomplete product.

---

## Principle V: Code Quality Gates Are Immutable

Quality limits exist to prevent bugs, not to be negotiated. When code exceeds
limits, the code is refactored — the limits are never raised.

**Rules:**
- Maximum function length: 100 lines (prefer 50).
- Maximum cyclomatic complexity: 15 per function.
- Maximum file size: 500 lines.
- NEVER raise thresholds in linter configs (`eslint.config.js`, ruff config).
- NEVER add `# noqa`, `// eslint-disable`, or equivalent suppression comments
  to bypass quality checks.
- When limits are exceeded: extract helper functions, split into modules, apply
  Single Responsibility Principle.
- CI MUST block PRs that exceed these limits. No exceptions.

**Rationale:** Studies show cyclomatic complexity >15 correlates exponentially
with defect rates. Functions over 100 lines cannot be understood without
scrolling. Files over 500 lines do too much. These limits are load-bearing
constraints, not aspirational targets.

---

## Principle VI: Docker Is the Runtime

The host machine has no Python, Django, Node.js, or npm installed. ALL backend
and frontend commands MUST run inside Docker containers.

**Rules:**
- Backend commands: `docker compose exec web python -m pytest`, `docker compose
  exec web python manage.py migrate`, etc.
- Frontend commands: `docker compose exec frontend npm test`, `docker compose
  exec frontend npm run lint`, etc.
- Only `git`, `docker`, `docker compose`, `gh`, and basic file operations
  (`ls`, `cat`, `grep`) run on the host.
- After any change to `apps/legacy/static/`, containers MUST be restarted
  (`docker compose down && docker compose up -d`) because `collectstatic` runs
  on container start.

**Rationale:** Consistency across development, CI, and production. No "works on
my machine" failures. Identical environment everywhere.

---

## Principle VII: Security by Default

Security is infrastructure, not a feature. Safe patterns are the default;
unsafe patterns require explicit justification.

**Rules:**
- Django ORM only — no raw SQL with string interpolation. `raw()` MUST use
  `%s` parameter placeholders, never f-strings.
- Django templates auto-escape by default. `|safe` and `{% autoescape off %}`
  MUST NOT be used on user-controlled content.
- React JSX auto-escapes by default. `dangerouslySetInnerHTML` MUST NOT be
  used unless content is sanitized with DOMPurify.
- CSRF protection is enabled globally. All POST/PUT/DELETE requests include
  CSRF tokens.
- URLs are validated before scraping (SSRF protection). Only `http://` and
  `https://` schemes allowed. Localhost and internal IPs are blocked.
- No secrets in git. `detect-secrets` runs as a pre-commit hook.
- Session cookies: `Secure` (in production), `HttpOnly`, `SameSite=Lax`.
- File uploads validated by content (not just extension). Size limits enforced.
- PostgreSQL required in all environments (no SQLite fallback).
- Rate limiting on all authentication and AI endpoints.

**Rationale:** Developers can verify security locally. Safe defaults mean
vulnerabilities require deliberate (and reviewable) opt-out, not accidental
omission.

---

## Governance

### Amendment Procedure

1. Propose amendment with rationale (issue or PR description).
2. Review against existing principles for conflicts.
3. If adopted, increment version:
   - **MAJOR**: Principle removed, redefined, or made backward-incompatible.
   - **MINOR**: New principle added or existing principle materially expanded.
   - **PATCH**: Clarification, wording improvement, or non-semantic refinement.
4. Update `Last Amended` date.
5. Propagate changes to dependent artifacts (spec templates, plan templates,
   task templates, CLAUDE.md rules).

### Compliance Review

- All feature specifications (`/speckit.specify`) MUST include a Constitution
  Check section validating alignment with each applicable principle.
- All implementation plans (`/speckit.plan`) MUST include a Constitution Check
  table showing compliance status per principle.
- CI pipelines enforce Principles V (code quality), VI (Docker runtime), and
  VII (security) automatically.
- Principles I (device access), II (privacy), III (multi-mode), and IV (AI
  enhancement) are validated during code review and QA.

### Responsible Development

Developers (human and AI) working on this project MUST fix pre-existing issues
as they encounter them. Ignoring broken linting, failing hooks, stale configs,
or tooling incompatibilities is not acceptable.

**Rules:**
- When a pre-commit hook, CI job, or linter fails on pre-existing code, fix the
  root cause before proceeding. Never skip hooks or suppress errors as a
  workaround.
- When running tests reveals pre-existing warnings or failures unrelated to your
  change, investigate and fix them if the fix is safe and bounded.
- When encountering stale dependencies, outdated configs, or broken tooling,
  update them as part of the current work — do not defer to a separate ticket.
- Leave the codebase healthier than you found it. Every change is an opportunity
  to improve quality, not just add features.

**Rationale:** Technical debt compounds. Small issues left unfixed become large
issues that block progress. A culture of "fix what you see" prevents decay and
keeps CI green for everyone.

---

## Amendment History

| Version | Date | Change | Type |
|---------|------|--------|------|
| 1.2.0 | 2026-03-28 | Added Responsible Development section to Governance — developers must fix pre-existing issues as they work. | MINOR |
| 1.1.0 | 2026-03-28 | Principle III expanded from "Dual-Mode" to "Multi-Mode" to add passkey authentication mode. | MINOR |
| 1.0.0 | 2026-03-24 | Initial constitution. 7 principles codified from existing project rules and codebase analysis. | MAJOR |

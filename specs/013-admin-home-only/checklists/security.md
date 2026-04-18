# Security Checklist: 013-admin-home-only

**Purpose**: Pre-implementation security gate for a feature whose entire purpose is hardening attack surface.
**Created**: 2026-04-18
**Feature**: [spec.md](../spec.md)
**Informed by**: HexStrike scan 2026-04-18 findings; constitution Principles II, III, VII; `.claude/rules/django-security.md`; `.claude/rules/react-security.md`.

## Threat model coverage

- [x] SEC-01 **Admin REST surface in passkey mode is zero**: every endpoint in `contracts/gated-endpoints.md` returns `404 {"detail":"Not found"}` with no fingerprint. Verified via T004.
- [x] SEC-02 **No auth-failure log line leaks endpoint existence**: `HomeOnlyAdminAuth.__call__` raises 404 before cookie extraction (T002); assertion T004 uses `caplog` on `security_logger`.
- [x] SEC-03 **Version string not returned publicly**: `GET /api/system/mode/` drops `version` key (T061, T062).
- [x] SEC-04 **Admin UI is not rendered in passkey mode**: both frontends hide sections (T013 asserts SPA; T025–T027 for legacy).

## API key handling

- [x] SEC-05 **API key never logged**: `security_logger.warning("cookie_admin set-api-key: key changed")` — no value. Verified by T033's `caplog` assertion.
- [x] SEC-06 **API key never echoed**: CLI never prints the key back after save; `set-api-key --stdin` reads silently.
- [x] SEC-07 **Empty key rejected**: T033 asserts empty string (key or stdin) → exit 2 with clear error, no DB write. Prevents accidental wipe.
- [x] SEC-08 **Encryption at rest preserved**: CLI writes via the `@openrouter_api_key` property setter, which encrypts. T033 round-trips through the property.

## CSRF / session / transport

- [x] SEC-09 **CSRF untouched on gated endpoints**: `HomeOnlyAdminAuth` does not change CSRF semantics; home-mode CSRF flow unchanged (existing test coverage).
- [x] SEC-10 **Session cookie behavior unchanged**: no `SessionAuth` or cookie-config edits.
- [x] SEC-11 **Rate-limit preserved on reset**: T011 keeps the `@ratelimit(key="ip", rate="1/h")` and `getattr(request, "limited", False)` check on `POST /api/system/reset/`.

## SSRF / input validation

- [x] SEC-12 **`sources repair` does not bypass SSRF protection**: uses the same helper as the HTTP handler, which already validates URLs before scraping. T043 covers happy + missing-key paths.
- [x] SEC-13 **`sources test` does not bypass SSRF protection**: T053 factoring routes both CLI and HTTP through `apps/recipes/services/source_health.py` that enforces URL validation.
- [x] SEC-14 **`prompts set --system-file` / `--user-file` cannot read arbitrary host files used to write database values**: yes — the CLI runs as the operator on the host; file reading is inherent to the CLI's trust boundary. Documented limitation, not a vulnerability. Prompt bodies are not logged.

## Audit log hygiene

- [x] SEC-15 **Mutating subcommands emit one `security_logger.warning`**: verified per-subcommand (T033..T046). Read-only subcommands emit none.
- [x] SEC-16 **Logged fields are non-sensitive**: API keys never logged; selector strings not logged (T041); prompt bodies not logged (T038); user/profile names in rename log are low-sensitivity admin data.
- [x] SEC-17 **No enumeration aid in passkey mode**: 404 body matches Ninja's default for unknown paths (`HttpError(404, "Not found")` → `{"detail": "Not found"}`).

## Constitution principle spot-checks

- [x] CON-01 **Principle II (Privacy by Architecture)**: No new data collected. `rename` does not touch email or any PII field (email is architecturally absent).
- [x] CON-02 **Principle III (Dual-Mode)**: This feature is the concrete implementation of "mode-specific endpoints MUST return 404; mode-specific UI MUST be hidden".
- [x] CON-03 **Principle V (Code Quality)**: `cookie_admin.py` split (T058) moves the already-oversized file into compliant modules; no linter thresholds raised; no suppression comments added.
- [x] CON-04 **Principle VII (Security by Default)**: Django ORM only (no raw SQL added); no `|safe` introduced; CSRF defaults preserved; rate-limit preserved on reset; new auth class raises `HttpError(404)` (no information disclosure).

## Test hardening

- [x] TST-01 **Passkey-mode 404 test asserts BOTH status and body**: T004 checks `== 404` AND `body == {"detail":"Not found"}`.
- [x] TST-02 **Log silence assertion**: T004 asserts no new `security_logger` lines during 404 probes.
- [x] TST-03 **CLI security-log assertions**: each mutating subcommand test asserts one warning is emitted; each read-only subcommand test asserts zero.
- [x] TST-04 **API key not in test snapshots**: T033 asserts the log record does NOT contain the sample key value.

## Release hygiene

- [x] REL-01 **Version bump is semantic MINOR**: `1.41.0 → 1.42.0` per repo convention for security hardening (T063).
- [x] REL-02 **Release notes include Security heading**: T073 scaffolds the release with the three SEC-01/SEC-03/SEC-04 bullets.
- [x] REL-03 **No `.env` / secret files touched**: T063 edits only `cookie/settings.py` default value.

## Open follow-ups (out of scope but tracked)

- [ ] FU-01 **Authenticated re-scan**: after release, run HexStrike (or equivalent) with valid passkey-mode admin creds against the hardened deployment. Record that no admin paths are discovered. (Per spec Out-of-scope; belongs in the appserver-repo pentest config.)
- [ ] FU-02 **`SECURE_PROXY_SSL_HEADER` / HTTP redirect**: infra-repo concern. Not in this feature's scope.

## Notes

- Checklist items map 1:1 to tasks or test assertions so CI-visible failures trace back to the responsible line. No item is "verify manually" alone.
- Re-run this checklist during code review; if any `[x]` turns into `[ ]` during implementation, block the PR.

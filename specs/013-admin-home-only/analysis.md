# Specification Analysis Report — 013-admin-home-only

**Date**: 2026-04-18
**Artifacts scanned**: spec.md, plan.md, tasks.md, research.md, data-model.md, contracts/*.md, constitution.md

## Findings

| ID | Category | Severity | Location | Summary | Recommendation | Status |
|----|----------|----------|----------|---------|----------------|--------|
| C1 | Constitution Alignment | HIGH | `apps/core/management/commands/cookie_admin.py` (710 lines pre-change) | Principle V caps Python files at 500 lines. `cookie_admin.py` is already 710 lines pre-change; adding ~18 subcommand handlers would push it past 1000. | Split into a package as part of this feature. | RESOLVED — T058 rewritten to mandate the split + T058a wiring verification; T067 validates post-split line counts. |
| A1 | Ambiguity | MEDIUM | spec.md Clarifications Q1 — "home_mode_only name kept as shorthand" | Spec uses the name `home_mode_only` as shorthand while plan/tasks/research all refer to `HomeOnlyAdminAuth`. Readers of spec-only may hunt for a non-existent decorator. | Spec Clarifications note already directs readers to the class; plan explicitly rules out the decorator approach. Acceptable as-is. | ACCEPT |
| I1 | Inconsistency | MEDIUM | tasks.md T053 (original) — "factor out the shared helper into a services/ module if duplication is non-trivial" | "if" makes the decision conditional on reviewer judgment, which invites duplication. | Decide definitively: always factor out. | RESOLVED — T053 rewritten to mandate `apps/recipes/services/source_health.py`. |
| M1 | Coverage | LOW | spec.md FR-007 (`GET /api/profiles/` unchanged) | No task explicitly asserts GET /api/profiles/ staying unchanged. | Implicit coverage via T012 (full backend suite green) is adequate. | ACCEPT |
| M2 | Coverage | LOW | spec.md FR-036 (home-mode logs unchanged) | No explicit log-diff test, relies on full suite. | Adequate — the 18 gated endpoints have existing home-mode tests that assert response shape; log-line assertions would be high-churn. | ACCEPT |
| I2 | Inconsistency | LOW | tasks.md T005 vs FR-040 | T005 updates "existing tests expecting 403" — FR-040 says "existing home-mode tests MUST pass unchanged". | The refactored tests are passkey-mode codifying the old inline 403 block (soon deleted). FR-040 scope is home-mode only. | ACCEPT — no action |
| U1 | Underspecification | LOW | tasks.md T058 subcommand module split | What does the `Command` class do if Django's loader doesn't accept a package? | Django has supported management-command packages since at least 3.0 (module exporting `Command` is sufficient). No issue. | ACCEPT |
| A2 | Ambiguity | LOW | spec.md FR-031 | `rename <user_id_or_username>` — what if in passkey mode the positional is all-digits AND also happens to be a username? | Decide precedence in implementation: try `int()` → `User.pk`; on failure fall back to `User.username`. Recorded in T056. | ACCEPT |
| C2 | Constitution Alignment | — (PASS) | Principles I (device access), II (privacy), III (dual-mode), IV (AI), V (quality — now resolved), VI (Docker), VII (security) | All rows PASS with C1 resolved. | — | PASS |

## Coverage Summary

All 46 requirements (FR-001..FR-042 + FR-017a, FR-027a, FR-032a, FR-032b) have at least one task. All 7 Success Criteria have at least one task or explicit quickstart verification step. No unmapped tasks.

| Requirement | Task IDs |
|-------------|----------|
| FR-001 HomeOnlyAdminAuth | T002 |
| FR-002 mode check before auth | T002, T003, T004 |
| FR-003 18 endpoints gated | T006, T007, T008, T009, T010, T011 |
| FR-004 home-mode unchanged | T001, T012 (full suite) |
| FR-005 delete inline 403 blocks | T011 |
| FR-006 AdminAuth unchanged | T002 (subclass, not modify) |
| FR-007 profiles/ unchanged | implicit via T012 |
| FR-008 dead helper removal | T011 |
| FR-009 version key removed | T061, T062 |
| FR-010 settings.html | T025 |
| FR-011 nav_header.html | T027 |
| FR-012 template-side only | (no-op) — decision encoded in spec; no task modifies `apps/legacy/views.py` |
| FR-013 SPA sections hidden | T015, T016, T017, T018, T019, T020, T021, T022, T023 |
| FR-014 user-self-service sections kept | T013 asserts their presence |
| FR-015 useMode from router.tsx | T015 |
| FR-016 hide not tree-shake | implicit |
| FR-017 set-api-key | T033, T048 |
| FR-017a empty rejected | T033, T048 |
| FR-018 test-api-key | T034, T049 |
| FR-019 set-default-model | T035, T050 |
| FR-020 prompts list | T036, T051 |
| FR-021 prompts show | T037, T051 |
| FR-022 prompts set | T038, T051 |
| FR-023 sources list | T039, T052 |
| FR-024 sources toggle | T040, T052 |
| FR-025 sources toggle-all | T040, T052 |
| FR-026 sources set-selector | T041, T052 |
| FR-027 sources test | T042, T053 |
| FR-027a exit/shape | T042, T053 |
| FR-028 sources repair | T043, T054 |
| FR-029 quota show | T044, T055 |
| FR-030 quota set | T044, T055 |
| FR-031 rename | T045, T056 |
| FR-032 security_logger hygiene | every test/impl pair |
| FR-032a mode-agnostic new subcommands | T045 tests both modes |
| FR-032b passkey guard refactor | T031, T047 |
| FR-033 --help lists all | T060, T058a |
| FR-034 status cache block | T032, T046, T057 |
| FR-035 no auth-log in 404 | T004 |
| FR-036 home-mode logs unchanged | implicit |
| FR-037 version 1.42.0 | T063 |
| FR-038 release notes | T073 |
| FR-039 per-endpoint 404 test | T004 |
| FR-040 home-mode tests unchanged | T012 |
| FR-041 CLI tests per subcommand | T033..T046 |
| FR-042 SPA component test | T013 |
| SC-001..SC-007 | covered by tests + quickstart T072 |

## Metrics

- Total Functional Requirements: 46 (FR-001..FR-042 + 4 sub-letters)
- Total Tasks: 74 (T001..T073 + T058a)
- Coverage %: 100% (every FR has >=1 task)
- Ambiguity count: 2 (both LOW)
- Duplication count: 0
- Critical issues count: 0 after remediation (C1 HIGH resolved, no CRITICALs remain)

## Constitution alignment

PASS. Principle V resolved via mandatory cookie_admin split (T058). All other principles PASS as documented in plan.md.

## Next actions

No CRITICAL or HIGH issues remain after remediation. Ready for `/speckit.checklist` (security-focused) and then `/speckit.implement`.

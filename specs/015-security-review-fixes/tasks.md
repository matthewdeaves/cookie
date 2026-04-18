---
description: "Task list for Security Review Fixes (Round 2) — trimmed scope"
---

# Tasks: Security Review Fixes (Round 2)

**Input**: Design documents from `/specs/015-security-review-fixes/`
**Prerequisites**: spec.md ✅, plan.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Included where spec requires them (CSRF, logout replay, innerHTML guard, CLI parity, code-quality gate, profile-id CLI).

**Scope changes from /speckit.analyze**: Story 5 (display name) dropped. US4 narrowed to 1 test. US9 narrowed to gate-only + full allowlist (no refactors). US7 added (profile ID in Settings + CLI --profile-id). Stories renumbered US1–US10.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

- [X] T001 Read all spec artifacts in `/home/matt/cookie/specs/015-security-review-fixes/` (spec.md, plan.md, research.md, data-model.md, contracts/) before writing any code.
- [X] T002 [P] Confirm branch is `015-security-review-fixes` and working tree is clean.
- [X] T003 [P] Confirm dev stack comes up cleanly: `docker compose up -d` succeeds; `docker compose exec web python -m pytest --collect-only >/dev/null` succeeds.

---

## Phase 2: Foundational

No cross-story blockers. Proceed to user stories.

---

## Phase 3: User Story 1 — Secrets never persist on production filesystem (P1) 🎯 MVP

**Goal**: Replace Debian `cron` with SHA256-pinned supercronic v0.2.44. Three cleanup jobs continue as `app` user. No secrets on disk.

- [X] T004 [US1] Create `/home/matt/cookie/crontab` with three schedule+command entries (device codes hourly, sessions daily 03:15, search images daily 03:30). No env vars in file. Header comment warning never to add secrets.
- [X] T005 [US1] Modify `/home/matt/cookie/Dockerfile.prod` stage 3: remove `cron` from `apt-get install`; add supercronic v0.2.44 install with SHA256 pin via `sha256sum -c` (compute SHA256 locally from the downloaded binary, cross-verify once against upstream SHA1 `6eb0a8e1...` for amd64). Support `$TARGETARCH` for multi-arch. `COPY crontab /app/crontab` with mode 0644 owned by `app`.
- [X] T006 [US1] Modify `/home/matt/cookie/entrypoint.prod.sh`: delete lines 57-68 that write `/etc/cron.d/cookie-cleanup` with secrets inline. Delete the `crontab /etc/cron.d/cookie-cleanup` and `cron` invocations. Add a preflight `supercronic -test /app/crontab || exit 1`. Launch supercronic as `su -s /bin/bash app -c "supercronic /app/crontab" &`, capture `SUPERCRONIC_PID`, add to the `cleanup` trap alongside `GUNICORN_PID` and `NGINX_PID`.
- [ ] T007 [US1] Build prod image locally: `docker build --file Dockerfile.prod --tag cookie:015-verify .`. Build must pass the `sha256sum -c` step.
- [ ] T008 [US1] Smoke-test per quickstart: start container, exec in, `grep -rE "SECRET_KEY|DATABASE_URL" /etc/ /var/ /tmp/ /app/` returns nothing. `which cron` empty. `which supercronic` set. `ps` shows supercronic as `app`.

**Checkpoint**: US1 complete. HIGH finding closed.

---

## Phase 4: User Story 2 — Logged-out session cookie is useless (P1)

**Goal**: `request.session.flush()` after logout. Replay returns 401.

- [X] T009 [US2] Write `/home/matt/cookie/tests/test_passkey_logout_replay.py` with two `@pytest.mark.django_db` tests: `test_logged_out_cookie_cannot_hit_auth_me` and `test_logged_out_cookie_cannot_hit_recipes_favorites`. Each logs in via `force_login` + session setup, POSTs to `/api/auth/logout/`, replays cookie, asserts 401. Run FIRST — expect failure on current code.
- [X] T010 [US2] Modify `/home/matt/cookie/apps/core/auth_api.py`: after `logout(request)` (line 33), add `request.session.flush()`.
- [X] T011 [US2] Run T009 tests — both pass. Run existing logout tests: `docker compose exec web python -m pytest tests/test_auth_api.py -k logout -v` — all pass (FR-007).

**Checkpoint**: US2 complete.

---

## Phase 5: User Story 3 — Production compose pinned (P1)

**Goal**: `:latest` → `:v1.44.0` in compose; release playbook updated.

- [X] T012 [US3] Modify `/home/matt/cookie/docker-compose.prod.yml`: change `image: ghcr.io/matthewdeaves/cookie:latest` → `image: ghcr.io/matthewdeaves/cookie:v1.44.0`.
- [X] T013 [US3] Modify `/home/matt/cookie/CLAUDE.md` Releases & Versioning section: add bullet "When tagging a release, update the compose image pin in `docker-compose.prod.yml` to match (`ghcr.io/matthewdeaves/cookie:vX.Y.Z`). Never ship `:latest` in production."
- [X] T014 [US3] Verify: `grep ':latest' docker-compose.prod.yml` returns nothing.

**Checkpoint**: US3 complete.

---

## Phase 6: User Story 4 — CSRF on select_profile (P2)

**Goal**: Integration test proves Django's CSRF middleware protects the session-mutation endpoint.

- [X] T015 [US4] Add `test_select_profile_post_without_csrf_token_returns_403` to `/home/matt/cookie/tests/test_csrf.py` (home mode, `@pytest.mark.django_db`). Create a profile, POST `/api/profiles/{id}/select/` with `content_type="application/json"` and no CSRF token — assert 403. Then repeat with valid CSRF token (set via `client.cookies["csrftoken"]` + `X-CSRFToken` header) — assert 200.
- [X] T016 [US4] Run the test. Expected: passes on current code (middleware already protects it). If it fails, add `@csrf_protect` to `select_profile` in `/home/matt/cookie/apps/profiles/api.py` and rerun.

**Checkpoint**: US4 complete.

---

## Phase 7: User Story 5 — Legacy innerHTML chokepoint (P3)

**Goal**: Zero `.innerHTML =` / `.innerHTML +=` outside `utils.js`. Regression guard in CI.

- [X] T017 [US5] Modify `/home/matt/cookie/apps/legacy/static/legacy/js/pages/search.js` around line 260: replace `elements.resultsGrid.innerHTML += html` with: `var wrapper = document.createElement('div'); Cookie.utils.setHtml(wrapper, html); while (wrapper.firstChild) { elements.resultsGrid.appendChild(wrapper.firstChild); }`. Preserve ES5 syntax.
- [X] T018 [US5] Write `/home/matt/cookie/tests/test_legacy_innerhtml_chokepoint.py` with `test_no_inner_html_outside_utils_js`: walk `apps/legacy/static/legacy/js/`, read every `.js` except `utils.js`, assert regex `\.innerHTML\s*(=|\+=)` has zero matches. Failure message lists `file:line content`.
- [X] T019 [US5] Run both: `grep -rnE "\.innerHTML\s*(=|\+=)" apps/legacy/static/legacy/js/ | grep -v utils.js` returns nothing; pytest test passes.
- [ ] T020 [US5] Manual: `docker compose down && docker compose up -d`, open legacy search UI, search for >20 results, click Load More, verify cards render and remain clickable.

**Checkpoint**: US5 complete.

---

## Phase 8: User Story 6 — `create-session --confirm` (P3)

**Goal**: Non-interactive `create-session --json` requires `--confirm`. Parity with `reset`.

- [X] T021 [US6] Add three tests to `/home/matt/cookie/tests/test_cookie_admin.py` under `TestCreateSessionConfirmParity`: `test_json_without_confirm_errors` (expects non-zero exit + JSON error mentioning `--confirm`), `test_json_with_confirm_succeeds`, `test_interactive_prompt_unchanged` (mock `input()` returning "y" → success; "n" → abort). Run FIRST — first test fails on current code.
- [X] T022 [US6] Modify `/home/matt/cookie/apps/core/management/commands/cookie_admin.py`: add `--confirm` to `create-session` subparser. In `_handle_create_session`, at top: if `options.get("as_json")` and not `options.get("confirm")`, call `self._error(f"--confirm flag required for non-interactive create-session. Re-run with: cookie_admin create-session {options['username']} --json --confirm", options)`.
- [X] T023 [US6] Run T021 tests — all pass. Run full `tests/test_cookie_admin.py` — no regressions.

**Checkpoint**: US6 complete.

---

## Phase 9: User Story 7 — Profile ID in passkey Settings + CLI `--profile-id` (P3)

**Goal**: Passkey users see their account ID in Settings. Admin uses `cookie_admin set-unlimited --profile-id N`.

### Backend CLI changes

- [X] T024 [US7] Modify `/home/matt/cookie/apps/core/management/commands/cookie_admin.py`: in `set-unlimited` and `remove-unlimited` subparser definitions, make `username` positional `nargs='?'` (optional), add `--profile-id` (type=int). In both `_handle_set_unlimited` and `_handle_remove_unlimited`: validate exactly one of username/`--profile-id` is present; if `--profile-id`, look up `Profile.objects.get(id=N)` → `user = profile.user`, then continue existing logic.
- [X] T025 [P] [US7] Add tests to `/home/matt/cookie/tests/test_cookie_admin.py`: `test_set_unlimited_by_profile_id_succeeds`, `test_set_unlimited_both_args_errors`, `test_set_unlimited_profile_id_not_found`, and mirror for `remove-unlimited`. Run — all pass.

### Modern SPA

- [X] T026 [P] [US7] Modify `/home/matt/cookie/frontend/src/components/settings/SettingsGeneral.tsx`: inside the About card, add a conditional block when `mode === 'passkey'` showing `Account ID: {profile.id}` as a read-only caption. Use `useMode()` for the mode check; `useProfile()` for `profile.id`.
- [ ] T027 [P] [US7] Add a Vitest test in the appropriate Settings test file (`frontend/src/test/SettingsComponents.test.tsx` or `Settings.passkey-hide.test.tsx`): in passkey mode mock, assert the "Account ID" caption renders with the profile ID; in home mode mock, assert it does NOT render.

### Legacy frontend

- [X] T028 [P] [US7] Modify `/home/matt/cookie/apps/legacy/templates/legacy/settings.html`: in the About section (around the Version/Source Code area), add `{% if auth_mode == 'passkey' %}<div class="about-row"><span>Account ID</span><span class="font-medium">{{ current_profile_id }}</span></div>{% endif %}`.
- [ ] T029 [US7] Restart dev stack (`docker compose down && docker compose up -d`). In passkey mode, verify both frontends show "Account ID: N". In home mode, verify neither shows it.

**Checkpoint**: US7 complete. CLI admin ops work end-to-end for multi-user deployments.

---

## Phase 10: User Story 9 — Dependabot (P3)

**Goal**: Weekly automated dependency PRs across 5 ecosystems.

- [X] T030 [US9] Create `/home/matt/cookie/.github/dependabot.yml` with exact contents from `contracts/dependabot-config.md` — 5 ecosystems, weekly Monday 09:00 Australia/Sydney, grouped minor+patch, assigned to matthewdeaves, labelled.
- [ ] T031 [US9] Post-merge verification: paste config into GitHub's Dependabot config validator. Confirm green.

**Checkpoint**: US9 complete.

---

## Phase 11: User Story 10 — CC + file-size gates (P3)

**Goal**: ruff C901 at max-complexity=15. Pytest file-size gate with EXEMPT_FILES allowlist covering all 15 current violators. No refactors in this spec.

- [X] T032 [US10] Modify `/home/matt/cookie/pyproject.toml` `[tool.ruff.lint]` block: add `"C90"` to `select`. Add `[tool.ruff.lint.mccabe]` section with `max-complexity = 15`. Extend `[tool.ruff.lint.per-file-ignores]` with `"*/migrations/*.py" = ["C901"]`.
- [X] T033 [US10] Write `/home/matt/cookie/tests/test_code_quality.py` with `EXEMPT_FILES` dict (all 15 current violators with their line counts per research.md Decision 3) and `test_py_file_size_under_limit` implementing the 4-branch algorithm from data-model.md section 3: new violation → fail; exempted but over ceiling → fail; exempted and under limit → fail (remove entry); otherwise pass.
- [X] T034 [US10] Run both gates: `docker compose exec web ruff check apps/ cookie/ tests/` exits 0; `docker compose exec web python -m pytest tests/test_code_quality.py -v` passes.

**Checkpoint**: US10 complete. Constitution Principle V enforced.

---

## Phase 12: Polish & Cross-Cutting

- [ ] T035 Bump `COOKIE_VERSION` in `/home/matt/cookie/cookie/settings.py` from `"1.43.0"` to `"1.44.0"`.
- [ ] T036 Update `/home/matt/cookie/CLAUDE.md` "Recent Changes" list: add `015-security-review-fixes` bullet summarizing the 9 findings fixed + profile-ID Settings feature + gates landed.
- [ ] T037 Full backend test run: `docker compose exec web python -m pytest`. All pre-existing + new tests pass.
- [ ] T038 Full frontend test run: `docker compose exec frontend npm test -- --run`. 516+ passing.
- [ ] T039 [P] Lint: `docker compose exec web ruff check apps/ cookie/ tests/` exits 0.
- [ ] T040 [P] Frontend lint: `docker compose exec frontend npm run lint` exits 0.
- [ ] T041 Commit all work. Open PR to master: `gh pr create --title "Security hardening round 2: secrets, sessions, CSRF, gates, profile-ID UX"`. Wait for CI green.
- [ ] T042 After PR merge: tag `v1.44.0`, create release via `gh release create v1.44.0 --latest --title "v1.44.0 — security review fixes round 2"` with notes summarizing the 9 findings + profile-ID feature + gates. Include the `--confirm` breaking-change callout.
- [ ] T043 File follow-up spec stub `016-code-quality-refactor` (can be a GitHub issue or a branch with a minimal `spec.md`): references every file in the `EXEMPT_FILES` allowlist and commits to refactoring them below 500 lines.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: start immediately.
- **Phase 2 (Foundational)**: none (empty).
- **Phases 3–11**: each depends only on Phase 1. Independent of each other.
- **Phase 12 (Polish)**: depends on all story phases complete.

### User Story Dependencies

All stories are independent — no shared file conflicts except:
- **US6 (T022) touches `cookie_admin.py`** and **US7 (T024) also touches `cookie_admin.py`**. Sequence T022 before T024 to keep diffs clean.
- **US10 (T033) file-size gate** references `tests/test_cookie_admin.py` in the allowlist. If US6 or US7 adds test lines to that file, re-audit the line count in `EXEMPT_FILES` before landing T033.

### Parallel Opportunities

Once Phase 1 is done:
- US1, US2, US3, US4, US5 (innerHTML), US9 (Dependabot), US10 can all run in parallel.
- US6 and US7 share `cookie_admin.py` — run sequentially (US6 first).
- Inside US7: backend CLI (T024–T025), SPA (T026–T027), and legacy (T028) can run in parallel once T024 lands.
- In Phase 12: T039/T040 are parallel.

---

## Implementation Strategy

### MVP (P1 stories only)

1. Phase 1 → Phase 3 (supercronic) + Phase 4 (logout) + Phase 5 (compose pin).
2. **STOP AND VALIDATE**: HIGH closed, logout hardened, prod reproducible. Shippable as `v1.44.0-rc1`.

### Full delivery (recommended)

Ship as a single `v1.44.0` after all 12 phases. The spec treats these as one hardening bundle. Total: **43 tasks** — lean enough for one PR.

---

## Notes

- [P] tasks edit different files and have no unfinished dependencies.
- [Story] labels map tasks to spec user stories for traceability.
- Commit after each logical group: each user story = one commit; each phase = one commit.
- No task may add `# noqa`, `// eslint-disable`, or raise any quality threshold. Constitution Principle V.
- No task may write secrets to disk anywhere. Constitution Principle VII.
- Supercronic binary pinned by locally-computed SHA256 — never use un-pinned downloads.
- Follow-up spec `016-code-quality-refactor` tracked at T043 — must be filed before this PR merges.

# Cookie 2 Development Workflow with Claude Code

> **Purpose:** Guide for using Claude Code effectively to build Cookie 2
> **Philosophy:** Land and Expand - Build core foundation, then iterate feature by feature

---

## Table of Contents

1. [Overview](#1-overview)
2. [Document Structure](#2-document-structure)
3. [Phase-by-Phase Workflow](#3-phase-by-phase-workflow)
4. [Session Management](#4-session-management)
5. [Testing Workflow](#5-testing-workflow)
6. [Troubleshooting](#6-troubleshooting)
7. [Best Practices](#7-best-practices)
8. [QA Workflow](#8-qa-workflow)

---

## 1. Overview

### Why This Structure?

Claude Code works best with:
- **Focused tasks** rather than massive documents
- **Iterative development** rather than big-bang implementations
- **Clear context** provided at the right time
- **Frequent checkpoints** to verify progress

The original `PLANNING.md` (95KB) has been split into focused phase documents. Use them one at a time as you progress through development.

### Key Principles

1. **One phase at a time** - Complete each phase before moving to the next
2. **Use /clear between phases** - Reset context to prevent drift
3. **Follow Session Scope** - Each phase has recommended session boundaries
4. **Test before proceeding** - Verify each phase works before continuing
5. **Use checklists** - Track progress within each phase document

---

## 2. Document Structure

### Guardrails (Always Active)

```
claude.md              # Critical rules, quick reference (auto-loaded)
```

This file is automatically loaded by Claude Code. It contains:
- Architecture decisions
- Figma interpretation rules
- Quick reference table
- File locations

### Phase Plans (Use One at a Time)

```
plans/
├── PHASE-1-FOUNDATION.md           # Django, Docker, profiles
├── PHASE-2-RECIPE-CORE.md          # Scraping, search sources
├── PHASE-3-USER-FEATURES.md        # Favorites, collections, history
├── PHASE-4-REACT-FOUNDATION.md     # React: profile, home, search
├── PHASE-5-LEGACY-FOUNDATION.md    # Legacy: profile, home, search
├── PHASE-6-REACT-RECIPE-PLAYMODE.md    # React: detail, play mode, collections
├── PHASE-7-LEGACY-RECIPE-PLAYMODE.md   # Legacy: detail, play mode, collections
├── PHASE-8A-AI-INFRASTRUCTURE.md   # OpenRouter service, prompts, settings UI
├── PHASE-8B-AI-FEATURES.md         # All 10 AI feature integrations
├── PHASE-9-POLISH.md               # Settings, testing, polish
└── QA-TESTING.md                   # Manual testing issues and fixes
```

### Reference Documents (As Needed)

```
FIGMA_TOOLING.md       # Theme sync tooling (use in Phase 3)
Cookie Recipe App Design/  # Figma export (reference during frontend phases)
```

---

## 3. Phase-by-Phase Workflow

### Starting a New Phase

```bash
# 1. Clear previous context
/clear

# 2. Load the phase document
"Read plans/PHASE-X-NAME.md and let's start implementing"

# 3. Check Session Scope table for recommended session boundaries
# 4. Work through tasks iteratively
# 5. Use /clear between sessions within the phase if recommended
```

### Phase 1: Foundation

**Goal:** Django + Docker + Profiles working

```bash
/clear
"Read plans/PHASE-1-FOUNDATION.md. Let's implement the Django project foundation."
```

**Sessions:**
- A: Django + Docker + nginx setup
- B: Models + API + middleware
- C: Routing + scripts + tests

**Checkpoint:** Run `docker compose up` and verify profile CRUD works.

### Phase 2: Recipe Core

**Goal:** Scraping and search working

```bash
/clear
"Read plans/PHASE-2-RECIPE-CORE.md. Let's implement recipe scraping."
```

**Sessions:**
- A: Recipe + SearchSource models
- B: Scraper service + image download
- C: API endpoints + search service
- D: Search API + tests

**Checkpoint:** Successfully scrape a recipe from allrecipes.com.

### Phase 3: User Features + Theme Tooling

**Goal:** Favorites, collections, theme sync ready

```bash
/clear
"Read plans/PHASE-3-USER-FEATURES.md. Let's implement favorites and collections."
```

**Sessions:**
- A: Favorites, Collections, History models
- B: Data isolation + theme sync + tests

**Checkpoint:** Favorites work per-profile; theme sync tool runs.

### Phase 4: React Frontend Foundation

**Goal:** React interface for profile/home/search

```bash
/clear
"Read plans/PHASE-4-REACT-FOUNDATION.md. Let's build the React frontend."
```

**Sessions:**
- A: React setup + profile selector
- B: Home screen + recipe cards
- C: Search + tests

**Checkpoint:** React interface shows profile selector, home, and search.

### Phase 5: Legacy Frontend Foundation

**Goal:** Legacy interface for profile/home/search

```bash
/clear
"Read plans/PHASE-5-LEGACY-FOUNDATION.md. Let's build the Legacy frontend for iOS 9."
```

**Sessions:**
- A: Legacy setup + profile selector
- B: Home screen + recipe cards
- C: Search + iOS 9 testing

**Checkpoint:** Legacy interface works on iOS 9.

### Phase 6: React Recipe Detail & Collections

**Goal:** Full recipe experience on React

```bash
/clear
"Read plans/PHASE-6-REACT-RECIPE-PLAYMODE.md. Let's implement recipe detail and play mode."
```

**Sessions:**
- A: Recipe detail + serving adjustment
- B: Play mode with timers
- C: Favorites + Collections UI
- D: Tests

**Checkpoint:** Play mode works with timers on React.

### Phase 7: Legacy Recipe Detail & Collections

**Goal:** Full recipe experience on Legacy (iOS 9)

```bash
/clear
"Read plans/PHASE-7-LEGACY-RECIPE-PLAYMODE.md. Let's implement recipe detail and play mode for iOS 9."
```

**Sessions:**
- A: Recipe detail + serving adjustment
- B: Play mode with timers (CRITICAL)
- C: Favorites + Collections UI
- D: iOS 9 manual testing

**Checkpoint:** Play mode works with timers on iOS 9.

### Phase 8A: AI Infrastructure

**Goal:** OpenRouter service and prompt management working

```bash
/clear
"Read plans/PHASE-8A-AI-INFRASTRUCTURE.md. Let's implement the OpenRouter service."
```

**Sessions:**
- A: OpenRouter service + prompts + validation
- B: Settings UI (both interfaces) + tests

**Checkpoint:** Can test API key; all 10 prompts editable in Settings.

### Phase 8B: AI Features

**Goal:** All 10 AI features integrated

```bash
/clear
"Read plans/PHASE-8B-AI-FEATURES.md. Let's implement recipe remix first."
```

**Sessions:**
- A: Recipe remix: Backend API + React UI
- B: Recipe remix: Legacy UI
- C: Serving adjustment + tips generation
- D: Discover feed + search ranking
- E: Timer naming + remix suggestions
- F: Selector repair + tests

**Checkpoint:** All AI features work with valid API key; hidden without key.

### Phase 9: Polish

**Goal:** Production-ready

```bash
/clear
"Read plans/PHASE-9-POLISH.md. Let's complete the Settings screens."
```

**Sessions:**
- A: Settings screens (both interfaces)
- B: Error handling + loading + toasts
- C: Final testing + verification

**Checkpoint:** All tests pass; both interfaces fully functional.

---

## 4. Session Management

### When to Use /clear

- **Between phases** - Always clear when starting a new phase
- **Between sessions** - Clear when moving to next session within a phase
- **After completing major features** - Prevent context bloat
- **When Claude seems confused** - Reset and provide fresh context
- **After long sessions** - Context can drift over time

### Context Loading Pattern

```bash
# Bad: Loading everything at once
"Read PLANNING.md, FIGMA_TOOLING.md, and all the phase plans"

# Good: Loading what you need
"Read plans/PHASE-2-RECIPE-CORE.md - we're implementing the scraper"
```

### Providing Context

```bash
# Good: Specific reference
"Looking at the Recipe model in plans/PHASE-2-RECIPE-CORE.md, implement the scraper service"

# Bad: Vague reference
"Implement scraping based on the plans"
```

---

## 5. Testing Workflow

### Run Tests After Each Task

**⚠️ ALL backend commands must run in Docker - the host has no Python/Django environment.**

```bash
# Run all backend tests
docker compose exec web python -m pytest

# Run specific test file
docker compose exec web python -m pytest tests/test_recipes.py

# Run with verbose output
docker compose exec web python -m pytest -v

# Django shell (for debugging)
docker compose exec web python manage.py shell

# Frontend tests
docker compose exec frontend npm test
```

### Manual Testing Checkpoints

After each phase, manually test:
1. **API endpoints** - Use curl or a REST client
2. **React frontend** - Modern browser
3. **Legacy frontend** - iOS 9 iPad (simulator or real device)

### Test-Driven Development

For complex features:

```bash
"Let's write the tests first for the Recipe scraper, then implement it"
```

---

## 6. Troubleshooting

### Claude Seems Confused

```bash
# 1. Clear context
/clear

# 2. Reload specific phase
"Read plans/PHASE-X.md"

# 3. Provide specific context
"We're implementing task X.Y - the specific feature is..."
```

### Code Doesn't Match Plans

```bash
# Check the guardrails
"Read claude.md and verify if this implementation matches the architecture decisions"
```

### Feature Creep

If Claude is adding features not in the plan:

```bash
"Let's focus only on the tasks listed in the phase document. We can revisit additional features later."
```

### Tests Failing

```bash
"The test test_xyz is failing. Read the test file and the implementation, then fix the issue."
```

---

## 7. Best Practices

### Do

- **One phase at a time** - Complete before moving on
- **Follow Session Scope** - Use recommended session boundaries
- **Use checklists** - Mark tasks complete as you go
- **Test frequently** - Verify each task works
- **Clear between sessions** - Prevent context drift
- **Use specific prompts** - Reference exact tasks and files

### Don't

- **Don't load all plans at once** - Causes instruction overload
- **Don't skip phases** - Each builds on the previous
- **Don't mix unrelated work** - Use separate sessions
- **Don't ignore failing tests** - Fix before proceeding
- **Don't add features not in plan** - Avoid scope creep

---

## 8. QA Workflow

### When Manual Testing is Needed

After completing frontend phases (5, 6, 7), you'll need manual testing on target devices. QA sessions follow the same pattern as implementation sessions but add a **research phase** before fixing.

### QA Document

QA issues are tracked in `plans/QA-TESTING.md`:
- **Issue Log** - Central tracking table (ID, summary, status, session)
- **Session Scope** - Groups related issues into focused sessions
- **Session Plans** - Research findings + tasks + verification for each issue

### Running QA Sessions

**Research phase** (understand before fixing):
```bash
/clear
"Read plans/QA-TESTING.md and research QA-B. Investigate how the existing codebase handles this. Check the Modern frontend pattern and Figma design intent."
```

**Fix phase** (implement the solution):
```bash
/clear
"Read plans/QA-TESTING.md and implement QA-B. Follow the tasks defined in the session plan."
```

### QA Workflow Cycle

1. **Test & Log** - Manual test on device, record issues with ID/summary/screenshots
2. **Research** - Investigate existing code patterns before defining fixes
3. **Fix** - Implement in focused session using `/clear`
4. **Verify** - Test fix on target device before marking complete

### Why Research Matters

Without researching existing patterns first, fixes may technically work but violate codebase architecture (e.g., adding a bottom nav when the app uses a header bar). The research phase ensures fixes fit the established patterns.

---

### Example Session Flow

```bash
# Start of day
/clear

# Load current phase
"Read plans/PHASE-2-RECIPE-CORE.md"

# Check Session Scope
"Let's start with Session A: Recipe + SearchSource models"

# Work on specific task
"Let's implement task 2.1 - the Recipe model"

# Test
"Run the tests for the models"

# Mark complete and continue
"That's working. Let's move to task 2.2 - SearchSource model"

# End of session checkpoint
"Summarize what we completed in Session A"

# Start next session (optionally /clear first)
/clear
"Read plans/PHASE-2-RECIPE-CORE.md - continuing with Session B"
```

---

## Quick Reference

### Phase Progression

| Phase | Goal | Key Deliverable |
|-------|------|-----------------|
| 1 | Foundation | Django + Docker + Profiles |
| 2 | Recipe Core | Scraping + Search |
| 3 | User Features | Favorites + Collections + Theme Sync |
| 4 | React Foundation | React: Profile, Home, Search |
| 5 | Legacy Foundation | Legacy: Profile, Home, Search |
| 6 | React Recipe | React: Detail + Play Mode + Collections |
| 7 | Legacy Recipe | Legacy: Detail + Play Mode + Collections |
| 8A | AI Infrastructure | OpenRouter + Prompts + Settings UI |
| 8B | AI Features | All 10 AI Feature Integrations |
| 9 | Polish | Settings + Testing |

### Key Commands

| Command | Purpose |
|---------|---------|
| `/clear` | Reset context between phases/sessions |
| `pytest` | Run all tests |
| `docker compose up` | Start the stack |
| `./bin/figma-sync-theme` | Sync Figma theme (Phase 3+) |

### Files Always Loaded

- `claude.md` - Guardrails and quick reference

### Files to Load Per Phase

- `plans/PHASE-X-NAME.md` - Current phase only

---

## Summary

1. **Start with Phase 1**, complete it fully, test it
2. **Use /clear** between phases and sessions
3. **Check Session Scope** for recommended session boundaries
4. **Load only the current phase document**
5. **Work through tasks iteratively**
6. **Test after each task**
7. **Mark tasks complete** in the checklist
8. **Don't skip ahead** - each phase builds on previous

This workflow ensures Claude Code has focused context, clear instructions, and can deliver quality implementations phase by phase.

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
3. **Test before proceeding** - Verify each phase works before continuing
4. **Use checklists** - Track progress within each phase document
5. **Keep sessions focused** - Don't mix unrelated tasks

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
├── PHASE-1-FOUNDATION.md          # Django, Docker, profiles
├── PHASE-2-RECIPE-CORE.md         # Scraping, search sources
├── PHASE-3-USER-FEATURES.md       # Favorites, collections, history
├── PHASE-4-5-FRONTENDS-FOUNDATION.md   # Both UIs: profile, home, search
├── PHASE-6-7-RECIPE-DETAIL-PLAYMODE.md # Detail, play mode, collections UI
├── PHASE-8A-AI-INFRASTRUCTURE.md  # OpenRouter service, prompts, settings UI
├── PHASE-8B-AI-FEATURES.md        # All 10 AI feature integrations
└── PHASE-9-POLISH.md              # Settings, testing, polish
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

# 3. Work through tasks iteratively
# Claude will use the checklist to track progress
```

### Phase 1: Foundation

**Goal:** Django + Docker + Profiles working

```bash
/clear
"Read plans/PHASE-1-FOUNDATION.md. Let's implement the Django project foundation."
```

**Checkpoint:** Run `docker compose up` and verify profile CRUD works.

### Phase 2: Recipe Core

**Goal:** Scraping and search working

```bash
/clear
"Read plans/PHASE-2-RECIPE-CORE.md. Let's implement recipe scraping."
```

**Checkpoint:** Successfully scrape a recipe from allrecipes.com.

### Phase 3: User Features + Theme Tooling

**Goal:** Favorites, collections, theme sync ready

```bash
/clear
"Read plans/PHASE-3-USER-FEATURES.md. Let's implement favorites and collections."
```

**Checkpoint:** Favorites work per-profile; theme sync tool runs.

### Phase 4-5: Frontend Foundation

**Goal:** Both UIs working for profile/home/search

```bash
/clear
"Read plans/PHASE-4-5-FRONTENDS-FOUNDATION.md. Let's build the React frontend first."
```

Then:
```bash
"Now let's build the Legacy frontend for iOS 9."
```

**Checkpoint:** Both interfaces show profile selector, home, and search.

### Phase 6-7: Recipe Detail & Collections UI

**Goal:** Full recipe experience on both UIs

```bash
/clear
"Read plans/PHASE-6-7-RECIPE-DETAIL-PLAYMODE.md. Let's implement recipe detail."
```

**Checkpoint:** Play mode works with timers on both interfaces.

### Phase 8A: AI Infrastructure

**Goal:** OpenRouter service and prompt management working

```bash
/clear
"Read plans/PHASE-8A-AI-INFRASTRUCTURE.md. Let's implement the OpenRouter service."
```

Work through infrastructure tasks:
1. OpenRouter service with configurable models
2. AIPrompt model with 10 default prompts
3. Response schema validation
4. Settings UI for prompt editing (both interfaces)

**Checkpoint:** Can test API key; all 10 prompts editable in Settings.

### Phase 8B: AI Features

**Goal:** All 10 AI features integrated

```bash
/clear
"Read plans/PHASE-8B-AI-FEATURES.md. Let's implement recipe remix first."
```

Work through features one at a time:
1. Recipe remix (both interfaces)
2. Serving adjustment
3. Tips generation
4. Discover suggestions
5. Search ranking
6. Timer naming
7. Remix suggestions
8. Selector repair

**Checkpoint:** All AI features work with valid API key; hidden without key.

### Phase 9: Polish

**Goal:** Production-ready

```bash
/clear
"Read plans/PHASE-9-POLISH.md. Let's complete the Settings screens."
```

**Checkpoint:** All tests pass; both interfaces fully functional.

---

## 4. Session Management

### When to Use /clear

- **Between phases** - Always clear when starting a new phase
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

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_recipes.py

# Run with verbose output
pytest -v
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
- **Use checklists** - Mark tasks complete as you go
- **Test frequently** - Verify each task works
- **Keep sessions focused** - One goal per session
- **Clear between phases** - Prevent context drift
- **Use specific prompts** - Reference exact tasks and files

### Don't

- **Don't load all plans at once** - Causes instruction overload
- **Don't skip phases** - Each builds on the previous
- **Don't mix unrelated work** - Use separate sessions
- **Don't ignore failing tests** - Fix before proceeding
- **Don't add features not in plan** - Avoid scope creep

### Example Session Flow

```bash
# Start of day
/clear

# Load current phase
"Read plans/PHASE-2-RECIPE-CORE.md"

# Work on specific task
"Let's implement task 2.3 - the async scraper service"

# Test
"Run the tests for the scraper"

# Mark complete and continue
"That's working. Let's move to task 2.4 - image download"

# End of session checkpoint
"Summarize what we completed today and what's next"
```

---

## Quick Reference

### Phase Progression

| Phase | Goal | Key Deliverable |
|-------|------|-----------------|
| 1 | Foundation | Django + Docker + Profiles |
| 2 | Recipe Core | Scraping + Search |
| 3 | User Features | Favorites + Collections + Theme Sync |
| 4-5 | Frontend Foundation | Both UIs: Profile, Home, Search |
| 6-7 | Recipe Detail | Detail + Play Mode + Collections UI |
| 8A | AI Infrastructure | OpenRouter + Prompts + Settings UI |
| 8B | AI Features | All 10 AI Feature Integrations |
| 9 | Polish | Settings + Testing |

### Key Commands

| Command | Purpose |
|---------|---------|
| `/clear` | Reset context between phases |
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
2. **Use /clear** between phases
3. **Load only the current phase document**
4. **Work through tasks iteratively**
5. **Test after each task**
6. **Mark tasks complete** in the checklist
7. **Don't skip ahead** - each phase builds on previous

This workflow ensures Claude Code has focused context, clear instructions, and can deliver quality implementations phase by phase.

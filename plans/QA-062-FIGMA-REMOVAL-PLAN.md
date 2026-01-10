# QA-062: Remove Figma Tooling and Design Assets - Implementation Plan

## Status
PENDING - Ready for execution

## Summary

Remove Figma-related files and tooling from the codebase. The project will use Claude Code's frontend-design skill for UI development instead of Figma.

**Approach: Minimal removal** - Delete Figma files/tooling, update active instructions only. Historical plan documents are left unchanged as they document what was done during development.

## Safety Analysis

**Confirmed Safe to Remove:**
- The React frontend theme (`frontend/src/styles/theme.css`) is complete and self-sufficient with all 40+ CSS variables for light and dark modes
- The frontend has NO npm dependencies on Figma (`package.json` verified)
- The frontend code has NO imports from the `Cookie Recipe App Design` folder
- The `legacy/` folder referenced in tooling does not exist - the tooling was built for an unused workflow
- The theme sync has already been done - removing the source won't affect the already-synced destination

## Files to Remove

### 1. Documentation
- `FIGMA_TOOLING.md` - 702-line planning document (no longer needed)

### 2. Figma Design Export
- `Cookie Recipe App Design/` - Entire directory containing:
  - `src/` - TypeScript/React components and styles
  - `guidelines/` - Empty placeholder
  - `package.json`, `vite.config.ts`, etc.
  - `README.md`, `ATTRIBUTIONS.md`

### 3. Python Tooling
- `tooling/` - Entire directory containing:
  - `lib/parser.py` - CSS parser
  - `lib/syncer.py` - Theme syncer
  - `lib/__init__.py` - Library init
  - `theme-mapping.json` - Variable mapping config

### 4. Executable Scripts
- `bin/figma-sync-theme` - Theme sync script

## Files to Update

Only update files with **active instructions** that Claude Code follows:

| File | Action |
|------|--------|
| `claude.md` | Remove "Figma Design Interpretation" section and Figma file location reference |
| `.claude/settings.local.json` | Remove `Bash(./bin/figma-sync-theme:*)` and `mcp__figma__get_metadata` permissions |

**NOT updating:** Historical plan documents (PLANNING.md, WORKFLOW.md, PHASE-*.md, QA-TESTING.md) - these are historical records of development decisions.

## Implementation Steps

### Step 1: Remove Files/Directories
```bash
rm FIGMA_TOOLING.md
rm -rf "Cookie Recipe App Design"
rm -rf tooling
rm bin/figma-sync-theme
```

### Step 2: Update claude.md
Remove the "Figma Design Interpretation" section (lines 29-51) which contains:
- Rules about interpreting Figma Settings AI Prompts page
- Instructions to scan screens for AI features
- List of 10 AI features (keep this info, just remove Figma framing)

Also remove the Figma export file location from the "File Locations" section.

### Step 3: Update Settings
Remove Figma-related permissions from `.claude/settings.local.json`:
- `Bash(./bin/figma-sync-theme:*)`
- `mcp__figma__get_metadata`

### Step 4: Verify No Breakage
```bash
# Frontend build
cd frontend && npm run build

# Frontend tests
cd frontend && npm test

# Python tests
./bin/dev test

# Docker build
docker compose build
```

## Verification Checklist

- [ ] Frontend builds successfully
- [ ] Frontend tests pass
- [ ] Python tests pass
- [ ] Docker container builds and runs
- [ ] `claude.md` no longer has Figma-specific instructions
- [ ] `.claude/settings.local.json` no longer has Figma permissions

## Risk Assessment

**Risk: LOW**
- All Figma assets are isolated (no runtime dependencies)
- Theme has already been synced to frontend
- Tooling references non-existent `legacy/` path (was never functional for legacy)
- No build pipelines depend on Figma tooling
- Historical docs with Figma references are harmless

## Execution Command

To execute this plan, ask Claude Code:
```
Execute the plan in plans/QA-062-FIGMA-REMOVAL-PLAN.md
```

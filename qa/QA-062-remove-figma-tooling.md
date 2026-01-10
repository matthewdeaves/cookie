# QA-062: Remove Figma Tooling and Design Assets

## Status
PENDING - Logged for future execution

## Problem

Figma tooling was set up for a design-to-code workflow that is no longer needed. Claude Code's frontend-design skill provides better results for this project.

## Affects
- Project structure (removing unused files)
- Documentation (removing stale references)
- No impact on frontend or backend functionality

## Priority
Low - Cleanup task, no functional impact

## Safety Analysis Completed

**Confirmed Safe to Remove:**
- React frontend theme (`frontend/src/styles/theme.css`) is complete with all 40+ CSS variables
- Frontend has NO npm dependencies on Figma
- Frontend has NO imports from `Cookie Recipe App Design` folder
- The `legacy/` folder referenced in tooling does not exist
- Theme sync was already completed - removing source doesn't affect destination

## Files to Remove

| Category | Path |
|----------|------|
| Documentation | `FIGMA_TOOLING.md` |
| Design Export | `Cookie Recipe App Design/` (entire folder) |
| Python Tooling | `tooling/` (entire folder) |
| Scripts | `bin/figma-sync-theme` |

## Documentation to Update

Remove Figma references from:
- `PLANNING.md`
- `WORKFLOW.md`
- `claude.md`
- `.claude/settings.local.json`
- `plans/PHASE-3-USER-FEATURES.md`
- `plans/PHASE-4-REACT-FOUNDATION.md`
- `plans/PHASE-6-REACT-RECIPE-PLAYMODE.md`
- `plans/PHASE-7-LEGACY-RECIPE-PLAYMODE.md`
- `plans/PHASE-8A-AI-INFRASTRUCTURE.md`
- `plans/PHASE-8B-AI-FEATURES.md`
- `plans/PHASE-9-POLISH.md`
- `plans/PHASE-10-GITHUB-ACTIONS-CICD.md`
- `plans/QA-TESTING.md`

## Implementation Plan

See `plans/README-PLAN.md` for full implementation steps.

## Verification Checklist

- [ ] Frontend builds successfully
- [ ] Frontend tests pass
- [ ] Python tests pass
- [ ] Docker container builds and runs
- [ ] Grep for "figma" returns only QA-062 documentation

## Risk Assessment

**Risk: LOW** - All Figma assets are isolated with no runtime dependencies

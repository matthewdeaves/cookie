# QA-062: Remove Figma Tooling and Design Assets

## Status
**WON'T FIX** - Deferred until future enhancement implemented

## Decision

Keeping Figma tooling in place until a future enhancement is created to update the legacy and modern themes using Claude Code's frontend-design skill. The Figma assets and tooling provide useful design reference and theme synchronization capabilities that should be replaced with a proper alternative before removal.

## Future Enhancement Required

Before removing Figma tooling, implement:
- FE-015: Replace Figma workflow with Claude Code frontend-design skill
- Establish new workflow for design-to-code without Figma dependency

## Original Problem

Figma tooling was set up for a design-to-code workflow. Claude Code's frontend-design skill may provide better results, but no replacement workflow has been established yet.

## Affects
- Project structure (Figma files remain)
- Documentation (Figma references remain)
- No impact on frontend or backend functionality

## Priority
Low - Cleanup task, no functional impact

## Files Retained

| Category | Path |
|----------|------|
| Documentation | `FIGMA_TOOLING.md` |
| Design Export | `Cookie Recipe App Design/` (entire folder) |
| Python Tooling | `tooling/` (entire folder) |
| Scripts | `bin/figma-sync-theme` |

## Risk Assessment

**Risk: NONE** - Keeping existing tooling has no negative impact

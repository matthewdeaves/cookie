# Figma-to-Code Tooling Planning Document

> **Created:** 2026-01-07
> **Purpose:** Deterministic tooling for syncing Figma exports to Cookie 2 codebase
> **Figma Export Location:** `/home/matt/cookie/Cookie Recipe App Design/`
> **When to Build:** Theme sync in Phase 3 (before frontends); diff/validate in Phase 5+ (after frontends exist)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Tool Suite](#2-tool-suite)
3. [Component Registry](#3-component-registry)
4. [Theme Sync Tool](#4-theme-sync-tool)
5. [Diff Tool](#5-diff-tool)
6. [Validation Tool](#6-validation-tool)
7. [Implementation Plan](#7-implementation-plan)

---

## 1. Overview

### Problem

When a new Figma export arrives, an LLM must:
- Manually compare files to find changes
- Guess which components map to which
- Risk missing subtle changes in colors, spacing, or structure

### Solution

Build deterministic tooling that:
- **Detects** exactly what changed between exports
- **Syncs** theme variables automatically to both frontends
- **Maps** Figma components to implementation files
- **Validates** that implementation matches design

### Principles

1. **Automation over manual comparison** - Scripts do the diff work
2. **Structured output** - JSON/Markdown reports, not prose
3. **Bidirectional awareness** - Know both what Figma has and what code has
4. **Fail loudly** - Missing mappings or broken syncs should error, not silently pass

---

## 2. Tool Suite

### Directory Structure

```
cookie/
├── bin/
│   ├── figma-diff          # Compare Figma export to current code
│   ├── figma-sync-theme    # Sync theme.css to both frontends
│   ├── figma-validate      # Validate implementation matches design
│   └── figma-report        # Generate full change report
├── tooling/
│   ├── figma-mapping.json  # Component registry
│   ├── theme-mapping.json  # CSS variable mappings
│   └── lib/
│       ├── parser.py       # Parse Figma export files
│       ├── differ.py       # Compare structures
│       ├── syncer.py       # Sync theme variables
│       └── reporter.py     # Generate reports
```

### Tool Summary

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| `figma-diff` | Detect changes | Figma export dir | JSON diff report |
| `figma-sync-theme` | Sync CSS variables | Figma theme.css | Updated frontend CSS files |
| `figma-validate` | Check implementation | Mapping + code | Pass/fail with details |
| `figma-report` | Human-readable summary | All above | Markdown report |

---

## 3. Component Registry

### `tooling/figma-mapping.json`

Maps Figma export files to implementation files in both frontends.

```json
{
  "version": "1.0.0",
  "last_updated": "2026-01-07T12:00:00Z",

  "screens": {
    "profile-selector": {
      "figma_source": "src/app/App.tsx:renderProfileSelector",
      "react": "frontend/src/screens/ProfileSelector.tsx",
      "legacy_template": "legacy/templates/legacy/profile_selector.html",
      "legacy_js": "legacy/static/legacy/js/pages/profile.js"
    },
    "home": {
      "figma_source": "src/app/App.tsx:renderHome",
      "react": "frontend/src/screens/Home.tsx",
      "legacy_template": "legacy/templates/legacy/home.html",
      "legacy_js": "legacy/static/legacy/js/pages/home.js"
    },
    "search": {
      "figma_source": "src/app/App.tsx:renderSearch",
      "react": "frontend/src/screens/Search.tsx",
      "legacy_template": "legacy/templates/legacy/search.html",
      "legacy_js": "legacy/static/legacy/js/pages/search.js"
    },
    "recipe-detail": {
      "figma_source": "src/app/App.tsx:renderRecipeDetail",
      "react": "frontend/src/screens/RecipeDetail.tsx",
      "legacy_template": "legacy/templates/legacy/recipe_detail.html",
      "legacy_js": "legacy/static/legacy/js/pages/detail.js"
    },
    "play-mode": {
      "figma_source": "src/app/App.tsx:renderPlayMode",
      "react": "frontend/src/screens/PlayMode.tsx",
      "legacy_template": "legacy/templates/legacy/play_mode.html",
      "legacy_js": "legacy/static/legacy/js/pages/play.js"
    },
    "favorites": {
      "figma_source": "src/app/App.tsx:renderFavorites",
      "react": "frontend/src/screens/Favorites.tsx",
      "legacy_template": "legacy/templates/legacy/favorites.html",
      "legacy_js": null
    },
    "collections": {
      "figma_source": "src/app/App.tsx:renderLists",
      "react": "frontend/src/screens/Collections.tsx",
      "legacy_template": "legacy/templates/legacy/collections.html",
      "legacy_js": null
    },
    "collection-detail": {
      "figma_source": "src/app/App.tsx:renderListDetail",
      "react": "frontend/src/screens/CollectionDetail.tsx",
      "legacy_template": "legacy/templates/legacy/collection_detail.html",
      "legacy_js": null
    },
    "settings": {
      "figma_source": "src/app/App.tsx:renderSettings",
      "react": "frontend/src/screens/Settings.tsx",
      "legacy_template": "legacy/templates/legacy/settings.html",
      "legacy_js": "legacy/static/legacy/js/pages/settings.js"
    }
  },

  "components": {
    "Header": {
      "figma_source": "src/app/components/Header.tsx",
      "react": "frontend/src/components/Header.tsx",
      "legacy_template": "legacy/templates/legacy/partials/header.html",
      "legacy_js": null
    },
    "RecipeCard": {
      "figma_source": "src/app/components/RecipeCard.tsx",
      "react": "frontend/src/components/RecipeCard.tsx",
      "legacy_template": "legacy/templates/legacy/partials/recipe_card.html",
      "legacy_js": null
    },
    "ProfileAvatar": {
      "figma_source": "src/app/components/ProfileAvatar.tsx",
      "react": "frontend/src/components/ProfileAvatar.tsx",
      "legacy_template": null,
      "legacy_css_class": ".profile-avatar"
    },
    "BreadcrumbNav": {
      "figma_source": "src/app/components/BreadcrumbNav.tsx",
      "react": "frontend/src/components/BreadcrumbNav.tsx",
      "legacy_template": "legacy/templates/legacy/partials/breadcrumb.html",
      "legacy_js": null
    },
    "EmptyState": {
      "figma_source": "src/app/components/EmptyState.tsx",
      "react": "frontend/src/components/EmptyState.tsx",
      "legacy_template": "legacy/templates/legacy/partials/empty_state.html",
      "legacy_js": null
    },
    "TimerWidget": {
      "figma_source": "src/app/components/TimerWidget.tsx",
      "react": "frontend/src/components/TimerWidget.tsx",
      "legacy_template": "legacy/templates/legacy/partials/timer.html",
      "legacy_js": "legacy/static/legacy/js/timer.js"
    },
    "AIRemixModal": {
      "figma_source": "src/app/components/AIRemixModal.tsx",
      "react": "frontend/src/components/AIRemixModal.tsx",
      "legacy_template": "legacy/templates/legacy/partials/remix_modal.html",
      "legacy_js": null
    }
  },

  "styles": {
    "theme": {
      "figma_source": "src/styles/theme.css",
      "react": "frontend/src/styles/theme.css",
      "legacy": "legacy/static/legacy/css/base.css"
    },
    "tailwind": {
      "figma_source": "src/styles/tailwind.css",
      "react": "frontend/src/styles/tailwind.css",
      "legacy": null
    }
  }
}
```

### Registry Rules

1. **All Figma files must be mapped** - Unmapped files cause validation failure
2. **Null is valid** - Legacy may not have equivalent for every component
3. **Version tracked** - `last_updated` helps identify stale mappings
4. **Screen functions identified** - `renderXxx` functions in App.tsx are tracked

---

## 4. Theme Sync Tool

### `bin/figma-sync-theme`

Automatically syncs CSS variables from Figma's `theme.css` to both frontends.

### Usage

```bash
# Sync theme to both frontends
./bin/figma-sync-theme

# Sync to React only
./bin/figma-sync-theme --react-only

# Sync to Legacy only (light mode values)
./bin/figma-sync-theme --legacy-only

# Dry run - show what would change
./bin/figma-sync-theme --dry-run
```

### `tooling/theme-mapping.json`

Maps Figma CSS variables to implementation variables:

```json
{
  "version": "1.0.0",

  "variables": {
    "colors": {
      "--background": {
        "react": "--background",
        "legacy": "background-color on body",
        "light_only": false
      },
      "--foreground": {
        "react": "--foreground",
        "legacy": "color on body",
        "light_only": false
      },
      "--primary": {
        "react": "--primary",
        "legacy": "--primary-color",
        "light_only": false
      },
      "--primary-foreground": {
        "react": "--primary-foreground",
        "legacy": null,
        "light_only": false
      },
      "--secondary": {
        "react": "--secondary",
        "legacy": "--secondary-bg",
        "light_only": false
      },
      "--accent": {
        "react": "--accent",
        "legacy": "--accent-color",
        "light_only": false
      },
      "--muted": {
        "react": "--muted",
        "legacy": "--muted-bg",
        "light_only": false
      },
      "--muted-foreground": {
        "react": "--muted-foreground",
        "legacy": "--muted-text",
        "light_only": false
      },
      "--destructive": {
        "react": "--destructive",
        "legacy": "--error-color",
        "light_only": false
      },
      "--border": {
        "react": "--border",
        "legacy": "--border-color",
        "light_only": false
      },
      "--card": {
        "react": "--card",
        "legacy": "--card-bg",
        "light_only": false
      },
      "--star": {
        "react": "--star",
        "legacy": "--star-color",
        "light_only": false
      },
      "--radius": {
        "react": "--radius",
        "legacy": "--border-radius",
        "light_only": false
      }
    },

    "dark_mode": {
      "strategy": "css_class",
      "class_name": ".dark",
      "legacy_support": false,
      "note": "Legacy uses light theme only - dark values ignored"
    }
  },

  "fonts": {
    "--font-size": {
      "react": "html font-size",
      "legacy": "html font-size"
    }
  }
}
```

### Sync Algorithm

```python
# tooling/lib/syncer.py

def sync_theme(figma_theme_path, react_theme_path, legacy_css_path, dry_run=False):
    """
    Sync Figma theme.css to both frontends.

    1. Parse Figma theme.css for :root and .dark variables
    2. For React: Copy/update theme.css directly (nearly identical)
    3. For Legacy: Extract :root (light) values only, map to legacy variable names
    4. Report changes made
    """

    figma_vars = parse_css_variables(figma_theme_path)
    mapping = load_theme_mapping()
    changes = []

    # React sync - mostly direct copy with minor adjustments
    react_changes = sync_to_react(figma_vars, react_theme_path, mapping, dry_run)
    changes.extend(react_changes)

    # Legacy sync - light values only, variable name translation
    legacy_changes = sync_to_legacy(
        figma_vars[':root'],  # Light mode only
        legacy_css_path,
        mapping,
        dry_run
    )
    changes.extend(legacy_changes)

    return {
        'success': True,
        'changes': changes,
        'dry_run': dry_run
    }
```

### Output Example

```
$ ./bin/figma-sync-theme --dry-run

Figma Theme Sync (DRY RUN)
==========================

React (frontend/src/styles/theme.css):
  [UPDATE] --primary: #6b8e5f → #7a9d6e
  [UPDATE] --accent: #a84f5f → #b85a6a
  [NO CHANGE] --background, --foreground, --secondary (14 vars)

Legacy (legacy/static/legacy/css/base.css):
  [UPDATE] --primary-color: #6b8e5f → #7a9d6e
  [UPDATE] --accent-color: #a84f5f → #b85a6a
  [SKIP] Dark mode variables (legacy is light-only)

Summary: 4 changes detected (2 React, 2 Legacy)
Run without --dry-run to apply changes.
```

---

## 5. Diff Tool

### `bin/figma-diff`

Compares the current Figma export to the previous export (or to current implementation).

### Usage

```bash
# Compare current export to last known state
./bin/figma-diff

# Compare to specific previous export
./bin/figma-diff --previous=/path/to/old/export

# Output as JSON
./bin/figma-diff --format=json > diff-report.json

# Compare specific file only
./bin/figma-diff --file=src/app/components/RecipeCard.tsx
```

### What It Detects

| Change Type | Detection Method |
|-------------|------------------|
| **New files** | File exists in export but not in registry |
| **Removed files** | File in registry but not in export |
| **Modified components** | AST diff of React component structure |
| **Theme changes** | CSS variable value comparison |
| **New screens** | New `renderXxx` function in App.tsx |
| **Interface changes** | TypeScript interface property changes |
| **Import changes** | New/removed imports in components |

### Diff Report Structure

```json
{
  "generated_at": "2026-01-07T14:30:00Z",
  "figma_export_path": "/home/matt/cookie/Cookie Recipe App Design",
  "comparison_base": "previous_export",

  "summary": {
    "total_changes": 5,
    "new_files": 1,
    "modified_files": 3,
    "removed_files": 0,
    "theme_changes": 2
  },

  "changes": [
    {
      "type": "new_file",
      "path": "src/app/components/NewComponent.tsx",
      "action_required": "Add to figma-mapping.json and implement in both frontends"
    },
    {
      "type": "modified",
      "path": "src/app/components/RecipeCard.tsx",
      "details": {
        "props_added": ["onShare"],
        "props_removed": [],
        "jsx_structure_changed": true,
        "lines_changed": 15
      },
      "mapped_files": {
        "react": "frontend/src/components/RecipeCard.tsx",
        "legacy": "legacy/templates/legacy/partials/recipe_card.html"
      },
      "action_required": "Update React component and legacy template"
    },
    {
      "type": "theme_change",
      "variable": "--primary",
      "old_value": "#6b8e5f",
      "new_value": "#7a9d6e",
      "action_required": "Run figma-sync-theme"
    }
  ],

  "unmapped_files": [
    "src/app/components/NewComponent.tsx"
  ],

  "action_items": [
    "1. Add NewComponent to figma-mapping.json",
    "2. Implement NewComponent in React frontend",
    "3. Implement NewComponent equivalent in Legacy (if needed)",
    "4. Update RecipeCard in both frontends (props changed)",
    "5. Run figma-sync-theme to update colors"
  ]
}
```

### State Tracking

The diff tool needs to track the previous state. Options:

**Option A: Git-based (Recommended)**
```bash
# Store Figma export hash after successful sync
git -C "Cookie Recipe App Design" rev-parse HEAD > .figma-last-sync
```

**Option B: Snapshot directory**
```bash
# Copy export to snapshot after successful sync
cp -r "Cookie Recipe App Design" .figma-snapshot/
```

**Option C: Hash manifest**
```json
// .figma-state.json
{
  "last_sync": "2026-01-07T12:00:00Z",
  "file_hashes": {
    "src/app/App.tsx": "sha256:abc123...",
    "src/app/components/RecipeCard.tsx": "sha256:def456..."
  }
}
```

---

## 6. Validation Tool

### `bin/figma-validate`

Validates that the implementation matches the Figma design.

### Usage

```bash
# Full validation
./bin/figma-validate

# Validate specific component
./bin/figma-validate --component=RecipeCard

# Validate React only
./bin/figma-validate --react-only

# Strict mode - fail on warnings
./bin/figma-validate --strict
```

### Validation Checks

| Check | Pass Condition |
|-------|----------------|
| **Mapping complete** | All Figma files have entries in figma-mapping.json |
| **Files exist** | All mapped implementation files exist |
| **Theme synced** | CSS variables match between Figma and implementations |
| **Props match** | Component props in React match Figma interfaces |
| **Screens complete** | All Figma screens have both React and Legacy implementations |

### Validation Report

```
$ ./bin/figma-validate

Figma Validation Report
=======================

Mapping Completeness:
  [PASS] All 9 screens mapped
  [PASS] All 7 components mapped
  [PASS] All style files mapped

File Existence:
  [PASS] All React files exist (16/16)
  [PASS] All Legacy templates exist (14/14)
  [WARN] Missing legacy JS: pages/favorites.js (acceptable - no JS needed)

Theme Sync:
  [FAIL] --primary mismatch
         Figma: #7a9d6e
         React: #6b8e5f
         Legacy: #6b8e5f
  [PASS] 13 other variables match

Component Props:
  [PASS] Header props match
  [PASS] RecipeCard props match
  [WARN] TimerWidget - Figma has onPause prop, React missing
  [PASS] 5 other components match

Summary: 1 FAIL, 2 WARN, 28 PASS
Action: Run figma-sync-theme, then add onPause to TimerWidget
```

---

## 7. Implementation Plan

### Phase 1: Theme Sync Foundation (During Phase 3 of main build)

**Goal:** Theme synchronization ready BEFORE frontend development begins

1. Create `tooling/` directory structure
2. Create `theme-mapping.json` with CSS variable mappings
3. Implement `tooling/lib/parser.py` - Parse CSS files
4. Implement `tooling/lib/syncer.py`
5. Create `bin/figma-sync-theme` script
6. Test with Figma's theme.css

**Deliverables:**
- [ ] Directory structure
- [ ] theme-mapping.json (complete)
- [ ] parser.py with CSS variable extraction
- [ ] syncer.py
- [ ] bin/figma-sync-theme (executable)
- [ ] Theme sync documentation

**Rationale:** Theme sync is immediately useful when building the React frontend (Phase 4). Having it ready beforehand ensures consistent theming from day one.

### Phase 2: Component Registry (During Phase 4 of main build)

**Goal:** Track component mappings as frontends are built

1. Create initial `figma-mapping.json` with all current mappings
2. Update mapping as components are implemented
3. Add validation for mapping completeness

**Deliverables:**
- [ ] figma-mapping.json (complete)
- [ ] Mapping documentation

### Phase 3: Diff Tool (After Phase 5)

**Goal:** Change detection

1. Implement `tooling/lib/differ.py`
2. Create `bin/figma-diff` script
3. Implement state tracking (.figma-state.json)
4. Add AST-based component diffing

**Deliverables:**
- [ ] differ.py
- [ ] bin/figma-diff (executable)
- [ ] State tracking mechanism

### Phase 4: Validation & Reporting (After Phase 6)

**Goal:** Complete tooling suite

1. Implement `tooling/lib/reporter.py`
2. Create `bin/figma-validate` script
3. Create `bin/figma-report` script
4. Add CI integration hooks

**Deliverables:**
- [ ] reporter.py
- [ ] bin/figma-validate (executable)
- [ ] bin/figma-report (executable)
- [ ] CI integration documentation

---

## Appendix: Quick Reference

### Commands Cheat Sheet

```bash
# After receiving new Figma export:

# 1. See what changed
./bin/figma-diff

# 2. Sync theme automatically
./bin/figma-sync-theme

# 3. Review action items
./bin/figma-report

# 4. After manual updates, validate
./bin/figma-validate
```

### File Locations

| File | Purpose |
|------|---------|
| `tooling/figma-mapping.json` | Component registry |
| `tooling/theme-mapping.json` | CSS variable mappings |
| `.figma-state.json` | Last sync state (auto-generated) |
| `bin/figma-*` | Executable scripts |

### Adding New Components

When Figma adds a new component:

1. `figma-diff` will flag it as unmapped
2. Add entry to `figma-mapping.json`
3. Implement in React frontend
4. Implement in Legacy frontend (if applicable)
5. Run `figma-validate` to confirm

### Troubleshooting

| Issue | Solution |
|-------|----------|
| "Unmapped file" error | Add file to figma-mapping.json |
| Theme out of sync | Run `figma-sync-theme` |
| Validation fails | Check figma-validate output for specific issues |
| Missing legacy file | Set to `null` in mapping if intentionally omitted |

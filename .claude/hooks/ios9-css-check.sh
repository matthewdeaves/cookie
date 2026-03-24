#!/bin/bash
# iOS 9 Safari CSS Compatibility Check
# BLOCKS CSS features that break on iOS 9.3 Safari in legacy stylesheets.
#
# This hook runs before Edit/Write operations on legacy CSS files.
# Two severity levels:
#   BLOCK  - Features that cause layout breakage or are completely unsupported
#            (including var() and gap). Prevents the edit from proceeding.
#   WARN   - Features with partial iOS 9 support (e.g., object-fit on <img>).
#            Logged but not blocked.
#
# Exit 0: Allow the edit (may include warnings)
# Exit 1: Block the edit (blocker found)

set -e

# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------

if ! command -v jq >/dev/null 2>&1; then
    echo "[ios9-css] jq not found - install with: sudo apt install jq"
    exit 0
fi

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_LOG_DIR="$SCRIPT_DIR/../logs"
HOOK_LOG="$HOOK_LOG_DIR/hooks.log"
mkdir -p "$HOOK_LOG_DIR"

log_hook() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ios9-css] $1" >> "$HOOK_LOG"
}

# ---------------------------------------------------------------------------
# Parse input
# ---------------------------------------------------------------------------

INPUT=$(cat)

FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
NEW_CONTENT=$(echo "$INPUT" | jq -r '.tool_input.new_string // .tool_input.content // empty')

# Skip if no file path or not a legacy CSS file
if [[ -z "$FILE_PATH" ]]; then
    exit 0
fi
if [[ ! "$FILE_PATH" =~ apps/legacy/static/legacy/css ]]; then
    exit 0
fi
if [[ -z "$NEW_CONTENT" ]]; then
    exit 0
fi

log_hook "Checking: $FILE_PATH"

BLOCKERS=""
WARNINGS=""

# ---------------------------------------------------------------------------
# BLOCKERS — these PREVENT the edit
# ---------------------------------------------------------------------------

# CSS Grid layout (display: grid, grid-template-*, grid-area, grid-column, grid-row)
# iOS 9 has zero CSS Grid support — layout will be completely broken
if echo "$NEW_CONTENT" | grep -qiE 'display\s*:\s*grid'; then
    BLOCKERS="${BLOCKERS}  - 'display: grid' (use flexbox with -webkit- prefix or floats)\n"
fi
if echo "$NEW_CONTENT" | grep -qiE 'grid-template(-columns|-rows|-areas)?\s*:'; then
    BLOCKERS="${BLOCKERS}  - 'grid-template-*' (use flexbox or float-based layout)\n"
fi
if echo "$NEW_CONTENT" | grep -qiE 'grid-(column|row|area)\s*:'; then
    BLOCKERS="${BLOCKERS}  - 'grid-column/row/area' (use flexbox order or positioning)\n"
fi

# display: inline-grid
if echo "$NEW_CONTENT" | grep -qiE 'display\s*:\s*inline-grid'; then
    BLOCKERS="${BLOCKERS}  - 'display: inline-grid' (use inline-flex or inline-block)\n"
fi

# position: sticky (iOS 9 does not support this)
if echo "$NEW_CONTENT" | grep -qiE 'position\s*:\s*sticky'; then
    BLOCKERS="${BLOCKERS}  - 'position: sticky' (use position: fixed or JS-based sticky)\n"
fi

# backdrop-filter (iOS 9 does not support this)
if echo "$NEW_CONTENT" | grep -qiE '(-webkit-)?backdrop-filter\s*:'; then
    BLOCKERS="${BLOCKERS}  - 'backdrop-filter' (use solid background-color with opacity)\n"
fi

# :focus-visible pseudo-class (not supported until much later)
if echo "$NEW_CONTENT" | grep -qE ':focus-visible'; then
    BLOCKERS="${BLOCKERS}  - ':focus-visible' (use :focus instead)\n"
fi

# :is() and :where() selectors
if echo "$NEW_CONTENT" | grep -qE ':(is|where)\s*\('; then
    BLOCKERS="${BLOCKERS}  - ':is()/:where()' selectors (expand to individual selectors)\n"
fi

# :has() selector
if echo "$NEW_CONTENT" | grep -qE ':has\s*\('; then
    BLOCKERS="${BLOCKERS}  - ':has()' selector (use JS-based class toggling)\n"
fi

# aspect-ratio property
if echo "$NEW_CONTENT" | grep -qiE 'aspect-ratio\s*:'; then
    BLOCKERS="${BLOCKERS}  - 'aspect-ratio' (use padding-bottom percentage hack)\n"
fi

# place-items / place-content / place-self (Grid/modern flexbox shorthands)
if echo "$NEW_CONTENT" | grep -qiE 'place-(items|content|self)\s*:'; then
    BLOCKERS="${BLOCKERS}  - 'place-items/content/self' (use align-items + justify-content)\n"
fi

# @container queries
if echo "$NEW_CONTENT" | grep -qE '@container\b'; then
    BLOCKERS="${BLOCKERS}  - '@container' queries (use media queries or JS)\n"
fi

# @layer
if echo "$NEW_CONTENT" | grep -qE '@layer\b'; then
    BLOCKERS="${BLOCKERS}  - '@layer' (not supported; use specificity ordering)\n"
fi

# @supports (iOS 9.3 has partial support but it's unreliable)
if echo "$NEW_CONTENT" | grep -qE '@supports\b'; then
    BLOCKERS="${BLOCKERS}  - '@supports' (unreliable on iOS 9; use unconditional styles)\n"
fi

# clamp() function
if echo "$NEW_CONTENT" | grep -qiE 'clamp\s*\('; then
    BLOCKERS="${BLOCKERS}  - 'clamp()' (use min/max with media queries, or fixed values)\n"
fi

# min() / max() CSS functions (not the selectors :min/:max)
if echo "$NEW_CONTENT" | grep -qiE ':\s*[^;]*(min|max)\s*\([^)]*[a-z]'; then
    # Heuristic: look for min()/max() in property values (after a colon)
    # Avoid matching selectors or non-CSS contexts
    if echo "$NEW_CONTENT" | grep -qiE '(width|height|font-size|padding|margin)\s*:.*\b(min|max)\s*\('; then
        BLOCKERS="${BLOCKERS}  - 'min()/max()' CSS functions (use media queries for responsive values)\n"
    fi
fi

# color-mix() function
if echo "$NEW_CONTENT" | grep -qiE 'color-mix\s*\('; then
    BLOCKERS="${BLOCKERS}  - 'color-mix()' (use pre-computed color values)\n"
fi

# Logical properties (margin-inline, padding-block, inset, etc.)
if echo "$NEW_CONTENT" | grep -qiE '(margin|padding|border)-(inline|block)(-start|-end)?\s*:'; then
    BLOCKERS="${BLOCKERS}  - Logical properties (margin-inline, etc.) (use margin-left/right/top/bottom)\n"
fi
if echo "$NEW_CONTENT" | grep -qiE '\binset\s*:'; then
    BLOCKERS="${BLOCKERS}  - 'inset' shorthand (use top/right/bottom/left individually)\n"
fi

# CSS custom properties var() — iOS 9 ignores these entirely
if echo "$NEW_CONTENT" | grep -qE 'var\(--'; then
    BLOCKERS="${BLOCKERS}  - 'var(--*)' CSS custom properties (use literal color values, e.g., #6b8e5f instead of var(--primary))\n"
fi

# Flexbox gap — iOS 9 does not support gap on flex containers
if echo "$NEW_CONTENT" | grep -qiE '\bgap\s*:'; then
    BLOCKERS="${BLOCKERS}  - 'gap' on flexbox (use margin-based spacing, e.g., .selector > * + * { margin-left: 0.5rem; })\n"
fi

# overflow: overlay (removed from spec, never in iOS 9)
if echo "$NEW_CONTENT" | grep -qiE 'overflow\s*:\s*overlay'; then
    BLOCKERS="${BLOCKERS}  - 'overflow: overlay' (use overflow: auto)\n"
fi

# scroll-behavior: smooth (not supported)
if echo "$NEW_CONTENT" | grep -qiE 'scroll-behavior\s*:\s*smooth'; then
    BLOCKERS="${BLOCKERS}  - 'scroll-behavior: smooth' (use JS-based smooth scrolling)\n"
fi

# overscroll-behavior (not supported)
if echo "$NEW_CONTENT" | grep -qiE 'overscroll-behavior'; then
    BLOCKERS="${BLOCKERS}  - 'overscroll-behavior' (not supported on iOS 9)\n"
fi

# accent-color (not supported)
if echo "$NEW_CONTENT" | grep -qiE 'accent-color\s*:'; then
    BLOCKERS="${BLOCKERS}  - 'accent-color' (not supported; style form elements manually)\n"
fi

# content-visibility (not supported)
if echo "$NEW_CONTENT" | grep -qiE 'content-visibility\s*:'; then
    BLOCKERS="${BLOCKERS}  - 'content-visibility' (not supported on iOS 9)\n"
fi

# ---------------------------------------------------------------------------
# WARNINGS — logged but do NOT block (partial support features)
# ---------------------------------------------------------------------------

# object-fit (partial support on iOS 9 — works on <img> but not <video>)
if echo "$NEW_CONTENT" | grep -qiE 'object-fit\s*:'; then
    WARNINGS="${WARNINGS}  - 'object-fit' (partial iOS 9 support — works on <img> only, not <video>)\n"
    WARNINGS="${WARNINGS}    Safe alternative: background-image with background-size: cover\n"
fi

# ---------------------------------------------------------------------------
# Report results
# ---------------------------------------------------------------------------

if [[ -n "$BLOCKERS" ]]; then
    log_hook "BLOCKED: iOS 9 incompatible CSS in $FILE_PATH"
    echo ""
    echo "BLOCKED: iOS 9 Incompatible CSS in Legacy Stylesheet"
    echo "====================================================="
    echo ""
    echo "The following CSS features do NOT work on iOS 9.3 Safari"
    echo "(iPad 2/3/4, iPad Mini 1) and MUST NOT be used:"
    echo ""
    echo -e "$BLOCKERS"
    echo ""
    echo "Safe alternatives for iOS 9:"
    echo "  var(--primary)         → #6b8e5f (use literal hex values from color map)"
    echo "  gap: 0.5rem            → .selector > * + * { margin-left: 0.5rem; }"
    echo "  display: grid          → display: -webkit-flex; display: flex"
    echo "  grid-template-columns  → flex children with percentage widths"
    echo "  position: sticky       → position: fixed (or JS IntersectionObserver polyfill)"
    echo "  backdrop-filter        → background-color: rgba(0,0,0,0.7)"
    echo "  :focus-visible         → :focus"
    echo "  :is()/:where()         → .class1, .class2 (expand selectors)"
    echo "  aspect-ratio: 16/9     → padding-bottom: 56.25% (on a wrapper)"
    echo "  clamp(1rem, 3vw, 2rem) → media queries with fixed values"
    echo "  margin-inline          → margin-left + margin-right"
    echo "  inset: 0               → top: 0; right: 0; bottom: 0; left: 0"
    echo "  scroll-behavior:smooth → JS: el.scrollIntoView({behavior:'smooth'})"
    echo ""
    echo "Reference: .claude/rules/es5-compliance.md (CSS section)"
    echo "Constitution: .specify/memory/constitution.md (Principle III)"
    echo ""
    exit 1
fi

if [[ -n "$WARNINGS" ]]; then
    log_hook "WARN: iOS 9 CSS concerns in $FILE_PATH"
    echo ""
    echo "WARNING: iOS 9 CSS Compatibility Concerns"
    echo "==========================================="
    echo ""
    echo "The following CSS features have limited or no iOS 9 support."
    echo "They are pre-existing technical debt and won't block this edit,"
    echo "but be aware they degrade on target devices:"
    echo ""
    echo -e "$WARNINGS"
    echo ""
    echo "If writing NEW CSS, prefer iOS 9 compatible alternatives."
    echo "If editing existing code, consider fixing these while you're there."
    echo ""
fi

log_hook "PASS: iOS 9 CSS compatible - $FILE_PATH"
exit 0

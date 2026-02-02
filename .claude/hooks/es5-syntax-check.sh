#!/bin/bash
# ES5 Syntax Check - BLOCKS ES6+ syntax in legacy frontend
#
# This hook runs before Edit/Write operations on legacy JS files.
# It checks for ES6+ syntax that breaks on iOS 9 Safari.
#
# Exit 0: Allow the edit
# Exit 1: Block the edit (ES6+ found)

set -e

# Require jq for JSON parsing
if ! command -v jq >/dev/null 2>&1; then
    echo "[es5-check] jq not found - install with: sudo apt install jq"
    exit 0  # Don't block, just warn
fi

# Hook logging setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_LOG_DIR="$SCRIPT_DIR/../logs"
HOOK_LOG="$HOOK_LOG_DIR/hooks.log"
mkdir -p "$HOOK_LOG_DIR"

log_hook() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [es5-check] $1" >> "$HOOK_LOG"
}

# Read JSON input from stdin
INPUT=$(cat)

# Extract file path and new content from JSON
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
NEW_CONTENT=$(echo "$INPUT" | jq -r '.tool_input.new_string // .tool_input.content // empty')

# Skip if no file path
if [[ -z "$FILE_PATH" ]]; then
    exit 0
fi

# Only check legacy JavaScript files
if [[ ! "$FILE_PATH" =~ apps/legacy/static/legacy/js ]]; then
    exit 0
fi

# Skip if no new content
if [[ -z "$NEW_CONTENT" ]]; then
    exit 0
fi

log_hook "Checking: $FILE_PATH"

VIOLATIONS=""

# Check for const declarations
if echo "$NEW_CONTENT" | grep -qE '\bconst\s+'; then
    VIOLATIONS="${VIOLATIONS}  - Found 'const' declaration (use 'var' for ES5)\n"
fi

# Check for let declarations
if echo "$NEW_CONTENT" | grep -qE '\blet\s+'; then
    VIOLATIONS="${VIOLATIONS}  - Found 'let' declaration (use 'var' for ES5)\n"
fi

# Check for arrow functions
if echo "$NEW_CONTENT" | grep -qE '=>'; then
    VIOLATIONS="${VIOLATIONS}  - Found arrow function '=>' (use 'function()' for ES5)\n"
fi

# Check for template literals
if echo "$NEW_CONTENT" | grep -qE '`[^`]*\$\{'; then
    VIOLATIONS="${VIOLATIONS}  - Found template literal with \${} (use string concatenation for ES5)\n"
fi

# Check for async functions
if echo "$NEW_CONTENT" | grep -qE '\basync\s+(function|\(|[a-zA-Z_])'; then
    VIOLATIONS="${VIOLATIONS}  - Found 'async' keyword (use callbacks/promises for ES5)\n"
fi

# Check for await
if echo "$NEW_CONTENT" | grep -qE '\bawait\s+'; then
    VIOLATIONS="${VIOLATIONS}  - Found 'await' keyword (use .then() for ES5)\n"
fi

# Check for class declarations
if echo "$NEW_CONTENT" | grep -qE '\bclass\s+[A-Z]'; then
    VIOLATIONS="${VIOLATIONS}  - Found 'class' declaration (use function constructors for ES5)\n"
fi

# Check for destructuring in variable declarations
if echo "$NEW_CONTENT" | grep -qE '\b(var|let|const)\s+\{.*\}\s*='; then
    VIOLATIONS="${VIOLATIONS}  - Found object destructuring (use direct property access for ES5)\n"
fi

if echo "$NEW_CONTENT" | grep -qE '\b(var|let|const)\s+\[.*\]\s*='; then
    VIOLATIONS="${VIOLATIONS}  - Found array destructuring (use array indices for ES5)\n"
fi

# Check for spread operator
if echo "$NEW_CONTENT" | grep -qE '\.\.\.[a-zA-Z_]'; then
    VIOLATIONS="${VIOLATIONS}  - Found spread operator '...' (use .concat() or loops for ES5)\n"
fi

# Check for default parameters
if echo "$NEW_CONTENT" | grep -qE 'function\s+\w+\s*\([^)]*=[^)]*\)'; then
    VIOLATIONS="${VIOLATIONS}  - Found default parameters (check inside function for ES5)\n"
fi

# Check for object method shorthand
if echo "$NEW_CONTENT" | grep -qE '\{\s*\w+\s*\([^)]*\)\s*\{'; then
    VIOLATIONS="${VIOLATIONS}  - Found method shorthand {method() {}} (use {method: function() {}} for ES5)\n"
fi

# Check for object property shorthand
if echo "$NEW_CONTENT" | grep -qE '\{\s*\w+\s*,|\{\s*\w+\s*\}'; then
    # This is a heuristic - might have false positives
    # Only warn, don't block
    log_hook "WARNING: Possible object shorthand {x} - verify it's {x: x} for ES5"
fi

if [[ -n "$VIOLATIONS" ]]; then
    log_hook "BLOCKED: ES6+ syntax in $FILE_PATH"
    echo ""
    echo "BLOCKED: ES6+ Syntax Detected in Legacy Frontend"
    echo "================================================"
    echo ""
    echo "iOS 9 Safari requires ES5 syntax only:"
    echo -e "$VIOLATIONS"
    echo ""
    echo "Common fixes:"
    echo "  const/let           → var"
    echo "  () => {}            → function() {}"
    echo "  \`Hello \${name}\`    → 'Hello ' + name"
    echo "  async/await         → callbacks or .then()"
    echo "  {x, y} = obj        → var x = obj.x; var y = obj.y;"
    echo "  [...arr]            → arr.slice() or arr.concat()"
    echo "  class Foo {}        → function Foo() {}"
    echo "  function(x = 1) {}  → function(x) { x = x || 1; }"
    echo "  {method() {}}       → {method: function() {}}"
    echo ""
    echo "Reference: .claude/rules/es5-compliance.md"
    echo ""
    echo "After fixing:"
    echo "  1. Re-attempt your edit"
    echo "  2. Restart containers: docker compose down && docker compose up -d"
    echo "  3. Verify: grep 'your change' ./staticfiles/legacy/js/..."
    echo "  4. Test on iPad: Clear Safari cache before testing"
    exit 1
fi

log_hook "PASS: ES5 compliant - $FILE_PATH"
exit 0

#!/bin/bash
# ES5 Syntax Check - BLOCKS ES6+ syntax in legacy frontend
#
# This hook runs before Edit/Write operations on legacy JS files.
# It checks for ES6+ syntax that breaks on iOS 9 Safari.
#
# Exit 0: Allow the edit
# Exit 1: Block the edit (ES6+ found)

set -e

# Source common hook library
source "$(dirname "${BASH_SOURCE[0]}")/lib/common.sh"
init_hook "es5-check"

# Extract file path and new content
FILE_PATH=$(get_file_path)
NEW_CONTENT=$(get_new_content)

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

# Run all checks in a single pass for efficiency
VIOLATIONS=$(echo "$NEW_CONTENT" | awk '
    # const declarations
    /\<const[[:space:]]+/ {
        violations = violations "  - Found const declaration (use var for ES5)\n"
    }

    # let declarations
    /\<let[[:space:]]+/ {
        violations = violations "  - Found let declaration (use var for ES5)\n"
    }

    # Arrow functions: => but not >= or <=
    # Look for patterns like ) => or x => or (x) =>
    /[)a-zA-Z_0-9][[:space:]]*=>/ {
        violations = violations "  - Found arrow function => (use function() for ES5)\n"
    }

    # Template literals with interpolation
    /`[^`]*\$\{/ {
        violations = violations "  - Found template literal ${} (use string concatenation for ES5)\n"
    }

    # async keyword
    /\<async[[:space:]]+(function|\(|[a-zA-Z_])/ {
        violations = violations "  - Found async keyword (use callbacks/promises for ES5)\n"
    }

    # await keyword
    /\<await[[:space:]]+/ {
        violations = violations "  - Found await keyword (use .then() for ES5)\n"
    }

    # class declarations
    /\<class[[:space:]]+[A-Z]/ {
        violations = violations "  - Found class declaration (use function constructors for ES5)\n"
    }

    # for...of loops
    /\<for[[:space:]]*\([^)]*\<of\>/ {
        violations = violations "  - Found for...of loop (use for loop with index for ES5)\n"
    }

    # Object destructuring: var/let/const { = or function({
    /\<(var|let|const)[[:space:]]+\{[^}]*\}[[:space:]]*=/ {
        violations = violations "  - Found object destructuring (use direct property access for ES5)\n"
    }

    # Array destructuring
    /\<(var|let|const)[[:space:]]+\[[^\]]*\][[:space:]]*=/ {
        violations = violations "  - Found array destructuring (use array indices for ES5)\n"
    }

    # Spread operator in array/object context (not rest params)
    /\.\.\.[a-zA-Z_][a-zA-Z0-9_]*/ {
        # Skip if it looks like rest parameter in function definition
        if (!/function[^{]*\.\.\.[a-zA-Z_]/) {
            violations = violations "  - Found spread operator ... (use .concat() or loops for ES5)\n"
        }
    }

    # Default parameters in function
    /function[[:space:]]+[a-zA-Z_][a-zA-Z0-9_]*[[:space:]]*\([^)]*=[^)]*\)/ {
        violations = violations "  - Found default parameters (use x = x || default inside function for ES5)\n"
    }

    # ES6 built-ins that dont exist in ES5
    /\<(Symbol|Map|Set|WeakMap|WeakSet|Proxy|Reflect)\>/ {
        violations = violations "  - Found ES6 built-in (Symbol/Map/Set/etc not available in ES5)\n"
    }

    # Object method shorthand { method() {} }
    /\{[^}]*[a-zA-Z_][a-zA-Z0-9_]*[[:space:]]*\([^)]*\)[[:space:]]*\{/ {
        # Crude check - may have false positives
        if (!/function/) {
            violations = violations "  - Possible method shorthand {method(){}} (use {method: function(){}} for ES5)\n"
        }
    }

    END {
        if (violations != "") {
            print violations
            exit 1
        }
        exit 0
    }
')
AWK_EXIT=$?

if [[ $AWK_EXIT -ne 0 ]]; then
    log_hook "BLOCKED: ES6+ syntax in $FILE_PATH"
    echo ""
    echo "BLOCKED: ES6+ Syntax Detected in Legacy Frontend"
    echo "================================================"
    echo ""
    echo "iOS 9 Safari requires ES5 syntax only:"
    echo -e "$VIOLATIONS"
    echo ""
    echo "Common fixes:"
    echo "  const/let           -> var"
    echo "  () => {}            -> function() {}"
    echo "  \`Hello \${name}\`    -> 'Hello ' + name"
    echo "  async/await         -> callbacks or .then()"
    echo "  for (x of arr)      -> for (var i = 0; i < arr.length; i++)"
    echo "  {x, y} = obj        -> var x = obj.x; var y = obj.y;"
    echo "  [...arr]            -> arr.slice() or arr.concat()"
    echo "  class Foo {}        -> function Foo() {}"
    echo "  function(x = 1)     -> function(x) { x = x || 1; }"
    echo "  {method() {}}       -> {method: function() {}}"
    echo ""
    echo "Reference: .claude/rules/es5-compliance.md"
    exit 1
fi

log_hook "PASS: ES5 compliant - $FILE_PATH"
exit 0

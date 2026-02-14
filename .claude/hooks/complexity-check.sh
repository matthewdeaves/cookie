#!/bin/bash
# Complexity Check - BLOCKS functions exceeding quality gates
#
# This hook runs before Edit/Write operations.
# It checks for functions exceeding max lines (100).
#
# Exit 0: Allow the edit
# Exit 1: Block the edit (quality gate exceeded)

set -e

# Source common hook library
source "$(dirname "${BASH_SOURCE[0]}")/lib/common.sh"
init_hook "complexity-check"

# Extract file path and new content
FILE_PATH=$(get_file_path)
NEW_CONTENT=$(get_new_content)

# Skip if no file path
if [[ -z "$FILE_PATH" ]]; then
    exit 0
fi

# Skip if no new content
if [[ -z "$NEW_CONTENT" ]]; then
    exit 0
fi

# Only check source files (not tests, not configs, not migrations)
if [[ "$FILE_PATH" =~ (test_|_test\.py|\.test\.|\.spec\.|conftest|config|settings|migrations/) ]]; then
    exit 0
fi

log_hook "Checking: $FILE_PATH"

MAX_LINES=100

# Check Python files
if [[ "$FILE_PATH" =~ \.py$ ]]; then
    # Use a temp file to capture both output and exit status
    RESULT=$(echo "$NEW_CONTENT" | awk -v max="$MAX_LINES" '
        BEGIN { violations = 0 }

        # Match function definitions (def at start or indented)
        /^[[:space:]]*def [a-zA-Z_]/ {
            # If we were in a function, check its length
            if (in_func && func_lines > max) {
                print "  - " func_name " (" func_lines " lines, max " max ")"
                violations++
            }
            # Start new function
            in_func = 1
            func_lines = 1
            # Extract function name
            match($0, /def ([a-zA-Z_][a-zA-Z0-9_]*)/, arr)
            func_name = arr[1]
            func_indent = match($0, /[^[:space:]]/) - 1
            next
        }

        # Match class definitions (ends current function)
        /^[[:space:]]*class [A-Z]/ {
            if (in_func && func_lines > max) {
                print "  - " func_name " (" func_lines " lines, max " max ")"
                violations++
            }
            in_func = 0
            next
        }

        # Track lines in function
        in_func {
            # Check if this line ends the function (same or less indent, non-empty, non-comment)
            if (/^[^[:space:]#]/ || (/^[[:space:]]/ && match($0, /[^[:space:]]/) - 1 <= func_indent && !/^[[:space:]]*#/ && !/^[[:space:]]*$/)) {
                if (!/^[[:space:]]*$/ && !/^[[:space:]]*#/) {
                    # End of function
                    if (func_lines > max) {
                        print "  - " func_name " (" func_lines " lines, max " max ")"
                        violations++
                    }
                    in_func = 0
                }
            }
            func_lines++
        }

        END {
            # Check last function
            if (in_func && func_lines > max) {
                print "  - " func_name " (" func_lines " lines, max " max ")"
                violations++
            }
            if (violations > 0) {
                exit 1
            }
        }
    ' 2>&1)
    AWK_EXIT=$?

    if [[ $AWK_EXIT -ne 0 ]]; then
        log_hook "BLOCKED: Function too long in $FILE_PATH"
        echo ""
        echo "BLOCKED: Function Length Exceeded"
        echo "=================================="
        echo ""
        echo "Functions exceeding $MAX_LINES lines:"
        echo "$RESULT"
        echo ""
        echo "Quality gate: Max $MAX_LINES lines per function (prefer 50)"
        echo ""
        echo "Next steps:"
        echo "  1. Extract helper functions to reduce size"
        echo "  2. Apply Single Responsibility Principle"
        echo "  3. See .claude/rules/code-quality.md for examples"
        echo ""
        echo "DO NOT raise the limit in linter configs!"
        exit 1
    fi
fi

# Check JavaScript/TypeScript files
if [[ "$FILE_PATH" =~ \.(js|ts|jsx|tsx)$ ]]; then
    RESULT=$(echo "$NEW_CONTENT" | awk -v max="$MAX_LINES" '
        BEGIN { violations = 0; depth = 0; in_func = 0 }

        # Track function starts
        /function[[:space:]]+[a-zA-Z_]|function[[:space:]]*\(|=>[[:space:]]*\{|[a-zA-Z_][a-zA-Z0-9_]*[[:space:]]*\([^)]*\)[[:space:]]*\{/ {
            if (!in_func) {
                in_func = 1
                func_start = NR
                func_depth = depth
                # Try to extract function name
                if (match($0, /function[[:space:]]+([a-zA-Z_][a-zA-Z0-9_]*)/, arr)) {
                    func_name = arr[1]
                } else if (match($0, /([a-zA-Z_][a-zA-Z0-9_]*)[[:space:]]*[=:][[:space:]]*(async[[:space:]]*)?function/, arr)) {
                    func_name = arr[1]
                } else if (match($0, /([a-zA-Z_][a-zA-Z0-9_]*)[[:space:]]*[=:][[:space:]]*(async[[:space:]]*)?\(/, arr)) {
                    func_name = arr[1]
                } else {
                    func_name = "(anonymous)"
                }
            }
        }

        # Count braces
        {
            # Count opening braces
            line = $0
            while (match(line, /\{/)) {
                depth++
                line = substr(line, RSTART + 1)
            }
            # Count closing braces
            line = $0
            while (match(line, /\}/)) {
                depth--
                if (in_func && depth <= func_depth) {
                    # Function ended
                    func_lines = NR - func_start + 1
                    if (func_lines > max) {
                        print "  - " func_name " (" func_lines " lines, max " max ")"
                        violations++
                    }
                    in_func = 0
                }
                line = substr(line, RSTART + 1)
            }
        }

        END {
            if (violations > 0) exit 1
        }
    ' 2>&1)
    AWK_EXIT=$?

    if [[ $AWK_EXIT -ne 0 ]]; then
        log_hook "BLOCKED: Function too long in $FILE_PATH"
        echo ""
        echo "BLOCKED: Function Length Exceeded"
        echo "=================================="
        echo ""
        echo "Functions exceeding $MAX_LINES lines:"
        echo "$RESULT"
        echo ""
        echo "Quality gate: Max $MAX_LINES lines per function (prefer 50)"
        echo ""
        echo "Next steps:"
        echo "  1. Extract helper functions to reduce size"
        echo "  2. Apply Single Responsibility Principle"
        echo "  3. See .claude/rules/code-quality.md for examples"
        echo ""
        echo "DO NOT raise the limit in ESLint config!"
        exit 1
    fi
fi

log_hook "PASS: Complexity OK - $FILE_PATH"
exit 0

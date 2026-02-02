#!/bin/bash
# Complexity Check - BLOCKS functions exceeding quality gates
#
# This hook runs before Edit/Write operations.
# It checks for functions exceeding max lines (100) or complexity (15).
#
# Exit 0: Allow the edit
# Exit 1: Block the edit (quality gate exceeded)

set -e

# Require jq for JSON parsing
if ! command -v jq >/dev/null 2>&1; then
    echo "[complexity-check] jq not found - install with: sudo apt install jq"
    exit 0  # Don't block, just warn
fi

# Hook logging setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_LOG_DIR="$SCRIPT_DIR/../logs"
HOOK_LOG="$HOOK_LOG_DIR/hooks.log"
mkdir -p "$HOOK_LOG_DIR"

log_hook() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [complexity-check] $1" >> "$HOOK_LOG"
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

# Skip if no new content
if [[ -z "$NEW_CONTENT" ]]; then
    exit 0
fi

# Only check source files (not tests, not configs)
if [[ "$FILE_PATH" =~ (test_|_test\.py|\.test\.|\.spec\.|config|settings) ]]; then
    exit 0
fi

log_hook "Checking: $FILE_PATH"

# Check Python files with basic heuristics
if [[ "$FILE_PATH" =~ \.py$ ]]; then
    # Count lines in functions (def to next def/class/end)
    # This is a simple heuristic, not perfect
    FUNCTION_LINES=$(echo "$NEW_CONTENT" | awk '
        /^def / || /^    def / {
            if (in_func && line_count > 100) {
                print "Function starting at line " start_line " has " line_count " lines (max: 100)"
                violations++
            }
            in_func = 1
            start_line = NR
            line_count = 0
        }
        in_func { line_count++ }
        /^def / || /^class / || /^[^ \t]/ {
            if (in_func && NR != start_line && line_count > 100) {
                print "Function starting at line " start_line " has " line_count " lines (max: 100)"
                violations++
            }
            in_func = 0
        }
        END {
            if (in_func && line_count > 100) {
                print "Function starting at line " start_line " has " line_count " lines (max: 100)"
                violations++
            }
            if (violations > 0) exit 1
        }
    ')

    if [[ $? -ne 0 ]]; then
        log_hook "BLOCKED: Function too long in $FILE_PATH"
        echo ""
        echo "BLOCKED: Function Length Exceeded"
        echo "=================================="
        echo ""
        echo "$FUNCTION_LINES"
        echo ""
        echo "Quality gate: Max 100 lines per function (prefer 50)"
        echo ""
        echo "Next steps:"
        echo "  1. Extract helper functions to reduce size"
        echo "  2. Apply Single Responsibility Principle"
        echo "  3. See .claude/rules/code-quality.md for refactoring examples"
        echo ""
        echo "DO NOT raise the limit in linter configs!"
        exit 1
    fi
fi

# Check JavaScript/TypeScript files
if [[ "$FILE_PATH" =~ \.(js|ts|jsx|tsx)$ ]]; then
    # Count lines in functions (function/arrow to closing brace)
    # Simple heuristic
    FUNCTION_LINES=$(echo "$NEW_CONTENT" | awk '
        /function |=>.*\{|^  [a-zA-Z_]+\(.*\).*\{/ {
            if (in_func && line_count > 100) {
                print "Function starting at line " start_line " has " line_count " lines (max: 100)"
                violations++
            }
            in_func = 1
            start_line = NR
            line_count = 0
            brace_depth = 0
        }
        in_func {
            line_count++
            # Track brace depth
            gsub(/[^{]/, "", $0)
            brace_depth += length($0)
            gsub(/[^}]/, "", $0)
            brace_depth -= length($0)

            if (brace_depth == 0 && line_count > 2) {
                if (line_count > 100) {
                    print "Function starting at line " start_line " has " line_count " lines (max: 100)"
                    violations++
                }
                in_func = 0
            }
        }
        END {
            if (violations > 0) exit 1
        }
    ')

    if [[ $? -ne 0 ]]; then
        log_hook "BLOCKED: Function too long in $FILE_PATH"
        echo ""
        echo "BLOCKED: Function Length Exceeded"
        echo "=================================="
        echo ""
        echo "$FUNCTION_LINES"
        echo ""
        echo "Quality gate: Max 100 lines per function (prefer 50)"
        echo ""
        echo "Next steps:"
        echo "  1. Extract helper functions to reduce size"
        echo "  2. Apply Single Responsibility Principle"
        echo "  3. See .claude/rules/code-quality.md for refactoring examples"
        echo ""
        echo "DO NOT raise the limit in ESLint config!"
        exit 1
    fi
fi

log_hook "PASS: Complexity OK - $FILE_PATH"
exit 0

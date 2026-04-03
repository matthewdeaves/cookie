#!/bin/bash
# Unsafe Django Template Check - BLOCKS XSS-prone patterns in templates
#
# This hook runs before Edit/Write operations on Django template files.
# It checks for |safe, mark_safe, and {% autoescape off %} usage that
# bypasses Django's auto-escaping and can lead to stored XSS.
#
# Exit 0: Allow the edit
# Exit 1: Block the edit (unsafe pattern found)

set -e

if ! command -v jq >/dev/null 2>&1; then
    exit 0
fi

# Hook logging setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_LOG_DIR="$SCRIPT_DIR/../logs"
HOOK_LOG="$HOOK_LOG_DIR/hooks.log"
mkdir -p "$HOOK_LOG_DIR"

log_hook() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [unsafe-template] $1" >> "$HOOK_LOG"
}

# Read JSON input from stdin
INPUT=$(cat)

FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
NEW_CONTENT=$(echo "$INPUT" | jq -r '.tool_input.new_string // .tool_input.content // empty')

if [[ -z "$FILE_PATH" ]]; then
    exit 0
fi

# Only check Django template files under apps/
if [[ ! "$FILE_PATH" =~ apps/.*\.html$ ]]; then
    exit 0
fi

if [[ -z "$NEW_CONTENT" ]]; then
    exit 0
fi

log_hook "Checking: $FILE_PATH"

VIOLATIONS=""

# Check for |safe filter (the main XSS vector)
if echo "$NEW_CONTENT" | grep -qE '\|safe\b'; then
    VIOLATIONS="${VIOLATIONS}  - Found '|safe' filter (bypasses Django auto-escaping)\n"
fi

# Check for {% autoescape off %}
if echo "$NEW_CONTENT" | grep -qE '\{%\s*autoescape\s+off\s*%\}'; then
    VIOLATIONS="${VIOLATIONS}  - Found '{% autoescape off %}' (disables escaping for entire block)\n"
fi

# Check for mark_safe in inline template code or template tags
if echo "$NEW_CONTENT" | grep -qE 'mark_safe\s*\('; then
    VIOLATIONS="${VIOLATIONS}  - Found 'mark_safe()' (marks string as safe HTML without escaping)\n"
fi

if [[ -n "$VIOLATIONS" ]]; then
    log_hook "BLOCKED: Unsafe template pattern in $FILE_PATH"
    echo ""
    echo "BLOCKED: Unsafe Django Template Pattern Detected"
    echo "================================================="
    echo ""
    echo "The following patterns bypass Django's auto-escaping and"
    echo "can lead to stored XSS vulnerabilities:"
    echo ""
    echo -e "$VIOLATIONS"
    echo ""
    echo "Safe alternatives:"
    echo "  {{ data|json_script:'id' }}  — for passing data to JavaScript"
    echo "  {{ variable }}               — auto-escaped by default"
    echo "  nh3.clean(text, tags=set())  — sanitize in Python before storage"
    echo ""
    echo "This project stripped all |safe usage to fix XSS (commit 7c63a99c)."
    echo "See: apps/recipes/services/sanitizer.py for the sanitization pattern."
    echo "See: .claude/rules/django-security.md for full security rules."
    echo ""
    exit 1
fi

log_hook "PASS: No unsafe template patterns - $FILE_PATH"
exit 0

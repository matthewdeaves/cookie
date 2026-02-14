#!/bin/bash
# Common functions for Claude Code hooks
#
# Source this at the start of hook scripts:
#   source "$(dirname "${BASH_SOURCE[0]}")/lib/common.sh"
#
# Provides:
#   - jq requirement check
#   - Logging setup (log_hook function)
#   - JSON input parsing (HOOK_INPUT, get_file_path, get_new_content)

# Exit if jq not available
require_jq() {
    if ! command -v jq >/dev/null 2>&1; then
        echo "[hook] jq not found - install with: sudo apt install jq"
        exit 0  # Don't block, just skip
    fi
}

# Setup logging
# Usage: setup_logging "hook-name"
setup_logging() {
    local hook_name="$1"
    HOOK_NAME="$hook_name"

    # Derive paths from this library file's location
    local lib_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    HOOK_LOG_DIR="$lib_dir/../../logs"
    HOOK_LOG="$HOOK_LOG_DIR/hooks.log"
    mkdir -p "$HOOK_LOG_DIR"
}

# Log a message with timestamp
# Usage: log_hook "message"
log_hook() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$HOOK_NAME] $1" >> "$HOOK_LOG"
}

# Read JSON input from stdin (call once, stores in HOOK_INPUT)
# Usage: read_input
read_input() {
    HOOK_INPUT=$(cat)
}

# Get file_path from hook input
# Usage: FILE_PATH=$(get_file_path)
get_file_path() {
    echo "$HOOK_INPUT" | jq -r '.tool_input.file_path // empty'
}

# Get new content from hook input (works for Edit and Write)
# Usage: NEW_CONTENT=$(get_new_content)
get_new_content() {
    echo "$HOOK_INPUT" | jq -r '.tool_input.new_string // .tool_input.content // empty'
}

# Get command from Bash hook input
# Usage: COMMAND=$(get_command)
get_command() {
    echo "$HOOK_INPUT" | jq -r '.tool_input.command // empty'
}

# Check if file path matches pattern
# Usage: if matches_path "apps/legacy/"; then ...
matches_path() {
    local pattern="$1"
    local file_path=$(get_file_path)
    [[ "$file_path" =~ $pattern ]]
}

# Check if file is a test file
# Usage: if is_test_file; then exit 0; fi
is_test_file() {
    local file_path=$(get_file_path)
    [[ "$file_path" =~ (test_|_test\.py|\.test\.|\.spec\.|tests/|__tests__/) ]]
}

# Standard initialization for Claude Code hooks
# Usage: init_hook "hook-name"
init_hook() {
    local hook_name="$1"
    require_jq
    setup_logging "$hook_name"
    read_input
}

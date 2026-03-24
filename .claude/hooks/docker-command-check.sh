#!/bin/bash
# Docker Command Check - WARNS about host commands that should use Docker
#
# This hook runs before Bash operations.
# It checks for Python/Django/npm commands that should run in containers.
#
# Exit 0: Allow (with warning if needed)
# Exit 1: Block (reserved for critical violations)

set -e

# Require jq for JSON parsing
if ! command -v jq >/dev/null 2>&1; then
    exit 0  # No jq, can't check
fi

# Hook logging setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_LOG_DIR="$SCRIPT_DIR/../logs"
HOOK_LOG="$HOOK_LOG_DIR/hooks.log"
mkdir -p "$HOOK_LOG_DIR"

log_hook() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [docker-check] $1" >> "$HOOK_LOG"
}

# Read JSON input from stdin
INPUT=$(cat)

# Extract command from Bash tool input
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Skip if no command
if [[ -z "$COMMAND" ]]; then
    exit 0
fi

log_hook "Checking command: $COMMAND"

WARNINGS=""

# Check for Python commands (should be in web container)
if echo "$COMMAND" | grep -qE '^\s*python\s+'; then
    if ! echo "$COMMAND" | grep -q "docker compose exec"; then
        WARNINGS="${WARNINGS}  - Running Python on host (should use: docker compose exec web python ...)\n"
    fi
fi

# Check for Django manage.py (should be in web container)
if echo "$COMMAND" | grep -qE 'manage\.py'; then
    if ! echo "$COMMAND" | grep -q "docker compose exec"; then
        WARNINGS="${WARNINGS}  - Running manage.py on host (should use: docker compose exec web python manage.py ...)\n"
    fi
fi

# Check for pytest (should be in web container)
if echo "$COMMAND" | grep -qE '^\s*pytest\s+'; then
    if ! echo "$COMMAND" | grep -q "docker compose exec"; then
        WARNINGS="${WARNINGS}  - Running pytest on host (should use: docker compose exec web python -m pytest)\n"
    fi
fi

# Check for pip (should be in web container)
if echo "$COMMAND" | grep -qE '^\s*pip\s+'; then
    if ! echo "$COMMAND" | grep -q "docker compose exec"; then
        WARNINGS="${WARNINGS}  - Running pip on host (should use: docker compose exec web pip ...)\n"
    fi
fi

# Check for npm commands (might need frontend container)
if echo "$COMMAND" | grep -qE '^\s*npm\s+(test|install|run)'; then
    # Check if we're in frontend directory or if it's frontend-related
    if ! echo "$COMMAND" | grep -q "docker compose exec"; then
        # Could be OK if in frontend dir on host, but warn anyway
        log_hook "WARNING: npm command on host - verify it's intentional"
    fi
fi

if [[ -n "$WARNINGS" ]]; then
    log_hook "WARNING: Possible host command in Docker-only environment"
    echo ""
    echo "⚠️  WARNING: Docker Environment Check"
    echo "====================================="
    echo ""
    echo "This command may run on host instead of in Docker:"
    echo -e "$WARNINGS"
    echo ""
    echo "The host has NO Python/Django installed!"
    echo ""
    echo "If you see 'ModuleNotFoundError', use Docker:"
    echo "  docker compose exec web python ..."
    echo "  docker compose exec frontend npm ..."
    echo ""
    echo "See .claude/rules/docker-environment.md for details"
    echo ""
    # Allow the command but warn
fi

log_hook "Checked: $COMMAND"
exit 0

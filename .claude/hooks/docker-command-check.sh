#!/bin/bash
# Docker Command Check - WARNS about host commands that should use Docker
#
# This hook runs before Bash operations.
# It checks for Python/Django/npm commands that should run in containers.
#
# Exit 0: Allow (with warning if needed)
# Exit 1: Block (reserved for critical violations)

set -e

# Source common hook library
source "$(dirname "${BASH_SOURCE[0]}")/lib/common.sh"
init_hook "docker-check"

# Extract command from Bash tool input
COMMAND=$(get_command)

# Skip if no command
if [[ -z "$COMMAND" ]]; then
    exit 0
fi

log_hook "Checking command: $COMMAND"

WARNINGS=""

# Helper to check if command already uses docker
uses_docker() {
    echo "$COMMAND" | grep -qE "(docker compose exec|docker exec|docker run)"
}

# Check for Python commands (should be in web container)
if echo "$COMMAND" | grep -qE '^\s*(python|python3)\s+'; then
    if ! uses_docker; then
        WARNINGS="${WARNINGS}  - python/python3: use 'docker compose exec web python ...'\n"
    fi
fi

# Check for Django manage.py (should be in web container)
if echo "$COMMAND" | grep -qE 'manage\.py'; then
    if ! uses_docker; then
        WARNINGS="${WARNINGS}  - manage.py: use 'docker compose exec web python manage.py ...'\n"
    fi
fi

# Check for pytest (should be in web container)
if echo "$COMMAND" | grep -qE '^\s*pytest'; then
    if ! uses_docker; then
        WARNINGS="${WARNINGS}  - pytest: use 'docker compose exec web python -m pytest'\n"
    fi
fi

# Check for pip (should be in web container)
if echo "$COMMAND" | grep -qE '^\s*pip3?\s+'; then
    if ! uses_docker; then
        WARNINGS="${WARNINGS}  - pip: use 'docker compose exec web pip ...'\n"
    fi
fi

# Check for ruff (should be in web container)
if echo "$COMMAND" | grep -qE '^\s*ruff\s+'; then
    if ! uses_docker; then
        WARNINGS="${WARNINGS}  - ruff: use 'docker compose exec web ruff ...'\n"
    fi
fi

# Check for mypy (should be in web container)
if echo "$COMMAND" | grep -qE '^\s*mypy\s+'; then
    if ! uses_docker; then
        WARNINGS="${WARNINGS}  - mypy: use 'docker compose exec web mypy ...'\n"
    fi
fi

# Check for django-admin (should be in web container)
if echo "$COMMAND" | grep -qE '^\s*django-admin\s+'; then
    if ! uses_docker; then
        WARNINGS="${WARNINGS}  - django-admin: use 'docker compose exec web django-admin ...'\n"
    fi
fi

# Check for npm commands (should be in frontend container)
if echo "$COMMAND" | grep -qE '^\s*npm\s+(test|install|run|start|build)'; then
    if ! uses_docker; then
        WARNINGS="${WARNINGS}  - npm: use 'docker compose exec frontend npm ...'\n"
    fi
fi

# Check for npx commands related to frontend
if echo "$COMMAND" | grep -qE '^\s*npx\s+(eslint|tsc|vite|vitest)'; then
    if ! uses_docker; then
        WARNINGS="${WARNINGS}  - npx: use 'docker compose exec frontend npx ...'\n"
    fi
fi

if [[ -n "$WARNINGS" ]]; then
    log_hook "WARNING: Possible host command in Docker-only environment"
    echo ""
    echo "WARNING: Docker Environment Check"
    echo "=================================="
    echo ""
    echo "These commands should run in Docker containers:"
    echo -e "$WARNINGS"
    echo ""
    echo "The host has NO Python/Django/Node installed!"
    echo ""
    echo "Correct usage:"
    echo "  docker compose exec web python ...       # Python/Django"
    echo "  docker compose exec web python -m pytest # Tests"
    echo "  docker compose exec frontend npm ...     # Frontend"
    echo ""
    echo "See .claude/rules/docker-environment.md for details"
    echo ""
    # Allow the command but warn - user might know what they're doing
fi

log_hook "Checked: $COMMAND"
exit 0

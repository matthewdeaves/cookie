#!/bin/bash
# Post-Edit Lint - Immediate feedback after file edits
#
# Runs linting on edited files to catch issues early.
# This is an informational hook - it warns but doesn't block.
#
# Claude Code hooks receive JSON on stdin.

set -e

# Source common hook library
source "$(dirname "${BASH_SOURCE[0]}")/lib/common.sh"
init_hook "lint"

# Extract file path from JSON (works for both Edit and Write tools)
FILE_PATH=$(get_file_path)

# Skip if no file path
if [[ -z "$FILE_PATH" ]]; then
    exit 0
fi

# Skip if file doesn't exist
if [[ ! -f "$FILE_PATH" ]]; then
    exit 0
fi

log_hook "Checking: $FILE_PATH"

# Derive project root from git or script location
PROJECT_ROOT=$(git -C "$(dirname "$FILE_PATH")" rev-parse --show-toplevel 2>/dev/null || echo "$SCRIPT_DIR/../..")
PROJECT_ROOT=$(cd "$PROJECT_ROOT" && pwd)

# Timeout for docker commands (10 seconds)
TIMEOUT_CMD="timeout 10"

# Python files - run Ruff
if [[ "$FILE_PATH" =~ \.py$ ]]; then
    # Skip test files and migrations
    if [[ "$FILE_PATH" =~ (test_|_test\.py|conftest\.py|migrations/) ]]; then
        exit 0
    fi

    # Check if Docker is available and web container is running
    if docker compose version >/dev/null 2>&1; then
        if docker compose ps --status running 2>/dev/null | grep -q web; then
            REL_PATH="${FILE_PATH#$PROJECT_ROOT/}"
            OUTPUT=$($TIMEOUT_CMD docker compose exec -T web ruff check "$REL_PATH" 2>&1) || {
                EXIT_CODE=$?
                if [[ $EXIT_CODE -eq 124 ]]; then
                    log_hook "TIMEOUT: Ruff check timed out"
                    echo "[lint] Ruff check timed out - skipping"
                    exit 0
                fi
                log_hook "Lint issues in $FILE_PATH"
                echo ""
                echo "[lint] Issues found in $(basename "$FILE_PATH"):"
                echo "$OUTPUT" | head -15
                echo ""
                echo "Auto-fix: docker compose exec web ruff check --fix $REL_PATH"
                exit 0
            }
            log_hook "OK: $FILE_PATH"
            echo "[lint] $(basename "$FILE_PATH") OK"
        else
            log_hook "SKIP: Web container not running"
        fi
    fi
fi

# Legacy JavaScript files - run ESLint with ES5 config
if [[ "$FILE_PATH" =~ apps/legacy/static/legacy/js/.*\.js$ ]]; then
    ESLINT_CONFIG="$PROJECT_ROOT/apps/legacy/static/legacy/.eslintrc.json"
    if [[ -f "$ESLINT_CONFIG" ]]; then
        # Check if npx is available
        if command -v npx >/dev/null 2>&1; then
            OUTPUT=$($TIMEOUT_CMD npx eslint --config "$ESLINT_CONFIG" "$FILE_PATH" 2>&1) || {
                EXIT_CODE=$?
                if [[ $EXIT_CODE -eq 124 ]]; then
                    log_hook "TIMEOUT: ESLint check timed out"
                    exit 0
                fi
                log_hook "Lint issues in $FILE_PATH"
                echo ""
                echo "[lint] Issues found in $(basename "$FILE_PATH"):"
                echo "$OUTPUT" | head -15
                echo ""
                exit 0
            }
            log_hook "OK: $FILE_PATH"
            echo "[lint] $(basename "$FILE_PATH") OK"
        else
            log_hook "SKIP: npx not available"
        fi
    fi
fi

# React/TypeScript files - run ESLint via Docker or local
if [[ "$FILE_PATH" =~ frontend/src/.*\.(ts|tsx)$ ]]; then
    # Prefer Docker if available
    if docker compose version >/dev/null 2>&1; then
        if docker compose ps --status running 2>/dev/null | grep -q frontend; then
            REL_PATH="${FILE_PATH#$PROJECT_ROOT/frontend/}"
            OUTPUT=$($TIMEOUT_CMD docker compose exec -T frontend npx eslint "src/$REL_PATH" 2>&1) || {
                EXIT_CODE=$?
                if [[ $EXIT_CODE -eq 124 ]]; then
                    log_hook "TIMEOUT: ESLint check timed out"
                    exit 0
                fi
                log_hook "Lint issues in $FILE_PATH"
                echo ""
                echo "[lint] Issues found in $(basename "$FILE_PATH"):"
                echo "$OUTPUT" | head -15
                echo ""
                exit 0
            }
            log_hook "OK: $FILE_PATH"
            echo "[lint] $(basename "$FILE_PATH") OK"
        else
            log_hook "SKIP: Frontend container not running"
        fi
    elif [[ -d "$PROJECT_ROOT/frontend/node_modules" ]]; then
        # Fallback to local npx
        cd "$PROJECT_ROOT/frontend"
        REL_PATH="${FILE_PATH#$PROJECT_ROOT/frontend/}"
        OUTPUT=$($TIMEOUT_CMD npx eslint "$REL_PATH" 2>&1) || {
            EXIT_CODE=$?
            if [[ $EXIT_CODE -eq 124 ]]; then
                log_hook "TIMEOUT: ESLint check timed out"
                exit 0
            fi
            log_hook "Lint issues in $FILE_PATH"
            echo ""
            echo "[lint] Issues found in $(basename "$FILE_PATH"):"
            echo "$OUTPUT" | head -15
            echo ""
            exit 0
        }
        log_hook "OK: $FILE_PATH"
        echo "[lint] $(basename "$FILE_PATH") OK"
    fi
fi

exit 0

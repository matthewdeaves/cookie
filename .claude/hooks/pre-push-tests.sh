#!/bin/bash
# Pre-Push Test Runner
#
# Runs tests before pushing to catch failures early.
# Only runs if pushing to protected branches (master, main, develop).
#
# Exit 0: Tests pass (or skipped for non-protected branch)
# Exit 1: Tests fail

set -e

# Hook logging setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_LOG_DIR="$SCRIPT_DIR/../logs"
HOOK_LOG="$HOOK_LOG_DIR/hooks.log"
mkdir -p "$HOOK_LOG_DIR"

log_hook() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [pre-push] $1" >> "$HOOK_LOG"
}

# Timeout for test runs (5 minutes)
TEST_TIMEOUT=300

# Track if we started containers
STARTED_CONTAINERS=false

cleanup() {
    if [[ "$STARTED_CONTAINERS" == "true" ]]; then
        log_hook "Stopping containers we started"
        docker compose down >/dev/null 2>&1 || true
    fi
}
trap cleanup EXIT

# Wait for container to be healthy
wait_for_container() {
    local container="$1"
    local max_wait=30
    local waited=0

    while [[ $waited -lt $max_wait ]]; do
        if docker compose ps --status running 2>/dev/null | grep -q "$container"; then
            # Check if container is accepting connections
            if docker compose exec -T "$container" echo "ready" >/dev/null 2>&1; then
                return 0
            fi
        fi
        sleep 1
        ((waited++))
    done

    return 1
}

# Read stdin to get push info (local_ref local_sha remote_ref remote_sha)
while read -r local_ref local_sha remote_ref remote_sha; do
    # Extract branch name from ref
    BRANCH=$(echo "$remote_ref" | sed 's|refs/heads/||')

    # Only run tests for protected branches
    if [[ "$BRANCH" != "master" && "$BRANCH" != "main" && "$BRANCH" != "develop" ]]; then
        log_hook "Skipping tests for non-protected branch: $BRANCH"
        continue
    fi

    log_hook "Running tests before push to $BRANCH"
    echo ""
    echo "Running tests before push to $BRANCH..."
    echo ""

    # Check if Docker is available
    if ! docker compose version >/dev/null 2>&1; then
        echo "[pre-push] Docker not available - skipping tests"
        log_hook "Docker not available - skipping"
        exit 0
    fi

    # Check if containers are running, start if needed
    if ! docker compose ps --status running 2>/dev/null | grep -q web; then
        echo "[pre-push] Starting containers..."
        docker compose up -d
        STARTED_CONTAINERS=true

        echo "[pre-push] Waiting for containers to be ready..."
        if ! wait_for_container "web"; then
            echo "[pre-push] Web container failed to start - skipping tests"
            log_hook "Web container failed to start"
            exit 0
        fi
        if ! wait_for_container "frontend"; then
            echo "[pre-push] Frontend container failed to start - skipping tests"
            log_hook "Frontend container failed to start"
            exit 0
        fi
    fi

    # Run backend and frontend tests in parallel
    echo "[pre-push] Running tests (timeout: ${TEST_TIMEOUT}s)..."

    BACKEND_LOG=$(mktemp)
    FRONTEND_LOG=$(mktemp)

    # Start backend tests in background
    (
        timeout $TEST_TIMEOUT docker compose exec -T web python -m pytest --tb=short -q 2>&1
        echo $? > "${BACKEND_LOG}.exit"
    ) > "$BACKEND_LOG" 2>&1 &
    BACKEND_PID=$!

    # Start frontend tests in background
    (
        timeout $TEST_TIMEOUT docker compose exec -T frontend npm test -- --watchAll=false 2>&1
        echo $? > "${FRONTEND_LOG}.exit"
    ) > "$FRONTEND_LOG" 2>&1 &
    FRONTEND_PID=$!

    # Wait for both to complete
    BACKEND_FAILED=false
    FRONTEND_FAILED=false

    wait $BACKEND_PID || true
    BACKEND_EXIT=$(cat "${BACKEND_LOG}.exit" 2>/dev/null || echo "1")
    if [[ "$BACKEND_EXIT" != "0" ]]; then
        BACKEND_FAILED=true
    fi

    wait $FRONTEND_PID || true
    FRONTEND_EXIT=$(cat "${FRONTEND_LOG}.exit" 2>/dev/null || echo "1")
    if [[ "$FRONTEND_EXIT" != "0" ]]; then
        FRONTEND_FAILED=true
    fi

    # Report results
    if [[ "$BACKEND_FAILED" == "true" ]] || [[ "$FRONTEND_FAILED" == "true" ]]; then
        echo ""
        echo "PUSH BLOCKED: Tests failed"
        echo "=========================="
        echo ""

        if [[ "$BACKEND_FAILED" == "true" ]]; then
            echo "Backend test output:"
            echo "--------------------"
            cat "$BACKEND_LOG" | tail -30
            echo ""
        fi

        if [[ "$FRONTEND_FAILED" == "true" ]]; then
            echo "Frontend test output:"
            echo "---------------------"
            cat "$FRONTEND_LOG" | tail -30
            echo ""
        fi

        echo "Fix the failing tests before pushing to $BRANCH."
        echo ""
        echo "To skip this check (not recommended):"
        echo "  git push --no-verify"
        echo ""

        rm -f "$BACKEND_LOG" "${BACKEND_LOG}.exit" "$FRONTEND_LOG" "${FRONTEND_LOG}.exit"
        log_hook "BLOCKED: Tests failed"
        exit 1
    fi

    rm -f "$BACKEND_LOG" "${BACKEND_LOG}.exit" "$FRONTEND_LOG" "${FRONTEND_LOG}.exit"

    echo ""
    echo "[pre-push] All tests passed!"
    log_hook "All tests passed"
done

exit 0

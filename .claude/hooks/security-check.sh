#!/bin/bash
# Security Pattern Check - BLOCKS dangerous code patterns
#
# This hook runs before Edit/Write operations.
# It checks for security anti-patterns that could introduce vulnerabilities.
#
# Exit 0: Allow the edit
# Exit 1: Block the edit (security issue found)

set -e

# Source common hook library
source "$(dirname "${BASH_SOURCE[0]}")/lib/common.sh"
init_hook "security-check"

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

# Skip test files and fixtures
if [[ "$FILE_PATH" =~ (test_|_test\.py|\.test\.|\.spec\.|tests/|fixtures/|__mocks__/) ]]; then
    exit 0
fi

log_hook "Checking: $FILE_PATH"

VIOLATIONS=""

# ============================================
# Python/Django Security Checks
# ============================================
if [[ "$FILE_PATH" =~ \.py$ ]]; then

    # SQL Injection: raw() with f-string or .format() or % formatting
    if echo "$NEW_CONTENT" | grep -qE '\.raw\s*\(\s*f["\x27]'; then
        VIOLATIONS="${VIOLATIONS}  - SQL Injection: .raw() with f-string (use %s placeholders)\n"
    fi
    if echo "$NEW_CONTENT" | grep -qE '\.raw\s*\([^)]*\.format\s*\('; then
        VIOLATIONS="${VIOLATIONS}  - SQL Injection: .raw() with .format() (use %s placeholders)\n"
    fi
    if echo "$NEW_CONTENT" | grep -qE '\.raw\s*\([^)]*%[^s]'; then
        VIOLATIONS="${VIOLATIONS}  - SQL Injection: .raw() with % formatting (use %s placeholders with params)\n"
    fi

    # SQL Injection: cursor.execute with f-string or .format()
    if echo "$NEW_CONTENT" | grep -qE 'execute\s*\(\s*f["\x27]'; then
        VIOLATIONS="${VIOLATIONS}  - SQL Injection: execute() with f-string (use %s placeholders)\n"
    fi
    if echo "$NEW_CONTENT" | grep -qE 'execute\s*\([^)]*\.format\s*\('; then
        VIOLATIONS="${VIOLATIONS}  - SQL Injection: execute() with .format() (use %s placeholders)\n"
    fi

    # Command Injection: shell=True
    if echo "$NEW_CONTENT" | grep -qE 'subprocess\.(run|call|Popen|check_output|check_call)\s*\([^)]*shell\s*=\s*True'; then
        VIOLATIONS="${VIOLATIONS}  - Command Injection Risk: subprocess with shell=True (use shell=False with list args)\n"
    fi
    if echo "$NEW_CONTENT" | grep -qE 'os\.system\s*\('; then
        VIOLATIONS="${VIOLATIONS}  - Command Injection Risk: os.system() (use subprocess with shell=False)\n"
    fi
    if echo "$NEW_CONTENT" | grep -qE 'os\.popen\s*\('; then
        VIOLATIONS="${VIOLATIONS}  - Command Injection Risk: os.popen() (use subprocess with shell=False)\n"
    fi

    # Dangerous eval/exec
    if echo "$NEW_CONTENT" | grep -qE '\beval\s*\('; then
        VIOLATIONS="${VIOLATIONS}  - Code Injection: eval() is dangerous (avoid or validate input strictly)\n"
    fi
    if echo "$NEW_CONTENT" | grep -qE '\bexec\s*\('; then
        VIOLATIONS="${VIOLATIONS}  - Code Injection: exec() is dangerous (avoid or validate input strictly)\n"
    fi

    # Deserialization attacks
    if echo "$NEW_CONTENT" | grep -qE 'pickle\.(loads|load)\s*\('; then
        VIOLATIONS="${VIOLATIONS}  - Deserialization Attack: pickle.load/loads is unsafe with untrusted data\n"
    fi
    if echo "$NEW_CONTENT" | grep -qE 'yaml\.load\s*\([^)]*\)' | grep -vqE 'Loader\s*='; then
        # yaml.load without Loader= is unsafe
        if echo "$NEW_CONTENT" | grep -qE 'yaml\.load\s*\(' && ! echo "$NEW_CONTENT" | grep -qE 'yaml\.(safe_load|load\s*\([^)]*Loader)'; then
            VIOLATIONS="${VIOLATIONS}  - Deserialization Attack: yaml.load() without Loader (use yaml.safe_load())\n"
        fi
    fi
    if echo "$NEW_CONTENT" | grep -qE 'marshal\.loads?\s*\('; then
        VIOLATIONS="${VIOLATIONS}  - Deserialization Attack: marshal is unsafe with untrusted data\n"
    fi

    # Hardcoded secrets patterns
    if echo "$NEW_CONTENT" | grep -qiE '(api_key|apikey|secret_key|secretkey|password|passwd|token)\s*=\s*["\x27][^"\x27]{8,}["\x27]'; then
        # Skip if it looks like a placeholder or env var reference
        if ! echo "$NEW_CONTENT" | grep -qiE '(api_key|apikey|secret_key|secretkey|password|passwd|token)\s*=\s*["\x27](xxx|your-|changeme|placeholder|os\.environ|getenv)'; then
            VIOLATIONS="${VIOLATIONS}  - Hardcoded Secret: possible hardcoded credential (use environment variables)\n"
        fi
    fi

    # SSRF: requests/urllib with user input
    if echo "$NEW_CONTENT" | grep -qE 'requests\.(get|post|put|delete|head|patch)\s*\(\s*[a-zA-Z_]'; then
        # If URL comes from a variable, warn about validation
        VIOLATIONS="${VIOLATIONS}  - SSRF Risk: requests with variable URL (validate URL scheme and host)\n"
    fi

fi

# ============================================
# Django Template Security Checks
# ============================================
if [[ "$FILE_PATH" =~ \.html$ ]]; then

    # XSS: |safe filter
    if echo "$NEW_CONTENT" | grep -qE '\{\{\s*[^}|]+\|safe\s*\}\}'; then
        # Check if it's json_script (which is safe) in the same block
        SAFE_LINE=$(echo "$NEW_CONTENT" | grep -E '\{\{\s*[^}|]+\|safe\s*\}\}' | head -1)
        if ! echo "$SAFE_LINE" | grep -qE 'json_script'; then
            VIOLATIONS="${VIOLATIONS}  - XSS Risk: |safe filter bypasses escaping (ensure content is trusted/sanitized)\n"
        fi
    fi

    # XSS: autoescape off
    if echo "$NEW_CONTENT" | grep -qE '\{%\s*autoescape\s+off'; then
        VIOLATIONS="${VIOLATIONS}  - XSS Risk: autoescape off disables protection (use sparingly, ensure content is safe)\n"
    fi

    # XSS: mark_safe in view passed to template
    if echo "$NEW_CONTENT" | grep -qE 'mark_safe\s*\('; then
        VIOLATIONS="${VIOLATIONS}  - XSS Risk: mark_safe() bypasses escaping (sanitize content first)\n"
    fi

fi

# ============================================
# React/JavaScript Security Checks
# ============================================
if [[ "$FILE_PATH" =~ \.(js|jsx|ts|tsx)$ ]]; then

    # XSS: dangerouslySetInnerHTML
    if echo "$NEW_CONTENT" | grep -qE 'dangerouslySetInnerHTML'; then
        # Check if DOMPurify is imported/used in the same content
        if ! echo "$NEW_CONTENT" | grep -qE '(DOMPurify|sanitize|purify)'; then
            VIOLATIONS="${VIOLATIONS}  - XSS Risk: dangerouslySetInnerHTML without sanitization (use DOMPurify)\n"
        fi
    fi

    # Code Injection: eval()
    if echo "$NEW_CONTENT" | grep -qE '\beval\s*\('; then
        VIOLATIONS="${VIOLATIONS}  - Code Injection: eval() is dangerous (avoid entirely)\n"
    fi

    # Code Injection: new Function()
    if echo "$NEW_CONTENT" | grep -qE 'new\s+Function\s*\('; then
        VIOLATIONS="${VIOLATIONS}  - Code Injection: new Function() is like eval (avoid entirely)\n"
    fi

    # innerHTML assignment
    if echo "$NEW_CONTENT" | grep -qE '\.innerHTML\s*='; then
        VIOLATIONS="${VIOLATIONS}  - XSS Risk: innerHTML assignment (use textContent or React JSX)\n"
    fi

    # outerHTML assignment
    if echo "$NEW_CONTENT" | grep -qE '\.outerHTML\s*='; then
        VIOLATIONS="${VIOLATIONS}  - XSS Risk: outerHTML assignment (use textContent or React JSX)\n"
    fi

    # document.write
    if echo "$NEW_CONTENT" | grep -qE 'document\.write\s*\('; then
        VIOLATIONS="${VIOLATIONS}  - XSS Risk: document.write() (use DOM manipulation instead)\n"
    fi

    # Hardcoded secrets in JS
    if echo "$NEW_CONTENT" | grep -qiE '(api_key|apiKey|secret|token|password)\s*[:=]\s*["\x27][^"\x27]{8,}["\x27]'; then
        if ! echo "$NEW_CONTENT" | grep -qiE '(api_key|apiKey|secret|token|password)\s*[:=]\s*["\x27](process\.env|import\.meta\.env|xxx|your-|changeme)'; then
            VIOLATIONS="${VIOLATIONS}  - Hardcoded Secret: possible hardcoded credential (use environment variables)\n"
        fi
    fi

fi

# ============================================
# Report Violations
# ============================================
if [[ -n "$VIOLATIONS" ]]; then
    log_hook "BLOCKED: Security issues in $FILE_PATH"
    echo ""
    echo "BLOCKED: Security Pattern Detected"
    echo "==================================="
    echo ""
    echo "File: $FILE_PATH"
    echo ""
    echo "Issues found:"
    echo -e "$VIOLATIONS"
    echo ""
    echo "References:"
    echo "  - .claude/rules/django-security.md"
    echo "  - .claude/rules/react-security.md"
    echo ""
    echo "If this is a false positive (e.g., intentional use with proper safeguards),"
    echo "add a comment explaining why it's safe, then re-attempt the edit."
    echo ""
    exit 1
fi

log_hook "PASS: No security issues - $FILE_PATH"
exit 0

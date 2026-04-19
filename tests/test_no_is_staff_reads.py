"""Regression guard: application code MUST NOT read `is_staff` for branching.

This static test walks `apps/` and asserts that the `is_staff` token appears
only in allowlisted locations. After feature 014-remove-is-staff, `is_staff`
is an inert Django-framework column with a permanent value of `False` for
all application-created users. Reading it for privilege decisions is a
regression and MUST fail the test suite.

Allowlist:
    * `apps/core/management/commands/_cookie_admin_users.py` — the single
      `is_staff=False` write in `_handle_create_user` (enforces FR-022).
    * `apps/core/passkey_api.py` — the `is_staff=False` write on user
      creation during WebAuthn registration (enforces FR-022).
    * `apps/core/migrations/*` — Django migration files (defensive;
      no matches currently expected).
    * This test file itself (self-referential).

Any other occurrence fails the test with a file:line pointer and a remediation
hint pointing at this feature spec.
"""

from __future__ import annotations

import pathlib
import re

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
APPS_DIR = REPO_ROOT / "apps"

# Compile allowlist rules as (path_suffix_pattern, line_pattern) tuples.
# Both patterns are regex — a match on BOTH path and line permits the occurrence.
ALLOWLIST: list[tuple[re.Pattern[str], re.Pattern[str]]] = [
    # cookie_admin (users mixin): default-False write in _handle_create_user.
    (
        re.compile(r"apps/core/management/commands/_cookie_admin_users\.py$"),
        re.compile(r"\bis_staff=False\b"),
    ),
    # passkey_api: default-False write on passkey user creation.
    (
        re.compile(r"apps/core/passkey_api\.py$"),
        re.compile(r"\bis_staff=False\b"),
    ),
    # Django migrations (defensive; no matches expected).
    (
        re.compile(r"apps/.*/migrations/.*\.py$"),
        re.compile(r"."),
    ),
]

# The exact token to scan for.
TOKEN_PATTERN = re.compile(r"\bis_staff\b")


def _is_allowlisted(rel_path: str, line: str) -> bool:
    for path_rx, line_rx in ALLOWLIST:
        if path_rx.search(rel_path) and line_rx.search(line):
            return True
    return False


def test_no_is_staff_reads_in_apps() -> None:
    """`is_staff` must not appear in apps/ outside allowlisted locations.

    If this test fails, the output names every offending file:line and
    recommends removing the read. See
    specs/014-remove-is-staff/spec.md (FR-021b) for context.
    """
    offenders: list[str] = []

    for py_file in APPS_DIR.rglob("*.py"):
        rel_path = str(py_file.relative_to(REPO_ROOT))
        try:
            text = py_file.read_text(encoding="utf-8")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if not TOKEN_PATTERN.search(line):
                continue
            if _is_allowlisted(rel_path, line):
                continue
            offenders.append(f"  {rel_path}:{lineno}  {line.strip()}")

    if offenders:
        msg = (
            "is_staff read found in application code outside the allowlist.\n"
            "`is_staff` is no longer a privilege signal. Use `Profile.unlimited_ai`\n"
            "for AI quota bypass, or delete the check. See\n"
            "specs/014-remove-is-staff/spec.md (FR-021b) for context.\n\n"
            "Offenders:\n" + "\n".join(offenders)
        )
        pytest.fail(msg)

"""Static code-quality gates per Constitution Principle V.

File-size limit: 500 lines per .py file in apps/ and tests/.
Pre-existing violations are grandfathered in EXEMPT_FILES with a ceiling.
Cleanup tracked in follow-up spec 016-code-quality-refactor.
"""

from __future__ import annotations

import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
MAX_FILE_LINES = 500

EXEMPT_FILES: dict[str, int] = {
    "apps/ai/api.py": 534,
    "apps/recipes/services/scraper.py": 517,
    "apps/ai/tests.py": 1852,
    "apps/recipes/tests.py": 564,
    "tests/test_passkey_api.py": 903,
    "tests/test_recipes_api.py": 857,
    "tests/test_cookie_admin.py": 830,
    "tests/test_ai_quota.py": 768,
    "tests/test_search.py": 718,
    "tests/test_system_api.py": 701,
    "tests/test_image_cache.py": 674,
    "tests/test_ai_api.py": 597,
    "tests/test_user_features.py": 524,
}


def _is_excluded(path: pathlib.Path) -> bool:
    rel = str(path.relative_to(REPO_ROOT))
    return "/migrations/" in rel


def test_py_file_size_under_limit() -> None:
    """Every .py in apps/ or tests/ must be <= MAX_FILE_LINES, or grandfathered."""
    offenders: list[str] = []
    stale_exemptions: list[str] = []

    scan_dirs = [REPO_ROOT / "apps", REPO_ROOT / "tests"]

    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
        for py_file in scan_dir.rglob("*.py"):
            if _is_excluded(py_file):
                continue

            rel = str(py_file.relative_to(REPO_ROOT))
            with py_file.open(encoding="utf-8") as fh:
                line_count = sum(1 for _ in fh)

            if line_count > MAX_FILE_LINES:
                if rel in EXEMPT_FILES:
                    ceiling = EXEMPT_FILES[rel]
                    if line_count > ceiling:
                        offenders.append(
                            f"  {rel}: {line_count} lines (ceiling is {ceiling} — file grew past its grandfathered limit)"
                        )
                else:
                    offenders.append(f"  {rel}: {line_count} lines (new violation — max {MAX_FILE_LINES})")
            elif rel in EXEMPT_FILES:
                stale_exemptions.append(
                    f"  {rel}: {line_count} lines (now under {MAX_FILE_LINES} — remove from EXEMPT_FILES)"
                )

    messages: list[str] = []
    if offenders:
        messages.append(f"File-size violations (max {MAX_FILE_LINES} lines per file):\n" + "\n".join(offenders))
    if stale_exemptions:
        messages.append(
            "Stale EXEMPT_FILES entries (files now under limit — remove them):\n" + "\n".join(stale_exemptions)
        )

    if messages:
        msg = "\n\n".join(messages)
        msg += "\n\nSee specs/015-security-review-fixes/spec.md FR-029 and .specify/memory/constitution.md Principle V."
        pytest.fail(msg)

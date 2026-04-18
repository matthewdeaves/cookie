"""Regression guard: .innerHTML = / .innerHTML += must not appear outside utils.js.

All HTML insertion in the legacy ES5 frontend routes through the audited
Cookie.utils.setHtml chokepoint in utils.js. Any bypass corrodes the
single-site-audit pattern and is a potential XSS vector.

See specs/015-security-review-fixes/spec.md FR-013.
"""

from __future__ import annotations

import pathlib
import re

import pytest

LEGACY_JS_DIR = pathlib.Path(__file__).resolve().parent.parent / "apps" / "legacy" / "static" / "legacy" / "js"
CHOKEPOINT_FILE = "utils.js"
PATTERN = re.compile(r"\.innerHTML\s*(=|\+=)")


def test_no_inner_html_outside_utils_js() -> None:
    offenders: list[str] = []

    for js_file in LEGACY_JS_DIR.rglob("*.js"):
        if js_file.name == CHOKEPOINT_FILE:
            continue
        try:
            text = js_file.read_text(encoding="utf-8")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if PATTERN.search(line):
                rel = js_file.relative_to(LEGACY_JS_DIR.parent.parent.parent.parent.parent)
                offenders.append(f"  {rel}:{lineno}  {line.strip()}")

    if offenders:
        msg = (
            ".innerHTML assignment found outside the audited utils.js chokepoint.\n"
            "Route all HTML insertion through Cookie.utils.setHtml().\n"
            "See specs/015-security-review-fixes/spec.md FR-013.\n\n"
            "Offenders:\n" + "\n".join(offenders)
        )
        pytest.fail(msg)

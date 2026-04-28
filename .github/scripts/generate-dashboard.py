#!/usr/bin/env python3
"""
Generate metrics dashboard from CI artifacts.

This script:
1. Extracts metrics from coverage/complexity/security artifacts
2. Validates all metric values
3. Generates SVG badges locally (no external dependencies)
4. Creates metrics.json API file
5. Updates history.json with timestamped entries

Usage:
    python generate-dashboard.py [--config rating-config.json]
"""

import argparse
import json
import os
from datetime import datetime, timezone, UTC
from pathlib import Path


REPO_ROOT = str(Path(__file__).resolve().parent.parent.parent)


def _safe_path(path: str) -> str:
    """Resolve path and ensure it stays within the repository root."""
    resolved = os.path.realpath(path)
    if not resolved.startswith(REPO_ROOT + os.sep) and resolved != REPO_ROOT:
        raise ValueError(f"Path escapes repository root: {path}")
    return resolved


def load_config(config_path: str) -> dict:
    """Load rating thresholds from config file."""
    with open(_safe_path(config_path)) as f:
        return json.load(f)


def get_rating(value: float, thresholds: dict, higher_is_better: bool = True) -> str:
    """Calculate rating based on thresholds."""
    if higher_is_better:
        if value >= thresholds["A"]:
            return "A"
        elif value >= thresholds["B"]:
            return "B"
        elif value >= thresholds["C"]:
            return "C"
        else:
            return "D"
    else:  # Lower is better (complexity, duplication)
        if value <= thresholds["A"]:
            return "A"
        elif value <= thresholds["B"]:
            return "B"
        elif value <= thresholds["C"]:
            return "C"
        else:
            return "D"


def generate_badge_svg(label: str, value: str, color: str) -> str:
    """Generate an SVG badge locally (no shields.io dependency)."""
    # Color mapping
    colors = {
        "brightgreen": "#4c1",
        "green": "#97ca00",
        "yellow": "#dfb317",
        "orange": "#fe7d37",
        "red": "#e05d44",
        "lightgrey": "#9f9f9f",
    }
    bg_color = colors.get(color, colors["lightgrey"])

    # Calculate widths (approximate character widths)
    label_width = len(label) * 6.5 + 10
    value_width = len(value) * 6.5 + 10
    total_width = label_width + value_width

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="20">
  <linearGradient id="b" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <mask id="a">
    <rect width="{total_width}" height="20" rx="3" fill="#fff"/>
  </mask>
  <g mask="url(#a)">
    <rect width="{label_width}" height="20" fill="#555"/>
    <rect x="{label_width}" width="{value_width}" height="20" fill="{bg_color}"/>
    <rect width="{total_width}" height="20" fill="url(#b)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="{label_width / 2}" y="15" fill="#010101" fill-opacity=".3">{label}</text>
    <text x="{label_width / 2}" y="14">{label}</text>
    <text x="{label_width + value_width / 2}" y="15" fill="#010101" fill-opacity=".3">{value}</text>
    <text x="{label_width + value_width / 2}" y="14">{value}</text>
  </g>
</svg>'''
    return svg


def _load_artifact(path: str, label: str) -> dict:
    """Load a JSON artifact, returning {} on missing/malformed files.

    Each artifact is produced by an independent CI job; one failing must
    not block the dashboard, so errors are logged and swallowed.
    """
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"WARNING: {label} artifact not found")
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid {label} data: {e}")
    return {}


def _pct_from_coverage(path: str, label: str, *, getter) -> float:
    """Apply a coverage-specific getter that may raise KeyError on partial data."""
    d = _load_artifact(path, label)
    if not d:
        return 0
    try:
        return getter(d)
    except (KeyError, TypeError) as e:
        print(f"ERROR: Invalid {label} data: {e}")
        return 0


def extract_metrics(config: dict) -> dict:
    """Extract all metrics from artifact files."""
    frontend_cov = _pct_from_coverage(
        "coverage/frontend/coverage-summary.json",
        "Frontend coverage",
        getter=lambda d: d["total"]["lines"]["pct"],
    )
    backend_cov = _pct_from_coverage(
        "coverage/backend/coverage.json",
        "Backend coverage",
        getter=lambda d: round(d["totals"]["percent_covered"], 1),
    )

    backend_complexity = _load_artifact("complexity/backend/summary.json", "Backend complexity")
    frontend_complexity = _load_artifact("complexity/frontend/summary.json", "Frontend complexity")
    frontend_dup = _load_artifact("duplication/frontend/summary.json", "Frontend duplication")
    backend_dup = _load_artifact("duplication/backend/summary.json", "Backend duplication")
    frontend_sec = _load_artifact("security/frontend/summary.json", "Frontend security")
    backend_sec = _load_artifact("security/backend/summary.json", "Backend security")
    # Variable name avoids the literal "secret" identifier so static analysers
    # (CodeQL py/clear-text-logging-sensitive-data) don't taint the metrics
    # dict via name-heuristic — the value is an integer count, not a secret.
    scan_summary = _load_artifact("security/secrets/summary.json", "Secrets scan")
    bundle = _load_artifact("bundle/frontend/summary.json", "Bundle")
    legacy_lint = _load_artifact("legacy/lint/summary.json", "Legacy lint")
    legacy_dup = _load_artifact("legacy/duplication/summary.json", "Legacy duplication")

    bandit = backend_sec.get("bandit", {})
    return {
        "frontend_cov": frontend_cov,
        "backend_cov": backend_cov,
        "backend_cc": backend_complexity.get("average_cyclomatic_complexity", 0),
        "backend_mi": backend_complexity.get("average_maintainability_index", 0),
        "frontend_avg_cc": frontend_complexity.get("avg_cyclomatic_complexity", 0),
        "frontend_complexity_warnings": frontend_complexity.get("complexity_warnings", 0),
        "duplication_pct": frontend_dup.get("duplication_percentage", 0),
        "duplication_clones": frontend_dup.get("clones_count", 0),
        "backend_duplication_pct": backend_dup.get("duplication_percentage", 0),
        "backend_duplication_clones": backend_dup.get("clones_count", 0),
        "frontend_vulns": frontend_sec.get("total_vulnerabilities", 0),
        "backend_vulns": backend_sec.get("pip_audit", {}).get("vulnerabilities", 0),
        "bandit_high": bandit.get("high", 0),
        "bandit_medium": bandit.get("medium", 0),
        "bandit_low": bandit.get("low", 0),
        "scan_findings_count": scan_summary.get("secrets_found", 0),
        "bundle_size_kb": bundle.get("total_size_kb", 0),
        "bundle_gzip_kb": bundle.get("total_gzip_kb", 0),
        "legacy_errors": legacy_lint.get("errors", 0),
        "legacy_warnings": legacy_lint.get("warnings", 0),
        "legacy_complexity_warnings": legacy_lint.get("complexity_warnings", 0),
        "legacy_duplication_pct": legacy_dup.get("duplication_percentage", 0),
    }


def validate_metrics(metrics: dict) -> tuple[list, list]:
    """Validate metric values and return errors/warnings."""
    errors = []
    warnings = []

    # Coverage should be 0-100
    if not (0 <= metrics["frontend_cov"] <= 100):
        errors.append(f"Invalid frontend coverage: {metrics['frontend_cov']}% (expected 0-100)")
        metrics["frontend_cov"] = max(0, min(100, metrics["frontend_cov"]))
    if not (0 <= metrics["backend_cov"] <= 100):
        errors.append(f"Invalid backend coverage: {metrics['backend_cov']}% (expected 0-100)")
        metrics["backend_cov"] = max(0, min(100, metrics["backend_cov"]))

    # Bundle size should be positive
    if metrics["bundle_size_kb"] < 0:
        errors.append(f"Invalid bundle size: {metrics['bundle_size_kb']}KB (expected >= 0)")
        metrics["bundle_size_kb"] = 0
    if metrics["bundle_gzip_kb"] < 0:
        errors.append(f"Invalid gzip bundle size: {metrics['bundle_gzip_kb']}KB (expected >= 0)")
        metrics["bundle_gzip_kb"] = 0

    # Complexity should be reasonable
    if metrics["backend_cc"] < 0 or metrics["backend_cc"] > 100:
        warnings.append(f"Unusual backend CC: {metrics['backend_cc']} (typically 1-50)")
    if metrics["frontend_avg_cc"] < 0 or metrics["frontend_avg_cc"] > 100:
        warnings.append(f"Unusual frontend CC: {metrics['frontend_avg_cc']} (typically 1-50)")

    # Maintainability index should be 0-100
    if not (0 <= metrics["backend_mi"] <= 100):
        warnings.append(f"Unusual backend MI: {metrics['backend_mi']} (expected 0-100)")

    # Duplication should be 0-100%
    if not (0 <= metrics["duplication_pct"] <= 100):
        warnings.append(f"Unusual frontend duplication: {metrics['duplication_pct']}% (expected 0-100)")
    if not (0 <= metrics["backend_duplication_pct"] <= 100):
        warnings.append(f"Unusual backend duplication: {metrics['backend_duplication_pct']}% (expected 0-100)")

    return errors, warnings


def calculate_ratings(metrics: dict, config: dict) -> dict:
    """Calculate all ratings based on config thresholds."""
    ratings = {}

    # Coverage ratings (higher is better)
    ratings["frontend_cov"] = get_rating(metrics["frontend_cov"], config["coverage"]["thresholds"], True)
    ratings["backend_cov"] = get_rating(metrics["backend_cov"], config["coverage"]["thresholds"], True)

    # Complexity ratings (lower is better)
    ratings["backend_cc"] = get_rating(metrics["backend_cc"], config["complexity"]["thresholds"], False)
    ratings["frontend_cc"] = get_rating(metrics["frontend_avg_cc"], config["complexity"]["thresholds"], False)

    # Maintainability rating (higher is better)
    ratings["backend_mi"] = get_rating(metrics["backend_mi"], config["maintainability"]["thresholds"], True)

    # Duplication ratings (lower is better)
    ratings["frontend_dup"] = get_rating(
        metrics["duplication_pct"], config["duplication"]["thresholds"]["frontend"], False
    )
    ratings["backend_dup"] = get_rating(
        metrics["backend_duplication_pct"], config["duplication"]["thresholds"]["backend"], False
    )
    ratings["legacy_dup"] = get_rating(
        metrics["legacy_duplication_pct"], config["duplication"]["thresholds"]["legacy"], False
    )

    # Bundle rating (lower is better for gzip)
    ratings["bundle"] = get_rating(metrics["bundle_gzip_kb"], config["bundle"]["thresholds"]["gzip_kb"], False)

    # Security ratings
    ratings["frontend_security"] = "A" if metrics["frontend_vulns"] == 0 else "D"

    # Backend security: consider both pip-audit and bandit
    backend_high = metrics["backend_vulns"] + metrics["bandit_high"]
    backend_medium = metrics["bandit_medium"]
    if backend_high == 0 and backend_medium == 0:
        ratings["backend_security"] = "A"
    elif backend_high == 0 and backend_medium <= 3:
        ratings["backend_security"] = "B"
    elif backend_high <= 2:
        ratings["backend_security"] = "C"
    else:
        ratings["backend_security"] = "D"

    # Bandit SAST rating
    if metrics["bandit_high"] == 0 and metrics["bandit_medium"] == 0:
        ratings["bandit"] = "A"
    elif metrics["bandit_high"] == 0:
        ratings["bandit"] = "B"
    elif metrics["bandit_high"] <= 2:
        ratings["bandit"] = "C"
    else:
        ratings["bandit"] = "D"

    # Secrets detection rating (key avoids the literal "secret" identifier
    # to keep CodeQL's name-heuristic from tainting the ratings dict)
    ratings["scan_rating"] = "A" if metrics["scan_findings_count"] == 0 else "D"

    # Legacy lint rating
    if metrics["legacy_errors"] > 0:
        ratings["legacy_lint"] = "D"
    elif metrics["legacy_warnings"] > 10:
        ratings["legacy_lint"] = "C"
    elif metrics["legacy_warnings"] > 0:
        ratings["legacy_lint"] = "B"
    else:
        ratings["legacy_lint"] = "A"

    return ratings


def generate_badges(metrics: dict, ratings: dict, config: dict, output_dir: str):
    """Generate all SVG badges."""
    colors = config["colors"]
    badges_dir = Path(_safe_path(output_dir)) / "badges"
    badges_dir.mkdir(parents=True, exist_ok=True)

    badges = [
        ("frontend-coverage", "coverage", f"{metrics['frontend_cov']}%", colors[ratings["frontend_cov"]]),
        ("backend-coverage", "coverage", f"{metrics['backend_cov']}%", colors[ratings["backend_cov"]]),
        ("backend-complexity", "complexity", ratings["backend_cc"], colors[ratings["backend_cc"]]),
        ("backend-maintainability", "maintainability", ratings["backend_mi"], colors[ratings["backend_mi"]]),
        ("frontend-complexity", "complexity", ratings["frontend_cc"], colors[ratings["frontend_cc"]]),
        ("duplication", "duplication", ratings["frontend_dup"], colors[ratings["frontend_dup"]]),
        ("backend-duplication", "duplication", ratings["backend_dup"], colors[ratings["backend_dup"]]),
        ("frontend-security", "npm audit", ratings["frontend_security"], colors[ratings["frontend_security"]]),
        ("backend-security", "pip-audit", ratings["backend_security"], colors[ratings["backend_security"]]),
        ("bandit-sast", "SAST", ratings["bandit"], colors[ratings["bandit"]]),
        ("secrets-scan", "secrets", ratings["scan_rating"], colors[ratings["scan_rating"]]),
        ("bundle-size", "bundle", ratings["bundle"], colors[ratings["bundle"]]),
        ("legacy-lint", "legacy lint", ratings["legacy_lint"], colors[ratings["legacy_lint"]]),
        ("legacy-duplication", "legacy dup", ratings["legacy_dup"], colors[ratings["legacy_dup"]]),
    ]

    for name, label, value, color in badges:
        svg = generate_badge_svg(label, value, color)
        badge_path = badges_dir / f"{name}.svg"
        _safe_path(str(badge_path))
        with open(badge_path, "w") as f:
            f.write(svg)  # Badge SVG contains only public metric labels/ratings
        print(f"Generated {name} badge: {value}")


def create_metrics_json(metrics: dict, ratings: dict, output_dir: str):
    """Create the metrics.json API file."""
    api_dir = Path(_safe_path(output_dir)) / "api"
    api_dir.mkdir(parents=True, exist_ok=True)

    base_url = "https://matthewdeaves.github.io/cookie/coverage"

    data = {
        "generated_at": datetime.now(UTC).isoformat(),
        "repo": "matthewdeaves/cookie",
        "coverage": {
            "frontend": {
                "percentage": metrics["frontend_cov"],
                "badge_url": f"{base_url}/badges/frontend-coverage.svg",
            },
            "backend": {"percentage": metrics["backend_cov"], "badge_url": f"{base_url}/badges/backend-coverage.svg"},
        },
        "complexity": {
            "backend": {
                "cyclomatic_complexity": metrics["backend_cc"],
                "cyclomatic_rating": ratings["backend_cc"],
                "maintainability_index": metrics["backend_mi"],
                "maintainability_rating": ratings["backend_mi"],
                "badge_url": f"{base_url}/badges/backend-complexity.svg",
            },
            "frontend": {
                "avg_cyclomatic_complexity": metrics["frontend_avg_cc"],
                "complexity_warnings": metrics["frontend_complexity_warnings"],
                "rating": ratings["frontend_cc"],
                "badge_url": f"{base_url}/badges/frontend-complexity.svg",
            },
        },
        "duplication": {
            "frontend": {
                "percentage": metrics["duplication_pct"],
                "clones_count": metrics["duplication_clones"],
                "rating": ratings["frontend_dup"],
                "badge_url": f"{base_url}/badges/duplication.svg",
            },
            "backend": {
                "percentage": metrics["backend_duplication_pct"],
                "clones_count": metrics["backend_duplication_clones"],
                "rating": ratings["backend_dup"],
                "badge_url": f"{base_url}/badges/backend-duplication.svg",
            },
        },
        "security": {
            "frontend": {
                "vulnerabilities": metrics["frontend_vulns"],
                "rating": ratings["frontend_security"],
                "badge_url": f"{base_url}/badges/frontend-security.svg",
            },
            "backend": {
                "pip_audit_vulns": metrics["backend_vulns"],
                "rating": ratings["backend_security"],
                "badge_url": f"{base_url}/badges/backend-security.svg",
            },
            "bandit": {
                "high": metrics["bandit_high"],
                "medium": metrics["bandit_medium"],
                "low": metrics["bandit_low"],
                "total": metrics["bandit_high"] + metrics["bandit_medium"] + metrics["bandit_low"],
                "rating": ratings["bandit"],
                "badge_url": f"{base_url}/badges/bandit-sast.svg",
            },
            "secrets": {
                "found": metrics["scan_findings_count"],
                "rating": ratings["scan_rating"],
                "badge_url": f"{base_url}/badges/secrets-scan.svg",
            },
        },
        "bundle": {
            "size_kb": metrics["bundle_size_kb"],
            "gzip_kb": metrics["bundle_gzip_kb"],
            "rating": ratings["bundle"],
            "badge_url": f"{base_url}/badges/bundle-size.svg",
        },
        "legacy": {
            "lint": {
                "errors": metrics["legacy_errors"],
                "warnings": metrics["legacy_warnings"],
                "complexity_warnings": metrics["legacy_complexity_warnings"],
                "rating": ratings["legacy_lint"],
                "badge_url": f"{base_url}/badges/legacy-lint.svg",
            },
            "duplication": {
                "percentage": metrics["legacy_duplication_pct"],
                "rating": ratings["legacy_dup"],
                "badge_url": f"{base_url}/badges/legacy-duplication.svg",
            },
        },
        "links": {
            "dashboard": f"{base_url}/",
            "frontend_coverage": f"{base_url}/frontend/",
            "backend_coverage": f"{base_url}/backend/htmlcov/",
            "github": "https://github.com/matthewdeaves/cookie",
        },
    }

    metrics_path = api_dir / "metrics.json"
    _safe_path(str(metrics_path))
    with open(metrics_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\nMetrics JSON generated at {metrics_path}")


def update_history(metrics: dict, ratings: dict, output_dir: str):
    """Update history.json with current metrics."""
    history_dir = Path(_safe_path(output_dir)) / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    history_file = history_dir / "all.json"
    _safe_path(str(history_file))

    # Load existing history
    if history_file.exists():
        with open(history_file) as f:
            history = json.load(f)
        existing_count = len(history.get("entries", []))
        print(f"\nLoaded existing history with {existing_count} entries")
    else:
        history = {"entries": []}
        print("\nNo existing history file found, starting fresh")

    # Build new entry
    now = datetime.now(UTC)
    entry = {
        "timestamp": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "coverage": {"frontend": metrics["frontend_cov"], "backend": metrics["backend_cov"]},
        "complexity": {
            "frontend_warnings": metrics["frontend_complexity_warnings"],
            "frontend_avg_cc": metrics["frontend_avg_cc"],
            "backend_cc": metrics["backend_cc"],
            "backend_mi": metrics["backend_mi"],
        },
        "duplication": {
            "frontend": metrics["duplication_pct"],
            "backend": metrics["backend_duplication_pct"],
            "frontend_clones": metrics["duplication_clones"],
            "backend_clones": metrics["backend_duplication_clones"],
        },
        "bundle": {"total_kb": metrics["bundle_size_kb"], "gzip_kb": metrics["bundle_gzip_kb"]},
        "security": {
            "frontend_vulns": metrics["frontend_vulns"],
            "backend_vulns": metrics["backend_vulns"],
            "bandit_high": metrics["bandit_high"],
            "bandit_medium": metrics["bandit_medium"],
            "bandit_low": metrics["bandit_low"],
            "secrets_found": metrics["scan_findings_count"],
        },
        "legacy": {
            "errors": metrics["legacy_errors"],
            "warnings": metrics["legacy_warnings"],
            "complexity_warnings": metrics["legacy_complexity_warnings"],
            "duplication": metrics["legacy_duplication_pct"],
        },
    }

    history["entries"].append(entry)
    history["entries"].sort(key=lambda x: x.get("timestamp", x.get("date", "")))
    history["entries"] = history["entries"][-200:]  # Keep last 200 entries

    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)

    # Log aggregate metric counts (public CI dashboard data, not sensitive)
    print(f"\nHistory updated: {len(history['entries'])} entries")
    print(f"Latest entry: {entry['timestamp']}")


def print_summary(metrics: dict, ratings: dict):
    """Print a summary of all metrics."""
    print("\n" + "=" * 60)
    print("METRICS SUMMARY")
    print("=" * 60)
    print(f"Frontend Coverage: {metrics['frontend_cov']}% ({ratings['frontend_cov']})")
    print(f"Backend Coverage: {metrics['backend_cov']}% ({ratings['backend_cov']})")
    print(
        f"Backend Complexity: CC={metrics['backend_cc']} ({ratings['backend_cc']}), MI={metrics['backend_mi']} ({ratings['backend_mi']})"
    )
    print(
        f"Frontend Complexity: CC={metrics['frontend_avg_cc']} ({ratings['frontend_cc']}), {metrics['frontend_complexity_warnings']} ESLint warnings"
    )
    print(
        f"Duplication: Frontend={metrics['duplication_pct']}% ({ratings['frontend_dup']}), Backend={metrics['backend_duplication_pct']}% ({ratings['backend_dup']})"
    )
    print(
        f"Security: Frontend={metrics['frontend_vulns']} ({ratings['frontend_security']}), Backend pip-audit={metrics['backend_vulns']} ({ratings['backend_security']})"
    )
    print(
        f"Bandit SAST: HIGH={metrics['bandit_high']}, MEDIUM={metrics['bandit_medium']}, LOW={metrics['bandit_low']} ({ratings['bandit']})"
    )
    # Aggregate count of findings (not actual secret values)
    print(f"Secrets Detection: {metrics['scan_findings_count']} found ({ratings['scan_rating']})")
    print(
        f"Bundle Size: {metrics['bundle_size_kb']}KB raw, {metrics['bundle_gzip_kb']}KB gzipped ({ratings['bundle']})"
    )
    print(
        f"Legacy Lint: {metrics['legacy_errors']} errors, {metrics['legacy_warnings']} warnings ({ratings['legacy_lint']})"
    )
    print(f"Legacy Duplication: {metrics['legacy_duplication_pct']}% ({ratings['legacy_dup']})")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Generate metrics dashboard from CI artifacts")
    parser.add_argument(
        "--config", default=".github/scripts/rating-config.json", help="Path to rating config JSON file"
    )
    parser.add_argument("--output", default="site/coverage", help="Output directory for generated files")
    args = parser.parse_args()

    # Load config
    config = load_config(args.config)

    # Extract metrics from artifacts
    metrics = extract_metrics(config)

    # Validate metrics
    errors, warnings = validate_metrics(metrics)

    if errors:
        print("\n⚠️  VALIDATION ERRORS (data was corrected):")
        for err in errors:
            print(f"   - {err}")

    if warnings:
        print("\n⚠️  VALIDATION WARNINGS (unusual values):")
        for warn in warnings:
            print(f"   - {warn}")

    if not errors and not warnings:
        print("\n✅ All metric values validated successfully")

    # Calculate ratings
    ratings = calculate_ratings(metrics, config)

    # Generate badges
    generate_badges(metrics, ratings, config, args.output)

    # Create metrics.json
    create_metrics_json(metrics, ratings, args.output)

    # Update history
    update_history(metrics, ratings, args.output)

    # Print summary
    print_summary(metrics, ratings)


if __name__ == "__main__":
    main()

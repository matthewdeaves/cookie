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
from datetime import datetime, timezone
from pathlib import Path


def load_config(config_path: str) -> dict:
    """Load rating thresholds from config file."""
    with open(config_path) as f:
        return json.load(f)


def get_rating(value: float, thresholds: dict, higher_is_better: bool = True) -> str:
    """Calculate rating based on thresholds."""
    if higher_is_better:
        if value >= thresholds['A']:
            return 'A'
        elif value >= thresholds['B']:
            return 'B'
        elif value >= thresholds['C']:
            return 'C'
        else:
            return 'D'
    else:  # Lower is better (complexity, duplication)
        if value <= thresholds['A']:
            return 'A'
        elif value <= thresholds['B']:
            return 'B'
        elif value <= thresholds['C']:
            return 'C'
        else:
            return 'D'


def generate_badge_svg(label: str, value: str, color: str) -> str:
    """Generate an SVG badge locally (no shields.io dependency)."""
    # Color mapping
    colors = {
        'brightgreen': '#4c1',
        'green': '#97ca00',
        'yellow': '#dfb317',
        'orange': '#fe7d37',
        'red': '#e05d44',
        'lightgrey': '#9f9f9f'
    }
    bg_color = colors.get(color, colors['lightgrey'])

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
    <text x="{label_width/2}" y="15" fill="#010101" fill-opacity=".3">{label}</text>
    <text x="{label_width/2}" y="14">{label}</text>
    <text x="{label_width + value_width/2}" y="15" fill="#010101" fill-opacity=".3">{value}</text>
    <text x="{label_width + value_width/2}" y="14">{value}</text>
  </g>
</svg>'''
    return svg


def extract_metrics(config: dict) -> dict:
    """Extract all metrics from artifact files."""
    metrics = {
        'frontend_cov': 0,
        'backend_cov': 0,
        'backend_cc': 0,
        'backend_mi': 0,
        'frontend_avg_cc': 0,
        'frontend_complexity_warnings': 0,
        'duplication_pct': 0,
        'duplication_clones': 0,
        'backend_duplication_pct': 0,
        'backend_duplication_clones': 0,
        'frontend_vulns': 0,
        'backend_vulns': 0,
        'bundle_size_kb': 0,
        'bundle_gzip_kb': 0,
        'legacy_errors': 0,
        'legacy_warnings': 0,
        'legacy_complexity_warnings': 0,
        'legacy_duplication_pct': 0,
    }

    # Frontend coverage
    try:
        with open('coverage/frontend/coverage-summary.json') as f:
            d = json.load(f)
            metrics['frontend_cov'] = d['total']['lines']['pct']
    except FileNotFoundError:
        print("WARNING: Frontend coverage artifact not found")
    except (json.JSONDecodeError, KeyError) as e:
        print(f"ERROR: Invalid frontend coverage data: {e}")

    # Backend coverage
    try:
        with open('coverage/backend/coverage.json') as f:
            d = json.load(f)
            metrics['backend_cov'] = round(d['totals']['percent_covered'], 1)
    except FileNotFoundError:
        print("WARNING: Backend coverage artifact not found")
    except (json.JSONDecodeError, KeyError) as e:
        print(f"ERROR: Invalid backend coverage data: {e}")

    # Backend complexity
    try:
        with open('complexity/backend/summary.json') as f:
            d = json.load(f)
            metrics['backend_cc'] = d.get('average_cyclomatic_complexity', 0)
            metrics['backend_mi'] = d.get('average_maintainability_index', 0)
    except FileNotFoundError:
        print("WARNING: Backend complexity artifact not found")
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid backend complexity data: {e}")

    # Frontend complexity
    try:
        with open('complexity/frontend/summary.json') as f:
            d = json.load(f)
            metrics['frontend_complexity_warnings'] = d.get('complexity_warnings', 0)
            metrics['frontend_avg_cc'] = d.get('avg_cyclomatic_complexity', 0)
    except FileNotFoundError:
        print("WARNING: Frontend complexity artifact not found")
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid frontend complexity data: {e}")

    # Frontend duplication
    try:
        with open('duplication/frontend/summary.json') as f:
            d = json.load(f)
            metrics['duplication_pct'] = d.get('duplication_percentage', 0)
            metrics['duplication_clones'] = d.get('clones_count', 0)
    except FileNotFoundError:
        print("WARNING: Frontend duplication artifact not found")
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid frontend duplication data: {e}")

    # Backend duplication
    try:
        with open('duplication/backend/summary.json') as f:
            d = json.load(f)
            metrics['backend_duplication_pct'] = d.get('duplication_percentage', 0)
            metrics['backend_duplication_clones'] = d.get('clones_count', 0)
    except FileNotFoundError:
        print("WARNING: Backend duplication artifact not found")
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid backend duplication data: {e}")

    # Frontend security
    try:
        with open('security/frontend/summary.json') as f:
            d = json.load(f)
            metrics['frontend_vulns'] = d.get('total_vulnerabilities', 0)
    except FileNotFoundError:
        print("WARNING: Frontend security artifact not found")
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid frontend security data: {e}")

    # Backend security
    try:
        with open('security/backend/summary.json') as f:
            d = json.load(f)
            metrics['backend_vulns'] = d.get('total_high_severity', 0)
    except FileNotFoundError:
        print("WARNING: Backend security artifact not found")
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid backend security data: {e}")

    # Bundle metrics
    try:
        with open('bundle/frontend/summary.json') as f:
            d = json.load(f)
            metrics['bundle_size_kb'] = d.get('total_size_kb', 0)
            metrics['bundle_gzip_kb'] = d.get('total_gzip_kb', 0)
    except FileNotFoundError:
        print("WARNING: Bundle artifact not found")
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid bundle data: {e}")

    # Legacy lint
    try:
        with open('legacy/lint/summary.json') as f:
            d = json.load(f)
            metrics['legacy_errors'] = d.get('errors', 0)
            metrics['legacy_warnings'] = d.get('warnings', 0)
            metrics['legacy_complexity_warnings'] = d.get('complexity_warnings', 0)
    except FileNotFoundError:
        print("WARNING: Legacy lint artifact not found")
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid legacy lint data: {e}")

    # Legacy duplication
    try:
        with open('legacy/duplication/summary.json') as f:
            d = json.load(f)
            metrics['legacy_duplication_pct'] = d.get('duplication_percentage', 0)
    except FileNotFoundError:
        print("WARNING: Legacy duplication artifact not found")
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid legacy duplication data: {e}")

    return metrics


def validate_metrics(metrics: dict) -> tuple[list, list]:
    """Validate metric values and return errors/warnings."""
    errors = []
    warnings = []

    # Coverage should be 0-100
    if not (0 <= metrics['frontend_cov'] <= 100):
        errors.append(f"Invalid frontend coverage: {metrics['frontend_cov']}% (expected 0-100)")
        metrics['frontend_cov'] = max(0, min(100, metrics['frontend_cov']))
    if not (0 <= metrics['backend_cov'] <= 100):
        errors.append(f"Invalid backend coverage: {metrics['backend_cov']}% (expected 0-100)")
        metrics['backend_cov'] = max(0, min(100, metrics['backend_cov']))

    # Bundle size should be positive
    if metrics['bundle_size_kb'] < 0:
        errors.append(f"Invalid bundle size: {metrics['bundle_size_kb']}KB (expected >= 0)")
        metrics['bundle_size_kb'] = 0
    if metrics['bundle_gzip_kb'] < 0:
        errors.append(f"Invalid gzip bundle size: {metrics['bundle_gzip_kb']}KB (expected >= 0)")
        metrics['bundle_gzip_kb'] = 0

    # Complexity should be reasonable
    if metrics['backend_cc'] < 0 or metrics['backend_cc'] > 100:
        warnings.append(f"Unusual backend CC: {metrics['backend_cc']} (typically 1-50)")
    if metrics['frontend_avg_cc'] < 0 or metrics['frontend_avg_cc'] > 100:
        warnings.append(f"Unusual frontend CC: {metrics['frontend_avg_cc']} (typically 1-50)")

    # Maintainability index should be 0-100
    if not (0 <= metrics['backend_mi'] <= 100):
        warnings.append(f"Unusual backend MI: {metrics['backend_mi']} (expected 0-100)")

    # Duplication should be 0-100%
    if not (0 <= metrics['duplication_pct'] <= 100):
        warnings.append(f"Unusual frontend duplication: {metrics['duplication_pct']}% (expected 0-100)")
    if not (0 <= metrics['backend_duplication_pct'] <= 100):
        warnings.append(f"Unusual backend duplication: {metrics['backend_duplication_pct']}% (expected 0-100)")

    return errors, warnings


def calculate_ratings(metrics: dict, config: dict) -> dict:
    """Calculate all ratings based on config thresholds."""
    ratings = {}

    # Coverage ratings (higher is better)
    ratings['frontend_cov'] = get_rating(metrics['frontend_cov'], config['coverage']['thresholds'], True)
    ratings['backend_cov'] = get_rating(metrics['backend_cov'], config['coverage']['thresholds'], True)

    # Complexity ratings (lower is better)
    ratings['backend_cc'] = get_rating(metrics['backend_cc'], config['complexity']['thresholds'], False)
    ratings['frontend_cc'] = get_rating(metrics['frontend_avg_cc'], config['complexity']['thresholds'], False)

    # Maintainability rating (higher is better)
    ratings['backend_mi'] = get_rating(metrics['backend_mi'], config['maintainability']['thresholds'], True)

    # Duplication ratings (lower is better)
    ratings['frontend_dup'] = get_rating(metrics['duplication_pct'], config['duplication']['thresholds']['frontend'], False)
    ratings['backend_dup'] = get_rating(metrics['backend_duplication_pct'], config['duplication']['thresholds']['backend'], False)
    ratings['legacy_dup'] = get_rating(metrics['legacy_duplication_pct'], config['duplication']['thresholds']['legacy'], False)

    # Bundle rating (lower is better for gzip)
    ratings['bundle'] = get_rating(metrics['bundle_gzip_kb'], config['bundle']['thresholds']['gzip_kb'], False)

    # Security ratings
    ratings['frontend_security'] = 'A' if metrics['frontend_vulns'] == 0 else 'D'
    ratings['backend_security'] = 'A' if metrics['backend_vulns'] == 0 else 'C' if metrics['backend_vulns'] <= 3 else 'D'

    # Legacy lint rating
    if metrics['legacy_errors'] > 0:
        ratings['legacy_lint'] = 'D'
    elif metrics['legacy_warnings'] > 10:
        ratings['legacy_lint'] = 'C'
    elif metrics['legacy_warnings'] > 0:
        ratings['legacy_lint'] = 'B'
    else:
        ratings['legacy_lint'] = 'A'

    return ratings


def generate_badges(metrics: dict, ratings: dict, config: dict, output_dir: str):
    """Generate all SVG badges."""
    colors = config['colors']
    badges_dir = Path(output_dir) / 'badges'
    badges_dir.mkdir(parents=True, exist_ok=True)

    badges = [
        ('frontend-coverage', 'coverage', f"{metrics['frontend_cov']}%", colors[ratings['frontend_cov']]),
        ('backend-coverage', 'coverage', f"{metrics['backend_cov']}%", colors[ratings['backend_cov']]),
        ('backend-complexity', 'complexity', ratings['backend_cc'], colors[ratings['backend_cc']]),
        ('backend-maintainability', 'maintainability', ratings['backend_mi'], colors[ratings['backend_mi']]),
        ('frontend-complexity', 'complexity', ratings['frontend_cc'], colors[ratings['frontend_cc']]),
        ('duplication', 'duplication', ratings['frontend_dup'], colors[ratings['frontend_dup']]),
        ('backend-duplication', 'duplication', ratings['backend_dup'], colors[ratings['backend_dup']]),
        ('frontend-security', 'security', ratings['frontend_security'], colors[ratings['frontend_security']]),
        ('backend-security', 'security', ratings['backend_security'], colors[ratings['backend_security']]),
        ('bundle-size', 'bundle', ratings['bundle'], colors[ratings['bundle']]),
        ('legacy-lint', 'legacy lint', ratings['legacy_lint'], colors[ratings['legacy_lint']]),
        ('legacy-duplication', 'legacy dup', ratings['legacy_dup'], colors[ratings['legacy_dup']]),
    ]

    for name, label, value, color in badges:
        svg = generate_badge_svg(label, value, color)
        badge_path = badges_dir / f'{name}.svg'
        with open(badge_path, 'w') as f:
            f.write(svg)
        print(f"Generated {name} badge: {value}")


def create_metrics_json(metrics: dict, ratings: dict, output_dir: str):
    """Create the metrics.json API file."""
    api_dir = Path(output_dir) / 'api'
    api_dir.mkdir(parents=True, exist_ok=True)

    base_url = 'https://matthewdeaves.github.io/cookie/coverage'

    data = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'repo': 'matthewdeaves/cookie',
        'coverage': {
            'frontend': {
                'percentage': metrics['frontend_cov'],
                'badge_url': f'{base_url}/badges/frontend-coverage.svg'
            },
            'backend': {
                'percentage': metrics['backend_cov'],
                'badge_url': f'{base_url}/badges/backend-coverage.svg'
            }
        },
        'complexity': {
            'backend': {
                'cyclomatic_complexity': metrics['backend_cc'],
                'cyclomatic_rating': ratings['backend_cc'],
                'maintainability_index': metrics['backend_mi'],
                'maintainability_rating': ratings['backend_mi'],
                'badge_url': f'{base_url}/badges/backend-complexity.svg'
            },
            'frontend': {
                'avg_cyclomatic_complexity': metrics['frontend_avg_cc'],
                'complexity_warnings': metrics['frontend_complexity_warnings'],
                'rating': ratings['frontend_cc'],
                'badge_url': f'{base_url}/badges/frontend-complexity.svg'
            }
        },
        'duplication': {
            'frontend': {
                'percentage': metrics['duplication_pct'],
                'clones_count': metrics['duplication_clones'],
                'rating': ratings['frontend_dup'],
                'badge_url': f'{base_url}/badges/duplication.svg'
            },
            'backend': {
                'percentage': metrics['backend_duplication_pct'],
                'clones_count': metrics['backend_duplication_clones'],
                'rating': ratings['backend_dup'],
                'badge_url': f'{base_url}/badges/backend-duplication.svg'
            }
        },
        'security': {
            'frontend': {
                'vulnerabilities': metrics['frontend_vulns'],
                'rating': ratings['frontend_security'],
                'badge_url': f'{base_url}/badges/frontend-security.svg'
            },
            'backend': {
                'vulnerabilities': metrics['backend_vulns'],
                'rating': ratings['backend_security'],
                'badge_url': f'{base_url}/badges/backend-security.svg'
            }
        },
        'bundle': {
            'size_kb': metrics['bundle_size_kb'],
            'gzip_kb': metrics['bundle_gzip_kb'],
            'rating': ratings['bundle'],
            'badge_url': f'{base_url}/badges/bundle-size.svg'
        },
        'legacy': {
            'lint': {
                'errors': metrics['legacy_errors'],
                'warnings': metrics['legacy_warnings'],
                'complexity_warnings': metrics['legacy_complexity_warnings'],
                'rating': ratings['legacy_lint'],
                'badge_url': f'{base_url}/badges/legacy-lint.svg'
            },
            'duplication': {
                'percentage': metrics['legacy_duplication_pct'],
                'rating': ratings['legacy_dup'],
                'badge_url': f'{base_url}/badges/legacy-duplication.svg'
            }
        },
        'links': {
            'dashboard': f'{base_url}/',
            'frontend_coverage': f'{base_url}/frontend/',
            'backend_coverage': f'{base_url}/backend/htmlcov/',
            'github': 'https://github.com/matthewdeaves/cookie'
        }
    }

    with open(api_dir / 'metrics.json', 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\nMetrics JSON generated at {api_dir}/metrics.json")


def update_history(metrics: dict, ratings: dict, output_dir: str):
    """Update history.json with current metrics."""
    history_dir = Path(output_dir) / 'history'
    history_dir.mkdir(parents=True, exist_ok=True)
    history_file = history_dir / 'all.json'

    # Load existing history
    if history_file.exists():
        with open(history_file) as f:
            history = json.load(f)
        existing_count = len(history.get('entries', []))
        print(f"\nLoaded existing history with {existing_count} entries")
    else:
        history = {'entries': []}
        print("\nNo existing history file found, starting fresh")

    # Build new entry
    now = datetime.now(timezone.utc)
    entry = {
        'timestamp': now.isoformat(),
        'date': now.strftime('%Y-%m-%d'),
        'coverage': {
            'frontend': metrics['frontend_cov'],
            'backend': metrics['backend_cov']
        },
        'complexity': {
            'frontend_warnings': metrics['frontend_complexity_warnings'],
            'frontend_avg_cc': metrics['frontend_avg_cc'],
            'backend_cc': metrics['backend_cc'],
            'backend_mi': metrics['backend_mi']
        },
        'duplication': {
            'frontend': metrics['duplication_pct'],
            'backend': metrics['backend_duplication_pct'],
            'frontend_clones': metrics['duplication_clones'],
            'backend_clones': metrics['backend_duplication_clones']
        },
        'bundle': {
            'total_kb': metrics['bundle_size_kb'],
            'gzip_kb': metrics['bundle_gzip_kb']
        },
        'security': {
            'frontend_vulns': metrics['frontend_vulns'],
            'backend_vulns': metrics['backend_vulns']
        },
        'legacy': {
            'errors': metrics['legacy_errors'],
            'warnings': metrics['legacy_warnings'],
            'duplication': metrics['legacy_duplication_pct']
        }
    }

    history['entries'].append(entry)
    history['entries'].sort(key=lambda x: x.get('timestamp', x.get('date', '')))
    history['entries'] = history['entries'][-200:]  # Keep last 200 entries

    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)

    print(f"\nHistory updated: {len(history['entries'])} entries")
    print(f"Latest entry: {entry['timestamp']}")


def print_summary(metrics: dict, ratings: dict):
    """Print a summary of all metrics."""
    print("\n" + "="*60)
    print("METRICS SUMMARY")
    print("="*60)
    print(f"Frontend Coverage: {metrics['frontend_cov']}% ({ratings['frontend_cov']})")
    print(f"Backend Coverage: {metrics['backend_cov']}% ({ratings['backend_cov']})")
    print(f"Backend Complexity: CC={metrics['backend_cc']} ({ratings['backend_cc']}), MI={metrics['backend_mi']} ({ratings['backend_mi']})")
    print(f"Frontend Complexity: CC={metrics['frontend_avg_cc']} ({ratings['frontend_cc']}), {metrics['frontend_complexity_warnings']} ESLint warnings")
    print(f"Duplication: Frontend={metrics['duplication_pct']}% ({ratings['frontend_dup']}), Backend={metrics['backend_duplication_pct']}% ({ratings['backend_dup']})")
    print(f"Security: Frontend={metrics['frontend_vulns']} ({ratings['frontend_security']}), Backend={metrics['backend_vulns']} ({ratings['backend_security']})")
    print(f"Bundle Size: {metrics['bundle_size_kb']}KB raw, {metrics['bundle_gzip_kb']}KB gzipped ({ratings['bundle']})")
    print(f"Legacy Lint: {metrics['legacy_errors']} errors, {metrics['legacy_warnings']} warnings ({ratings['legacy_lint']})")
    print(f"Legacy Duplication: {metrics['legacy_duplication_pct']}% ({ratings['legacy_dup']})")
    print("="*60)


def main():
    parser = argparse.ArgumentParser(description='Generate metrics dashboard from CI artifacts')
    parser.add_argument('--config', default='.github/scripts/rating-config.json',
                        help='Path to rating config JSON file')
    parser.add_argument('--output', default='site/coverage',
                        help='Output directory for generated files')
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


if __name__ == '__main__':
    main()

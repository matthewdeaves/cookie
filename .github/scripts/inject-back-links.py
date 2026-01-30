#!/usr/bin/env python3
"""
Inject "Back to Dashboard" links into all HTML report files.

This script adds a floating back button to all generated HTML reports
(coverage, complexity, duplication) so users can easily navigate back
to the main dashboard.

Usage:
    python inject-back-links.py [--site-dir site/coverage]
"""

import argparse
import glob
import os


BACK_LINK_HTML = '''<div style="position:fixed;top:10px;right:10px;z-index:9999;"><a href="/cookie/coverage/" style="background:#0066cc;color:white;padding:8px 16px;border-radius:6px;text-decoration:none;font-family:-apple-system,BlinkMacSystemFont,sans-serif;font-size:14px;box-shadow:0 2px 4px rgba(0,0,0,0.2);">&#8592; Back to Dashboard</a></div>'''


def inject_back_links(site_dir: str):
    """Inject back links into all HTML files except the main dashboard."""
    count = 0
    skipped = 0

    for html_file in glob.glob(f'{site_dir}/**/*.html', recursive=True):
        # Skip the main dashboard index
        if html_file == f'{site_dir}/index.html':
            continue

        try:
            with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Skip if already has the back link or no body tag
            if BACK_LINK_HTML in content:
                skipped += 1
                continue

            if '</body>' not in content:
                skipped += 1
                continue

            # Inject the back link before </body>
            content = content.replace('</body>', BACK_LINK_HTML + '</body>')

            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"Injected: {html_file}")
            count += 1

        except Exception as e:
            print(f"Skipped {html_file}: {e}")
            skipped += 1

    print(f"\nInjected back links into {count} files")
    if skipped:
        print(f"Skipped {skipped} files (already injected or no body tag)")


def main():
    parser = argparse.ArgumentParser(description='Inject back links into HTML reports')
    parser.add_argument('--site-dir', default='site/coverage',
                        help='Directory containing HTML reports')
    args = parser.parse_args()

    inject_back_links(args.site_dir)


if __name__ == '__main__':
    main()

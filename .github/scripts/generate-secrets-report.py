#!/usr/bin/env python3
"""
Generate secrets detection summary and HTML report.

Processes detect-secrets scan results and generates reports for the metrics dashboard.

Usage:
    python generate-secrets-report.py

Exit codes:
    0 - No secrets found
    1 - Secrets detected (requires review)
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def main():
    security_dir = Path("security")
    security_dir.mkdir(exist_ok=True)

    secrets_found_list = []
    total_secrets = 0

    try:
        with open(security_dir / "secrets-scan.json") as f:
            results = json.load(f)

        secrets_data = results.get("results", {})
        for filename, secrets in secrets_data.items():
            for secret in secrets:
                secrets_found_list.append(
                    {
                        "file": filename,
                        "line": secret.get("line_number", "?"),
                        "type": secret.get("type", "unknown"),
                    }
                )
        total_secrets = len(secrets_found_list)
    except (json.JSONDecodeError, FileNotFoundError):
        pass

    # Generate summary JSON
    summary = {
        "secrets_found": total_secrets,
        "rating": "A" if total_secrets == 0 else "D",
        "files_with_secrets": len({s["file"] for s in secrets_found_list}),
    }
    with open(security_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    # Generate HTML report
    rating_color = "#4c1" if total_secrets == 0 else "#e05d44"
    rating = "A" if total_secrets == 0 else "D"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Secrets Detection Report</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 1200px; margin: 0 auto; padding: 2rem; background: #f5f5f5; color: #333; }}
    h1 {{ font-size: 2rem; margin-bottom: 0.5rem; }}
    .subtitle {{ color: #666; margin-bottom: 2rem; }}
    h2 {{ font-size: 1.25rem; margin: 2rem 0 1rem; border-bottom: 2px solid #e1e4e8; padding-bottom: 0.5rem; }}
    .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
    .stat {{ background: white; padding: 1rem; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
    .stat-value {{ font-size: 2rem; font-weight: bold; }}
    .stat-label {{ color: #666; font-size: 0.85rem; }}
    .rating {{ display: inline-block; padding: 0.25rem 0.75rem; border-radius: 4px; color: white; font-weight: bold; }}
    table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 2rem; }}
    th, td {{ padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid #e1e4e8; }}
    th {{ background: #f6f8fa; font-weight: 600; }}
    tr:hover {{ background: #f6f8fa; }}
    .back-link {{ display: inline-block; margin-bottom: 1rem; color: #0066cc; text-decoration: none; }}
    .back-link:hover {{ text-decoration: underline; }}
    code {{ background: #f3f4f6; padding: 0.1rem 0.3rem; border-radius: 3px; font-size: 0.85rem; }}
    .success {{ color: #4c1; }}
    .danger {{ color: #e05d44; }}
  </style>
</head>
<body>
  <a href="../index.html" class="back-link">&larr; Back to Dashboard</a>
  <h1>Secrets Detection Report</h1>
  <p class="subtitle">Scanning for accidentally committed secrets, API keys, and credentials</p>

  <div class="summary">
    <div class="stat">
      <div class="stat-value" style="color:{rating_color}">{total_secrets}</div>
      <div class="stat-label">Secrets Found</div>
    </div>
    <div class="stat">
      <div class="stat-value"><span class="rating" style="background:{rating_color}">{rating}</span></div>
      <div class="stat-label">Rating</div>
    </div>
  </div>
"""

    if secrets_found_list:
        html += """<h2>Detected Secrets</h2>
<table>
<thead><tr><th>File</th><th>Line</th><th>Type</th></tr></thead>
<tbody>"""
        for s in secrets_found_list:
            html += f"<tr><td><code>{s['file']}</code></td><td>{s['line']}</td><td>{s['type']}</td></tr>"
        html += "</tbody></table>"
    else:
        html += (
            '<p class="success" style="margin:1rem 0;font-size:1.25rem;">&check; No secrets detected in codebase</p>'
        )

    html += f"""
  <p style="color:#666;font-size:0.85rem;margin-top:2rem;">
    Generated: {datetime.now().isoformat()}<br>
    Tool: detect-secrets (scanning against .secrets.baseline)
  </p>
</body>
</html>"""

    with open(security_dir / "secrets-report.html", "w") as f:
        f.write(html)

    # Print results
    if total_secrets > 0:
        print(f"WARNING: Found {total_secrets} potential secret(s)")
        for s in secrets_found_list:
            print(f"  {s['file']}:{s['line']} - {s['type']}")
        print("\nPlease review and remove secrets, or update .secrets.baseline if false positives.")
        sys.exit(1)
    else:
        print("No secrets detected")


if __name__ == "__main__":
    main()

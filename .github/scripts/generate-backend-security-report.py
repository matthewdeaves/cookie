#!/usr/bin/env python3
"""
Generate combined backend security summary and HTML report.

Processes pip-audit and Bandit SAST results into a unified summary
and generates an HTML report for the metrics dashboard.

Usage:
    python generate-backend-security-report.py
"""

import json
from datetime import datetime
from pathlib import Path


def main():
    security_dir = Path("security")
    security_dir.mkdir(exist_ok=True)

    # Parse pip-audit results
    pip_vulns = 0
    try:
        with open(security_dir / "pip-audit.json") as f:
            data = json.load(f)
            if isinstance(data, dict):
                for dep in data.get("dependencies", []):
                    pip_vulns += len(dep.get("vulns", []))
            elif isinstance(data, list):
                pip_vulns = len(data)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Note: Could not parse pip-audit output: {e}")

    # Parse Bandit results
    bandit_issues = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    bandit_results = []
    try:
        with open(security_dir / "bandit.json") as f:
            data = json.load(f)
            bandit_results = data.get("results", [])
            for result in bandit_results:
                severity = result.get("issue_severity", "LOW")
                bandit_issues[severity] = bandit_issues.get(severity, 0) + 1
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Note: Could not parse Bandit output: {e}")

    # Calculate combined rating
    high_severity = pip_vulns + bandit_issues["HIGH"]
    medium_severity = bandit_issues["MEDIUM"]

    if high_severity == 0 and medium_severity == 0:
        rating = "A"
    elif high_severity == 0 and medium_severity <= 3:
        rating = "B"
    elif high_severity <= 2:
        rating = "C"
    else:
        rating = "D"

    summary = {
        "pip_audit": {"vulnerabilities": pip_vulns},
        "bandit": {
            "high": bandit_issues["HIGH"],
            "medium": bandit_issues["MEDIUM"],
            "low": bandit_issues["LOW"],
            "total": sum(bandit_issues.values()),
        },
        "total_high_severity": high_severity,
        "rating": rating,
    }

    with open(security_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    # Generate HTML report
    rating_colors = {"A": "#4c1", "B": "#97ca00", "C": "#dfb317", "D": "#e05d44"}
    rating_color = rating_colors.get(rating, "#9f9f9f")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Backend Security Report</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 1200px; margin: 0 auto; padding: 2rem; background: #f5f5f5; color: #333; }}
    h1 {{ font-size: 2rem; margin-bottom: 0.5rem; }}
    .subtitle {{ color: #666; margin-bottom: 2rem; }}
    h2 {{ font-size: 1.25rem; margin: 2rem 0 1rem; border-bottom: 2px solid #e1e4e8; padding-bottom: 0.5rem; }}
    .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
    .stat {{ background: white; padding: 1rem; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
    .stat-value {{ font-size: 2rem; font-weight: bold; }}
    .stat-label {{ color: #666; font-size: 0.85rem; }}
    .rating {{ display: inline-block; padding: 0.25rem 0.75rem; border-radius: 4px; color: white; font-weight: bold; }}
    table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 2rem; }}
    th, td {{ padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid #e1e4e8; }}
    th {{ background: #f6f8fa; font-weight: 600; }}
    tr:hover {{ background: #f6f8fa; }}
    .severity-high {{ color: #e05d44; font-weight: bold; }}
    .severity-medium {{ color: #dfb317; font-weight: bold; }}
    .severity-low {{ color: #97ca00; }}
    .back-link {{ display: inline-block; margin-bottom: 1rem; color: #0066cc; text-decoration: none; }}
    .back-link:hover {{ text-decoration: underline; }}
    code {{ background: #f3f4f6; padding: 0.1rem 0.3rem; border-radius: 3px; font-size: 0.85rem; }}
  </style>
</head>
<body>
  <a href="../index.html" class="back-link">&larr; Back to Dashboard</a>
  <h1>Backend Security Report</h1>
  <p class="subtitle">Dependency vulnerabilities (pip-audit) and code security (Bandit SAST)</p>

  <div class="summary">
    <div class="stat">
      <div class="stat-value">{pip_vulns}</div>
      <div class="stat-label">pip-audit Vulns</div>
    </div>
    <div class="stat">
      <div class="stat-value" style="color:#e05d44">{bandit_issues["HIGH"]}</div>
      <div class="stat-label">Bandit HIGH</div>
    </div>
    <div class="stat">
      <div class="stat-value" style="color:#dfb317">{bandit_issues["MEDIUM"]}</div>
      <div class="stat-label">Bandit MEDIUM</div>
    </div>
    <div class="stat">
      <div class="stat-value" style="color:#97ca00">{bandit_issues["LOW"]}</div>
      <div class="stat-label">Bandit LOW</div>
    </div>
    <div class="stat">
      <div class="stat-value"><span class="rating" style="background:{rating_color}">{rating}</span></div>
      <div class="stat-label">Rating</div>
    </div>
  </div>

  <h2>Bandit SAST Issues</h2>
"""

    if bandit_results:
        html += """<table>
  <thead><tr><th>Severity</th><th>Issue</th><th>File</th><th>Line</th></tr></thead>
  <tbody>"""
        # Sort by severity (HIGH first)
        severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        sorted_results = sorted(
            bandit_results,
            key=lambda x: severity_order.get(x.get("issue_severity", "LOW"), 3),
        )
        for issue in sorted_results:
            sev = issue.get("issue_severity", "LOW")
            sev_class = f"severity-{sev.lower()}"
            filename = issue.get("filename", "").replace("/home/runner/work/cookie/cookie/", "")
            html += f"""<tr>
    <td class="{sev_class}">{sev}</td>
    <td>{issue.get("issue_text", "Unknown")}</td>
    <td><code>{filename}</code></td>
    <td>{issue.get("line_number", "-")}</td>
  </tr>"""
        html += "</tbody></table>"
    else:
        html += '<p style="color:#4c1;margin:1rem 0;">&check; No Bandit issues found</p>'

    html += f"""
  <p style="color:#666;font-size:0.85rem;margin-top:2rem;">
    Generated: {datetime.now().isoformat()}<br>
    Tools: pip-audit (dependency vulnerabilities), Bandit (SAST code analysis)
  </p>
</body>
</html>"""

    with open(security_dir / "backend-security.html", "w") as f:
        f.write(html)

    print(f"Security summary: {json.dumps(summary, indent=2)}")


if __name__ == "__main__":
    main()

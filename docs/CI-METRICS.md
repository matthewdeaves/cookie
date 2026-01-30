# CI Metrics System Documentation

This document explains how the Cookie project's CI metrics system works, how to add new metrics, and how to troubleshoot common issues.

## Overview

The CI pipeline collects code quality metrics on every push to main/master and publishes them to GitHub Pages at:
- **Dashboard:** https://matthewdeaves.github.io/cookie/coverage/
- **API Endpoint:** https://matthewdeaves.github.io/cookie/coverage/api/metrics.json
- **Historical Data:** https://matthewdeaves.github.io/cookie/coverage/history/all.json

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CI Workflow (ci.yml)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Frontend   │  │   Backend    │  │  Complexity  │  │   Security   │   │
│  │   Tests      │  │   Tests      │  │   Analysis   │  │   Scans      │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         │                 │                 │                 │           │
│         ▼                 ▼                 ▼                 ▼           │
│  ┌──────────────────────────────────────────────────────────────────┐     │
│  │                    Upload Artifacts                               │     │
│  │  (frontend-coverage, backend-coverage, complexity, security...)   │     │
│  └───────────────────────────────┬──────────────────────────────────┘     │
│                                  │                                         │
└──────────────────────────────────┼─────────────────────────────────────────┘
                                   │
                                   ▼  triggers on: workflow_run completed
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Coverage Workflow (coverage.yml)                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                      Download All Artifacts                         │    │
│  └────────────────────────────────┬───────────────────────────────────┘    │
│                                   │                                         │
│                                   ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │              generate-dashboard.py                                  │    │
│  │  - Extract metrics from artifacts                                   │    │
│  │  - Validate all values                                              │    │
│  │  - Calculate ratings using rating-config.json                       │    │
│  │  - Generate SVG badges locally                                      │    │
│  │  - Create metrics.json API file                                     │    │
│  │  - Update history.json with timestamp                               │    │
│  └────────────────────────────────┬───────────────────────────────────┘    │
│                                   │                                         │
│                                   ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                   Deploy to GitHub Pages                            │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Rating Thresholds

Ratings are configured in `.github/scripts/rating-config.json`. Here's why each threshold was chosen:

### Coverage (Higher is Better)
| Rating | Threshold | Rationale |
|--------|-----------|-----------|
| A | ≥ 80% | Industry standard for "well-tested" code |
| B | ≥ 60% | Acceptable coverage, room for improvement |
| C | ≥ 40% | Minimal coverage, needs attention |
| D | < 40% | Critically undertested |

### Cyclomatic Complexity (Lower is Better)
| Rating | Threshold | Rationale |
|--------|-----------|-----------|
| A | ≤ 5 | Simple, easy to understand and test |
| B | ≤ 10 | Moderate complexity, acceptable |
| C | ≤ 20 | Complex, consider refactoring |
| D | > 20 | Very complex, hard to maintain |

### Duplication (Lower is Better)
| Rating | Threshold | Rationale |
|--------|-----------|-----------|
| A | ≤ 3% | Minimal duplication |
| B | ≤ 5% | Acceptable, minor refactoring opportunities |
| C | ≤ 10% | Needs attention |
| D | > 10% | Significant duplication, refactor |

### Bundle Size - Gzipped (Lower is Better)
| Rating | Threshold | Rationale |
|--------|-----------|-----------|
| A | ≤ 150KB | Fast load times on 3G |
| B | ≤ 300KB | Acceptable for most connections |
| C | ≤ 500KB | Large, consider code splitting |
| D | > 500KB | Very large, investigate |

## Adding a New Metric

### Step 1: Add Collection to CI Workflow

In `.github/workflows/ci.yml`, add a new job to collect your metric:

```yaml
your-metric:
  name: Your Metric Analysis
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v6

    - name: Run analysis
      run: |
        # Your analysis commands here
        echo '{"your_value": 42, "rating": "A"}' > summary.json

    - uses: actions/upload-artifact@v4
      with:
        name: your-metric
        path: summary.json
```

### Step 2: Add Artifact Download to Coverage Workflow

In `.github/workflows/coverage.yml`, add the download step:

```yaml
- name: Download your metric
  uses: actions/download-artifact@v7
  with:
    name: your-metric
    path: your-metric
    run-id: ${{ github.event.workflow_run.id }}
    github-token: ${{ secrets.GITHUB_TOKEN }}
  continue-on-error: true  # Remove if metric is critical
```

### Step 3: Add Extraction to generate-dashboard.py

In `.github/scripts/generate-dashboard.py`, add metric extraction:

```python
# In extract_metrics():
try:
    with open('your-metric/summary.json') as f:
        d = json.load(f)
        metrics['your_value'] = d.get('your_value', 0)
except FileNotFoundError:
    print("WARNING: Your metric artifact not found")
```

### Step 4: Add Rating Thresholds

In `.github/scripts/rating-config.json`:

```json
{
  "your_metric": {
    "thresholds": {
      "A": 90,
      "B": 70,
      "C": 50
    },
    "description": "Your metric description (higher/lower is better)"
  }
}
```

### Step 5: Add Badge Generation

In `generate-dashboard.py`, add to the badges list:

```python
('your-metric', 'your label', ratings['your_metric'], colors[ratings['your_metric']]),
```

### Step 6: Add to Dashboard HTML

Update the dashboard template in `coverage.yml` to display your metric.

## Running Metrics Locally

You can test the metrics generation scripts locally:

```bash
# Create mock artifact directories
mkdir -p coverage/frontend coverage/backend complexity/backend

# Run the dashboard generator
python .github/scripts/generate-dashboard.py --config .github/scripts/rating-config.json --output test-output

# Check generated files
ls test-output/badges/
cat test-output/api/metrics.json
```

## Troubleshooting

### Dashboard shows stale data

1. Check if the CI workflow completed successfully
2. Look for artifact download failures in the coverage workflow logs
3. Verify the artifact names match between ci.yml and coverage.yml

### Badge shows "N/A"

The artifact wasn't found or the data couldn't be parsed. Check:
1. The artifact was uploaded successfully in ci.yml
2. The file path in extract_metrics() matches the actual path
3. The JSON structure matches what the parser expects

### History not updating

1. Check if `site/coverage/history/all.json` exists on gh-pages branch
2. Look for errors in the history update step
3. Verify the timestamp is being generated correctly

### Validation warnings

These indicate unusual but not invalid values. Investigate if:
- Coverage is outside 0-100%
- Complexity is > 100
- Bundle size is negative

### Critical artifacts failing

If `continue-on-error` is removed (critical artifacts), the entire deployment fails if that artifact is missing. Check:
1. The test/analysis job completed successfully
2. The artifact upload step succeeded
3. The artifact name is spelled correctly

## File Locations

| File | Purpose |
|------|---------|
| `.github/workflows/ci.yml` | Main CI workflow - runs tests and analysis |
| `.github/workflows/coverage.yml` | Dashboard generation and deployment |
| `.github/scripts/rating-config.json` | Rating thresholds configuration |
| `.github/scripts/generate-dashboard.py` | Main dashboard generation script |
| `.github/scripts/inject-back-links.py` | Adds navigation to HTML reports |

## API Response Format

The `metrics.json` API returns:

```json
{
  "generated_at": "2024-01-15T10:30:00Z",
  "repo": "matthewdeaves/cookie",
  "coverage": {
    "frontend": {"percentage": 85.5, "badge_url": "..."},
    "backend": {"percentage": 78.2, "badge_url": "..."}
  },
  "complexity": {
    "backend": {"cyclomatic_complexity": 4.2, "maintainability_index": 82},
    "frontend": {"avg_cyclomatic_complexity": 3.8}
  },
  "duplication": {
    "frontend": {"percentage": 2.1, "clones_count": 5},
    "backend": {"percentage": 1.8, "clones_count": 3}
  },
  "security": {
    "frontend": {"vulnerabilities": 0},
    "backend": {"vulnerabilities": 0}
  },
  "bundle": {
    "size_kb": 741,
    "gzip_kb": 197
  },
  "links": {
    "dashboard": "https://matthewdeaves.github.io/cookie/coverage/",
    "github": "https://github.com/matthewdeaves/cookie"
  }
}
```

## Historical Data Format

The `history/all.json` file contains timestamped entries:

```json
{
  "entries": [
    {
      "timestamp": "2024-01-15T10:30:00Z",
      "date": "2024-01-15",
      "coverage": {"frontend": 85.5, "backend": 78.2},
      "complexity": {"frontend_avg_cc": 3.8, "backend_cc": 4.2},
      "duplication": {"frontend": 2.1, "backend": 1.8},
      "bundle": {"total_kb": 741, "gzip_kb": 197},
      "security": {"frontend_vulns": 0, "backend_vulns": 0}
    }
  ]
}
```

Entries are kept for the last 200 CI runs, with timestamps preserving intra-day data.

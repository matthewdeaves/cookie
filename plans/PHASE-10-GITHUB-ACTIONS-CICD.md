# Phase 10: GitHub Actions CI/CD Pipeline

## Overview

Configure GitHub Actions to run all tests on every PR and commit to main branch, with automatic Docker image builds and pushes to Docker Hub on successful merges. The production image should be ready out-of-the-box to run on any machine (Ubuntu, Apple Silicon Macs, Windows with Docker Desktop) and accessible from any browser on the local network.

**Docker Hub Repository:** `mndeaves/cookie`

---

## Session Scope

| Session | Tasks | Focus | Files Changed |
|---------|-------|-------|---------------|
| A | 10.1-10.2 | CI workflow + coverage infrastructure | `.github/workflows/ci.yml`, `frontend/package.json`, `frontend/vitest.config.ts`, `requirements.txt` |
| B | 10.3 | Coverage publishing to GitHub Pages | `.github/workflows/coverage.yml` |
| C | 10.4 | Production Dockerfile | `Dockerfile.prod`, `entrypoint.prod.sh` |
| D | 10.5-10.6 | Django settings + CD workflow | `cookie/settings.py`, `.github/workflows/cd.yml` |
| E | 10.8 | Production container hardening | `Dockerfile.prod`, `entrypoint.prod.sh`, `cookie/settings.py` |
| F | 10.9 | Dev/Prod coexistence + tooling review | `bin/*`, `docker-compose.yml`, `docker-compose.prod.yml` |

**Manual (outside Claude Code sessions):** 10.7 - Configure GitHub repository secrets, Pages, and branch protection in the GitHub web UI.

---

## Phase 10.1: Create CI Workflow

Create `.github/workflows/ci.yml` for the main CI pipeline.

### Pre-CI Local Verification

> **Prerequisite:** This phase assumes all tests are already passing from previous phases (1-9). If not, fix failing tests before proceeding.

Before creating the CI workflow, verify all tests pass locally:

```bash
# Backend tests
docker compose exec web python -m pytest -v

# Frontend tests
docker compose exec frontend npm test
```

If any tests fail, fix them before proceeding. CI will fail if tests don't pass locally.

### Jobs (All Run in Parallel)

| Job | Purpose | Runtime |
|-----|---------|---------|
| `frontend-lint` | ESLint checks | ~30s |
| `frontend-typecheck` | TypeScript compilation | ~30s |
| `frontend-test` | Vitest with coverage | ~1m |
| `backend-test` | pytest with coverage | ~2m |
| `backend-complexity` | Radon complexity analysis | ~30s |
| `frontend-complexity` | ESLint complexity analysis | ~30s |
| `ci-success` | Status gate (waits for all) | ~5s |

### File: `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  frontend-lint:
    name: Frontend Lint (ESLint)
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Run ESLint
        run: npm run lint

  frontend-typecheck:
    name: Frontend Type Check (TypeScript)
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Run TypeScript compiler
        run: npx tsc --noEmit

  frontend-test:
    name: Frontend Tests (Vitest)
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Run Vitest with coverage
        run: npm run test:coverage

      - name: Upload frontend coverage artifact
        uses: actions/upload-artifact@v4
        with:
          name: frontend-coverage
          path: frontend/coverage/
          retention-days: 30

  backend-test:
    name: Backend Tests (pytest)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run pytest with coverage
        run: |
          pytest tests/ \
            --cov=apps \
            --cov=cookie \
            --cov-report=xml:coverage.xml \
            --cov-report=html:htmlcov \
            --cov-report=json:coverage.json \
            --cov-report=term \
            -v
        env:
          DJANGO_SETTINGS_MODULE: cookie.settings
          DATABASE_PATH: /tmp/test_db.sqlite3

      - name: Upload backend coverage artifact
        uses: actions/upload-artifact@v4
        with:
          name: backend-coverage
          path: |
            coverage.xml
            coverage.json
            htmlcov/
          retention-days: 30

  backend-complexity:
    name: Backend Complexity (radon)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install radon
        run: pip install radon

      - name: Generate complexity reports
        run: |
          mkdir -p complexity

          # Cyclomatic Complexity (CC) - JSON and text
          radon cc apps/ cookie/ -a -s --json > complexity/cc.json
          radon cc apps/ cookie/ -a -s > complexity/cc.txt

          # Maintainability Index (MI) - JSON and text
          radon mi apps/ cookie/ -s --json > complexity/mi.json
          radon mi apps/ cookie/ -s > complexity/mi.txt

          # Raw metrics (LOC, LLOC, SLOC, comments, etc.)
          radon raw apps/ cookie/ -s --json > complexity/raw.json

          # Halstead metrics
          radon hal apps/ cookie/ --json > complexity/hal.json

          # Generate HTML report
          echo "Generating complexity HTML report..."
          python3 << 'EOF'
          import json
          import os

          # Load complexity data
          with open('complexity/cc.json') as f:
              cc_data = json.load(f)
          with open('complexity/mi.json') as f:
              mi_data = json.load(f)

          # Calculate averages
          total_cc = 0
          cc_count = 0
          for file_path, functions in cc_data.items():
              for func in functions:
                  total_cc += func.get('complexity', 0)
                  cc_count += 1

          avg_cc = round(total_cc / cc_count, 2) if cc_count > 0 else 0

          mi_scores = [v.get('mi', 0) for v in mi_data.values() if isinstance(v, dict)]
          avg_mi = round(sum(mi_scores) / len(mi_scores), 2) if mi_scores else 0

          # Generate summary JSON
          summary = {
              'average_cyclomatic_complexity': avg_cc,
              'average_maintainability_index': avg_mi,
              'total_functions_analyzed': cc_count,
              'total_files_analyzed': len(mi_data),
              'cc_rating': 'A' if avg_cc <= 5 else 'B' if avg_cc <= 10 else 'C' if avg_cc <= 20 else 'D',
              'mi_rating': 'A' if avg_mi >= 80 else 'B' if avg_mi >= 60 else 'C' if avg_mi >= 40 else 'D'
          }

          with open('complexity/summary.json', 'w') as f:
              json.dump(summary, f, indent=2)

          print(f"Average CC: {avg_cc} ({summary['cc_rating']})")
          print(f"Average MI: {avg_mi} ({summary['mi_rating']})")
          EOF

      - name: Upload complexity artifact
        uses: actions/upload-artifact@v4
        with:
          name: backend-complexity
          path: complexity/
          retention-days: 30

  frontend-complexity:
    name: Frontend Complexity (ESLint)
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Generate complexity report
        run: |
          mkdir -p complexity

          # Run ESLint with complexity rules and JSON output
          npx eslint src/ \
            --rule '{"complexity": ["warn", 10]}' \
            --rule '{"max-depth": ["warn", 4]}' \
            --rule '{"max-nested-callbacks": ["warn", 3]}' \
            --rule '{"max-lines-per-function": ["warn", 50]}' \
            -f json > complexity/eslint-report.json || true

          # Count lines of code
          echo '{}' > complexity/loc.json
          find src -name '*.ts' -o -name '*.tsx' | head -100 | while read file; do
            wc -l "$file"
          done > complexity/loc.txt || true

          # Generate summary
          node << 'EOF'
          const fs = require('fs');

          let report = [];
          try {
            report = JSON.parse(fs.readFileSync('complexity/eslint-report.json', 'utf8'));
          } catch (e) {
            report = [];
          }

          let complexityWarnings = 0;
          let totalFiles = report.length;

          report.forEach(file => {
            file.messages.forEach(msg => {
              if (msg.ruleId === 'complexity') complexityWarnings++;
            });
          });

          const summary = {
            total_files: totalFiles,
            complexity_warnings: complexityWarnings,
            rating: complexityWarnings === 0 ? 'A' : complexityWarnings <= 5 ? 'B' : complexityWarnings <= 10 ? 'C' : 'D'
          };

          fs.writeFileSync('complexity/summary.json', JSON.stringify(summary, null, 2));
          console.log('Frontend complexity:', JSON.stringify(summary));
          EOF

      - name: Upload complexity artifact
        uses: actions/upload-artifact@v4
        with:
          name: frontend-complexity
          path: frontend/complexity/
          retention-days: 30

  ci-success:
    name: CI Success
    runs-on: ubuntu-latest
    needs: [frontend-lint, frontend-typecheck, frontend-test, backend-test, backend-complexity, frontend-complexity]
    if: always()
    steps:
      - name: Check all jobs passed
        run: |
          # Core jobs must pass
          if [[ "${{ needs.frontend-lint.result }}" != "success" ]] || \
             [[ "${{ needs.frontend-typecheck.result }}" != "success" ]] || \
             [[ "${{ needs.frontend-test.result }}" != "success" ]] || \
             [[ "${{ needs.backend-test.result }}" != "success" ]]; then
            echo "One or more CI jobs failed"
            exit 1
          fi
          # Complexity jobs are informational (warn but don't fail)
          if [[ "${{ needs.backend-complexity.result }}" != "success" ]] || \
             [[ "${{ needs.frontend-complexity.result }}" != "success" ]]; then
            echo "Warning: Complexity analysis had issues, but continuing..."
          fi
          echo "All CI jobs passed successfully"
```

---

## Phase 10.2: Add Coverage Infrastructure

### Update: `frontend/package.json`

Add the coverage dependency and script:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "lint": "eslint .",
    "preview": "vite preview",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage"
  },
  "devDependencies": {
    "@vitest/coverage-v8": "^2.1.8"
  }
}
```

### Update: `frontend/vitest.config.ts`

```typescript
import { defineConfig, mergeConfig } from 'vitest/config'
import viteConfig from './vite.config'

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      globals: true,
      environment: 'jsdom',
      setupFiles: './src/test/setup.ts',
      css: true,
      coverage: {
        provider: 'v8',
        reporter: ['text', 'json', 'json-summary', 'lcov', 'html'],
        reportsDirectory: './coverage',
        include: ['src/**/*.{ts,tsx}'],
        exclude: [
          'src/test/**',
          'src/**/*.d.ts',
          'src/main.tsx',
          'src/vite-env.d.ts'
        ],
      },
    },
  })
)
```

### Update: `requirements.txt`

Add pytest-cov, radon (code complexity), and whitenoise (static file serving):

```
pytest-cov>=4.0
radon>=6.0
whitenoise>=6.0
```

> **Note:** Verify `pytest-django` is already in requirements.txt (should exist from earlier phases). If not, add `pytest-django>=4.0`.

---

## Phase 10.3: Create Coverage & Metrics Publishing Workflow

### File: `.github/workflows/coverage.yml`

```yaml
name: Coverage & Metrics Report

on:
  workflow_run:
    workflows: ["CI"]
    types: [completed]
    branches: [main, master]

permissions:
  contents: write
  pages: write
  id-token: write

jobs:
  publish-coverage:
    name: Publish Coverage & Metrics to GitHub Pages
    runs-on: ubuntu-latest
    if: github.event.workflow_run.conclusion == 'success'
    steps:
      - uses: actions/checkout@v4

      - name: Download frontend coverage
        uses: actions/download-artifact@v4
        with:
          name: frontend-coverage
          path: coverage/frontend
          run-id: ${{ github.event.workflow_run.id }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
        continue-on-error: true

      - name: Download backend coverage
        uses: actions/download-artifact@v4
        with:
          name: backend-coverage
          path: coverage/backend
          run-id: ${{ github.event.workflow_run.id }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
        continue-on-error: true

      - name: Download backend complexity
        uses: actions/download-artifact@v4
        with:
          name: backend-complexity
          path: complexity/backend
          run-id: ${{ github.event.workflow_run.id }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
        continue-on-error: true

      - name: Download frontend complexity
        uses: actions/download-artifact@v4
        with:
          name: frontend-complexity
          path: complexity/frontend
          run-id: ${{ github.event.workflow_run.id }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
        continue-on-error: true

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Generate coverage and metrics dashboard
        run: |
          mkdir -p coverage-report/frontend
          mkdir -p coverage-report/backend
          mkdir -p coverage-report/complexity
          mkdir -p coverage-report/badges
          mkdir -p coverage-report/api

          # Copy coverage reports if they exist
          if [ -d "coverage/frontend" ]; then
            cp -r coverage/frontend/* coverage-report/frontend/ 2>/dev/null || true
          fi
          if [ -d "coverage/backend/htmlcov" ]; then
            cp -r coverage/backend/htmlcov coverage-report/backend/ 2>/dev/null || true
          fi

          # Copy complexity reports
          if [ -d "complexity/backend" ]; then
            cp -r complexity/backend/* coverage-report/complexity/ 2>/dev/null || true
          fi
          if [ -d "complexity/frontend" ]; then
            cp -r complexity/frontend/* coverage-report/complexity/ 2>/dev/null || true
          fi

          # Generate all metrics and badges
          python3 << 'EOF'
          import urllib.request
          import json
          import os
          from datetime import datetime

          def get_color(pct, invert=False):
              try:
                  pct = float(pct)
              except:
                  return 'lightgrey'
              if invert:  # For complexity (lower is better)
                  if pct <= 5: return 'brightgreen'
                  elif pct <= 10: return 'green'
                  elif pct <= 20: return 'yellow'
                  else: return 'red'
              else:  # For coverage (higher is better)
                  if pct >= 80: return 'brightgreen'
                  elif pct >= 60: return 'yellow'
                  elif pct >= 40: return 'orange'
                  else: return 'red'

          def get_rating_color(rating):
              return {'A': 'brightgreen', 'B': 'green', 'C': 'yellow', 'D': 'red'}.get(rating, 'lightgrey')

          def download_badge(name, value, color, label=None):
              label = label or name
              url = f'https://img.shields.io/badge/{label}-{value}-{color}'
              try:
                  urllib.request.urlretrieve(url, f'coverage-report/badges/{name}.svg')
                  print(f"Generated {name} badge: {value}")
              except Exception as e:
                  print(f"Failed to generate {name} badge: {e}")

          # Extract coverage percentages
          frontend_cov = 0
          backend_cov = 0

          try:
              with open('coverage/frontend/coverage-summary.json') as f:
                  d = json.load(f)
                  frontend_cov = d['total']['lines']['pct']
          except: pass

          try:
              with open('coverage/backend/coverage.json') as f:
                  d = json.load(f)
                  backend_cov = round(d['totals']['percent_covered'], 1)
          except: pass

          # Extract complexity metrics
          backend_cc = 0
          backend_mi = 0
          backend_cc_rating = 'N/A'
          backend_mi_rating = 'N/A'
          frontend_complexity_warnings = 0
          frontend_complexity_rating = 'N/A'

          try:
              with open('complexity/backend/summary.json') as f:
                  d = json.load(f)
                  backend_cc = d.get('average_cyclomatic_complexity', 0)
                  backend_mi = d.get('average_maintainability_index', 0)
                  backend_cc_rating = d.get('cc_rating', 'N/A')
                  backend_mi_rating = d.get('mi_rating', 'N/A')
          except: pass

          try:
              with open('complexity/frontend/summary.json') as f:
                  d = json.load(f)
                  frontend_complexity_warnings = d.get('complexity_warnings', 0)
                  frontend_complexity_rating = d.get('rating', 'N/A')
          except: pass

          # Generate badges
          download_badge('frontend-coverage', f'{frontend_cov}%25', get_color(frontend_cov), 'coverage')
          download_badge('backend-coverage', f'{backend_cov}%25', get_color(backend_cov), 'coverage')
          download_badge('backend-complexity', f'{backend_cc_rating}', get_rating_color(backend_cc_rating), 'complexity')
          download_badge('backend-maintainability', f'{backend_mi_rating}', get_rating_color(backend_mi_rating), 'maintainability')
          download_badge('frontend-complexity', f'{frontend_complexity_rating}', get_rating_color(frontend_complexity_rating), 'complexity')

          # Create metrics.json API file for blog integration
          metrics = {
              'generated_at': datetime.utcnow().isoformat() + 'Z',
              'repo': 'mndeaves/cookie',
              'coverage': {
                  'frontend': {
                      'percentage': frontend_cov,
                      'badge_url': 'https://mndeaves.github.io/cookie/coverage/badges/frontend-coverage.svg'
                  },
                  'backend': {
                      'percentage': backend_cov,
                      'badge_url': 'https://mndeaves.github.io/cookie/coverage/badges/backend-coverage.svg'
                  }
              },
              'complexity': {
                  'backend': {
                      'cyclomatic_complexity': backend_cc,
                      'cyclomatic_rating': backend_cc_rating,
                      'maintainability_index': backend_mi,
                      'maintainability_rating': backend_mi_rating,
                      'badge_url': 'https://mndeaves.github.io/cookie/coverage/badges/backend-complexity.svg'
                  },
                  'frontend': {
                      'complexity_warnings': frontend_complexity_warnings,
                      'rating': frontend_complexity_rating,
                      'badge_url': 'https://mndeaves.github.io/cookie/coverage/badges/frontend-complexity.svg'
                  }
              },
              'links': {
                  'dashboard': 'https://mndeaves.github.io/cookie/coverage/',
                  'frontend_coverage': 'https://mndeaves.github.io/cookie/coverage/frontend/',
                  'backend_coverage': 'https://mndeaves.github.io/cookie/coverage/backend/htmlcov/',
                  'github': 'https://github.com/mndeaves/cookie'
              }
          }

          with open('coverage-report/api/metrics.json', 'w') as f:
              json.dump(metrics, f, indent=2)

          print(f"\nMetrics JSON generated at coverage-report/api/metrics.json")
          print(f"Frontend Coverage: {frontend_cov}%")
          print(f"Backend Coverage: {backend_cov}%")
          print(f"Backend Complexity: CC={backend_cc} ({backend_cc_rating}), MI={backend_mi} ({backend_mi_rating})")
          print(f"Frontend Complexity: {frontend_complexity_warnings} warnings ({frontend_complexity_rating})")
          EOF

          # Create index.html dashboard
          cat > coverage-report/index.html << 'HTMLEOF'
          <!DOCTYPE html>
          <html lang="en">
          <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Cookie - Code Quality Dashboard</title>
            <style>
              * { box-sizing: border-box; margin: 0; padding: 0; }
              body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                max-width: 1000px;
                margin: 0 auto;
                padding: 2rem;
                background: #f5f5f5;
                color: #333;
              }
              h1 { font-size: 2rem; margin-bottom: 0.5rem; color: #1a1a1a; }
              .subtitle { color: #666; margin-bottom: 2rem; }
              h2 { font-size: 1.5rem; margin: 2rem 0 1rem; color: #1a1a1a; border-bottom: 2px solid #e1e4e8; padding-bottom: 0.5rem; }
              .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; }
              .card {
                background: white;
                border-radius: 12px;
                padding: 1.5rem;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
              }
              .card h3 {
                font-size: 1.1rem;
                margin-bottom: 0.75rem;
                display: flex;
                align-items: center;
                gap: 0.75rem;
                flex-wrap: wrap;
              }
              .card p { color: #666; margin-bottom: 1rem; font-size: 0.9rem; }
              .card a {
                display: inline-block;
                padding: 0.5rem 1rem;
                background: #0066cc;
                color: white;
                text-decoration: none;
                border-radius: 6px;
                font-weight: 500;
                font-size: 0.9rem;
              }
              .card a:hover { background: #0052a3; }
              .badge { height: 20px; }
              .metric { font-size: 2rem; font-weight: 700; color: #1a1a1a; }
              .metric-label { font-size: 0.85rem; color: #666; }
              .metrics-row { display: flex; gap: 2rem; margin: 1rem 0; }
              .metric-item { text-align: center; }
              .api-note {
                background: #e8f4fd;
                border: 1px solid #b8daff;
                border-radius: 8px;
                padding: 1rem;
                margin-top: 2rem;
              }
              .api-note code {
                background: #fff;
                padding: 0.2rem 0.5rem;
                border-radius: 4px;
                font-size: 0.85rem;
              }
              .footer {
                margin-top: 2rem;
                text-align: center;
                color: #999;
                font-size: 0.875rem;
              }
              .footer a { color: #666; }
            </style>
          </head>
          <body>
            <h1>Cookie Code Quality Dashboard</h1>
            <p class="subtitle">Test coverage and code complexity metrics</p>

            <h2>Test Coverage</h2>
            <div class="cards">
              <div class="card">
                <h3>
                  Frontend (React/TypeScript)
                  <img src="badges/frontend-coverage.svg" alt="Frontend coverage" class="badge">
                </h3>
                <p>React components, API client, utilities, and hooks</p>
                <a href="frontend/index.html">View Detailed Report</a>
              </div>
              <div class="card">
                <h3>
                  Backend (Django/Python)
                  <img src="badges/backend-coverage.svg" alt="Backend coverage" class="badge">
                </h3>
                <p>Django apps, API endpoints, models, and services</p>
                <a href="backend/htmlcov/index.html">View Detailed Report</a>
              </div>
            </div>

            <h2>Code Complexity</h2>
            <div class="cards">
              <div class="card">
                <h3>
                  Backend Complexity
                  <img src="badges/backend-complexity.svg" alt="Backend complexity" class="badge">
                  <img src="badges/backend-maintainability.svg" alt="Backend maintainability" class="badge">
                </h3>
                <p>Cyclomatic complexity and maintainability index (radon)</p>
                <div class="metrics-row">
                  <div class="metric-item">
                    <div class="metric" id="backend-cc">-</div>
                    <div class="metric-label">Avg. Complexity</div>
                  </div>
                  <div class="metric-item">
                    <div class="metric" id="backend-mi">-</div>
                    <div class="metric-label">Maintainability</div>
                  </div>
                </div>
              </div>
              <div class="card">
                <h3>
                  Frontend Complexity
                  <img src="badges/frontend-complexity.svg" alt="Frontend complexity" class="badge">
                </h3>
                <p>ESLint complexity analysis (max cyclomatic: 10)</p>
                <div class="metrics-row">
                  <div class="metric-item">
                    <div class="metric" id="frontend-warnings">-</div>
                    <div class="metric-label">Warnings</div>
                  </div>
                </div>
              </div>
            </div>

            <div class="api-note">
              <strong>API Endpoint:</strong> Fetch metrics programmatically for your blog or dashboard:<br>
              <code>GET <a href="api/metrics.json">https://mndeaves.github.io/cookie/coverage/api/metrics.json</a></code>
            </div>

            <p class="footer">
              Last updated: <span id="date"></span><br>
              <a href="https://github.com/mndeaves/cookie">View on GitHub</a>
            </p>

            <script>
              document.getElementById('date').textContent = new Date().toLocaleString();

              // Load metrics from API
              fetch('api/metrics.json')
                .then(r => r.json())
                .then(data => {
                  document.getElementById('backend-cc').textContent = data.complexity.backend.cyclomatic_complexity || '-';
                  document.getElementById('backend-mi').textContent = data.complexity.backend.maintainability_index || '-';
                  document.getElementById('frontend-warnings').textContent = data.complexity.frontend.complexity_warnings || '0';
                })
                .catch(() => {});
            </script>
          </body>
          </html>
          HTMLEOF

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./coverage-report
          destination_dir: coverage
          keep_files: false
```

---

## Phase 10.4: Create Production Dockerfile (Multi-Architecture)

### File: `Dockerfile.prod`

```dockerfile
# ===========================================
# Stage 1: Build Frontend Assets
# ===========================================
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

# Copy package files first for better caching
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy frontend source
COPY frontend/ .

# Build production assets
RUN npm run build

# ===========================================
# Stage 2: Python Dependencies
# ===========================================
FROM python:3.12-slim AS python-deps

WORKDIR /app

# Install build dependencies for any native extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn whitenoise

# ===========================================
# Stage 3: Production Image
# ===========================================
FROM python:3.12-slim AS production

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libffi8 \
    && rm -rf /var/lib/apt/lists/*

# Security: Create non-root user
RUN useradd --create-home --shell /bin/bash app

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=python-deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=python-deps /usr/local/bin/gunicorn /usr/local/bin/gunicorn

# Copy Django application
COPY --chown=app:app apps/ apps/
COPY --chown=app:app cookie/ cookie/
COPY --chown=app:app tests/ tests/
COPY --chown=app:app manage.py .
COPY --chown=app:app pytest.ini .
COPY --chown=app:app conftest.py .

# Copy built frontend assets from frontend-builder
COPY --from=frontend-builder --chown=app:app /frontend/dist /app/frontend/dist

# Create necessary directories
RUN mkdir -p /app/staticfiles /app/data/media && \
    chown -R app:app /app/staticfiles /app/data

# Copy and setup entrypoint
COPY --chown=app:app entrypoint.prod.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Switch to non-root user
USER app

# Environment defaults for out-of-the-box deployment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBUG=false \
    ALLOWED_HOSTS=* \
    GUNICORN_WORKERS=2 \
    GUNICORN_THREADS=4

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/system/health/')" || exit 1

# Run entrypoint
ENTRYPOINT ["/entrypoint.sh"]
```

### File: `entrypoint.prod.sh`

```bash
#!/bin/bash
set -e

# Data directory for persistent storage
DATA_DIR="/app/data"
mkdir -p "$DATA_DIR/media"

# Link database to data directory if not already there
if [ ! -f "$DATA_DIR/db.sqlite3" ]; then
    echo "Initializing database..."
fi

# Use data directory for database
export DATABASE_PATH="$DATA_DIR/db.sqlite3"

# Generate secret key if not provided
if [ -z "$SECRET_KEY" ]; then
    SECRET_KEY_FILE="$DATA_DIR/.secret_key"
    if [ ! -f "$SECRET_KEY_FILE" ]; then
        echo "Generating new secret key..."
        python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" > "$SECRET_KEY_FILE"
    fi
    export SECRET_KEY=$(cat "$SECRET_KEY_FILE")
fi

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn on 0.0.0.0:8000..."
exec gunicorn \
    --bind 0.0.0.0:8000 \
    --workers ${GUNICORN_WORKERS:-2} \
    --threads ${GUNICORN_THREADS:-4} \
    --worker-class gthread \
    --worker-tmp-dir /dev/shm \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    --enable-stdio-inheritance \
    cookie.wsgi:application
```

---

## Phase 10.5: Update Django Settings for Production

### Before Modifying settings.py

First, read the existing `cookie/settings.py` to understand its current structure:

```bash
# View existing settings
cat cookie/settings.py
```

The existing file has:
- MIDDLEWARE with `apps.core.middleware.DeviceDetectionMiddleware`
- Database OPTIONS with WAL mode and timeout settings
- LOGGING configuration
- Session settings

**IMPORTANT:** Make surgical edits to preserve existing functionality. Do NOT replace the entire file.

### Surgical Changes to: `cookie/settings.py`

#### Change 1: Add `import os` at the top

```python
# Add after existing imports
import os
```

#### Change 2: Replace hardcoded SECRET_KEY, DEBUG, ALLOWED_HOSTS

Replace:
```python
SECRET_KEY = 'django-insecure-dev-key-change-in-production'

DEBUG = True

ALLOWED_HOSTS = ['*']
```

With:
```python
# ===========================================
# Environment-based Configuration
# ===========================================

DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

def get_secret_key():
    """Get secret key from environment or generate one."""
    env_key = os.environ.get('SECRET_KEY')
    if env_key:
        return env_key
    if DEBUG:
        return 'django-insecure-dev-key-change-in-production'
    from django.core.management.utils import get_random_secret_key
    return get_random_secret_key()

SECRET_KEY = get_secret_key()

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

# CSRF trusted origins (for reverse proxies)
csrf_origins = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
CSRF_TRUSTED_ORIGINS = [o.strip() for o in csrf_origins.split(',') if o.strip()]
```

#### Change 3: Add WhiteNoise to MIDDLEWARE

Insert `'whitenoise.middleware.WhiteNoiseMiddleware',` immediately after `'django.middleware.security.SecurityMiddleware',`:

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ADD THIS LINE
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'apps.core.middleware.DeviceDetectionMiddleware',
]
```

#### Change 4: Add STATICFILES_DIRS and WhiteNoise storage

After the existing `STATIC_ROOT = BASE_DIR / 'staticfiles'` line, add:

```python
# Include built frontend assets in static files
STATICFILES_DIRS = [
    BASE_DIR / 'frontend' / 'dist',
]

# WhiteNoise configuration for efficient static file serving
# Note: For Django 4.2+, use STORAGES dict instead:
# STORAGES = {
#     "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
#     "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
# }
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

#### Change 5: Update MEDIA_ROOT for production data directory

Replace:
```python
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

With:
```python
MEDIA_URL = '/media/'
data_dir = os.environ.get('DATA_DIR', str(BASE_DIR))
MEDIA_ROOT = Path(data_dir) / 'data' / 'media' if not DEBUG else BASE_DIR / 'media'
```

#### Change 6: Add DATABASE_PATH environment variable support

Replace the DATABASES `'NAME'` value:

```python
# Support custom database path for Docker volumes
DATABASE_PATH = os.environ.get('DATABASE_PATH', str(BASE_DIR / 'db.sqlite3'))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': DATABASE_PATH,  # Changed from: BASE_DIR / 'db.sqlite3'
        # ... keep existing OPTIONS unchanged ...
    }
}
```

### What to PRESERVE (do not modify)

- All existing LOGGING configuration
- All existing SESSION_* settings
- Existing TEMPLATES configuration
- Existing INSTALLED_APPS
- Existing database OPTIONS (timeout, transaction_mode, init_command)

---

## Phase 10.6: Create CD Workflow (Multi-Architecture)

### File: `.github/workflows/cd.yml`

```yaml
name: CD

on:
  # Trigger after CI workflow completes successfully
  workflow_run:
    workflows: ["CI"]
    types: [completed]
    branches: [main, master]
  # Allow manual trigger with custom tag
  workflow_dispatch:
    inputs:
      tag:
        description: 'Custom tag for Docker image (optional)'
        required: false
        type: string

env:
  REGISTRY: docker.io
  IMAGE_NAME: mndeaves/cookie

jobs:
  build-and-push:
    name: Build and Push Docker Image
    runs-on: ubuntu-latest
    # Only run if CI succeeded (for workflow_run trigger) or manual trigger
    if: github.event_name == 'workflow_dispatch' || github.event.workflow_run.conclusion == 'success'
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.IMAGE_NAME }}
          tags: |
            type=sha,prefix=
            type=raw,value=latest,enable={{is_default_branch}}
            type=raw,value=${{ inputs.tag }},enable=${{ inputs.tag != '' }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          file: ./Dockerfile.prod
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          platforms: linux/amd64,linux/arm64
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Update Docker Hub description
        uses: peter-evans/dockerhub-description@v4
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
          repository: ${{ env.IMAGE_NAME }}
          short-description: "Cookie - Self-hosted recipe manager"
          readme-filepath: ./README.md
        continue-on-error: true
```

---

## Phase 10.7: Configure GitHub Repository

### Required Secrets

Add in GitHub repo > Settings > Secrets and variables > Actions:

| Secret | Value |
|--------|-------|
| `DOCKERHUB_USERNAME` | `mndeaves` |
| `DOCKERHUB_TOKEN` | Docker Hub access token (create at hub.docker.com > Account Settings > Security > Access Tokens) |

### Enable GitHub Pages

1. Go to Settings > Pages
2. Source: Deploy from a branch
3. Branch: `gh-pages` / `/ (root)`
4. Save

### Branch Protection (Recommended)

Configure for `main`/`master`:
- Require pull request before merging
- Require status checks to pass: `ci-success`
- Require branches to be up to date before merging

---

## Complete File Summary

### New Files to Create

| File | Description |
|------|-------------|
| `.github/workflows/ci.yml` | CI pipeline - lint, typecheck, tests |
| `.github/workflows/cd.yml` | CD pipeline - Docker build and push |
| `.github/workflows/coverage.yml` | Coverage reports to GitHub Pages |
| `Dockerfile.prod` | Multi-stage production Dockerfile |
| `entrypoint.prod.sh` | Production entrypoint script |

### Files to Modify

| File | Changes |
|------|---------|
| `frontend/package.json` | Add `@vitest/coverage-v8` dependency and `test:coverage` script |
| `frontend/vitest.config.ts` | Add coverage configuration |
| `requirements.txt` | Add `pytest-cov>=4.0`, `radon>=6.0`, and `whitenoise>=6.0` |
| `cookie/settings.py` | Surgical edits: add WhiteNoise middleware, env vars, STATICFILES_DIRS (preserve existing LOGGING, SESSION, OPTIONS) |

---

## CI/CD Pipeline Flow Diagram

```
                        PR/Push to main
                              |
                              v
        +--------------------------------------------------+
        |                  CI WORKFLOW                      |
        |                                                   |
        |  +-----------+  +------------+  +-------------+  |
        |  | lint      |  | typecheck  |  | backend     |  |
        |  | (ESLint)  |  | (tsc)      |  | (pytest)    |  |
        |  +-----+-----+  +-----+------+  +------+------+  |
        |        |              |                |         |
        |        |    +---------+                |         |
        |        |    |                          |         |
        |        v    v                          |         |
        |  +-----------+                         |         |
        |  | frontend  |                         |         |
        |  | (vitest)  |                         |         |
        |  +-----+-----+                         |         |
        |        |                               |         |
        |        +---------------+---------------+         |
        |                        |                         |
        |                        v                         |
        |                 +-----------+                    |
        |                 | ci-success|                    |
        |                 +-----+-----+                    |
        +------------------------|--------------------------+
                                 |
                     (CI completes on main)
                                 |
                                 v
                    [workflow_run trigger]
                                 |
                +----------------+----------------+
                |                                 |
                v                                 v
   +------------------------+      +------------------------+
   |     CD WORKFLOW        |      |   COVERAGE WORKFLOW    |
   |  (only if CI passed)   |      |   (only if CI passed)  |
   |                        |      |                        |
   | +------------------+   |      | +------------------+   |
   | | build-and-push   |   |      | | publish-coverage |   |
   | | (Multi-Arch)     |   |      | | (GitHub Pages)   |   |
   | +--------+---------+   |      | +--------+---------+   |
   |          |             |      |          |             |
   |          v             |      |          v             |
   | mndeaves/cookie:latest |      | mndeaves.github.io/    |
   | mndeaves/cookie:<sha>  |      | cookie/coverage/       |
   | (amd64 + arm64)        |      |                        |
   +------------------------+      +------------------------+
```

---

## Out-of-the-Box Deployment

### Quick Start (Any Platform)

```bash
docker run -d -p 8000:8000 -v cookie-data:/app/data mndeaves/cookie:latest
```

Access from any browser on the same network:
- **Local:** `http://localhost:8000`
- **Network:** `http://<host-ip>:8000`

### Platform-Specific Commands

**Ubuntu/Debian:**
```bash
curl -fsSL https://get.docker.com | sh
docker run -d --name cookie --restart unless-stopped -p 8000:8000 -v cookie-data:/app/data mndeaves/cookie:latest
```

**macOS (Apple Silicon/Intel):**
```bash
docker run -d --name cookie -p 8000:8000 -v cookie-data:/app/data mndeaves/cookie:latest
```

**Windows (PowerShell):**
```powershell
docker run -d --name cookie -p 8000:8000 -v cookie-data:/app/data mndeaves/cookie:latest
```

### What Works Automatically

| Feature | Status |
|---------|--------|
| Database initialization | Auto-created on first run |
| Secret key | Auto-generated, persisted in volume |
| Static files | Served via WhiteNoise |
| Network binding | Bound to 0.0.0.0 |
| Host validation | Accepts all hosts by default |
| Multi-architecture | amd64 + arm64 images |

---

## Verification Checklist

### CI (Phase 10.1-10.2)
- [ ] Create PR with small change
- [ ] All 4 jobs run in parallel
- [ ] ci-success blocks merge if any job fails
- [ ] Coverage artifacts uploaded

### Coverage (Phase 10.3)
- [ ] GitHub Pages enabled
- [ ] Coverage dashboard accessible at `/coverage/`
- [ ] Frontend and backend reports linked
- [ ] Badges rendered correctly

### CD (Phase 10.4-10.6)
- [ ] Docker Hub secrets configured
- [ ] Multi-arch image built on merge
- [ ] Image tagged with SHA and latest
- [ ] Works on amd64 and arm64

### Full Integration
- [ ] PR -> CI passes -> Merge
- [ ] CD builds and pushes image
- [ ] Coverage publishes to Pages
- [ ] Pull image on different platforms
- [ ] Access from mobile on same network

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | Auto-generated | Django secret key |
| `DEBUG` | `false` | Debug mode |
| `ALLOWED_HOSTS` | `*` | Allowed hostnames |
| `CSRF_TRUSTED_ORIGINS` | (empty) | For HTTPS reverse proxies |
| `DATABASE_PATH` | `/app/data/db.sqlite3` | Database location |
| `GUNICORN_WORKERS` | `2` | Worker processes |
| `GUNICORN_THREADS` | `4` | Threads per worker |

---

## API Endpoints for Blog Integration

All metrics are published to GitHub Pages and can be fetched programmatically.

### Metrics JSON API

**URL:** `https://mndeaves.github.io/cookie/coverage/api/metrics.json`

**Response:**
```json
{
  "generated_at": "2024-01-15T10:30:00Z",
  "repo": "mndeaves/cookie",
  "coverage": {
    "frontend": {
      "percentage": 85.5,
      "badge_url": "https://mndeaves.github.io/cookie/coverage/badges/frontend-coverage.svg"
    },
    "backend": {
      "percentage": 78.2,
      "badge_url": "https://mndeaves.github.io/cookie/coverage/badges/backend-coverage.svg"
    }
  },
  "complexity": {
    "backend": {
      "cyclomatic_complexity": 4.2,
      "cyclomatic_rating": "A",
      "maintainability_index": 72.5,
      "maintainability_rating": "B",
      "badge_url": "https://mndeaves.github.io/cookie/coverage/badges/backend-complexity.svg"
    },
    "frontend": {
      "complexity_warnings": 0,
      "rating": "A",
      "badge_url": "https://mndeaves.github.io/cookie/coverage/badges/frontend-complexity.svg"
    }
  },
  "links": {
    "dashboard": "https://mndeaves.github.io/cookie/coverage/",
    "frontend_coverage": "https://mndeaves.github.io/cookie/coverage/frontend/",
    "backend_coverage": "https://mndeaves.github.io/cookie/coverage/backend/htmlcov/",
    "github": "https://github.com/mndeaves/cookie"
  }
}
```

### Badge URLs (for README or blog)

| Badge | URL |
|-------|-----|
| Frontend Coverage | `https://mndeaves.github.io/cookie/coverage/badges/frontend-coverage.svg` |
| Backend Coverage | `https://mndeaves.github.io/cookie/coverage/badges/backend-coverage.svg` |
| Backend Complexity | `https://mndeaves.github.io/cookie/coverage/badges/backend-complexity.svg` |
| Backend Maintainability | `https://mndeaves.github.io/cookie/coverage/badges/backend-maintainability.svg` |
| Frontend Complexity | `https://mndeaves.github.io/cookie/coverage/badges/frontend-complexity.svg` |

### Detailed Reports

| Report | URL |
|--------|-----|
| Dashboard | `https://mndeaves.github.io/cookie/coverage/` |
| Frontend Coverage (HTML) | `https://mndeaves.github.io/cookie/coverage/frontend/` |
| Backend Coverage (HTML) | `https://mndeaves.github.io/cookie/coverage/backend/htmlcov/` |

### Example: Fetching Metrics for Blog

**JavaScript:**
```javascript
fetch('https://mndeaves.github.io/cookie/coverage/api/metrics.json')
  .then(r => r.json())
  .then(data => {
    console.log(`Frontend Coverage: ${data.coverage.frontend.percentage}%`);
    console.log(`Backend Coverage: ${data.coverage.backend.percentage}%`);
    console.log(`Backend Complexity: ${data.complexity.backend.cyclomatic_rating}`);
  });
```

**cURL:**
```bash
curl -s https://mndeaves.github.io/cookie/coverage/api/metrics.json | jq '.coverage'
```

### Embedding Badges in Markdown

```markdown
![Frontend Coverage](https://mndeaves.github.io/cookie/coverage/badges/frontend-coverage.svg)
![Backend Coverage](https://mndeaves.github.io/cookie/coverage/badges/backend-coverage.svg)
![Backend Complexity](https://mndeaves.github.io/cookie/coverage/badges/backend-complexity.svg)
```

### Complexity Ratings Explained

**Cyclomatic Complexity (CC):**
- **A** (1-5): Simple, low risk
- **B** (6-10): Moderate complexity
- **C** (11-20): Complex, higher risk
- **D** (21+): Very complex, refactor recommended

**Maintainability Index (MI):**
- **A** (80-100): Highly maintainable
- **B** (60-79): Moderately maintainable
- **C** (40-59): Difficult to maintain
- **D** (0-39): Very difficult to maintain

---

## Phase 10.8: Production Container Hardening

Harden the production Docker image for security while keeping the dev environment flexible with full tooling for debugging.

### Design Philosophy

| Environment | Purpose | Characteristics |
|-------------|---------|-----------------|
| **Production** | Minimal attack surface | Non-root user, no dev tools, no test files, read-only where possible |
| **Development** | Full debugging capability | Root access, hot reload, test frameworks, source maps |

### Tasks

#### 10.8.1 Remove Unnecessary Files from Production Image

**Current issue:** Test files are copied into production image unnecessarily.

```dockerfile
# REMOVE these lines from Dockerfile.prod:
COPY --chown=app:app tests/ tests/
COPY --chown=app:app pytest.ini .
COPY --chown=app:app conftest.py .
```

**Impact:** ~50KB reduction, removes test infrastructure from production.

#### 10.8.2 Add .dockerignore for Build Context

Create `.dockerignore` to exclude unnecessary files from build context:

```
# .dockerignore
__pycache__/
*.pyc
*.pyo
.git/
.gitignore
.env
*.md
!README.md
tests/
pytest.ini
conftest.py
.coverage
htmlcov/
.pytest_cache/
node_modules/
frontend/node_modules/
frontend/coverage/
*.log
.DS_Store
plans/
qa/
```

**Impact:** Faster builds, smaller build context sent to Docker daemon.

#### 10.8.3 Fix Volume Mount Permissions

**Current issue:** `mkdir` fails if volume is owned by different UID.

**Option A - Graceful degradation:**
```bash
# entrypoint.prod.sh
mkdir -p "$DATA_DIR/media" 2>/dev/null || {
    echo "Warning: Could not create media directory. Ensure volume has correct permissions."
    echo "Run: sudo chown -R 1000:1000 /path/to/data"
}
```

**Option B - Document in README:**
```markdown
## First-time Setup

Before running the container, create the data directory with correct permissions:

```bash
mkdir -p ./data
# Option 1: Match container user (UID 1000)
sudo chown -R 1000:1000 ./data

# Option 2: World-writable (less secure, easier)
chmod 777 ./data
```
```

#### 10.8.4 Fix STATICFILES_DIRS for Dev Compatibility

**Current issue:** `collectstatic` fails in dev if `frontend/dist` doesn't exist.

```python
# cookie/settings.py
_frontend_dist = BASE_DIR / 'frontend' / 'dist'
STATICFILES_DIRS = [_frontend_dist] if _frontend_dist.exists() else []
```

#### 10.8.5 Migrate to STORAGES Setting (Django 5.1+ Compatibility)

**Current issue:** `STATICFILES_STORAGE` deprecated in Django 4.2, removed in Django 5.1.

```python
# cookie/settings.py - Replace STATICFILES_STORAGE with:
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
```

#### 10.8.6 Security Headers (Future Enhancement)

Consider adding security headers via WhiteNoise or Django middleware:

```python
# cookie/settings.py (production only)
if not DEBUG:
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
    # If behind HTTPS proxy:
    # SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

#### 10.8.7 Read-Only Filesystem (Future Enhancement)

For maximum security, consider making the container filesystem read-only:

```yaml
# docker-compose.prod.yml
services:
  web:
    read_only: true
    tmpfs:
      - /tmp
      - /app/staticfiles
    volumes:
      - ./data:/app/data  # Only writable mount
```

### Verification Checklist

- [ ] Production image doesn't contain `tests/`, `pytest.ini`, `conftest.py`
- [ ] `.dockerignore` excludes dev files from build context
- [ ] Container starts with volume mount (correct permissions)
- [ ] `collectstatic` works in both dev and production
- [ ] No Django deprecation warnings for `STATICFILES_STORAGE`
- [ ] Container runs as non-root user (`app`)
- [ ] Health check passes

### Dev Environment Remains Unchanged

The development `docker-compose.yml` and `Dockerfile` (if separate) should retain:
- Volume mounts for hot reload
- Test frameworks and tools
- Debug mode enabled
- Source maps for frontend
- Full logging verbosity

This separation ensures developers have full debugging capability while production remains locked down.

---

## Phase 10.9: Dev/Prod Coexistence + Tooling Review

Enable running development and production containers simultaneously on the same machine. Review existing tooling in `/bin` and extend for production workflows.

### Port Strategy

| Environment | Port | URL | Purpose |
|-------------|------|-----|---------|
| **Development** | 9876 | `http://localhost:9876` | Active development, hot reload |
| **Production** | 80 | `http://localhost` | Pre-deployment testing, mirrors real deployment |

**Rationale:**
- Dev on high port avoids conflicts with system services
- Prod on port 80 tests real-world access patterns
- Both can run simultaneously for comparison testing
- Prepares for future pentest/security review before actual deployment

### Tasks

#### 10.9.1 Review Existing `/bin` Scripts

**Current scripts:**

| Script | Purpose | Status |
|--------|---------|--------|
| `bin/dev` | Docker compose wrapper for dev stack | Review & extend |
| `bin/figma-sync-theme` | Sync Figma CSS variables to frontends | Keep as-is |

**`bin/dev` commands:**
- `up/start` - Start dev stack
- `down/stop` - Stop dev stack
- `restart` - Restart dev stack
- `build` - Rebuild images
- `logs` - View logs
- `test` - Run pytest
- `shell` - Django shell
- `manage <cmd>` - Django management commands
- `migrate` - Run migrations
- `npm <cmd>` - Frontend npm commands
- `status` - Container status

#### 10.9.2 Create `bin/prod` Script

Mirror `bin/dev` functionality for production container:

```bash
#!/bin/bash
set -e

# Cookie production helper script
# Usage: bin/prod <command> [args]

cd "$(dirname "$0")/.."

COMPOSE_FILE="docker-compose.prod.yml"
CONTAINER_NAME="cookie-prod"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

usage() {
    echo "Usage: bin/prod <command> [args]"
    echo ""
    echo "Commands:"
    echo "  up, start      Start production container"
    echo "  down, stop     Stop production container"
    echo "  restart        Restart production container"
    echo "  build          Build production image from Dockerfile.prod"
    echo "  pull           Pull latest image from Docker Hub"
    echo "  logs           View logs (use -f to follow)"
    echo "  shell          Open shell in container"
    echo "  status         Show container status"
    echo "  health         Check health endpoint"
    echo ""
    echo "Production runs on port 80 (http://localhost)"
    echo "Development runs on port 9876 (http://localhost:9876)"
}

case "${1:-}" in
    up|start)
        echo -e "${GREEN}Starting production container...${NC}"
        docker compose -f "$COMPOSE_FILE" up -d
        echo -e "${GREEN}Production started at http://localhost${NC}"
        ;;
    down|stop)
        echo -e "${YELLOW}Stopping production container...${NC}"
        docker compose -f "$COMPOSE_FILE" down
        ;;
    restart)
        docker compose -f "$COMPOSE_FILE" restart
        ;;
    build)
        echo -e "${GREEN}Building production image...${NC}"
        docker build -f Dockerfile.prod -t cookie:prod .
        ;;
    pull)
        echo -e "${GREEN}Pulling latest image from Docker Hub...${NC}"
        docker pull mndeaves/cookie:latest
        ;;
    logs)
        shift
        docker compose -f "$COMPOSE_FILE" logs "$@"
        ;;
    shell)
        docker compose -f "$COMPOSE_FILE" exec web /bin/bash
        ;;
    status)
        docker compose -f "$COMPOSE_FILE" ps
        ;;
    health)
        curl -s http://localhost/api/system/health/ | python3 -m json.tool
        ;;
    help|-h|--help)
        usage
        ;;
    *)
        echo -e "${RED}Unknown command: ${1:-}${NC}"
        usage
        exit 1
        ;;
esac
```

#### 10.9.3 Create `docker-compose.prod.yml`

Production compose file using pre-built image:

```yaml
# docker-compose.prod.yml
# Production container for local testing before deployment

services:
  web:
    image: mndeaves/cookie:latest
    # Or build locally:
    # build:
    #   context: .
    #   dockerfile: Dockerfile.prod
    container_name: cookie-prod
    ports:
      - "80:8000"
    volumes:
      - ./data-prod:/app/data
    environment:
      - DEBUG=false
      - ALLOWED_HOSTS=localhost,127.0.0.1
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/system/health/')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

#### 10.9.4 Update `docker-compose.yml` for Dev Port

Change dev stack from port 80 to 9876:

```yaml
# docker-compose.yml (dev)
services:
  nginx:
    ports:
      - "9876:80"  # Changed from "80:80"
```

Update `bin/dev` to reflect new port:
```bash
echo -e "${GREEN}Stack started. Access at http://localhost:9876${NC}"
```

#### 10.9.5 Create `bin/both` Script (Optional)

Helper to manage both environments:

```bash
#!/bin/bash
# bin/both - Manage dev and prod together

case "${1:-}" in
    status)
        echo "=== Development (port 9876) ==="
        docker compose ps 2>/dev/null || echo "Not running"
        echo ""
        echo "=== Production (port 80) ==="
        docker compose -f docker-compose.prod.yml ps 2>/dev/null || echo "Not running"
        ;;
    up)
        bin/dev up
        bin/prod up
        ;;
    down)
        bin/dev down
        bin/prod down
        ;;
    *)
        echo "Usage: bin/both <status|up|down>"
        ;;
esac
```

### Design Decisions

| Question | Decision |
|----------|----------|
| **Shared database?** | No. Production container is completely self-contained with its own database in `data-prod/db.sqlite3` |
| **Shared media?** | No. Production has its own media directory in `data-prod/media/` |
| **Network isolation?** | Default Docker networks are separate, no action needed |
| **Resource limits?** | No. Not required for local pre-deployment testing |

**Key principle:** The production container is fully self-contained. Dev and prod environments are completely isolated from each other.

**Pre-pentest checklist:**
- [ ] Production container runs as non-root
- [ ] No dev tools in production image
- [ ] Environment variables for secrets (not hardcoded)
- [ ] Health check endpoint works
- [ ] Logs don't expose sensitive data
- [ ] CORS/CSRF configured correctly
- [ ] Static files served efficiently (WhiteNoise)

### Verification Checklist

- [ ] `bin/dev up` starts dev stack on port 9876
- [ ] `bin/prod up` starts prod container on port 80
- [ ] Both can run simultaneously without conflicts
- [ ] `bin/prod health` returns healthy status
- [ ] Separate data directories for dev and prod
- [ ] `bin/prod pull` fetches latest from Docker Hub

### File Changes Summary

| File | Action |
|------|--------|
| `bin/dev` | Update port message (9876) |
| `bin/prod` | Create new script |
| `bin/both` | Create new script (optional) |
| `docker-compose.yml` | Change nginx port to 9876 |
| `docker-compose.prod.yml` | Create new file |

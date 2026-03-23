# Cookie

[![CI](https://github.com/matthewdeaves/cookie/actions/workflows/ci.yml/badge.svg)](https://github.com/matthewdeaves/cookie/actions/workflows/ci.yml)
[![Frontend Coverage](https://matthewdeaves.github.io/cookie/coverage/badges/frontend-coverage.svg)](https://matthewdeaves.github.io/cookie/coverage/frontend/)
[![Backend Coverage](https://matthewdeaves.github.io/cookie/coverage/badges/backend-coverage.svg)](https://matthewdeaves.github.io/cookie/coverage/backend/htmlcov/)
[![Complexity](https://matthewdeaves.github.io/cookie/coverage/badges/backend-complexity.svg)](https://matthewdeaves.github.io/cookie/coverage/)
[![Security](https://matthewdeaves.github.io/cookie/coverage/badges/frontend-security.svg)](https://matthewdeaves.github.io/cookie/coverage/)
[![Bundle Size](https://matthewdeaves.github.io/cookie/coverage/badges/bundle-size.svg)](https://matthewdeaves.github.io/cookie/coverage/)

[**View Metrics Dashboard**](https://matthewdeaves.github.io/cookie/coverage/) - Test coverage, complexity analysis, security audits, and bundle size reports

A self-hosted recipe manager for searching, importing, organising, and cooking through recipes from popular cooking websites.

> **Note:** Cookie is a work in progress. I'm laying the foundations now and will be blogging about how I improve the code over time, using software metrics to guide development decisions. Read more: [Rapid Prototyping with Claude Code](https://matthewdeaves.com/blog/2026-01-11-rapid-prototyping-with-claude-code)

## Quick Start (Production)

Create a `.env` file with a Postgres password, then start:

```bash
echo "POSTGRES_PASSWORD=changeme" > .env
curl -O https://raw.githubusercontent.com/matthewdeaves/cookie/master/docker-compose.prod.yml
docker compose -f docker-compose.prod.yml --env-file .env up -d
```

Open http://localhost and start importing recipes.

**That's it.** Data persists in Docker volumes (`cookie-postgres-data`, `cookie-media`).

See [Deployment Guide](docs/DEPLOYMENT.md) for configuration options, updates, and network access.

## Quick Start (Development)

Clone and run the development stack:

```bash
git clone https://github.com/matthewdeaves/cookie.git
cd cookie
bin/dev up
```

Open http://localhost:3000 - hot reload enabled for both frontend and backend.

See [WORKFLOW.md](WORKFLOW.md) for development commands and testing with Claude Code.

## Screenshots

<table>
  <tr>
    <td align="center"><img src="docs/images/desktop/home-recently-viewed.webp" width="280" alt="Home recently viewed"><br><strong>Home</strong></td>
    <td align="center"><img src="docs/images/desktop/search-results-beef.webp" width="280" alt="Search recipes"><br><strong>Search</strong></td>
    <td align="center"><img src="docs/images/desktop/recipe-detail-ingredients-light-theme.webp" width="280" alt="Recipe light theme"><br><strong>Recipe</strong></td>
  </tr>
  <tr>
    <td align="center"><img src="docs/images/mobile/cooking-mode-timer-active.webp" width="280" alt="Mobile cook mode"><br><strong>Cook Mode</strong></td>
    <td align="center"><img src="docs/images/mobile/remix-tips-generated.webp" width="280" alt="AI generated tips"><br><strong>AI Tips</strong></td>
    <td align="center"><img src="docs/images/desktop/discover-personalized-recommendations.webp" width="280" alt="Personalized discover"><br><strong>Discover</strong></td>
  </tr>
  <tr>
    <td align="center"><img src="docs/images/ipad/ipad-recipe-biryani-ingredients.webp" width="280" alt="iPad recipe view"><br><strong>iPad</strong></td>
    <td align="center"><img src="docs/images/legacy-ipad/recipe-detail-tips.webp" width="280" alt="Legacy iPad"><br><strong>Legacy iPad</strong></td>
    <td align="center"><img src="docs/images/desktop/settings-recipe-sources.webp" width="280" alt="Settings"><br><strong>Settings</strong></td>
  </tr>
</table>

<p align="center">
  <a href="docs/SCREENSHOTS.md"><strong>View full screenshot gallery</strong></a> including all features and legacy iPad support
</p>

## Features

**Import**
- Search 15 popular recipe sites simultaneously (AllRecipes, BBC Good Food, Serious Eats, Simply Recipes, Epicurious, Bon Appetit, Tasty, The Kitchn, Budget Bytes, Delish, Skinnytaste, Southern Living, The Pioneer Woman, Taste of Home, BBC Food)
- Import any recipe by URL
- Automatic extraction of ingredients, steps, and timings

**Organise**
- Multi-profile system (family members, dietary preferences)
- Collections and favorites
- Recipe notes and modifications

**Cook**
- Step-by-step cooking mode
- Built-in timers with audio alerts
- Wake-lock to keep screen on

**AI-Powered (optional)**
- Recipe remix suggestions
- Serving size adjustments with recalculated ingredients
- Cooking tips and substitutions
- Personalized discovery suggestions
- All AI features hidden when no API key configured

## Architecture

```
                    ┌───────────────────────────────────────────────────┐
                    │           Production Container                    │
   Port 80          │                                                   │
  ─────────────────►│ nginx                                             │
                    │  ├─ /api/, /admin/, /legacy/ ► gunicorn ─► Django │
                    │  ├─ /static/ ──► /app/staticfiles/                │
                    │  ├─ /media/ ──► /app/data/media/                  │
                    │  └─ / ──► React SPA (/app/frontend/dist/)         │
                    │                                                   │
                    │  Browser Detection:                               │
                    │  └─ iOS <11, IE, Edge Legacy ──► /legacy/         │
                    └───────────────────────────────────────────────────┘
                                         │
                                         ▼
                              ┌──────────────────┐
                              │   PostgreSQL     │
                              └──────────────────┘
                                         │
                                         ▼ (optional)
                              ┌──────────────────┐
                              │   OpenRouter AI  │
                              └──────────────────┘
```

- Production: nginx + gunicorn (web container) + PostgreSQL (db container)
- Automatic legacy browser detection and redirect

## Tech Stack

| Layer | Technology |
|-------|------------|
| Web Server | nginx (routing, static files, browser detection) |
| Backend | Django 5, django-ninja, gunicorn |
| Frontend | React 19, TypeScript, Vite, Tailwind |
| Legacy | ES5 JavaScript (iOS 9 compatibility) |
| Database | PostgreSQL |
| AI | OpenRouter (Claude, GPT-4, Gemini) |
| Deployment | Docker Compose (amd64, arm64) |

## Compatibility

- Modern frontend: any modern browser
- Legacy frontend: tested on iPad 3 (iOS 9.3.6 Safari)
- Responsive design for mobile, tablet, and desktop

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `DEBUG` | No | Set to `false` in production (default) |
| `ALLOWED_HOSTS` | No | Comma-separated hostnames (default: `*`) |
| `CSRF_TRUSTED_ORIGINS` | No | Full URLs for CSRF protection |
| `SECRET_KEY` | No | Auto-generated if not set |

AI features are configured through the Settings UI, not environment variables.

### Data Persistence

Data is stored in two Docker volumes:
- `cookie-postgres-data` - PostgreSQL database
- `cookie-media` - Uploaded images

## Data Privacy

- Fully self-hosted - all data stays on your server (apart from when using OpenRouter)
- PostgreSQL database stored locally
- No telemetry or external tracking
- AI requests go to OpenRouter only if configured

## Basic Usage

1. **Import recipes**: Search across 15 sites or paste any recipe URL
2. **Organise**: Create profiles for family members, add recipes to collections
3. **Cook**: Open a recipe and enter cooking mode for step-by-step guidance
4. **AI features**: Add an OpenRouter API key in Settings to enable remix suggestions, cooking tips, and personalized discovery

## Development

### Prerequisites

- Docker and Docker Compose

### Getting Started

```bash
git clone https://github.com/matthewdeaves/cookie.git
cd cookie
bin/dev up        # Start development stack on port 3000
```

### Development Commands (`bin/dev`)

```bash
bin/dev up              # Start development stack (port 3000)
bin/dev down            # Stop development stack
bin/dev logs -f         # Follow logs
bin/dev test            # Run pytest
bin/dev shell           # Django shell
bin/dev migrate         # Run migrations
bin/dev npm test        # Run frontend tests
```

### Production Commands (`bin/prod`)

```bash
bin/prod up             # Start production container (port 80)
bin/prod down           # Stop production container
bin/prod pull           # Pull latest image from GHCR
bin/prod update         # Pull and restart
bin/prod logs -f        # Follow logs
bin/prod health         # Check container health
bin/prod build          # Build production image locally
```

### Port Configuration

| Environment | Port | URL |
|-------------|------|-----|
| Development | 3000 | http://localhost:3000 |
| Production  | 80   | http://localhost |

## Code Quality

22-job CI pipeline (path filters skip docs/markdown):

**Frontend (7 jobs):** lint (ESLint), typecheck (TypeScript), test (Vitest), complexity, duplication, security (npm audit), bundle analysis

**Backend (5 jobs):** lint (ruff), test (pytest), complexity (radon), duplication (jscpd), security (pip-audit + Bandit SAST)

**Legacy (2 jobs):** lint (ESLint ES5), duplication (jscpd)

**Security & Infrastructure (7 jobs):** secrets detection, Trivy container scan, Semgrep SAST, Hadolint Dockerfile lint, Gitleaks, Django deploy check, migration check

**Final (1 job):** ci-success aggregator

- [Quality Dashboard](https://matthewdeaves.github.io/cookie/coverage/) - comprehensive metrics with live data and detailed reports
- [Metrics JSON API](https://matthewdeaves.github.io/cookie/coverage/api/metrics.json) - programmatic access to all metrics
- Automated dependency updates via Dependabot (weekly for pip, npm, GitHub Actions)
- Auto-generated GitHub releases with categorized changelog on version tags

## Documentation

- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment, configuration, reverse proxy setup
- [Architecture](docs/ARCHITECTURE.md) - System design, data models, API structure
- [AI Features](docs/AI-FEATURES.md) - AI capabilities, configuration, customization
- [Screenshots](docs/SCREENSHOTS.md) - Full visual tour of modern and legacy frontends
- [WORKFLOW.md](WORKFLOW.md) - Development workflow and commands
- [plans/](plans/) - Implementation planning documents

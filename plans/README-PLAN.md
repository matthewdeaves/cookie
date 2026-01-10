# Plan: Create README and Documentation for Cookie

## Objective
Create a clear, practical README that helps users understand what the application does and how to use it.

## Key Principles
- **No waffle** - concise, factual, no marketing fluff
- **Let code speak** - metrics, architecture, real numbers
- **Genuinely useful** - not just marketing, actually helpful
- **Professional tone** - no excessive emojis, no superlatives
- **Getting started focus** - prioritise quick start with production and development containers

---

## Deliverables

### 1. `/home/matt/cookie/README.md` (Primary - ~180-220 lines)

**Structure:**

```
# Cookie

[![CI](https://github.com/matthewdeaves/cookie/actions/workflows/ci.yml/badge.svg)](https://github.com/matthewdeaves/cookie/actions/workflows/ci.yml)
[![Frontend Coverage](https://matthewdeaves.github.io/cookie/coverage/badges/frontend-coverage.svg)](https://matthewdeaves.github.io/cookie/coverage/frontend/)
[![Backend Coverage](https://matthewdeaves.github.io/cookie/coverage/badges/backend-coverage.svg)](https://matthewdeaves.github.io/cookie/coverage/backend/htmlcov/)
[![Complexity](https://matthewdeaves.github.io/cookie/coverage/badges/backend-complexity.svg)](https://matthewdeaves.github.io/cookie/coverage/)
[![Security](https://matthewdeaves.github.io/cookie/coverage/badges/frontend-security.svg)](https://matthewdeaves.github.io/cookie/coverage/)
[![Bundle Size](https://matthewdeaves.github.io/cookie/coverage/badges/bundle-size.svg)](https://matthewdeaves.github.io/cookie/coverage/)

A self-hosted recipe manager for searching, importing, organising, and cooking through recipes from popular cooking websites.

## Quick Start (Production)

Run the production container with a single command:

```bash
docker run -d -p 80:80 -v cookie-data:/app/data mndeaves/cookie:latest
```

Open http://localhost and start importing recipes.

**That's it.** Data persists in the `cookie-data` volume.

See [Deployment Guide](docs/DEPLOYMENT.md) for configuration options, updates, and network access.

## Quick Start (Development)

Clone and run the development stack:

```bash
git clone https://github.com/matthewdeaves/cookie.git
cd cookie
bin/dev up
```

Open http://localhost:3000 - hot reload enabled for both frontend and backend.

See [WORKFLOW.md](WORKFLOW.md) for development commands and testing.

## Screenshots
- Hero composite showing modern frontend (see Screenshot Requirements below)
- Collapsible section for legacy frontend screenshots

## Features (grouped into categories)

**Import**
- Search 15 popular recipe sites simultaneously (BBC Good Food, Serious Eats, etc.)
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
- All AI features hidden when no API key configured

## Architecture

```
                    ┌─────────────────────────────────────────────────┐
                    │            Production Container                  │
   Port 80          │                                                 │
  ─────────────────►│  nginx                                          │
                    │   ├─ /api/, /admin/, /legacy/ ──► gunicorn ───► Django
                    │   ├─ /static/ ──► /app/staticfiles/             │
                    │   ├─ /media/ ──► /app/data/media/               │
                    │   └─ / ──► React SPA (/app/frontend/dist/)      │
                    │                                                 │
                    │   Browser Detection:                            │
                    │   └─ iOS <11, IE, Edge Legacy ──► /legacy/      │
                    └─────────────────────────────────────────────────┘
                                         │
                                         ▼
                              ┌──────────────────┐
                              │  SQLite + WAL    │
                              │  /app/data/      │
                              └──────────────────┘
                                         │
                                         ▼ (optional)
                              ┌──────────────────┐
                              │   OpenRouter AI  │
                              └──────────────────┘
```

- Single container: nginx (port 80) + gunicorn (internal)
- Automatic legacy browser detection and redirect
- Dev/prod parity: both use nginx for routing

## Tech Stack

| Layer | Technology |
|-------|------------|
| Web Server | nginx (routing, static files, browser detection) |
| Backend | Django 5, django-ninja, gunicorn |
| Frontend | React 18, TypeScript, Vite 7, Tailwind 4 |
| Legacy | ES5 JavaScript (iOS 9 compatibility) |
| Database | SQLite + WAL mode |
| AI | OpenRouter (Claude, GPT-4, Gemini) |
| Deployment | Docker (amd64, arm64), single container |

## Compatibility
- Modern frontend: any modern browser
- Legacy frontend: tested on iPad 3 (iOS 9.3.6 Safari)
- Responsive design for mobile, tablet, and desktop

## Configuration

### Environment Variables
| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | No | Enable AI features (remix, tips, nutrition) |
| `DEBUG` | No | Set to `false` in production (default) |
| `ALLOWED_HOSTS` | No | Comma-separated hostnames (default: `*`) |
| `SECRET_KEY` | No | Auto-generated if not set |

### Data Persistence
```bash
# Docker volume (recommended)
docker run -v cookie-data:/app/data mndeaves/cookie:latest

# Or bind mount
docker run -v /path/to/data:/app/data mndeaves/cookie:latest
```

Data stored in `/app/data`:
- `db.sqlite3` - SQLite database
- `media/` - Uploaded images
- `.secret_key` - Auto-generated Django secret key

- AI features: optional, hidden when no API key configured

## Data Privacy
- Fully self-hosted - all data stays on your server
- SQLite database stored locally
- No telemetry or external tracking
- AI requests go to OpenRouter only if configured

## Basic Usage
- Brief walkthrough: search/import a recipe, organise into collections, use cooking mode
- How to set up profiles
- Where to configure AI/OpenRouter key

## Development

### Prerequisites
- Docker and Docker Compose

### Getting Started
```bash
git clone https://github.com/mndeaves/cookie.git
cd cookie
bin/dev up        # Start development stack on port 3000
```

### Development Commands (`bin/dev`)
```bash
bin/dev up        # Start development stack (port 3000)
bin/dev down      # Stop development stack
bin/dev logs -f   # Follow logs
bin/dev test      # Run pytest
bin/dev shell     # Django shell
bin/dev migrate   # Run migrations
bin/dev npm test  # Run frontend tests
```

### Production Commands (`bin/prod`)
```bash
bin/prod up       # Start production container (port 80)
bin/prod down     # Stop production container
bin/prod pull     # Pull latest image from Docker Hub
bin/prod update   # Pull and restart
bin/prod logs -f  # Follow logs
bin/prod health   # Check container health
bin/prod build    # Build production image locally
```

### Port Configuration
| Environment | Port | URL |
|-------------|------|-----|
| Development | 3000 | http://localhost:3000 |
| Production  | 80   | http://localhost |

- Link to WORKFLOW.md

## Code Quality
- 15-job CI pipeline (path filters skip docs/markdown):
  - Frontend: lint (ESLint), typecheck (TypeScript), test (Vitest), complexity, duplication, security (npm audit), bundle analysis
  - Backend: lint (ruff), test (pytest), complexity (radon), duplication (jscpd), security (pip-audit)
  - Legacy: lint (ESLint ES5), duplication (jscpd)
  - Final: ci-success aggregator
- [Quality Dashboard](https://matthewdeaves.github.io/cookie/coverage/) - comprehensive metrics with live data and detailed reports
- Metrics JSON API: https://matthewdeaves.github.io/cookie/coverage/api/metrics.json
- Automated dependency updates via Dependabot (weekly for pip, npm, GitHub Actions)
- Auto-generated GitHub releases with categorized changelog on version tags

## Project Structure

```
cookie/
├── apps/                    # Django applications
│   ├── ai/                  # AI/OpenRouter integration
│   ├── core/                # App settings, system endpoints
│   ├── legacy/              # ES5 frontend templates
│   ├── profiles/            # User profiles
│   └── recipes/             # Recipe models, search, scraping
├── frontend/                # React frontend (Vite + TypeScript)
├── nginx/                   # nginx configs (dev + prod)
├── bin/                     # Helper scripts
│   ├── dev                  # Development commands
│   └── prod                 # Production commands
├── docker-compose.yml       # Development stack (port 3000)
├── docker-compose.prod.yml  # Production container (port 80)
├── Dockerfile.prod          # Production image build
└── docs/                    # Documentation
```

- Links to phase documents

## Documentation
- Link to docs/DEPLOYMENT.md
- Link to WORKFLOW.md
- Link to plans/ directory

## License
```

### 2. `/home/matt/cookie/docs/ARCHITECTURE.md` (New - ~60-80 lines)

**Content:**
- Expanded architecture diagram
- Directory structure with purpose of each app
- Data flow explanation
- Database schema overview (models and relationships)
- API structure (endpoints grouped by app)

### 3. `/home/matt/cookie/docs/AI-FEATURES.md` (New - ~50-60 lines)

**Content:**
- Table of all 10 AI features:
  | Feature | Endpoint | Purpose | Fallback |
- OpenRouter configuration
- Prompt customization (Settings UI)
- How to add/modify AI features

---

## Screenshot Requirements

All screenshots should be placed in `/home/matt/cookie/docs/images/`

### Modern Frontend (React) - Required

| Filename | Description | What to Show |
|----------|-------------|--------------|
| `modern-recipe-list.png` | Recipe library view | List of saved recipes with thumbnails, showing search/filter options |
| `modern-recipe-detail.png` | Single recipe view | A recipe with ingredients, steps, and action buttons visible |
| `modern-cooking-mode.png` | Cooking mode active | Step-by-step view with current instruction highlighted, timer visible |
| `modern-search-results.png` | Multi-site search | Search results from multiple sources, showing site badges |
| `modern-collections.png` | Collections view | Recipe collections/folders with recipe counts |

### Legacy Frontend (ES5) - Required

| Filename | Description | What to Show |
|----------|-------------|--------------|
| `legacy-recipe-list.png` | Recipe library view | Same content as modern but showing the legacy UI style |
| `legacy-cooking-mode.png` | Cooking mode active | Step-by-step view in legacy interface |

### Hero Image - Required

| Filename | Description | What to Show |
|----------|-------------|--------------|
| `hero-composite.png` | Main README image | Side-by-side or grid composite of: recipe list, recipe detail, and cooking mode from modern frontend. Aim for ~1200px wide, optimised for web (<500KB) |

### Optional (nice to have)

| Filename | Description | What to Show |
|----------|-------------|--------------|
| `modern-import-url.png` | URL import dialog | The modal/form for importing a recipe by URL |
| `modern-ai-remix.png` | AI remix feature | AI suggestions for recipe variations |
| `modern-settings.png` | Settings page | Configuration options including AI key setup |
| `legacy-mobile.png` | Legacy on mobile | Legacy frontend on a smaller viewport |

### Screenshot Guidelines
- Use a clean browser window (no bookmarks bar, minimal chrome)
- Use realistic recipe data (not "Test Recipe 1")
- Light mode preferred for consistency
- Crop to content area (no browser address bar)
- PNG format, reasonable compression
- Modern screenshots: ~1000-1200px wide
- Legacy screenshots: can be narrower to show mobile-first design

---

## Implementation Steps

### Step 1: Create README.md

**1a. Launch verification agents (in parallel):**
- Agent 1: Find all environment variables in Django settings
- Agent 2: Find the 15 recipe search sources
- Agent 3: List all AI features and their endpoints
- Agent 4: Get Docker run command from DEPLOYMENT.md
- Agent 5: Get test commands from package.json and pyproject.toml
- Agent 6: List directory structure and Django apps
- Agent 7: Count and list CI jobs from ci.yml
- Agent 8: Fetch https://matthewdeaves.github.io/cookie/coverage/ to verify dashboard structure and available metrics

**1b. Wait for agents, then write README.md sections:**
1. Write header with badge row (6 badges: CI, Frontend/Backend Coverage, Complexity, Security, Bundle)
2. Write one-line description: "A self-hosted recipe manager for searching, importing, organising, and cooking through recipes from popular cooking websites."
3. Write Quick Start (Production) section - docker run command, single container
4. Write Quick Start (Development) section - git clone, bin/dev up, port 3000
5. Add Screenshots section with hero composite, collapsible legacy section
6. Write Features section (use verified search sources and AI features)
7. Write Architecture section (ASCII diagram from DEPLOYMENT.md style)
8. Write Tech Stack table
9. Write Compatibility section (browsers, devices)
10. Write Configuration section (use verified environment variables)
11. Write Data Privacy section
12. Write Basic Usage section (import recipe, collections, cooking mode)
13. Write Development section (detailed commands from bin/dev and bin/prod)
14. Write Code Quality section:
    - List 15 CI jobs grouped by area (Frontend, Backend, Legacy)
    - Link to Quality Dashboard: https://matthewdeaves.github.io/cookie/coverage/
    - Mention JSON API endpoint for programmatic access: /coverage/api/metrics.json
    - Note: Dashboard shows live metrics loaded from JSON API
15. Write Project Structure section (use verified directory structure)
16. Write Documentation links section
17. Add MIT License section

### Step 2: Create docs/ARCHITECTURE.md

**2a. Launch verification agents (in parallel):**
- Agent 1: List all Django apps with their models.py contents
- Agent 2: Find all API router/endpoint definitions
- Agent 3: List frontend/src directory structure

**2b. Wait for agents, then write ARCHITECTURE.md:**
1. Expanded architecture diagram
2. Directory structure explanation (use verified app list)
3. Data model overview (use verified models)
4. API endpoint structure (use verified endpoints)

### Step 3: Create docs/AI-FEATURES.md

**3a. Launch verification agents (in parallel):**
- Agent 1: Find all OpenRouter/AI API calls with their purposes
- Agent 2: Find prompt customization storage/settings
- Agent 3: Find API key check patterns and fallback behaviour

**3b. Wait for agents, then write AI-FEATURES.md:**
1. Feature reference table (use verified feature list)
2. Configuration guide
3. Customization notes (use verified prompt mechanism)

---

## Sub-Agent Verification Tasks

During implementation, launch sub-agents (using Task tool with `subagent_type=Explore`) to verify details from the codebase. Do not guess or assume - verify before writing.

### Before writing README.md, verify:

| What to Verify | How | Use in Section |
|----------------|-----|----------------|
| Exact environment variable names | Search for `os.environ` or `env` in settings files | Configuration |
| List of 15 recipe search sources | Find the search provider configs/constants | Features (Import) |
| All AI feature endpoints and names | Search for AI/OpenRouter API calls | Features (AI-Powered) |
| Docker run command syntax | Check docker-compose.yml and DEPLOYMENT.md | Quick Start |
| Test commands (pytest, vitest) | Check package.json scripts and pyproject.toml | Development |
| Directory structure and Django apps | List top-level dirs and backend apps | Project Structure |
| Actual CI job count and names | Read ci.yml workflow file | Code Quality |
| Quality dashboard structure | WebFetch https://matthewdeaves.github.io/cookie/coverage/ | Code Quality |

### Before writing ARCHITECTURE.md, verify:

| What to Verify | How | Use in Section |
|----------------|-----|----------------|
| All Django apps and their purpose | List backend/ subdirectories, read each app's models.py | Directory structure |
| Database models and relationships | Read all models.py files | Data model overview |
| API endpoint structure | Search for `@api` or router definitions | API structure |
| Frontend component structure | List frontend/src directories | Architecture diagram |

### Before writing AI-FEATURES.md, verify:

| What to Verify | How | Use in Section |
|----------------|-----|----------------|
| Complete list of AI features | Search for OpenRouter calls, AI endpoints | Feature table |
| Prompt customization mechanism | Find settings/prompts storage | Customization notes |
| Fallback behaviour when no API key | Search for API key checks | Feature table |
| Which models are supported | Find model selection code | Configuration |

### Sub-Agent Launch Pattern

For each verification task, launch an Explore agent with a specific question:

```
Task(
  subagent_type="Explore",
  prompt="Find all environment variables used in the Django settings.
         List each variable name and its purpose.
         Check backend/cookie/settings.py and any .env.example files.",
  description="Find env variables"
)
```

Launch multiple verification agents in parallel where tasks are independent.

---

## What NOT to Do
- No emojis in headers
- No superlatives ("amazing", "powerful", "revolutionary")
- No separate CONTRIBUTING.md (unclear contribution model)
- No API docs (django-ninja generates OpenAPI)

---

## Verification
1. Read through README for clarity and conciseness
2. Verify all links work (DEPLOYMENT.md, WORKFLOW.md, plans/)
3. Test the Quick Start docker command
4. Ensure architecture diagram is accurate
5. Cross-check metrics against actual CI output
6. Verify all screenshots display correctly and are reasonably sized
7. Check hero composite renders well on GitHub (dark and light mode)

---

## Files to Modify/Create
- **Create**: `/home/matt/cookie/README.md`
- **Create**: `/home/matt/cookie/docs/ARCHITECTURE.md`
- **Create**: `/home/matt/cookie/docs/AI-FEATURES.md`
- **Create**: `/home/matt/cookie/docs/images/` directory
- **Create**: Screenshots as listed in Screenshot Requirements section

## Files to Reference (read-only)
- `/home/matt/cookie/docs/DEPLOYMENT.md` - style reference
- `/home/matt/cookie/WORKFLOW.md` - link target
- `/home/matt/cookie/.github/workflows/ci.yml` - CI job details (15 jobs), path filters skip docs/markdown
- `/home/matt/cookie/.github/workflows/coverage.yml` - GitHub Pages dashboard generation
- `/home/matt/cookie/.github/workflows/cd.yml` - Docker builds on version tags (latest tag only)
- `/home/matt/cookie/.github/workflows/release.yml` - Auto-generated GitHub releases with changelog
- `/home/matt/cookie/.github/dependabot.yml` - Automated dependency updates (weekly)
- `/home/matt/cookie/pyproject.toml` - ruff configuration for Python linting
- `/home/matt/cookie/claude.md` - architecture decisions
- `/home/matt/cookie/plans/` - phase documents

## Docker/Deployment Files to Reference
- `/home/matt/cookie/Dockerfile.prod` - Production image (nginx + gunicorn)
- `/home/matt/cookie/docker-compose.yml` - Development stack (port 3000)
- `/home/matt/cookie/docker-compose.prod.yml` - Production container (port 80)
- `/home/matt/cookie/nginx/nginx.conf` - Development nginx config
- `/home/matt/cookie/nginx/nginx.prod.conf` - Production nginx config (browser detection, static serving)
- `/home/matt/cookie/entrypoint.prod.sh` - Production entrypoint (starts nginx + gunicorn)
- `/home/matt/cookie/bin/dev` - Development helper script
- `/home/matt/cookie/bin/prod` - Production helper script
- `/home/matt/cookie/apps/legacy/static/legacy/.eslintrc.json` - Legacy ES5 linting config

## GitHub Pages Dashboard Details

The CI pipeline publishes to `https://matthewdeaves.github.io/cookie/`:

**Site Structure:**
- `/` - Redirects to `/coverage/`
- `/coverage/` - Main quality dashboard with live metrics from JSON API
- `/coverage/api/metrics.json` - JSON API for programmatic access
- `/coverage/badges/` - SVG badges for README
- `/coverage/frontend/` - Frontend coverage report (Vitest)
- `/coverage/backend/htmlcov/` - Backend coverage report (pytest-cov)
- `/coverage/complexity/` - Backend complexity report (radon)
- `/coverage/duplication/frontend/` - Frontend duplication report (jscpd)
- `/coverage/duplication/backend/` - Backend duplication report (jscpd)
- `/coverage/legacy/` - Legacy lint report (ESLint ES5)
- `/coverage/legacy/duplication/` - Legacy duplication report (jscpd)

**Dashboard Sections:**
1. Test Coverage - Frontend (Vitest) and Backend (pytest-cov) with detailed reports
2. Code Complexity - Backend (radon CC/MI) and Frontend (ESLint) with metrics
3. Security - Frontend (npm audit) and Backend (pip-audit) vulnerability counts
4. Code Duplication - Frontend and Backend (jscpd) with clone counts and percentages
5. Bundle Size - Vite production build output in KB
6. Legacy Frontend - iOS 9 compatible ES5 code lint and duplication

**Available Badges (from `/coverage/badges/`):**
- `frontend-coverage.svg` - Frontend test coverage %
- `backend-coverage.svg` - Backend test coverage %
- `backend-complexity.svg` - Cyclomatic complexity rating (A-D)
- `backend-maintainability.svg` - Maintainability index rating
- `frontend-complexity.svg` - ESLint complexity rating
- `duplication.svg` - Frontend code duplication rating
- `backend-duplication.svg` - Backend code duplication rating
- `legacy-lint.svg` - Legacy ES5 lint rating
- `legacy-duplication.svg` - Legacy code duplication rating
- `frontend-security.svg` - npm audit rating
- `backend-security.svg` - pip-audit rating
- `bundle-size.svg` - Vite bundle size rating

**JSON API Structure (`/coverage/api/metrics.json`):**
```json
{
  "generated_at": "ISO timestamp",
  "coverage": { "frontend": {...}, "backend": {...} },
  "complexity": { "frontend": {...}, "backend": {...} },
  "duplication": { "frontend": {...}, "backend": {...} },
  "security": { "frontend": {...}, "backend": {...} },
  "bundle": { "size_kb": ..., "rating": ... },
  "legacy": { "lint": {...}, "duplication": {...} },
  "links": { "dashboard": ..., "github": ... }
}
```

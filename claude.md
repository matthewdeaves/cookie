# Claude Code Instructions for Cookie

**Recipe manager with dual frontends: Modern (React) + Legacy (iOS 9 iPad)**

## Critical Rules - Read These First

> **Complete rules in `.claude/rules/` directory** - This file is an overview. For detailed patterns, see individual rule files.

### 1. Docker is the ONLY Environment

⚠️ **The host has NO Python/Django installed!**

❌ Never run: `python`, `pytest`, `manage.py` on host
✅ Always use: `docker compose exec web python ...`

**See:** `.claude/rules/docker-environment.md` for complete command reference

---

### 2. Legacy Frontend = ES5 JavaScript ONLY

⚠️ **iOS 9 Safari compatibility required!**

❌ Forbidden: `const`, `let`, arrow functions, template literals, `async/await`
✅ Required: `var`, `function()`, string concatenation, callbacks

**See:** `.claude/rules/es5-compliance.md` for complete syntax rules

**After legacy changes:**
```bash
docker compose down && docker compose up -d  # Restart to run collectstatic
```

---

### 3. Code Quality Limits are IMMUTABLE

❌ **NEVER raise these limits in linter configs:**
- Max function length: 100 lines (prefer 50)
- Max complexity: 15
- Max file size: 500 lines

✅ **ALWAYS refactor** by extracting helper functions

**See:** `.claude/rules/code-quality.md` for refactoring examples

---

### 4. AI Features Must Hide When Unavailable

⚠️ **10 AI features total** - When API key missing or API fails:

❌ Don't: Show disabled buttons, display errors to users
✅ Do: Hide ALL AI features completely

**See:** `.claude/rules/ai-features.md` for complete list and fallback patterns

---

### 5. Security First

**Django:** SQL injection, XSS, CSRF protection
**React:** XSS prevention, URL validation, safe rendering

**See:**
- `.claude/rules/django-security.md`
- `.claude/rules/react-security.md`

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Django 5.x + Django Ninja (REST API) |
| **Database** | PostgreSQL |
| **Modern Frontend** | React 19 + TypeScript + Vite + Tailwind 4 |
| **Legacy Frontend** | ES5 JavaScript (iOS 9 Safari) |
| **Scraping** | recipe-scrapers + curl_cffi |
| **AI** | OpenRouter (10 features) |
| **Testing** | pytest (backend), Vitest (frontend) |

---

## Quick Reference

### Figma Design Interpretation

- **Settings AI Prompts page is LAYOUT ONLY** - Shows 4 example prompts, but project has 10 AI features
- **Scan screens for sparkles icons** - Indicate actual AI features
- **Nutrition is SCRAPED ONLY** - No AI for nutrition analysis

### 10 AI Features

1. `recipe_remix` - Create variations
2. `serving_adjustment` - Scale ingredients (AI-only, no frontend fallback)
3. `tips_generation` - Generate cooking tips
4. `discover_favorites` - Suggest based on favorites
5. `discover_seasonal` - Seasonal/holiday recipes
6. `discover_new` - Outside comfort zone
7. `search_ranking` - Rank search results
8. `timer_naming` - Descriptive timer labels
9. `remix_suggestions` - Contextual remix prompts
10. `selector_repair` - Auto-fix broken CSS selectors

### Architecture Decisions

| Question | Answer |
|----------|--------|
| Environments? | Single (dev=prod) |
| Search sources? | 15 curated (not all 563) |
| Remix source_url? | Nullable (user-generated) |
| Remix visibility? | Per-profile only |
| Serving adjustment? | AI-only, not persisted |
| AI unavailable? | Hide all AI features |
| Unit toggle? | Persisted profile setting |
| Play mode state? | Stateless (browser-only) |
| Legacy dark mode? | No (light only) |
| Timer audio? | Default browser notification |
| Re-scraping URL? | Creates new recipe (no dedup) |

---

## Testing & QA

### Manual QA (especially iPad testing)

```bash
/qa-session           # Full QA checklist
/qa-session legacy    # iOS 9 iPad testing
/qa-session ai        # AI features
```

### Running Tests

```bash
# Backend
docker compose exec web python -m pytest
docker compose exec web python -m pytest --cov

# Frontend
docker compose exec frontend npm test
docker compose exec frontend npm run test:watch
docker compose exec frontend npm run test:coverage
```

---

## File Locations

- **Figma export:** `/home/matt/cookie/Cookie Recipe App Design/`
- **recipe-scrapers:** `/home/matt/recipe-scrapers`
- **curl_cffi:** `/home/matt/curl_cffi`
- **Phase plans:** `/home/matt/cookie/plans/`
- **Workflow guide:** `/home/matt/cookie/WORKFLOW.md`

---

## .claude/ Directory Structure

Cookie uses Claude Code's extensibility features:

```
.claude/
├── rules/                    # Domain-specific knowledge
│   ├── es5-compliance.md    # iOS 9 Safari ES5 requirements
│   ├── docker-environment.md # Docker-only command patterns
│   ├── code-quality.md      # Immutable quality gates
│   ├── ai-features.md       # 10 AI features + fallback patterns
│   ├── django-security.md   # SQL injection, XSS, CSRF
│   └── react-security.md    # React XSS, safe rendering
├── hooks/                    # Pre-commit validation (auto-runs)
│   ├── es5-syntax-check.sh  # Blocks ES6+ in legacy/
│   ├── complexity-check.sh  # Blocks functions >100 lines
│   └── docker-command-check.sh # Warns about host commands
├── skills/                   # User-invocable workflows
│   └── qa-session/          # Manual testing checklist
└── settings.local.json       # Hooks config + permissions
```

**Hooks auto-run before Edit/Write/Bash operations** - No manual action needed!

---

## Data Model Key Points

- **Images stored locally** - Two-tier: search cache (30-day TTL) + recipe images (permanent)
- **Remixes persisted** - New Recipe records with `is_remix=True`, `host="user-generated"`
- **Remixes per-profile** - Not shared between profiles
- **Remix orphaning** - If original deleted, remixes become standalone
- **Serving adjustment** - NOT persisted, AI-computed on-the-fly
- **Full recipe-scrapers support** - DB schema supports ALL fields (ingredient_groups, equipment, etc.)

---

## Image Cache Monitoring

Check health:
```bash
curl http://localhost/api/recipes/cache/health/
```

View caching logs:
```bash
docker compose logs -f web | grep "Cached image from"
```

Cleanup old images (30+ days):
```bash
docker compose exec -T web python manage.py cleanup_search_images --days=30 --dry-run
docker compose exec -T web python manage.py cleanup_search_images --days=30  # actual delete
```

---

## Phase Files

| Phase | File | Focus |
|-------|------|-------|
| 1 | `PHASE-1-FOUNDATION.md` | Django + Docker + Profiles |
| 2 | `PHASE-2-RECIPE-CORE.md` | Scraping + Search |
| 3 | `PHASE-3-USER-FEATURES.md` | Favorites + Collections |
| 4 | `PHASE-4-REACT-FOUNDATION.md` | React: Profile, Home, Search |
| 5 | `PHASE-5-LEGACY-FOUNDATION.md` | Legacy: Profile, Home, Search |
| 6 | `PHASE-6-REACT-RECIPE-PLAYMODE.md` | React: Detail + Play Mode |
| 7 | `PHASE-7-LEGACY-RECIPE-PLAYMODE.md` | Legacy: Detail + Play Mode |
| 8A | `PHASE-8A-AI-INFRASTRUCTURE.md` | OpenRouter + Prompts |
| 8B | `PHASE-8B-AI-FEATURES.md` | All 10 AI Features |
| 9 | `PHASE-9-POLISH.md` | Settings + Testing |

---

## GitHub

- **Repository:** https://github.com/matthewdeaves/cookie.git
- **CI:** `.github/workflows/ci.yml`
- **Claude Code Review:** `.github/workflows/claude-code-review.yml`

---

## For Complete Rules

This file is a quick reference. For detailed patterns and examples:

1. **ES5 compliance:** `.claude/rules/es5-compliance.md`
2. **Docker commands:** `.claude/rules/docker-environment.md`
3. **Code quality:** `.claude/rules/code-quality.md`
4. **AI features:** `.claude/rules/ai-features.md`
5. **Django security:** `.claude/rules/django-security.md`
6. **React security:** `.claude/rules/react-security.md`

**Hooks auto-run - no need to remember!** 🎉

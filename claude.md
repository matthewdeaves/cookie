# Claude Code Instructions for Cookie 2

## Critical Rules

### Docker is the ONLY Environment

**⚠️ STOP - READ THIS FIRST ⚠️**

The host machine has NO Python/Django installed. ALL backend commands MUST run inside Docker:

```bash
# Tests
docker compose exec web python -m pytest

# Django shell
docker compose exec web python manage.py shell

# Any management command
docker compose exec web python manage.py <command>

# Frontend tests
docker compose exec frontend npm test
```

**If you see `ModuleNotFoundError: No module named 'django'`, you ran on the host instead of the container.**

---

### Figma Design Interpretation

1. **Settings AI Prompts page is FOR LAYOUT ONLY** - The 4 prompts shown (Recipe Remix, Serving Adjustment, Tips Generation, Nutrition Analysis) are just examples to show how the settings page should look. DO NOT use this to determine which AI features exist.

2. **Scan OTHER screens for AI features** - To find all AI integrations, look for:
   - Sparkles icons (indicate AI-powered features)
   - Buttons/toggles that trigger AI functionality
   - Features that require generated content

3. **Actual AI features (10 total):**
   - `recipe_remix` - Create recipe variations
   - `serving_adjustment` - Scale ingredients
   - `tips_generation` - Generate cooking tips
   - `discover_favorites` - Suggest based on user favorites
   - `discover_seasonal` - Suggest seasonal/holiday recipes
   - `discover_new` - Suggest outside comfort zone
   - `search_ranking` - Rank search results by relevance
   - `timer_naming` - Generate descriptive timer labels
   - `remix_suggestions` - Generate contextual remix prompts per recipe
   - `selector_repair` - Auto-fix broken CSS selectors for search sources

4. **Nutrition is SCRAPED ONLY** - No AI for nutrition analysis. Display whatever the recipe-scrapers library extracts from the source site.

### Architecture Decisions

5. **Single environment** - One Docker environment for dev that uses production-grade tools (nginx, Gunicorn). No separate dev/test/prod configurations.

6. **15 curated search sources** - Not the full 563 from recipe-scrapers. Only the most popular sites with implemented search.

7. **source_url nullable for remixes** - Remixed recipes don't have a source URL since they're AI-generated, not scraped.

8. **Discover view = mixed feed** - Combine results from all 3 AI search types (favorites-based, seasonal, try-new) into one unified feed. Include a mix of similar recipes, opposite/new cuisines, and date-relevant suggestions.

9. **AI fallback = HIDE features** - When OpenRouter API key is not set or API fails:
   - Hide ALL AI-dependent features from the user
   - Hide buttons, toggles, options that require AI
   - Return suitable error from backend API if called
   - Serving Adjustment is AI-ONLY (no frontend math fallback) - hide +/- buttons completely

10. **Collections terminology** - Use "Collections" in UI (not "Lists"). The internal code may use "lists" but user-facing text should say "Collections".

### Legacy Frontend

11. **Light theme only** - No dark mode for iOS 9 legacy interface
12. **Function over form** - Full user journey with simplified layout
13. **ES5 JavaScript only** - No const/let, arrow functions, template literals, async/await
14. **Timers are REQUIRED** - Play mode must have working timers on legacy

### Container Restart After Legacy Changes (IMPORTANT)

**After ANY change to legacy frontend files (JS, CSS), restart containers:**

```bash
docker compose down && docker compose up -d
```

The entrypoint script automatically runs `collectstatic` on every container start.

**Why restart is required:**
- Static files are served from `./staticfiles/` on the host (mounted into nginx)
- `collectstatic` copies from `apps/legacy/static/` to `./staticfiles/`
- The entrypoint runs this automatically, but only on container start

**Quick verification before QA:**
```bash
# Check static file has your changes
grep "unique string from your change" ./staticfiles/legacy/js/pages/detail.js

# Check container logs show collectstatic ran
docker compose logs web | grep "Collecting static"
```

**Template changes (.html)** - No restart needed, Django serves directly.

**Remind user to clear iPad Safari cache** after deploying changes:
Settings → Safari → Clear History and Website Data

### Data Model

15. **Full recipe-scrapers support** - Database schema supports ALL fields from the library (ingredient_groups, equipment, dietary_restrictions, etc.)

16. **Images stored locally** - Two-tier storage: (1) Search results cached immediately for iOS 9 compatibility, (2) Recipe images downloaded at import/scrape time and stored permanently. Search cache has 30-day TTL (cleanup via `cleanup_search_images` command), recipe images permanent.

17. **Serving adjustment not persisted** - Computed on-the-fly via AI, original recipe data stays pristine. AI-only, no frontend math fallback.

18. **Remixes ARE persisted** - Create new Recipe records with `is_remix=True`. No need to track parent recipe (original_recipe FK removed - UI doesn't use it).

19. **Unit toggle persisted** - Metric/Imperial is a profile setting applied to all recipe views. Uses AI conversion when needed, or code conversion if scraped data is granular enough.

20. **Discover for new users** - Show seasonal/holiday suggestions based on current date and worldwide holidays when user has no favorites/history.

21. **Timer audio** - Use default browser notification sound. No custom audio files.

22. **Recipe deletion + remixes** - When original recipe is deleted, remixes become standalone (orphans). They keep `is_remix=True` but have no link to original.

23. **Debug mode** - Ignore for now. Figma shows it in Settings but defer implementation until needed.

24. **Remixed recipe fields** - For `is_remix=True` recipes: `host="user-generated"`, `site_name="User Generated"`. Frontend displays "User Generated" badge.

25. **Serving adjustment visibility** - Only show when BOTH: (a) API key configured, AND (b) recipe has servings value. Hide completely if either condition fails.

26. **GitHub repo** - https://github.com/matthewdeaves/cookie.git (shown in Settings About section)

27. **Re-scraping creates new recipe** - Importing a URL that already exists creates a new Recipe record. No deduplication or cache lookup. Tips regenerated for new recipe.

28. **Remixes are per-profile** - When Profile A creates a remix, Profile B cannot see it. Remixes belong to the creating profile only.

29. **Play mode is stateless** - No server-side state. If user navigates away mid-cook, they lose their place. This is acceptable.

30. **Testing framework** - pytest for all tests (unit + integration). Use Django's test client for API tests.

31. **ALL backend commands run in Docker** - The host has NO Python/Django environment. NEVER run Python, pytest, manage.py, or any backend command on the host. Docker is the ONLY environment.
    - **Backend tests:** `docker compose exec web python -m pytest`
    - **Django shell:** `docker compose exec web python manage.py shell`
    - **Management commands:** `docker compose exec web python manage.py <command>`
    - **Frontend tests:** `docker compose exec frontend npm test` (runs and exits)
    - **Frontend watch:** `docker compose exec frontend npm run test:watch`

    ⚠️ If you see `ModuleNotFoundError: No module named 'django'`, you forgot to use the container!

32. **Selector AI fallback** - When a search source's CSS selector fails, AI analyzes the HTML and suggests a new selector. Auto-updates the source setting on success.

## File Locations

- **Figma export:** `/home/matt/cookie/Cookie Recipe App Design/`
- **recipe-scrapers:** `/home/matt/recipe-scrapers`
- **curl_cffi:** `/home/matt/curl_cffi`
- **Phase plans:** `/home/matt/cookie/plans/` (10 focused phase files)
- **Workflow guide:** `/home/matt/cookie/WORKFLOW.md`

### Phase Files

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

## Quick Reference

| Question | Answer |
|----------|--------|
| How many AI prompts? | 10 |
| How many search sources? | 15 |
| Nutrition AI? | No, scraped only |
| Environments? | Single (dev=prod) |
| Remix source_url? | Nullable |
| Remix host/site_name? | "user-generated" / "User Generated" |
| Track remix parent? | No (UI doesn't use it) |
| AI unavailable behavior? | Hide all AI features |
| Serving adjustment persisted? | No, AI-only on-the-fly |
| Serving adjustment fallback? | None - hide when no API key |
| Serving adjustment no servings? | Hide (can't scale without base) |
| Unit toggle persisted? | Yes, profile setting applied to all views |
| Timer audio? | Default browser notification |
| Legacy dark mode? | No, light only |
| Discover for new user? | Seasonal/holiday only |
| Debug mode? | Ignore for now |
| GitHub repo? | github.com/matthewdeaves/cookie.git |
| Re-scraping URL? | Creates new recipe (no dedup) |
| Remix visibility? | Per-profile only |
| Play mode state? | Stateless, browser-only |
| Testing framework? | pytest |
| Selector failure fallback? | AI suggests new selector |

## Image Cache Monitoring

The image caching system (QA-009) uses background threading to cache search result images for iOS 9 compatibility. Monitor system health and performance using these tools:

### Health Check Endpoint

Check cache status and statistics:
```bash
curl http://localhost/api/recipes/cache/health/
```

Returns:
```json
{
  "status": "healthy",
  "cache_stats": {
    "total": 50,
    "success": 48,
    "pending": 0,
    "failed": 2,
    "success_rate": "96.0%"
  }
}
```

### Background Thread Activity

View logs for background caching operations:
```bash
docker compose logs -f web | grep "Cached image from"
docker compose logs -f web | grep "Background image caching"
```

### Database Queries

Check cache statistics directly:
```bash
docker compose exec -T web python manage.py shell
```

```python
from apps.recipes.models import CachedSearchImage
CachedSearchImage.objects.filter(status='success').count()
CachedSearchImage.objects.filter(status='failed').count()
CachedSearchImage.objects.filter(status='pending').count()
```

### Performance Metrics

Monitor search API response time:
```bash
time curl "http://localhost/api/recipes/search/?q=chicken"
# Expected: 2-4 seconds (search + fire-and-forget caching)
# Images appear on refresh/subsequent searches
```

### Cleanup Automation

Run weekly cleanup to remove old cached images (30+ days):
```bash
# Dry run to preview deletions
docker compose exec -T web python manage.py cleanup_search_images --days=30 --dry-run

# Actually delete old images
docker compose exec -T web python manage.py cleanup_search_images --days=30
```

Add to crontab for weekly automation:
```bash
# Run weekly on Sunday at 2am
0 2 * * 0 cd /path/to/cookie && docker compose exec -T web python manage.py cleanup_search_images --days=30
```

### Image Quality Settings

- **Format**: All images converted to JPEG for iOS 9 compatibility (no WebP support)
- **Quality**: JPEG quality=92 for high-DPI displays (Retina, 4K)
- **File sizes**: Average 50-100KB per image
- **Storage**: Two-tier system
  - Search cache: `media/search_images/` (30-day TTL)
  - Recipe images: `media/recipe_images/` (permanent)

### Production Configuration

Gunicorn configured with threading support for background caching:
```bash
# Dockerfile CMD
gunicorn --bind 0.0.0.0:8000 --reload --workers 2 --threads 2 cookie.wsgi:application
```

- **Workers**: 2 processes to handle concurrent requests
- **Threads**: 2 threads per worker for background threading
- **Worker class**: sync (default, compatible with threading.Thread)

### Troubleshooting

**Images not appearing:**
1. Check health endpoint for failed caches
2. Verify background threads are running (check logs)
3. Check media directory permissions: `ls -l media/search_images/`

**High failure rate:**
1. Check logs for HTTP errors: `docker compose logs web | grep "Failed to cache"`
2. Verify curl_cffi is working: Test scraping manually
3. Check network connectivity to external recipe sites

**Slow performance:**
1. Verify threading is enabled (check Gunicorn config)
2. Check for pending caches: May indicate thread backlog
3. Monitor CPU/memory usage during searches

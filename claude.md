# Claude Code Instructions for Cookie 2

## Critical Rules

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

### Data Model

15. **Full recipe-scrapers support** - Database schema supports ALL fields from the library (ingredient_groups, equipment, dietary_restrictions, etc.)

16. **Images stored locally** - Download and store images at scrape time, no proxy

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

31. **Selector AI fallback** - When a search source's CSS selector fails, AI analyzes the HTML and suggests a new selector. Auto-updates the source setting on success.

## File Locations

- **Figma export:** `/home/matt/cookie2/Cookie Recipe App Design/`
- **Cookie 1 reference:** `/home/matt/cookie` (research only, no code copying)
- **recipe-scrapers:** `/home/matt/recipe-scrapers`
- **curl_cffi:** `/home/matt/curl_cffi`
- **Phase plans:** `/home/matt/cookie2/plans/` (modular, per-phase; Phase 8 split into 8A/8B)
- **Workflow guide:** `/home/matt/cookie2/WORKFLOW.md`

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

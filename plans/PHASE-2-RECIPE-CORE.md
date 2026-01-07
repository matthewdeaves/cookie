# Phase 2: Recipe Core

> **Goal:** Recipe scraping and storage working
> **Prerequisite:** Phase 1 complete
> **Deliverable:** Can scrape recipes from URLs, search across 15 sites

---

## Session Scope

| Session | Tasks | Focus |
|---------|-------|-------|
| A | 2.1-2.2 | Recipe + SearchSource models |
| B | 2.3-2.4 | Scraper service + image download |
| C | 2.5-2.6 | API endpoints + search service |
| D | 2.7-2.8 | Search API + tests |

---

## Tasks

- [ ] 2.1 Recipe model with full recipe-scrapers fields
- [ ] 2.2 SearchSource model with 15 curated sites (data migration)
- [ ] 2.3 Async scraper service with curl_cffi
- [ ] 2.4 Image download and local storage
- [ ] 2.5 Recipe API endpoints (scrape, list, detail, delete)
- [ ] 2.6 Async multi-site search service
- [ ] 2.7 Search API endpoint with source filtering
- [ ] 2.8 Write pytest tests for scraper and search services

---

## Recipe Model

Full support for all recipe-scrapers fields:

```python
class Recipe(models.Model):
    # Source information
    source_url = models.URLField(max_length=2000, null=True, blank=True, db_index=True)
    canonical_url = models.URLField(max_length=2000, blank=True)
    host = models.CharField(max_length=255)  # e.g., "allrecipes.com"
    site_name = models.CharField(max_length=255, blank=True)

    # Core content
    title = models.CharField(max_length=500)
    author = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    # Images (stored locally)
    image = models.ImageField(upload_to='recipe_images/', blank=True)
    image_url = models.URLField(max_length=2000, blank=True)

    # Ingredients
    ingredients = models.JSONField(default=list)
    ingredient_groups = models.JSONField(default=list)

    # Instructions
    instructions = models.JSONField(default=list)
    instructions_text = models.TextField(blank=True)

    # Timing (in minutes)
    prep_time = models.PositiveIntegerField(null=True, blank=True)
    cook_time = models.PositiveIntegerField(null=True, blank=True)
    total_time = models.PositiveIntegerField(null=True, blank=True)

    # Servings
    yields = models.CharField(max_length=100, blank=True)
    servings = models.PositiveIntegerField(null=True, blank=True)

    # Categorization
    category = models.CharField(max_length=100, blank=True)
    cuisine = models.CharField(max_length=100, blank=True)
    cooking_method = models.CharField(max_length=100, blank=True)
    keywords = models.JSONField(default=list)
    dietary_restrictions = models.JSONField(default=list)

    # Equipment and extras
    equipment = models.JSONField(default=list)

    # Nutrition (scraped from source)
    nutrition = models.JSONField(default=dict)

    # Ratings
    rating = models.FloatField(null=True, blank=True)
    rating_count = models.PositiveIntegerField(null=True, blank=True)

    # Language
    language = models.CharField(max_length=10, blank=True)

    # Links
    links = models.JSONField(default=list)

    # AI-generated content
    ai_tips = models.JSONField(default=list, blank=True)

    # Remix tracking
    is_remix = models.BooleanField(default=False)
    remix_profile = models.ForeignKey('profiles.Profile', on_delete=models.CASCADE, null=True, blank=True, related_name='remixes')

    # Timestamps
    scraped_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['host']),
            models.Index(fields=['is_remix']),
            models.Index(fields=['scraped_at']),
        ]
```

---

## SearchSource Model

```python
class SearchSource(models.Model):
    host = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_enabled = models.BooleanField(default=True)
    search_url_template = models.CharField(max_length=500)
    result_selector = models.CharField(max_length=255)
    logo_url = models.URLField(blank=True)

    # Maintenance tracking
    last_validated_at = models.DateTimeField(null=True, blank=True)
    consecutive_failures = models.PositiveIntegerField(default=0)
    needs_attention = models.BooleanField(default=False)
```

---

## 15 Curated Search Sources

| Site | Host | Search URL Template |
|------|------|---------------------|
| AllRecipes | allrecipes.com | `https://www.allrecipes.com/search?q={query}` |
| BBC Good Food | bbcgoodfood.com | `https://www.bbcgoodfood.com/search?q={query}` |
| BBC Food | bbc.co.uk/food | `https://www.bbc.co.uk/food/search?q={query}` |
| Bon Appetit | bonappetit.com | `https://www.bonappetit.com/search?q={query}` |
| Budget Bytes | budgetbytes.com | `https://www.budgetbytes.com/?s={query}` |
| Delish | delish.com | `https://www.delish.com/search/?q={query}` |
| Epicurious | epicurious.com | `https://www.epicurious.com/search?q={query}` |
| Food Network | foodnetwork.com | `https://www.foodnetwork.com/search/{query}-` |
| Food52 | food52.com | `https://food52.com/recipes/search?q={query}` |
| Jamie Oliver | jamieoliver.com | `https://www.jamieoliver.com/search/?s={query}` |
| Tasty | tasty.co | `https://tasty.co/search?q={query}` |
| Serious Eats | seriouseats.com | `https://www.seriouseats.com/search?q={query}` |
| Simply Recipes | simplyrecipes.com | `https://www.simplyrecipes.com/search?q={query}` |
| Taste of Home | tasteofhome.com | `https://www.tasteofhome.com/search/?q={query}` |
| The Kitchn | thekitchn.com | `https://www.thekitchn.com/search?q={query}` |

**Note:** CSS selectors TBD - validate each during implementation.

---

## API Endpoints

```
# Recipes
GET    /api/recipes/                      # List saved recipes (with filters)
POST   /api/recipes/scrape/               # Scrape recipe from URL
GET    /api/recipes/{id}/                 # Get recipe detail
DELETE /api/recipes/{id}/                 # Delete recipe
GET    /api/recipes/search/               # Search web (async, returns results to import)

# Search Sources
GET    /api/sources/                      # List all 15 sources with status
GET    /api/sources/test/{host}/          # Test a source's selector
POST   /api/sources/test-all/             # Test all sources
PUT    /api/sources/{host}/               # Update source settings
```

---

## Scraper Service

Key implementation details:

```python
# apps/recipes/services/scraper.py
from recipe_scrapers import scrape_html
from curl_cffi.requests import AsyncSession

class RecipeScraper:
    BROWSER_PROFILES = ['chrome136', 'safari184', 'firefox133']

    async def scrape_url(self, url: str) -> Recipe:
        # Fetch HTML with browser fingerprint
        async with AsyncSession(impersonate='chrome136') as session:
            response = await session.get(url, timeout=30)
            html = response.text

        # Parse with recipe-scrapers
        scraper = scrape_html(html, org_url=url)

        # Download and store image locally
        image_file = await self._download_image(scraper.image())

        # Create Recipe record with all fields
        return Recipe.objects.create(
            source_url=url,
            host=scraper.host(),
            title=scraper.title(),
            # ... all other fields
            image=image_file,
        )
```

---

## Search Service

Key implementation details:

```python
# apps/recipes/services/search.py
class RecipeSearch:
    MAX_CONCURRENT = 10
    RATE_LIMIT_DELAY = 1.5  # seconds between requests to same domain

    async def search(self, query: str, page: int = 1, per_page: int = 6) -> dict:
        enabled_sources = await SearchSource.get_enabled_sources()
        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT)

        async with AsyncSession(impersonate='chrome136') as session:
            tasks = [
                self._search_site(session, semaphore, source, query)
                for source in enabled_sources
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten, deduplicate, paginate
        return {
            'results': paginated_results,
            'total': total,
            'page': page,
            'has_more': has_more,
            'sites': site_counts
        }
```

---

## Acceptance Criteria

1. Can scrape a recipe from any of the 15 curated sites
2. Recipe images are downloaded and stored locally
3. All recipe-scrapers fields are captured
4. Multi-site search returns results from enabled sources
5. Source filtering works in search
6. Re-scraping same URL creates new recipe (no dedup)
7. Rate limiting prevents site blocking (1.5s delay per domain)

---

## Checkpoint (End of Phase)

```
[ ] POST /api/recipes/scrape/ with allrecipes.com URL - recipe created
[ ] Recipe image saved to local storage (check media folder)
[ ] Recipe has title, ingredients, instructions populated
[ ] GET /api/recipes/search/?q=cookies - returns results from multiple sites
[ ] Search with source filter - returns only from specified source
[ ] Scrape same URL twice - two different recipe records exist
[ ] pytest - all scraper and search tests pass
```

---

## Testing Notes

Use pytest with Django test client:

```python
@pytest.mark.asyncio
async def test_scrape_recipe():
    recipe = await RecipeScraper().scrape_url('https://allrecipes.com/recipe/...')
    assert recipe.title
    assert recipe.ingredients
    assert recipe.instructions
    assert recipe.image

@pytest.mark.asyncio
async def test_multi_site_search():
    results = await RecipeSearch().search('chocolate chip cookies')
    assert results['total'] > 0
    assert len(results['sites']) > 1
```

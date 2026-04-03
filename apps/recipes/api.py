"""
Recipe API endpoints.
"""

import hashlib
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from ninja import Router, Schema, Status
from ninja.errors import HttpError

from django_ratelimit.core import is_ratelimited

from apps.core.auth import AdminAuth, SessionAuth
from apps.profiles.utils import aget_current_profile_or_none, get_current_profile_or_none

from .models import Recipe
from .services.image_cache import SearchImageCache
from .services.scraper import RecipeScraper, FetchError, ParseError
from .services.search import RecipeSearch

router = Router(tags=["recipes"])


# Schemas


class LinkedRecipeOut(Schema):
    """Minimal recipe info for linked recipe navigation."""

    id: int
    title: str
    relationship: str  # "original", "remix", "sibling"


class RecipeOut(Schema):
    id: int
    source_url: Optional[str]
    canonical_url: str
    host: str
    site_name: str
    title: str
    author: str
    description: str
    image_url: str
    image: Optional[str]  # Local image path
    ingredients: list
    ingredient_groups: list
    instructions: list
    instructions_text: str
    prep_time: Optional[int]
    cook_time: Optional[int]
    total_time: Optional[int]
    yields: str
    servings: Optional[int]
    category: str
    cuisine: str
    cooking_method: str
    keywords: list
    dietary_restrictions: list
    equipment: list
    nutrition: dict
    rating: Optional[float]
    rating_count: Optional[int]
    language: str
    links: list
    ai_tips: list
    is_remix: bool
    remix_profile_id: Optional[int]
    remixed_from_id: Optional[int]
    linked_recipes: List[LinkedRecipeOut] = []
    scraped_at: str
    updated_at: str

    @staticmethod
    def resolve_image(obj):
        if obj.image:
            return obj.image.url
        return None

    @staticmethod
    def resolve_scraped_at(obj):
        return obj.scraped_at.isoformat()

    @staticmethod
    def resolve_updated_at(obj):
        return obj.updated_at.isoformat()

    @staticmethod
    def resolve_remixed_from_id(obj):
        return getattr(obj, "remixed_from_id", None)

    @staticmethod
    def resolve_linked_recipes(obj):
        # Return linked_recipes if set, otherwise empty list
        return getattr(obj, "linked_recipes", [])


class RecipeListOut(Schema):
    """Condensed recipe output for list views."""

    id: int
    title: str
    host: str
    image_url: str
    image: Optional[str]
    total_time: Optional[int]
    rating: Optional[float]
    is_remix: bool
    scraped_at: str

    @staticmethod
    def resolve_image(obj):
        if obj.image:
            return obj.image.url
        return None

    @staticmethod
    def resolve_scraped_at(obj):
        return obj.scraped_at.isoformat()


class ScrapeIn(Schema):
    url: str


class ErrorOut(Schema):
    detail: str


class SearchResultOut(Schema):
    url: str
    title: str
    host: str
    image_url: str  # External URL (fallback)
    cached_image_url: Optional[str] = None  # Local cached URL
    description: str
    rating_count: Optional[int] = None


class SearchOut(Schema):
    results: List[SearchResultOut]
    total: int
    page: int
    has_more: bool
    sites: dict


# Endpoints
# NOTE: Static routes must come before dynamic routes (e.g., /search/ before /{recipe_id}/)


@router.get("/", response=List[RecipeListOut], auth=SessionAuth())
def list_recipes(
    request,
    host: Optional[str] = None,
    is_remix: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
):
    """
    List saved recipes with optional filters.

    - **host**: Filter by source host (e.g., "allrecipes.com")
    - **is_remix**: Filter by remix status
    - **limit**: Number of recipes to return (default 50)
    - **offset**: Offset for pagination

    Returns only recipes owned by the current profile.
    """
    profile = get_current_profile_or_none(request)
    if not profile:
        return []

    limit = min(max(limit, 1), 100)
    offset = max(offset, 0)

    # Only show recipes owned by this profile
    qs = Recipe.objects.filter(profile=profile).order_by("-scraped_at")

    if host:
        qs = qs.filter(host=host)
    if is_remix is not None:
        qs = qs.filter(is_remix=is_remix)

    return qs[offset : offset + limit]


@router.post(
    "/scrape/",
    response={201: RecipeOut, 400: ErrorOut, 403: ErrorOut, 429: ErrorOut, 502: ErrorOut},
    auth=SessionAuth(),
)
async def scrape_recipe(request, payload: ScrapeIn):
    """
    Scrape a recipe from a URL.

    The URL is fetched, parsed for recipe data, and saved to the database.
    If the recipe has an image, it will be downloaded and stored locally.
    The recipe will be owned by the current profile.

    Note: Re-scraping the same URL will create a new recipe record.
    """
    limited = await sync_to_async(is_ratelimited)(request, group="scrape", key="ip", rate="5/h", increment=True)
    if limited:
        return Status(429, {"detail": "Too many scrape requests. Please try again later."})

    profile = await aget_current_profile_or_none(request)
    if not profile:
        return Status(403, {"detail": "Profile required to scrape recipes"})

    scraper = RecipeScraper()
    logger.info(f"Scrape request: {payload.url}")

    try:
        recipe = await scraper.scrape_url(payload.url, profile)
        logger.info(f'Scrape success: {payload.url} -> recipe {recipe.id} "{recipe.title}"')
        return Status(201, recipe)
    except FetchError as e:
        logger.warning(f"Scrape fetch error: {payload.url} - {e}")
        return Status(502, {"detail": str(e)})
    except ParseError as e:
        logger.warning(f"Scrape parse error: {payload.url} - {e}")
        return Status(400, {"detail": str(e)})


async def _get_or_fetch_results(query: str) -> list:
    """Return cached search results, or fetch and cache them."""
    normalized_query = query.lower().strip()
    query_hash = hashlib.sha256(normalized_query.encode()).hexdigest()[:16]
    cache_key = f"search_{query_hash}"
    cached_all = await sync_to_async(cache.get)(cache_key)

    if cached_all is not None:
        return cached_all

    search = RecipeSearch()
    full_results = await search.search(query=query, per_page=10000)
    all_result_dicts = full_results.get("results", [])
    await sync_to_async(cache.set)(cache_key, all_result_dicts, settings.SEARCH_CACHE_TIMEOUT)
    return all_result_dicts


def _aggregate_sites(result_dicts: list) -> dict:
    """Count results per host from the full unfiltered result list."""
    sites: dict[str, int] = {}
    for r in result_dicts:
        sites[r["host"]] = sites.get(r["host"], 0) + 1
    return sites


def _paginate_results(
    all_results: list,
    source_list: Optional[list],
    sites: dict,
    page: int,
    per_page: int,
) -> dict:
    """Filter by sources, paginate, and return a SearchOut-shaped dict."""
    filtered = all_results
    if source_list:
        filtered = [r for r in filtered if r["host"] in source_list]

    total = len(filtered)
    start = (page - 1) * per_page
    end = start + per_page

    return {
        "results": filtered[start:end],
        "total": total,
        "page": page,
        "has_more": end < total,
        "sites": sites,
    }


async def _cache_and_map_images(results: list) -> None:
    """Populate cached_image_url on each result dict, caching as needed."""
    image_urls = [r["image_url"] for r in results if r.get("image_url")]
    image_cache = SearchImageCache()
    cached_urls = await image_cache.get_cached_urls_batch(image_urls)

    uncached_urls = [url for url in image_urls if url not in cached_urls]
    if uncached_urls:
        await image_cache.cache_images(uncached_urls)
        new_cached = await image_cache.get_cached_urls_batch(uncached_urls)
        cached_urls.update(new_cached)

    for result in results:
        external_url = result.get("image_url", "")
        result["cached_image_url"] = cached_urls.get(external_url)


@router.get("/search/", response=SearchOut)
async def search_recipes(
    request,
    q: str,
    sources: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
):
    """
    Search for recipes across multiple sites.

    - **q**: Search query
    - **sources**: Comma-separated list of hosts to search (optional)
    - **page**: Page number (default 1)
    - **per_page**: Results per page (default 20)

    Returns recipe URLs from enabled search sources.
    Uses cached images when available for iOS 9 compatibility.
    Use the scrape endpoint to save a recipe from the results.
    """
    limited = await sync_to_async(is_ratelimited)(request, group="search", key="ip", rate="60/h", increment=True)
    if limited:
        raise HttpError(429, "Too many search requests. Please try again later.")

    source_list = None
    if sources:
        source_list = [s.strip() for s in sources.split(",") if s.strip()]

    all_result_dicts = await _get_or_fetch_results(q)
    sites = _aggregate_sites(all_result_dicts)
    results = _paginate_results(all_result_dicts, source_list, sites, page, per_page)
    await _cache_and_map_images(results["results"])
    return results


@router.get("/cache/health/", response={200: dict}, auth=AdminAuth())
def cache_health(request):
    """
    Health check endpoint for image cache monitoring.

    Returns cache statistics and status for monitoring the background
    image caching system. Use this to verify caching is working correctly
    and to track cache hit rates.
    """
    from apps.recipes.models import CachedSearchImage

    total = CachedSearchImage.objects.count()
    success = CachedSearchImage.objects.filter(status=CachedSearchImage.STATUS_SUCCESS).count()
    pending = CachedSearchImage.objects.filter(status=CachedSearchImage.STATUS_PENDING).count()
    failed = CachedSearchImage.objects.filter(status=CachedSearchImage.STATUS_FAILED).count()

    return {
        "status": "healthy",
        "cache_stats": {
            "total": total,
            "success": success,
            "pending": pending,
            "failed": failed,
            "success_rate": f"{(success / total * 100):.1f}%" if total > 0 else "N/A",
        },
    }


# Dynamic routes with {recipe_id} must come last


@router.get("/{recipe_id}/", response={200: RecipeOut, 404: ErrorOut}, auth=SessionAuth())
def get_recipe(request, recipe_id: int):
    """
    Get a recipe by ID.

    Only returns recipes owned by the current profile.
    Includes linked_recipes for navigation between original and remixes.
    """
    profile = get_current_profile_or_none(request)
    if not profile:
        return Status(404, {"detail": "Recipe not found"})

    # Only allow access to recipes owned by this profile
    recipe = get_object_or_404(Recipe, id=recipe_id, profile=profile)

    # Build linked recipes list for navigation
    linked_recipes = []

    # Add original recipe if this is a remix
    if recipe.remixed_from_id:
        original = recipe.remixed_from
        if original and original.profile_id == profile.id:
            linked_recipes.append(
                {
                    "id": original.id,
                    "title": original.title,
                    "relationship": "original",
                }
            )
            # Add siblings (other remixes of the same original)
            siblings = (
                Recipe.objects.filter(
                    remixed_from=original,
                    profile=profile,
                )
                .exclude(id=recipe.id)
                .values("id", "title")
            )
            for sibling in siblings:
                linked_recipes.append(
                    {
                        "id": sibling["id"],
                        "title": sibling["title"],
                        "relationship": "sibling",
                    }
                )

    # Add children (remixes of this recipe)
    children = Recipe.objects.filter(
        remixed_from=recipe,
        profile=profile,
    ).values("id", "title")
    for child in children:
        linked_recipes.append(
            {
                "id": child["id"],
                "title": child["title"],
                "relationship": "remix",
            }
        )

    # Attach linked recipes to the recipe object for serialization
    recipe.linked_recipes = linked_recipes

    return recipe


@router.delete("/{recipe_id}/", response={204: None, 404: ErrorOut}, auth=SessionAuth())
def delete_recipe(request, recipe_id: int):
    """
    Delete a recipe by ID.

    Only the owning profile can delete a recipe.
    """
    profile = get_current_profile_or_none(request)
    if not profile:
        return Status(404, {"detail": "Recipe not found"})

    # Only allow deletion of recipes owned by this profile
    recipe = get_object_or_404(Recipe, id=recipe_id, profile=profile)
    recipe.delete()
    return Status(204, None)

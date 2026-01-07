"""
Recipe API endpoints.
"""

from typing import List, Optional

from asgiref.sync import sync_to_async
from django.db.models import Q
from django.shortcuts import get_object_or_404
from ninja import Router, Schema

from apps.profiles.utils import get_current_profile_or_none

from .models import Recipe
from .services.scraper import RecipeScraper, FetchError, ParseError
from .services.search import RecipeSearch

router = Router(tags=['recipes'])


# Schemas

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
    image_url: str
    description: str


class SearchOut(Schema):
    results: List[SearchResultOut]
    total: int
    page: int
    has_more: bool
    sites: dict


# Endpoints
# NOTE: Static routes must come before dynamic routes (e.g., /search/ before /{recipe_id}/)

@router.get('/', response=List[RecipeListOut])
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

    Remixes are only visible to the profile that created them.
    """
    profile = get_current_profile_or_none(request)
    qs = Recipe.objects.all().order_by('-scraped_at')

    # Filter remix visibility: non-remixes OR remixes owned by current profile
    if profile:
        qs = qs.filter(Q(is_remix=False) | Q(remix_profile=profile))
    else:
        qs = qs.filter(is_remix=False)

    if host:
        qs = qs.filter(host=host)
    if is_remix is not None:
        qs = qs.filter(is_remix=is_remix)

    return qs[offset:offset + limit]


@router.post('/scrape/', response={201: RecipeOut, 400: ErrorOut, 502: ErrorOut})
async def scrape_recipe(request, payload: ScrapeIn):
    """
    Scrape a recipe from a URL.

    The URL is fetched, parsed for recipe data, and saved to the database.
    If the recipe has an image, it will be downloaded and stored locally.

    Note: Re-scraping the same URL will create a new recipe record.
    """
    scraper = RecipeScraper()

    try:
        recipe = await scraper.scrape_url(payload.url)
        return 201, recipe
    except FetchError as e:
        return 502, {'detail': str(e)}
    except ParseError as e:
        return 400, {'detail': str(e)}


@router.get('/search/', response=SearchOut)
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
    Use the scrape endpoint to save a recipe from the results.
    """
    source_list = None
    if sources:
        source_list = [s.strip() for s in sources.split(',') if s.strip()]

    search = RecipeSearch()
    results = await search.search(
        query=q,
        sources=source_list,
        page=page,
        per_page=per_page,
    )
    return results


# Dynamic routes with {recipe_id} must come last

@router.get('/{recipe_id}/', response={200: RecipeOut, 404: ErrorOut})
def get_recipe(request, recipe_id: int):
    """
    Get a recipe by ID.

    Remixes are only visible to the profile that created them.
    """
    recipe = get_object_or_404(Recipe, id=recipe_id)

    # Check remix visibility
    if recipe.is_remix:
        profile = get_current_profile_or_none(request)
        if not profile or recipe.remix_profile_id != profile.id:
            return 404, {'detail': 'Recipe not found'}

    return recipe


@router.delete('/{recipe_id}/', response={204: None, 404: ErrorOut})
def delete_recipe(request, recipe_id: int):
    """
    Delete a recipe by ID.

    Remixes can only be deleted by the profile that created them.
    """
    recipe = get_object_or_404(Recipe, id=recipe_id)

    # Check remix visibility
    if recipe.is_remix:
        profile = get_current_profile_or_none(request)
        if not profile or recipe.remix_profile_id != profile.id:
            return 404, {'detail': 'Recipe not found'}

    recipe.delete()
    return 204, None

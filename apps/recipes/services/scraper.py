"""
Recipe scraper service using curl_cffi and recipe-scrapers.
"""

import hashlib
import logging
import re
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from curl_cffi.requests import AsyncSession
from recipe_scrapers import scrape_html

logger = logging.getLogger(__name__)


class ScraperError(Exception):
    """Base exception for scraper errors."""
    pass


class FetchError(ScraperError):
    """Failed to fetch URL."""
    pass


class ParseError(ScraperError):
    """Failed to parse recipe from HTML."""
    pass


class RecipeScraper:
    """
    Async recipe scraper with browser fingerprint impersonation.

    Uses curl_cffi to bypass anti-bot measures and recipe-scrapers
    to parse structured recipe data from HTML.
    """

    BROWSER_PROFILES = ['chrome136', 'safari18_0', 'firefox133']
    DEFAULT_TIMEOUT = 30

    def __init__(self):
        self.timeout = self.DEFAULT_TIMEOUT

    async def scrape_url(self, url: str) -> 'Recipe':
        """
        Scrape a recipe from a URL and save it to the database.

        Args:
            url: The recipe URL to scrape

        Returns:
            Recipe model instance

        Raises:
            FetchError: If the URL cannot be fetched
            ParseError: If the HTML cannot be parsed as a recipe
        """
        # Import here to avoid circular imports
        from apps.recipes.models import Recipe

        # Fetch HTML
        html = await self._fetch_html(url)

        # Parse recipe data
        data = self._parse_recipe(html, url)

        # Check for cached search image first, then download if needed
        image_file = None
        if data.get('image_url'):
            # Try to reuse cached image from search results
            from apps.recipes.models import CachedSearchImage

            try:
                cached = await sync_to_async(
                    CachedSearchImage.objects.get
                )(
                    external_url=data['image_url'],
                    status=CachedSearchImage.STATUS_SUCCESS
                )

                if cached.image:
                    # Reuse cached image file
                    with cached.image.open('rb') as f:
                        image_file = ContentFile(f.read())

                    # Update access time to prevent cleanup
                    cached.last_accessed_at = timezone.now()
                    await sync_to_async(cached.save)(update_fields=['last_accessed_at'])

                    logger.info(f"Reused cached image for {data['image_url']}")

            except CachedSearchImage.DoesNotExist:
                pass

            # If no cache, download as normal
            if not image_file:
                image_file = await self._download_image(data['image_url'])

        # Create recipe record
        recipe = Recipe(
            source_url=url,
            canonical_url=data.get('canonical_url', ''),
            host=data['host'],
            site_name=data.get('site_name', ''),
            title=data['title'],
            author=data.get('author', ''),
            description=data.get('description', ''),
            image_url=data.get('image_url', ''),
            ingredients=data.get('ingredients', []),
            ingredient_groups=data.get('ingredient_groups', []),
            instructions=data.get('instructions', []),
            instructions_text=data.get('instructions_text', ''),
            prep_time=data.get('prep_time'),
            cook_time=data.get('cook_time'),
            total_time=data.get('total_time'),
            yields=data.get('yields', ''),
            servings=data.get('servings'),
            category=data.get('category', ''),
            cuisine=data.get('cuisine', ''),
            cooking_method=data.get('cooking_method', ''),
            keywords=data.get('keywords', []),
            dietary_restrictions=data.get('dietary_restrictions', []),
            equipment=data.get('equipment', []),
            nutrition=data.get('nutrition', {}),
            rating=data.get('rating'),
            rating_count=data.get('rating_count'),
            language=data.get('language', ''),
            links=data.get('links', []),
        )

        # Save first to get an ID for the image path
        await sync_to_async(recipe.save)()

        # Attach image if downloaded
        if image_file:
            filename = self._generate_image_filename(url, data.get('image_url', ''))
            await sync_to_async(recipe.image.save)(filename, image_file, save=True)

        return recipe

    async def _fetch_html(self, url: str) -> str:
        """
        Fetch HTML from URL with browser impersonation.

        Tries multiple browser profiles if initial request fails.
        """
        errors = []

        for profile in self.BROWSER_PROFILES:
            try:
                async with AsyncSession(impersonate=profile) as session:
                    response = await session.get(
                        url,
                        timeout=self.timeout,
                        allow_redirects=True,
                    )

                    if response.status_code == 200:
                        return response.text

                    errors.append(f"{profile}: HTTP {response.status_code}")

            except Exception as e:
                errors.append(f"{profile}: {str(e)}")
                continue

        raise FetchError(f"Failed to fetch {url}: {'; '.join(errors)}")

    def _parse_recipe(self, html: str, url: str) -> dict:
        """
        Parse recipe data from HTML using recipe-scrapers.
        """
        try:
            # supported_only=False allows scraping from any domain using schema.org
            scraper = scrape_html(html, org_url=url, supported_only=False)
        except Exception as e:
            raise ParseError(f"Failed to parse recipe: {str(e)}")

        # Extract host from URL
        parsed_url = urlparse(url)
        host = parsed_url.netloc.replace('www.', '')

        # Build recipe data dict with safe attribute access
        data = {
            'host': host,
            'title': self._safe_get(scraper, 'title', ''),
            'canonical_url': self._safe_get(scraper, 'canonical_url', ''),
            'site_name': self._safe_get(scraper, 'site_name', ''),
            'author': self._safe_get(scraper, 'author', ''),
            'description': self._safe_get(scraper, 'description', ''),
            'image_url': self._safe_get(scraper, 'image', ''),
            'ingredients': self._safe_get(scraper, 'ingredients', []),
            'ingredient_groups': self._safe_get_ingredient_groups(scraper),
            'instructions': self._safe_get(scraper, 'instructions_list', []),
            'instructions_text': self._safe_get(scraper, 'instructions', ''),
            'prep_time': self._parse_time(self._safe_get(scraper, 'prep_time')),
            'cook_time': self._parse_time(self._safe_get(scraper, 'cook_time')),
            'total_time': self._parse_time(self._safe_get(scraper, 'total_time')),
            'yields': self._safe_get(scraper, 'yields', ''),
            'servings': self._parse_servings(self._safe_get(scraper, 'yields', '')),
            'category': self._safe_get(scraper, 'category', ''),
            'cuisine': self._safe_get(scraper, 'cuisine', ''),
            'cooking_method': self._safe_get(scraper, 'cooking_method', ''),
            'keywords': self._safe_get(scraper, 'keywords', []),
            'dietary_restrictions': self._safe_get(scraper, 'dietary_restrictions', []),
            'equipment': self._safe_get(scraper, 'equipment', []),
            'nutrition': self._safe_get(scraper, 'nutrients', {}),
            'rating': self._parse_rating(self._safe_get(scraper, 'ratings')),
            'rating_count': self._parse_rating_count(self._safe_get(scraper, 'ratings_count')),
            'language': self._safe_get(scraper, 'language', ''),
            'links': self._safe_get(scraper, 'links', []),
        }

        if not data['title']:
            raise ParseError("Recipe has no title")

        return data

    def _safe_get(self, scraper, attr: str, default=None):
        """Safely get an attribute from the scraper."""
        try:
            method = getattr(scraper, attr, None)
            if callable(method):
                result = method()
                return result if result is not None else default
            return default
        except Exception:
            return default

    def _safe_get_ingredient_groups(self, scraper) -> list:
        """Get ingredient groups if available."""
        try:
            groups = scraper.ingredient_groups()
            if groups:
                return [
                    {
                        'purpose': getattr(g, 'purpose', ''),
                        'ingredients': getattr(g, 'ingredients', [])
                    }
                    for g in groups
                ]
        except Exception:
            pass
        return []

    def _parse_time(self, value) -> int | None:
        """Parse time value to minutes."""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            # Try to extract number
            match = re.search(r'(\d+)', value)
            if match:
                return int(match.group(1))
        return None

    def _parse_servings(self, yields: str) -> int | None:
        """Extract serving count from yields string."""
        if not yields:
            return None
        match = re.search(r'(\d+)', yields)
        if match:
            return int(match.group(1))
        return None

    def _parse_rating(self, value) -> float | None:
        """Parse rating value to float."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _parse_rating_count(self, value) -> int | None:
        """Parse rating count to int."""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    async def _download_image(self, image_url: str) -> ContentFile | None:
        """
        Download recipe image and return as ContentFile.
        """
        if not image_url:
            return None

        try:
            async with AsyncSession(impersonate='chrome136') as session:
                response = await session.get(
                    image_url,
                    timeout=self.timeout,
                    allow_redirects=True,
                )

                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    if 'image' in content_type or self._is_image_url(image_url):
                        return ContentFile(response.content)

        except Exception as e:
            logger.warning(f"Failed to download image {image_url}: {e}")

        return None

    def _is_image_url(self, url: str) -> bool:
        """Check if URL looks like an image."""
        image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
        parsed = urlparse(url)
        return parsed.path.lower().endswith(image_extensions)

    def _generate_image_filename(self, recipe_url: str, image_url: str) -> str:
        """Generate a unique filename for the recipe image."""
        # Create hash from URLs for uniqueness
        url_hash = hashlib.md5(
            f"{recipe_url}{image_url}".encode()
        ).hexdigest()[:12]

        # Get extension from image URL
        ext = '.jpg'  # default
        if image_url:
            parsed = urlparse(image_url)
            path_ext = Path(parsed.path).suffix.lower()
            if path_ext in ('.jpg', '.jpeg', '.png', '.gif', '.webp'):
                ext = path_ext

        return f"recipe_{url_hash}{ext}"

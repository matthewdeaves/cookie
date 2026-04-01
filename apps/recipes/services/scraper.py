"""
Recipe scraper service using curl_cffi and recipe-scrapers.
"""

import hashlib
import logging
import re
import threading
from io import BytesIO
from urllib.parse import urlparse

from PIL import Image
from asgiref.sync import sync_to_async
from django.core.files.base import ContentFile
from django.utils import timezone
from curl_cffi.requests import AsyncSession
from recipe_scrapers import scrape_html

from apps.core.validators import (
    MAX_HTML_SIZE,
    MAX_IMAGE_SIZE,
    MAX_REDIRECT_HOPS,
    check_content_size,
    check_response_size,
    validate_url,
    validate_redirect_url,
)
from apps.recipes.services.fingerprint import BROWSER_PROFILES

# Limit decompression bomb attacks via PIL
Image.MAX_IMAGE_PIXELS = 178_956_970  # ~180 megapixels

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

    Browser profiles are centralized in fingerprint.py for maintainability.
    """

    DEFAULT_TIMEOUT = 30

    def __init__(self):
        self.timeout = self.DEFAULT_TIMEOUT

    async def scrape_url(self, url: str, profile: "Profile") -> "Recipe":
        """
        Scrape a recipe from a URL and save it to the database.

        Args:
            url: The recipe URL to scrape
            profile: The profile that will own this recipe

        Returns:
            Recipe model instance

        Raises:
            FetchError: If the URL cannot be fetched
            ParseError: If the HTML cannot be parsed as a recipe
        """
        # Import here to avoid circular imports
        from apps.recipes.models import Recipe

        # Validate URL for SSRF protection
        try:
            validate_url(url)
        except ValueError as e:
            raise FetchError(str(e))

        # Fetch HTML
        html = await self._fetch_html(url)

        # Parse recipe data
        data = self._parse_recipe(html, url)

        # Check for cached search image first, then download if needed
        image_file = None
        if data.get("image_url"):
            # Try to reuse cached image from search results
            from apps.recipes.models import CachedSearchImage

            try:
                cached = await sync_to_async(CachedSearchImage.objects.get)(
                    external_url=data["image_url"], status=CachedSearchImage.STATUS_SUCCESS
                )

                if cached.image:
                    # Reuse cached image file
                    with cached.image.open("rb") as f:
                        image_file = ContentFile(f.read())

                    # Update access time to prevent cleanup
                    cached.last_accessed_at = timezone.now()
                    await sync_to_async(cached.save)(update_fields=["last_accessed_at"])

                    logger.info(f"Reused cached image for {data['image_url']}")

            except CachedSearchImage.DoesNotExist:
                pass

            # If no cache, download as normal
            if not image_file:
                image_file = await self._download_image(data["image_url"])

        # Create recipe record
        recipe = Recipe(
            profile=profile,
            source_url=url,
            canonical_url=data.get("canonical_url", ""),
            host=data["host"],
            site_name=data.get("site_name", ""),
            title=data["title"],
            author=data.get("author", ""),
            description=data.get("description", ""),
            image_url=data.get("image_url", ""),
            ingredients=data.get("ingredients", []),
            ingredient_groups=data.get("ingredient_groups", []),
            instructions=data.get("instructions", []),
            instructions_text=data.get("instructions_text", ""),
            prep_time=data.get("prep_time"),
            cook_time=data.get("cook_time"),
            total_time=data.get("total_time"),
            yields=data.get("yields", ""),
            servings=data.get("servings"),
            category=data.get("category", ""),
            cuisine=data.get("cuisine", ""),
            cooking_method=data.get("cooking_method", ""),
            keywords=data.get("keywords", []),
            dietary_restrictions=data.get("dietary_restrictions", []),
            equipment=data.get("equipment", []),
            nutrition=data.get("nutrition", {}),
            rating=data.get("rating"),
            rating_count=data.get("rating_count"),
            language=data.get("language", ""),
            links=data.get("links", []),
        )

        # Save first to get an ID for the image path
        await sync_to_async(recipe.save)()

        # Attach image if downloaded
        if image_file:
            filename = self._generate_image_filename(url, data.get("image_url", ""))
            await sync_to_async(recipe.image.save)(filename, image_file, save=True)

        # Fire-and-forget: Generate AI tips in background thread (non-blocking)
        thread = threading.Thread(target=self._generate_tips_background, args=(recipe.id,), daemon=True)
        thread.start()

        return recipe

    def _generate_tips_background(self, recipe_id: int):
        """Generate AI tips for a recipe in background thread."""
        try:
            import django

            django.setup()  # Ensure Django is configured in thread

            from apps.core.models import AppSettings
            from apps.ai.services.tips import generate_tips

            # Check if AI is available
            settings_obj = AppSettings.get()
            if not settings_obj.openrouter_api_key:
                logger.debug(f"Skipping tips generation for recipe {recipe_id}: No API key")
                return

            # Generate tips
            generate_tips(recipe_id)
            logger.info(f"Auto-generated tips for recipe {recipe_id}")

        except Exception as e:
            # Log but don't fail - tips generation is optional
            logger.warning(f"Failed to auto-generate tips for recipe {recipe_id}: {e}")

    async def _fetch_html(self, url: str) -> str:
        """
        Fetch HTML from URL with browser impersonation.

        Follows redirects manually with per-hop SSRF validation (max 5 hops).
        Enforces response size limit (10MB).
        Tries multiple browser profiles if initial request fails.
        """
        errors = []

        for profile in BROWSER_PROFILES:
            try:
                html = await self._fetch_with_redirects(url, profile, MAX_HTML_SIZE)
                if html is not None:
                    return html
                errors.append(f"{profile}: empty response")
            except FetchError:
                raise
            except ValueError as e:
                raise FetchError(str(e))
            except Exception as e:
                errors.append(f"{profile}: {str(e)}")
                continue

        raise FetchError(f"Failed to fetch {url}: {'; '.join(errors)}")

    async def _fetch_with_redirects(self, url, profile, max_size):
        """Fetch URL following redirects with per-hop SSRF validation."""
        current_url = url
        for _ in range(MAX_REDIRECT_HOPS):
            async with AsyncSession(impersonate=profile) as session:
                response = await session.get(
                    current_url,
                    timeout=self.timeout,
                    allow_redirects=False,
                )

                if response.status_code in (301, 302, 303, 307, 308):
                    location = response.headers.get("location")
                    if not location:
                        raise FetchError("Redirect without Location header")
                    validate_redirect_url(location)
                    current_url = location
                    continue

                if response.status_code == 200:
                    if not check_response_size(response, max_size):
                        raise FetchError(f"Response too large (Content-Length > {max_size})")
                    content = response.text
                    check_content_size(content.encode("utf-8", errors="replace"), max_size)
                    return content

                return None

        raise FetchError(f"Too many redirects (>{MAX_REDIRECT_HOPS})")

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
        host = parsed_url.netloc.replace("www.", "")

        # Build recipe data dict with safe attribute access
        data = {
            "host": host,
            "title": self._safe_get(scraper, "title", ""),
            "canonical_url": self._safe_get(scraper, "canonical_url", ""),
            "site_name": self._safe_get(scraper, "site_name", ""),
            "author": self._safe_get(scraper, "author", ""),
            "description": self._safe_get(scraper, "description", ""),
            "image_url": self._safe_get(scraper, "image", ""),
            "ingredients": self._safe_get(scraper, "ingredients", []),
            "ingredient_groups": self._safe_get_ingredient_groups(scraper),
            "instructions": self._safe_get(scraper, "instructions_list", []),
            "instructions_text": self._safe_get(scraper, "instructions", ""),
            "prep_time": self._parse_time(self._safe_get(scraper, "prep_time")),
            "cook_time": self._parse_time(self._safe_get(scraper, "cook_time")),
            "total_time": self._parse_time(self._safe_get(scraper, "total_time")),
            "yields": self._safe_get(scraper, "yields", ""),
            "servings": self._parse_servings(self._safe_get(scraper, "yields", "")),
            "category": self._safe_get(scraper, "category", ""),
            "cuisine": self._safe_get(scraper, "cuisine", ""),
            "cooking_method": self._safe_get(scraper, "cooking_method", ""),
            "keywords": self._safe_get(scraper, "keywords", []),
            "dietary_restrictions": self._safe_get(scraper, "dietary_restrictions", []),
            "equipment": self._safe_get(scraper, "equipment", []),
            "nutrition": self._safe_get(scraper, "nutrients", {}),
            "rating": self._parse_rating(self._safe_get(scraper, "ratings")),
            "rating_count": self._parse_rating_count(self._safe_get(scraper, "ratings_count")),
            "language": self._safe_get(scraper, "language", ""),
            "links": self._safe_get(scraper, "links", []),
        }

        if not data["title"]:
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
            logger.debug("Failed to get %s from scraper", attr, exc_info=True)
            return default

    def _safe_get_ingredient_groups(self, scraper) -> list:
        """Get ingredient groups if available."""
        try:
            groups = scraper.ingredient_groups()
            if groups:
                return [
                    {"purpose": getattr(g, "purpose", ""), "ingredients": getattr(g, "ingredients", [])} for g in groups
                ]
        except Exception:
            logger.warning("Failed to get ingredient groups from scraper", exc_info=True)
        return []

    def _parse_time(self, value) -> int | None:
        """Parse time value to minutes."""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            # Try to extract number
            match = re.search(r"(\d+)", value)
            if match:
                return int(match.group(1))
        return None

    def _parse_servings(self, yields: str) -> int | None:
        """Extract serving count from yields string."""
        if not yields:
            return None
        match = re.search(r"(\d+)", yields)
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

        Validates image URL against SSRF blocklist before fetching.
        Follows redirects manually with per-hop validation (max 5 hops).
        Enforces response size limit (50MB).
        WebP images are converted to JPEG for iOS 9 compatibility.
        """
        if not image_url:
            return None

        # Validate image URL for SSRF protection (FR-001)
        try:
            validate_url(image_url)
        except ValueError:
            logger.warning("Blocked image URL (SSRF): %s", image_url)
            return None

        for profile in BROWSER_PROFILES:
            try:
                content = await self._fetch_image_with_redirects(image_url, profile)
                if content is not None:
                    content = self._convert_webp_to_jpeg(content)
                    return ContentFile(content)
            except Exception as e:
                logger.warning(
                    "Failed to download image %s with %s: %s",
                    image_url,
                    profile,
                    e,
                )
                continue

        return None

    async def _fetch_image_with_redirects(self, url, profile):
        """Fetch image following redirects with per-hop SSRF validation."""
        current_url = url
        for _ in range(MAX_REDIRECT_HOPS):
            async with AsyncSession(impersonate=profile) as session:
                response = await session.get(
                    current_url,
                    timeout=self.timeout,
                    allow_redirects=False,
                )

                if response.status_code in (301, 302, 303, 307, 308):
                    location = response.headers.get("location")
                    if not location:
                        return None
                    try:
                        validate_redirect_url(location)
                    except ValueError:
                        return None
                    current_url = location
                    continue

                if response.status_code == 200:
                    content_type = response.headers.get("content-type", "")
                    if "image" not in content_type and not self._is_image_url(current_url):
                        return None
                    if not check_response_size(response, MAX_IMAGE_SIZE):
                        logger.warning("Image too large: %s", current_url)
                        return None
                    content = response.content
                    if len(content) > MAX_IMAGE_SIZE:
                        logger.warning("Image content too large: %s", current_url)
                        return None
                    return content

                return None

        logger.warning("Too many redirects for image: %s", url)
        return None

    def _convert_webp_to_jpeg(self, content: bytes) -> bytes:
        """Convert WebP images to JPEG for iOS 9 compatibility.

        Also resizes very large images to reduce file size.
        Rejects images that exceed the size limit (decompression bomb protection).
        """
        if len(content) > MAX_IMAGE_SIZE:
            logger.warning("Image content too large for processing: %d bytes", len(content))
            return content

        try:
            img = Image.open(BytesIO(content))

            # Check if conversion is needed (WebP or very large)
            needs_conversion = img.format == "WEBP"
            needs_resize = img.width > 1200 or img.height > 1200

            if not needs_conversion and not needs_resize:
                return content

            # Resize if too large (max 1200px on longest side)
            if needs_resize:
                img.thumbnail((1200, 1200), Image.Resampling.LANCZOS)

            # Convert to RGB if needed (for JPEG)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Save as JPEG
            output = BytesIO()
            img.save(output, format="JPEG", quality=85, optimize=True)
            logger.info(f"Converted image: {img.format} -> JPEG, resized: {needs_resize}")
            return output.getvalue()

        except Exception as e:
            logger.warning(f"Image conversion failed: {e}, using original")
            return content

    def _is_image_url(self, url: str) -> bool:
        """Check if URL looks like an image."""
        image_extensions = (".jpg", ".jpeg", ".png", ".gif", ".webp")
        parsed = urlparse(url)
        return parsed.path.lower().endswith(image_extensions)

    def _generate_image_filename(self, recipe_url: str, image_url: str) -> str:
        """Generate a unique filename for the recipe image.

        Always uses .jpg extension since images are converted to JPEG
        for iOS 9 compatibility.
        """
        # Create hash from URLs for uniqueness
        url_hash = hashlib.md5(f"{recipe_url}{image_url}".encode(), usedforsecurity=False).hexdigest()[:12]

        return f"recipe_{url_hash}.jpg"

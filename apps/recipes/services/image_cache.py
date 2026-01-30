"""
Search result image caching service for iOS 9 compatibility.

Implements fire-and-forget batch downloads to cache external recipe images
locally, avoiding CORS and security issues on older Safari browsers.
"""

import asyncio
import hashlib
import io
import logging
from pathlib import Path
from urllib.parse import urlparse

from asgiref.sync import sync_to_async
from curl_cffi.requests import AsyncSession
from django.core.files.base import ContentFile
from PIL import Image

from apps.recipes.services.fingerprint import BROWSER_PROFILES

logger = logging.getLogger(__name__)


class SearchImageCache:
    """
    Service for caching search result images to local storage.

    Enables iOS 9 Safari compatibility by downloading external recipe images
    to the server immediately (fire-and-forget), then returning local URLs
    that don't trigger CORS restrictions.

    Browser profiles are centralized in fingerprint.py for maintainability.
    """

    MAX_CONCURRENT = 5
    DOWNLOAD_TIMEOUT = 15

    async def cache_images(self, image_urls: list) -> None:
        """
        Fire-and-forget batch download of search result images.

        Args:
            image_urls: List of external image URLs to cache

        Returns:
            None (errors logged but not raised)
        """
        if not image_urls:
            return

        # Create semaphore to limit concurrent downloads
        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT)

        # Create download tasks
        tasks = [self._download_and_save(None, semaphore, url) for url in image_urls]

        # Run concurrently without awaiting completion
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _download_and_save(self, session: AsyncSession, semaphore: asyncio.Semaphore, url: str) -> None:
        """
        Download and cache a single image with status tracking.

        Args:
            session: AsyncSession (can be None, will create if needed)
            semaphore: Semaphore to limit concurrent downloads
            url: External image URL to cache
        """
        # Import here to avoid circular imports
        from apps.recipes.models import CachedSearchImage

        async with semaphore:
            try:
                # Get or create cache record
                cached, created = await sync_to_async(CachedSearchImage.objects.get_or_create)(
                    external_url=url, defaults={"status": CachedSearchImage.STATUS_PENDING}
                )

                # Skip if already successfully cached
                if cached.status == CachedSearchImage.STATUS_SUCCESS and cached.image:
                    return

                # Download image
                image_data = await self._fetch_image(url)
                if not image_data:
                    cached.status = CachedSearchImage.STATUS_FAILED
                    await sync_to_async(cached.save)(update_fields=["status"])
                    return

                # Convert to JPEG for iOS 9 compatibility (no WebP support)
                converted_data = self._convert_to_jpeg(image_data)
                if not converted_data:
                    cached.status = CachedSearchImage.STATUS_FAILED
                    await sync_to_async(cached.save)(update_fields=["status"])
                    return

                # Generate filename and save
                filename = self._generate_filename(url)
                cached.image = ContentFile(converted_data, name=filename)
                cached.status = CachedSearchImage.STATUS_SUCCESS
                await sync_to_async(cached.save)(update_fields=["image", "status"])
                logger.info(f"Cached image from {url}")

            except Exception as e:
                logger.error(f"Failed to cache image from {url}: {e}")
                # Try to mark as failed if we have a record
                try:
                    from apps.recipes.models import CachedSearchImage

                    cached = await sync_to_async(CachedSearchImage.objects.get)(external_url=url)
                    cached.status = CachedSearchImage.STATUS_FAILED
                    await sync_to_async(cached.save)(update_fields=["status"])
                except Exception:
                    pass

    async def _fetch_image(self, url: str) -> bytes | None:
        """
        Fetch image content from URL with browser profile fallback.

        Tries multiple browser profiles if initial request fails.
        Browser profiles are configured in fingerprint.py.

        Args:
            url: Image URL to fetch

        Returns:
            Image bytes or None if fetch fails
        """
        if not self._is_image_url(url):
            return None

        # Try each browser profile until one succeeds
        for profile in BROWSER_PROFILES:
            try:
                async with AsyncSession(impersonate=profile) as session:
                    response = await session.get(
                        url,
                        timeout=self.DOWNLOAD_TIMEOUT,
                        allow_redirects=True,
                    )

                    if response.status_code == 200:
                        content_type = response.headers.get("content-type", "")
                        if "image" in content_type:
                            return response.content

            except Exception as e:
                logger.debug(f"Failed to fetch image {url} with {profile}: {e}")
                continue

        return None

    async def get_cached_urls_batch(self, urls: list) -> dict:
        """
        Batch lookup of cached image URLs for API response.

        Args:
            urls: List of external image URLs to check

        Returns:
            Dict mapping external_url → cached_image_url (or None if not cached)
        """
        if not urls:
            return {}

        # Import here to avoid circular imports
        from apps.recipes.models import CachedSearchImage

        # Query all at once
        cached_images = await sync_to_async(
            lambda: list(
                CachedSearchImage.objects.filter(
                    external_url__in=urls,
                    status=CachedSearchImage.STATUS_SUCCESS,
                    image__isnull=False,
                ).exclude(image="")
            )
        )()

        # Build result dict
        result = {}
        for cached in cached_images:
            if cached.image:
                result[cached.external_url] = cached.image.url
                # Update access time without saving to DB unnecessarily
                # (updated via auto_now on next modification)

        return result

    def _generate_filename(self, image_url: str) -> str:
        """
        Generate unique hash-based filename for cached image.

        Args:
            image_url: External image URL

        Returns:
            Filename like 'search_{hash}.{ext}'
        """
        # Create hash from URL for uniqueness (not for security)
        url_hash = hashlib.md5(image_url.encode(), usedforsecurity=False).hexdigest()[:12]

        # Get extension from image URL
        ext = ".jpg"  # default
        if image_url:
            parsed = urlparse(image_url)
            path_ext = Path(parsed.path).suffix.lower()
            if path_ext in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
                ext = path_ext

        return f"search_{url_hash}{ext}"

    def _convert_to_jpeg(self, image_data: bytes) -> bytes | None:
        """
        Convert image to JPEG format for iOS 9 compatibility.

        iOS 9 Safari doesn't support WebP (added in Safari 14/iOS 14).
        This converts any image format (WebP, PNG, etc.) to JPEG.

        Args:
            image_data: Raw image bytes in any format

        Returns:
            JPEG image bytes, or None if conversion fails
        """
        try:
            # Open image from bytes
            img = Image.open(io.BytesIO(image_data))

            # Convert RGBA to RGB (JPEG doesn't support transparency)
            if img.mode in ("RGBA", "LA", "P"):
                # Create white background
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")

            # Save as JPEG
            output = io.BytesIO()
            img.save(output, format="JPEG", quality=92, optimize=True)
            return output.getvalue()

        except Exception as e:
            logger.error(f"Failed to convert image to JPEG: {e}")
            return None

    def _is_image_url(self, url: str) -> bool:
        """
        Check if URL looks like an image based on extension.

        Args:
            url: URL to check

        Returns:
            True if URL has image extension, False otherwise
        """
        image_extensions = (".jpg", ".jpeg", ".png", ".gif", ".webp")
        parsed = urlparse(url)
        return parsed.path.lower().endswith(image_extensions)

"""
Tests for search result image caching service.

This service is critical for iOS 9 compatibility - it downloads external images
and converts them to JPEG format (iOS 9 Safari doesn't support WebP).
"""

import io
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from PIL import Image

from apps.recipes.services.image_cache import SearchImageCache


@pytest.fixture
def image_cache():
    """Create a SearchImageCache instance."""
    return SearchImageCache()


@pytest.fixture
def sample_jpeg_bytes():
    """Create sample JPEG image bytes."""
    img = Image.new('RGB', (100, 100), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    return buffer.getvalue()


@pytest.fixture
def sample_png_bytes():
    """Create sample PNG image bytes."""
    img = Image.new('RGB', (100, 100), color='blue')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()


@pytest.fixture
def sample_rgba_png_bytes():
    """Create sample PNG with transparency."""
    img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()


@pytest.fixture
def sample_webp_bytes():
    """Create sample WebP image bytes."""
    img = Image.new('RGB', (100, 100), color='green')
    buffer = io.BytesIO()
    img.save(buffer, format='WEBP')
    return buffer.getvalue()


class TestSearchImageCacheHelpers:
    """Tests for helper methods that don't require database."""

    def test_generate_filename_creates_hash(self, image_cache):
        """Test filename generation creates unique hash-based names."""
        url1 = 'https://example.com/image1.jpg'
        url2 = 'https://example.com/image2.jpg'

        filename1 = image_cache._generate_filename(url1)
        filename2 = image_cache._generate_filename(url2)

        # Should have search_ prefix
        assert filename1.startswith('search_')
        assert filename2.startswith('search_')

        # Should have extension
        assert filename1.endswith('.jpg')
        assert filename2.endswith('.jpg')

        # Should be different for different URLs
        assert filename1 != filename2

    def test_generate_filename_preserves_extension(self, image_cache):
        """Test filename preserves original extension."""
        assert image_cache._generate_filename('https://example.com/img.jpg').endswith('.jpg')
        assert image_cache._generate_filename('https://example.com/img.jpeg').endswith('.jpeg')
        assert image_cache._generate_filename('https://example.com/img.png').endswith('.png')
        assert image_cache._generate_filename('https://example.com/img.gif').endswith('.gif')
        assert image_cache._generate_filename('https://example.com/img.webp').endswith('.webp')

    def test_generate_filename_default_extension(self, image_cache):
        """Test filename defaults to .jpg for unknown extensions."""
        assert image_cache._generate_filename('https://example.com/img').endswith('.jpg')
        assert image_cache._generate_filename('https://example.com/img.unknown').endswith('.jpg')

    def test_generate_filename_deterministic(self, image_cache):
        """Test same URL always generates same filename."""
        url = 'https://example.com/consistent.jpg'
        filename1 = image_cache._generate_filename(url)
        filename2 = image_cache._generate_filename(url)
        assert filename1 == filename2

    def test_is_image_url_accepts_valid_extensions(self, image_cache):
        """Test URL validation accepts image extensions."""
        assert image_cache._is_image_url('https://example.com/image.jpg') is True
        assert image_cache._is_image_url('https://example.com/image.jpeg') is True
        assert image_cache._is_image_url('https://example.com/image.png') is True
        assert image_cache._is_image_url('https://example.com/image.gif') is True
        assert image_cache._is_image_url('https://example.com/image.webp') is True

    def test_is_image_url_case_insensitive(self, image_cache):
        """Test URL validation is case-insensitive."""
        assert image_cache._is_image_url('https://example.com/IMAGE.JPG') is True
        assert image_cache._is_image_url('https://example.com/Image.PNG') is True
        assert image_cache._is_image_url('https://example.com/photo.WEBP') is True

    def test_is_image_url_rejects_non_images(self, image_cache):
        """Test URL validation rejects non-image extensions."""
        assert image_cache._is_image_url('https://example.com/page.html') is False
        assert image_cache._is_image_url('https://example.com/data.json') is False
        assert image_cache._is_image_url('https://example.com/script.js') is False
        assert image_cache._is_image_url('https://example.com/noextension') is False

    def test_is_image_url_handles_query_strings(self, image_cache):
        """Test URL validation handles query strings correctly."""
        # Extension before query string should be detected
        assert image_cache._is_image_url('https://example.com/image.jpg?width=100') is True
        assert image_cache._is_image_url('https://example.com/image.png?v=2') is True


class TestImageConversion:
    """Tests for image format conversion (critical for iOS 9)."""

    def test_convert_jpeg_to_jpeg(self, image_cache, sample_jpeg_bytes):
        """Test JPEG passthrough (should still work)."""
        result = image_cache._convert_to_jpeg(sample_jpeg_bytes)

        assert result is not None
        # Verify it's valid JPEG
        img = Image.open(io.BytesIO(result))
        assert img.format == 'JPEG'

    def test_convert_png_to_jpeg(self, image_cache, sample_png_bytes):
        """Test PNG to JPEG conversion."""
        result = image_cache._convert_to_jpeg(sample_png_bytes)

        assert result is not None
        img = Image.open(io.BytesIO(result))
        assert img.format == 'JPEG'
        assert img.mode == 'RGB'

    def test_convert_rgba_to_jpeg(self, image_cache, sample_rgba_png_bytes):
        """Test RGBA (transparent) PNG to JPEG conversion."""
        result = image_cache._convert_to_jpeg(sample_rgba_png_bytes)

        assert result is not None
        img = Image.open(io.BytesIO(result))
        assert img.format == 'JPEG'
        assert img.mode == 'RGB'  # Transparency should be flattened

    def test_convert_webp_to_jpeg(self, image_cache, sample_webp_bytes):
        """Test WebP to JPEG conversion (critical for iOS 9)."""
        result = image_cache._convert_to_jpeg(sample_webp_bytes)

        assert result is not None
        img = Image.open(io.BytesIO(result))
        assert img.format == 'JPEG'
        assert img.mode == 'RGB'

    def test_convert_invalid_image_returns_none(self, image_cache):
        """Test conversion of invalid image data returns None."""
        result = image_cache._convert_to_jpeg(b'not an image')
        assert result is None

    def test_convert_empty_bytes_returns_none(self, image_cache):
        """Test conversion of empty bytes returns None."""
        result = image_cache._convert_to_jpeg(b'')
        assert result is None

    def test_convert_preserves_dimensions(self, image_cache):
        """Test conversion preserves image dimensions."""
        # Create 200x150 image
        img = Image.new('RGB', (200, 150), color='purple')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')

        result = image_cache._convert_to_jpeg(buffer.getvalue())

        result_img = Image.open(io.BytesIO(result))
        assert result_img.size == (200, 150)

    def test_convert_quality_setting(self, image_cache, sample_png_bytes):
        """Test JPEG quality is set appropriately (92 for high-DPI displays)."""
        result = image_cache._convert_to_jpeg(sample_png_bytes)

        # Result should be reasonable size (quality=92 is high but not lossless)
        assert result is not None
        assert len(result) > 0
        # File should be smaller than uncompressed but still high quality
        # Exact size depends on image content, so just verify it's valid
        img = Image.open(io.BytesIO(result))
        assert img.format == 'JPEG'

    def test_convert_palette_mode_image(self, image_cache):
        """Test conversion of palette (P) mode images."""
        # Create palette mode image (like some GIFs/PNGs)
        img = Image.new('P', (100, 100))
        img.putpalette([i for i in range(256)] * 3)  # Simple grayscale palette
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')

        result = image_cache._convert_to_jpeg(buffer.getvalue())

        assert result is not None
        result_img = Image.open(io.BytesIO(result))
        assert result_img.format == 'JPEG'
        assert result_img.mode == 'RGB'

    def test_convert_grayscale_image(self, image_cache):
        """Test conversion of grayscale (L) mode images."""
        img = Image.new('L', (100, 100), color=128)
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')

        result = image_cache._convert_to_jpeg(buffer.getvalue())

        assert result is not None
        result_img = Image.open(io.BytesIO(result))
        assert result_img.format == 'JPEG'


@pytest.mark.django_db(transaction=True)
class TestImageCaching:
    """Tests for the full image caching flow."""

    @patch('apps.recipes.services.image_cache.AsyncSession')
    async def test_cache_images_empty_list(self, mock_session_class, image_cache):
        """Test caching empty list does nothing."""
        await image_cache.cache_images([])
        mock_session_class.assert_not_called()

    @patch('apps.recipes.services.image_cache.AsyncSession')
    async def test_fetch_image_success(self, mock_session_class, image_cache, sample_jpeg_bytes):
        """Test successful image fetch."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'image/jpeg'}
        mock_response.content = sample_jpeg_bytes

        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        result = await image_cache._fetch_image('https://example.com/image.jpg')

        assert result == sample_jpeg_bytes

    @patch('apps.recipes.services.image_cache.AsyncSession')
    async def test_fetch_image_non_200_returns_none(self, mock_session_class, image_cache):
        """Test fetch returns None on non-200 response."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        result = await image_cache._fetch_image('https://example.com/image.jpg')

        assert result is None

    @patch('apps.recipes.services.image_cache.AsyncSession')
    async def test_fetch_image_non_image_content_type_returns_none(
        self, mock_session_class, image_cache
    ):
        """Test fetch returns None when content-type is not image."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'text/html'}
        mock_response.content = b'<html></html>'

        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        result = await image_cache._fetch_image('https://example.com/image.jpg')

        assert result is None

    async def test_fetch_image_non_image_url_returns_none(self, image_cache):
        """Test fetch returns None for non-image URLs."""
        result = await image_cache._fetch_image('https://example.com/page.html')
        assert result is None

    @patch('apps.recipes.services.image_cache.AsyncSession')
    async def test_fetch_image_tries_multiple_profiles_on_failure(
        self, mock_session_class, image_cache, sample_jpeg_bytes
    ):
        """Test fetch tries multiple browser profiles if first fails."""
        call_count = 0

        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Connection failed")
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {'content-type': 'image/jpeg'}
            mock_response.content = sample_jpeg_bytes
            return mock_response

        mock_session = MagicMock()
        mock_session.get = AsyncMock(side_effect=side_effect)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        result = await image_cache._fetch_image('https://example.com/image.jpg')

        # Should have tried multiple profiles
        assert call_count >= 3
        assert result == sample_jpeg_bytes

    @patch('apps.recipes.services.image_cache.AsyncSession')
    async def test_download_and_save_creates_cached_record(
        self, mock_session_class, image_cache, sample_jpeg_bytes, db
    ):
        """Test download creates CachedSearchImage record."""
        import asyncio
        from asgiref.sync import sync_to_async
        from apps.recipes.models import CachedSearchImage

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'image/jpeg'}
        mock_response.content = sample_jpeg_bytes

        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        semaphore = asyncio.Semaphore(5)
        url = 'https://example.com/test-image-create.jpg'

        await image_cache._download_and_save(None, semaphore, url)

        # Verify record was created (use sync_to_async for DB access)
        @sync_to_async
        def verify_record():
            cached = CachedSearchImage.objects.get(external_url=url)
            assert cached.status == CachedSearchImage.STATUS_SUCCESS
            assert cached.image is not None
            assert cached.image.name.endswith('.jpg')

        await verify_record()

    @patch('apps.recipes.services.image_cache.AsyncSession')
    async def test_download_and_save_marks_failed_on_error(
        self, mock_session_class, image_cache, db
    ):
        """Test download marks record as failed on error."""
        import asyncio
        from asgiref.sync import sync_to_async
        from apps.recipes.models import CachedSearchImage

        mock_session = MagicMock()
        mock_session.get = AsyncMock(side_effect=Exception("Network error"))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        semaphore = asyncio.Semaphore(5)
        url = 'https://example.com/failing-image-mark.jpg'

        # Create the record first (simulating get_or_create)
        @sync_to_async
        def create_record():
            return CachedSearchImage.objects.create(
                external_url=url,
                status=CachedSearchImage.STATUS_PENDING,
            )

        await create_record()

        await image_cache._download_and_save(None, semaphore, url)

        # Verify record was marked as failed
        @sync_to_async
        def verify_failed():
            cached = CachedSearchImage.objects.get(external_url=url)
            assert cached.status == CachedSearchImage.STATUS_FAILED

        await verify_failed()

    @patch('apps.recipes.services.image_cache.AsyncSession')
    async def test_download_and_save_skips_already_cached(
        self, mock_session_class, image_cache, sample_jpeg_bytes, db
    ):
        """Test download skips images already successfully cached."""
        import asyncio
        from asgiref.sync import sync_to_async
        from apps.recipes.models import CachedSearchImage
        from django.core.files.base import ContentFile

        url = 'https://example.com/already-cached-skip.jpg'

        # Create already-cached record
        @sync_to_async
        def create_cached_record():
            cached = CachedSearchImage.objects.create(
                external_url=url,
                status=CachedSearchImage.STATUS_SUCCESS,
            )
            cached.image.save('existing.jpg', ContentFile(sample_jpeg_bytes))
            return cached

        await create_cached_record()

        semaphore = asyncio.Semaphore(5)

        await image_cache._download_and_save(None, semaphore, url)

        # Session should not have been used
        mock_session_class.assert_not_called()

    @patch('apps.recipes.services.image_cache.AsyncSession')
    async def test_download_and_save_retries_failed_images(
        self, mock_session_class, image_cache, sample_jpeg_bytes, db
    ):
        """Test download retries previously failed images."""
        import asyncio
        from asgiref.sync import sync_to_async
        from apps.recipes.models import CachedSearchImage

        url = 'https://example.com/retry-image-test.jpg'

        # Create previously failed record
        @sync_to_async
        def create_failed_record():
            return CachedSearchImage.objects.create(
                external_url=url,
                status=CachedSearchImage.STATUS_FAILED,
            )

        await create_failed_record()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'image/jpeg'}
        mock_response.content = sample_jpeg_bytes

        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        semaphore = asyncio.Semaphore(5)

        await image_cache._download_and_save(None, semaphore, url)

        # Should now be successful
        @sync_to_async
        def verify_success():
            cached = CachedSearchImage.objects.get(external_url=url)
            assert cached.status == CachedSearchImage.STATUS_SUCCESS

        await verify_success()


@pytest.mark.django_db(transaction=True)
class TestBatchCachedUrlLookup:
    """Tests for batch cached URL lookup."""

    async def test_get_cached_urls_batch_empty_list(self, image_cache):
        """Test batch lookup with empty list returns empty dict."""
        result = await image_cache.get_cached_urls_batch([])
        assert result == {}

    async def test_get_cached_urls_batch_no_matches(self, image_cache, db):
        """Test batch lookup with no cached images returns empty dict."""
        urls = [
            'https://example.com/uncached1.jpg',
            'https://example.com/uncached2.jpg',
        ]
        result = await image_cache.get_cached_urls_batch(urls)
        assert result == {}

    async def test_get_cached_urls_batch_returns_cached(
        self, image_cache, sample_jpeg_bytes, db
    ):
        """Test batch lookup returns URLs for cached images."""
        from asgiref.sync import sync_to_async
        from apps.recipes.models import CachedSearchImage
        from django.core.files.base import ContentFile

        url1 = 'https://example.com/batch-cached1.jpg'
        url2 = 'https://example.com/batch-cached2.jpg'
        url3 = 'https://example.com/batch-uncached.jpg'

        # Create cached records
        @sync_to_async
        def create_records():
            cached1 = CachedSearchImage.objects.create(
                external_url=url1,
                status=CachedSearchImage.STATUS_SUCCESS,
            )
            cached1.image.save('batch-cached1.jpg', ContentFile(sample_jpeg_bytes))

            cached2 = CachedSearchImage.objects.create(
                external_url=url2,
                status=CachedSearchImage.STATUS_SUCCESS,
            )
            cached2.image.save('batch-cached2.jpg', ContentFile(sample_jpeg_bytes))

        await create_records()

        result = await image_cache.get_cached_urls_batch([url1, url2, url3])

        assert url1 in result
        assert url2 in result
        assert url3 not in result
        assert '/media/search_images/' in result[url1]
        assert '/media/search_images/' in result[url2]

    async def test_get_cached_urls_batch_excludes_pending(
        self, image_cache, db
    ):
        """Test batch lookup excludes pending images."""
        from asgiref.sync import sync_to_async
        from apps.recipes.models import CachedSearchImage

        url = 'https://example.com/batch-pending.jpg'

        @sync_to_async
        def create_pending():
            CachedSearchImage.objects.create(
                external_url=url,
                status=CachedSearchImage.STATUS_PENDING,
            )

        await create_pending()

        result = await image_cache.get_cached_urls_batch([url])
        assert url not in result

    async def test_get_cached_urls_batch_excludes_failed(
        self, image_cache, db
    ):
        """Test batch lookup excludes failed images."""
        from asgiref.sync import sync_to_async
        from apps.recipes.models import CachedSearchImage

        url = 'https://example.com/batch-failed.jpg'

        @sync_to_async
        def create_failed():
            CachedSearchImage.objects.create(
                external_url=url,
                status=CachedSearchImage.STATUS_FAILED,
            )

        await create_failed()

        result = await image_cache.get_cached_urls_batch([url])
        assert url not in result

    async def test_get_cached_urls_batch_excludes_empty_images(
        self, image_cache, db
    ):
        """Test batch lookup excludes records with empty image field."""
        from asgiref.sync import sync_to_async
        from apps.recipes.models import CachedSearchImage

        url = 'https://example.com/batch-empty-image.jpg'

        @sync_to_async
        def create_empty_image():
            CachedSearchImage.objects.create(
                external_url=url,
                status=CachedSearchImage.STATUS_SUCCESS,
                # image field is empty
            )

        await create_empty_image()

        result = await image_cache.get_cached_urls_batch([url])
        assert url not in result


@pytest.mark.django_db
class TestCachedSearchImageModel:
    """Tests for CachedSearchImage model behavior."""

    def test_model_str_representation(self, db):
        """Test model string representation."""
        from apps.recipes.models import CachedSearchImage

        cached = CachedSearchImage.objects.create(
            external_url='https://example.com/image.jpg',
        )
        assert 'example.com/image.jpg' in str(cached)

    def test_model_status_choices(self, db):
        """Test model status field choices."""
        from apps.recipes.models import CachedSearchImage

        # Pending (default)
        cached = CachedSearchImage.objects.create(
            external_url='https://example.com/1.jpg',
        )
        assert cached.status == CachedSearchImage.STATUS_PENDING

        # Success
        cached.status = CachedSearchImage.STATUS_SUCCESS
        cached.save()
        assert cached.status == 'success'

        # Failed
        cached.status = CachedSearchImage.STATUS_FAILED
        cached.save()
        assert cached.status == 'failed'

    def test_model_external_url_unique(self, db):
        """Test external_url is unique."""
        from apps.recipes.models import CachedSearchImage
        from django.db import IntegrityError

        CachedSearchImage.objects.create(
            external_url='https://example.com/unique.jpg',
        )

        with pytest.raises(IntegrityError):
            CachedSearchImage.objects.create(
                external_url='https://example.com/unique.jpg',
            )

    def test_model_timestamps_auto_set(self, db):
        """Test created_at and last_accessed_at are auto-set."""
        from apps.recipes.models import CachedSearchImage
        from django.utils import timezone

        before = timezone.now()
        cached = CachedSearchImage.objects.create(
            external_url='https://example.com/timestamps.jpg',
        )
        after = timezone.now()

        assert before <= cached.created_at <= after
        assert before <= cached.last_accessed_at <= after


class TestConcurrencyLimits:
    """Tests for concurrency control."""

    def test_max_concurrent_default(self, image_cache):
        """Test default max concurrent downloads."""
        assert image_cache.MAX_CONCURRENT == 5

    def test_download_timeout_default(self, image_cache):
        """Test default download timeout."""
        assert image_cache.DOWNLOAD_TIMEOUT == 15

    @patch('apps.recipes.services.image_cache.AsyncSession')
    async def test_semaphore_limits_concurrency(self, mock_session_class, image_cache):
        """Test semaphore limits concurrent downloads."""
        import asyncio

        active_count = 0
        max_active = 0

        async def track_concurrency(*args, **kwargs):
            nonlocal active_count, max_active
            active_count += 1
            max_active = max(max_active, active_count)
            await asyncio.sleep(0.1)  # Simulate download time
            active_count -= 1

            mock_response = MagicMock()
            mock_response.status_code = 404  # Fail fast
            return mock_response

        mock_session = MagicMock()
        mock_session.get = AsyncMock(side_effect=track_concurrency)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        # Try to cache 10 images (more than MAX_CONCURRENT)
        urls = [f'https://example.com/img{i}.jpg' for i in range(10)]

        # Patch _is_image_url to always return True
        with patch.object(image_cache, '_is_image_url', return_value=True):
            await image_cache.cache_images(urls)

        # Max concurrent should not exceed limit
        assert max_active <= image_cache.MAX_CONCURRENT

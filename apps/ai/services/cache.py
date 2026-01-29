"""AI response caching utilities using Django cache framework."""

import hashlib
import json
import logging
from functools import wraps
from typing import Callable, Optional

from django.core.cache import cache

logger = logging.getLogger(__name__)

# Cache timeout constants (in seconds)
CACHE_TIMEOUT_SHORT = 60 * 30  # 30 minutes - for timer names
CACHE_TIMEOUT_MEDIUM = 60 * 60 * 4  # 4 hours - for remix suggestions


def _make_cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate a deterministic cache key from function arguments.

    Args:
        prefix: A prefix for the cache key (typically function name).
        *args: Positional arguments to include in key.
        **kwargs: Keyword arguments to include in key.

    Returns:
        A cache key string like 'ai:prefix:hash'.
    """
    # Create a deterministic representation of the arguments
    key_data = {
        'args': list(args),
        'kwargs': sorted(kwargs.items()),
    }
    key_json = json.dumps(key_data, sort_keys=True, default=str)

    # Hash to keep key length manageable
    key_hash = hashlib.sha256(key_json.encode()).hexdigest()[:16]

    return f'ai:{prefix}:{key_hash}'


def cache_ai_response(
    prefix: str,
    timeout: int = CACHE_TIMEOUT_MEDIUM,
    key_args: Optional[list[int]] = None,
    key_kwargs: Optional[list[str]] = None,
) -> Callable:
    """Decorator to cache AI service responses.

    Args:
        prefix: Cache key prefix (typically function name).
        timeout: Cache timeout in seconds.
        key_args: Indices of positional args to include in cache key (default: all).
        key_kwargs: Names of kwargs to include in cache key (default: all).

    Returns:
        Decorated function that caches its results.

    Example:
        @cache_ai_response('timer_name', timeout=1800)
        def generate_timer_name(step_text: str, duration_minutes: int) -> dict:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key from selected arguments
            if key_args is not None:
                cache_args = tuple(args[i] for i in key_args if i < len(args))
            else:
                cache_args = args

            if key_kwargs is not None:
                cache_kwargs = {k: v for k, v in kwargs.items() if k in key_kwargs}
            else:
                cache_kwargs = kwargs

            cache_key = _make_cache_key(prefix, *cache_args, **cache_kwargs)

            # Check cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f'Cache hit for {prefix}: {cache_key}')
                return cached_result

            # Call the actual function
            result = func(*args, **kwargs)

            # Cache the result
            cache.set(cache_key, result, timeout)
            logger.debug(f'Cached {prefix} result: {cache_key}')

            return result
        return wrapper
    return decorator


def invalidate_ai_cache(prefix: str, *args, **kwargs) -> bool:
    """Invalidate a specific AI cache entry.

    Args:
        prefix: Cache key prefix.
        *args: Arguments used in the original cache key.
        **kwargs: Keyword arguments used in the original cache key.

    Returns:
        True if a key was deleted, False otherwise.
    """
    cache_key = _make_cache_key(prefix, *args, **kwargs)
    return cache.delete(cache_key)

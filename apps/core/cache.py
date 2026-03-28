"""PostgreSQL-safe database cache backend.

Django's built-in DatabaseCache uses a non-atomic read-then-write pattern
for set(), which causes IntegrityError on concurrent inserts (duplicate key).
This backend catches those errors and retries as an update.
"""

from django.core.cache.backends.db import DatabaseCache
from django.db import IntegrityError


class PostgreSafeDatabaseCache(DatabaseCache):
    """DatabaseCache that handles concurrent INSERT races gracefully."""

    def _base_set(self, mode, key, value, timeout=None):
        try:
            return super()._base_set(mode, key, value, timeout)
        except IntegrityError:
            # Another worker inserted the same key between our SELECT and INSERT.
            # Retry — the second attempt will see the existing row and UPDATE it.
            return super()._base_set(mode, key, value, timeout)

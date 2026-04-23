"""PostgreSQL-safe database cache backend.

Django's built-in DatabaseCache has two concurrency issues on Postgres:

1. ``_base_set`` does SELECT-then-INSERT, which races into IntegrityError
   on concurrent inserts of the same key.
2. ``incr`` / ``decr`` do SELECT-then-UPDATE on the raw row, which races
   into lost updates: N concurrent incrs on the same key can settle at
   fewer than N because each reads the same pre-value and each writes the
   same post-value.

This backend wraps set in a savepoint + retry (fix #1) and wraps incr/decr
in a per-key advisory lock (fix #2) so quota counters and other
incr-based counters remain accurate under load.
"""

import hashlib

from django.core.cache.backends.db import DatabaseCache
from django.db import IntegrityError, connections, router, transaction


class PostgreSafeDatabaseCache(DatabaseCache):
    """DatabaseCache with Postgres-safe set/incr semantics."""

    def _base_set(self, mode, key, value, timeout=None):
        try:
            with transaction.atomic():
                return super()._base_set(mode, key, value, timeout)
        except IntegrityError:
            # Another worker inserted the same key between our SELECT and INSERT.
            # The savepoint rolled back the failed INSERT, so the transaction is
            # clean.  Retry — the second attempt will see the existing row and
            # UPDATE it.
            return super()._base_set(mode, key, value, timeout)

    def _advisory_lock_id(self, full_key: str) -> int:
        """Stable non-negative 32-bit int from a cache key for pg_advisory_xact_lock.

        blake2b with digest_size=4 gives exactly 4 bytes; non-cryptographic use
        (we just need a deterministic mapping from key-string to int32).
        """
        digest = hashlib.blake2b(full_key.encode("utf-8"), digest_size=4).digest()
        return int.from_bytes(digest, "big", signed=False) & 0x7FFFFFFF

    def incr(self, key, delta=1, version=None):
        """Atomic per-key increment using a transaction-scoped advisory lock.

        Django's DatabaseCache.incr reads the row, computes the new value in
        Python, then UPDATEs — racey across connections. Advisory-lock
        serialisation makes concurrent incrs on the same key linearisable
        while allowing parallelism across different keys.
        """
        full_key = self.make_key(key, version=version)
        lock_id = self._advisory_lock_id(full_key)
        db = router.db_for_write(self.cache_model_class)
        with transaction.atomic(using=db):
            with connections[db].cursor() as cursor:
                cursor.execute("SELECT pg_advisory_xact_lock(%s)", [lock_id])
            return super().incr(key, delta=delta, version=version)

    def decr(self, key, delta=1, version=None):
        """Atomic decrement — same story as incr."""
        return self.incr(key, delta=-delta, version=version)

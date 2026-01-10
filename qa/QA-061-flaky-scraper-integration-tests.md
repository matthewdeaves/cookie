# QA-061: Flaky Scraper Integration Tests in CI

## Status
**OPEN** - Intermittent CI failures

## Phase
Testing Infrastructure

## Issue

The scraper integration tests (`tests/test_scraper.py::TestScraperIntegration`) intermittently fail in CI with database flush errors:

```
ERROR tests/test_scraper.py::TestScraperIntegration::test_scrape_url_creates_recipe
ERROR tests/test_scraper.py::TestScraperIntegration::test_scrape_url_with_image_download

django.core.management.base.CommandError: Database file:memorydb_default?mode=memory&cache=shared couldn't be flushed.
```

**Failure rate:** ~40% of recent CI runs on master (2 failures out of 5 runs).

---

## Root Cause Analysis

### The Problem

The `TestScraperIntegration` tests are **async tests** that use the `db` fixture:

```python
class TestScraperIntegration:
    @pytest.fixture
    def test_profile(self, db):  # Uses db fixture
        from apps.profiles.models import Profile
        return Profile.objects.create(name='Test User', avatar_color='#d97850')

    async def test_scrape_url_creates_recipe(self, ...):  # Async test
        ...
```

### Why This Fails

1. **Async tests don't properly isolate database transactions** with pytest-django's default `db` fixture.

2. When using async with pytest-django, the test runs against a **different DB connection** than the fixture setup/teardown, causing transaction isolation to break.

3. Django's `TransactionTestCase` (used for cleanup) calls `flush` command during teardown, which fails when the database state is inconsistent between async contexts.

4. The SQLite in-memory database (`file:memorydb_default?mode=memory&cache=shared`) is particularly susceptible because the shared cache can have state conflicts between connections.

---

## Research

### Known Issues

- [pytest-asyncio #226](https://github.com/pytest-dev/pytest-asyncio/issues/226): "Database is not properly rolled back after async tests" - confirmed issue with pytest-django and async tests.

- [Django #32409](https://code.djangoproject.com/ticket/32409): "TestCase async tests are not transaction-aware" - Django core issue.

- [pytest-django #580](https://github.com/pytest-dev/pytest-django/issues/580): "Database transactions with asyncio" - discussion of the underlying problem.

### Key Finding

From the pytest-asyncio issue:
> "When using pytest-django's `pytest.mark.django_db` marker in conjunction with `pytest.mark.asyncio`, any writes to the database are not rolled back when the test completes and affect subsequent tests."

From pytest-django docs:
> "When using async with `database_sync_to_async`, transactions don't seem to work. As a result all changes to the test database will be kept."

### SQLite Flush Issue

From [Django database flush debugging](https://eoinnoble.com/posts/database-couldnt-be-flushed/):
> "TransactionTestCase._fixture_teardown calls the flush management command, which calls sql_flush to build the SQL for the teardown. That builds a list of table names with connection.introspection.django_table_names."

When async tests leave the database in an inconsistent state, the flush command can fail.

---

## Solution Options

### Option 1: Use `transaction=True` marker (Recommended)

Mark async tests to use transactional database access:

```python
import pytest

@pytest.mark.django_db(transaction=True)
class TestScraperIntegration:
    ...
```

**Pros:**
- Proper transaction isolation for async tests
- Matches Django's TransactionTestCase behavior

**Cons:**
- Slower tests (database flush between tests)

### Option 2: Use `serialized_rollback=True`

```python
@pytest.mark.django_db(transaction=True, serialized_rollback=True)
class TestScraperIntegration:
    ...
```

**Pros:**
- Preserves database state between tests
- Most reliable isolation

**Cons:**
- ~3x slower (serializes/deserializes DB state)

### Option 3: Convert to sync tests with `sync_to_async`

Wrap async code in sync test functions:

```python
from asgiref.sync import async_to_sync

def test_scrape_url_creates_recipe(self, ...):
    result = async_to_sync(scraper.scrape_url)(url, profile)
    ...
```

**Pros:**
- Works with standard `db` fixture
- No transaction mode needed

**Cons:**
- Less idiomatic for async code
- May hide async-specific bugs

### Option 4: Use pytest-asyncio with Django's async test client

Use Django 4.1+ async test utilities properly integrated.

---

## Recommendation

**Option 1** - Add `@pytest.mark.django_db(transaction=True)` to the `TestScraperIntegration` class.

This is the standard fix for async tests with pytest-django and directly addresses the root cause.

---

## Priority

**Medium** - Causes intermittent CI failures but doesn't block development. Tests pass on retry.

## Affected Components

- `tests/test_scraper.py` - Scraper integration tests
- `pytest.ini` - pytest configuration

---

## Implementation Plan

### Step 1: Add transaction marker

**File:** `tests/test_scraper.py`

```python
import pytest

@pytest.mark.django_db(transaction=True)
class TestScraperIntegration:
    """Integration tests for recipe scraper."""
    ...
```

### Step 2: Remove redundant db fixture usage

The `transaction=True` marker handles database access, so the `db` fixture in `test_profile` may be redundant:

```python
@pytest.fixture
def test_profile(self):  # Remove db parameter
    from apps.profiles.models import Profile
    return Profile.objects.create(name='Test User', avatar_color='#d97850')
```

### Step 3: Verify fix

Run the integration tests multiple times to confirm stability:

```bash
for i in {1..10}; do pytest tests/test_scraper.py::TestScraperIntegration -v; done
```

### Step 4: Monitor CI

Watch subsequent CI runs to confirm the flakiness is resolved.

---

## References

- [pytest-asyncio #226 - Database rollback issue](https://github.com/pytest-dev/pytest-asyncio/issues/226)
- [Django #32409 - Async transaction awareness](https://code.djangoproject.com/ticket/32409)
- [pytest-django #580 - Database transactions with asyncio](https://github.com/pytest-dev/pytest-django/issues/580)
- [pytest-django database docs](https://pytest-django.readthedocs.io/en/latest/database.html)
- [Django database flush debugging](https://eoinnoble.com/posts/database-couldnt-be-flushed/)

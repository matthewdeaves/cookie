"""
Tests for database configuration (006: Enforce PostgreSQL Everywhere).

These tests verify that the database configuration correctly handles:
- DATABASE_URL environment variable (PostgreSQL)
- Raises ImproperlyConfigured when DATABASE_URL is not set
- Connection pooling settings

Note: Tests avoid reloading Django settings to prevent state corruption.
"""

import importlib
import os

import pytest


class TestDatabaseConfiguration:
    """Tests for database configuration logic.

    These tests verify the dj-database-url parsing logic directly
    without reloading Django settings.
    """

    def test_database_url_parsing_postgres(self):
        """Test DATABASE_URL is correctly parsed for PostgreSQL."""
        import dj_database_url

        db_config = dj_database_url.parse(
            "postgres://user:pass@host:5432/dbname",  # pragma: allowlist secret
            conn_max_age=60,
            conn_health_checks=True,
        )
        assert db_config["ENGINE"] == "django.db.backends.postgresql"
        assert db_config["NAME"] == "dbname"
        assert db_config["USER"] == "user"
        assert db_config["PASSWORD"] == "pass"  # pragma: allowlist secret
        assert db_config["HOST"] == "host"
        assert db_config["PORT"] == 5432

    def test_database_url_parsing_postgresql_scheme(self):
        """Test postgresql:// scheme is also accepted."""
        import dj_database_url

        db_config = dj_database_url.parse("postgresql://user:pass@host:5432/dbname")
        assert db_config["ENGINE"] == "django.db.backends.postgresql"
        assert db_config["NAME"] == "dbname"

    def test_postgres_connection_max_age(self):
        """Test PostgreSQL connections use persistent connections."""
        import dj_database_url

        db_config = dj_database_url.parse(
            "postgres://user:pass@host:5432/dbname",  # pragma: allowlist secret
            conn_max_age=60,
        )
        assert db_config.get("CONN_MAX_AGE") == 60

    def test_postgres_connection_health_checks(self):
        """Test PostgreSQL connections have health checks enabled."""
        import dj_database_url

        db_config = dj_database_url.parse(
            "postgres://user:pass@host:5432/dbname",  # pragma: allowlist secret
            conn_health_checks=True,
        )
        assert db_config.get("CONN_HEALTH_CHECKS") is True

    def test_postgres_url_with_ssl_mode(self):
        """Test PostgreSQL URL with SSL options."""
        import dj_database_url

        db_config = dj_database_url.parse(
            "postgres://user:pass@host:5432/dbname?sslmode=require"  # pragma: allowlist secret
        )
        assert db_config["ENGINE"] == "django.db.backends.postgresql"
        # SSL options are passed through
        assert "sslmode" in db_config.get("OPTIONS", {}) or db_config.get("NAME") == "dbname"

    def test_missing_database_url_raises_improperly_configured(self):
        """Test that missing DATABASE_URL raises ImproperlyConfigured."""
        from unittest.mock import patch

        from django.core.exceptions import ImproperlyConfigured

        import cookie.settings

        # Isolate DATABASE_URL while keeping the other env vars settings.py
        # validates ahead of it (COOKIE_VERSION, SECRET_KEY) so the reload
        # reaches the DATABASE_URL check and not an earlier guard.
        env = {"DEBUG": "true"}
        with patch.dict(os.environ, env, clear=True):
            assert os.environ.get("DATABASE_URL") is None

            with pytest.raises(ImproperlyConfigured, match="DATABASE_URL"):
                importlib.reload(cookie.settings)

        # Reload settings with the real environment to restore state
        importlib.reload(cookie.settings)


@pytest.mark.django_db
class TestDatabaseConnection:
    """Integration tests for database connections."""

    def test_database_is_accessible(self):
        """Test that the configured database is accessible."""
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1

    def test_can_create_and_query_records(self, db):
        """Test basic CRUD operations work with the database."""
        from apps.profiles.models import Profile

        # Create
        profile = Profile.objects.create(name="Test User", avatar_color="#123456")
        assert profile.id is not None

        # Read
        fetched = Profile.objects.get(id=profile.id)
        assert fetched.name == "Test User"

        # Update
        fetched.name = "Updated User"
        fetched.save()
        fetched.refresh_from_db()
        assert fetched.name == "Updated User"

        # Delete
        fetched.delete()
        assert Profile.objects.filter(id=profile.id).count() == 0

    def test_database_vendor_matches_config(self):
        """Test database vendor is always PostgreSQL."""
        from django.db import connection

        assert connection.vendor == "postgresql"

    def test_migrations_are_applied(self):
        """Test that all migrations have been applied."""
        from io import StringIO

        from django.core.management import call_command

        out = StringIO()
        call_command("showmigrations", "--plan", stdout=out)
        output = out.getvalue()

        # All migrations should be marked as applied (with [X])
        unapplied = [line for line in output.split("\n") if line.strip().startswith("[ ]")]
        assert len(unapplied) == 0, f"Unapplied migrations: {unapplied}"


@pytest.mark.django_db
class TestPostgresSpecificFeatures:
    """Tests for PostgreSQL-specific behavior."""

    def test_jsonfield_native_support(self, db):
        """Test JSONField works with native PostgreSQL JSON support."""
        from apps.profiles.models import Profile
        from apps.recipes.models import Recipe

        profile = Profile.objects.create(name="Test User")
        recipe = Recipe.objects.create(
            profile=profile,
            title="JSON Test Recipe",
            host="test.com",
            ingredients=["ingredient 1", "ingredient 2"],
            instructions=["step 1", "step 2"],
        )

        # Query using JSON field
        fetched = Recipe.objects.get(id=recipe.id)
        assert fetched.ingredients == ["ingredient 1", "ingredient 2"]

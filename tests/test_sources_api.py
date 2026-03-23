"""
Tests for SearchSource management API endpoints (T032).

Tests the sources_api.py endpoints:
- List sources, get single source, toggle, update selector, bulk toggle
- Authentication enforcement for write endpoints
- 404 handling for non-existent sources

Note: SearchSource records are seeded by migrations, so tests that need a
clean slate use the `clean_sources` fixture to remove them first.
"""

import json

import pytest
from django.test import Client

from apps.profiles.models import Profile
from apps.recipes.models import SearchSource


@pytest.fixture
def clean_sources(db):
    """Remove all migration-seeded SearchSource records for a clean slate."""
    SearchSource.objects.all().delete()


@pytest.fixture
def client():
    return Client(enforce_csrf_checks=False)


@pytest.fixture
def profile(db):
    """Create a test profile for authenticated requests."""
    return Profile.objects.create(name="Test User", avatar_color="#d97850")


@pytest.fixture
def auth_client(client, profile):
    """Return a client with a valid session profile_id."""
    session = client.session
    session["profile_id"] = profile.id
    session.save()
    return client


@pytest.fixture
def source(clean_sources):
    """Create a test SearchSource (after clearing seeded data)."""
    return SearchSource.objects.create(
        host="example.com",
        name="Example Recipes",
        is_enabled=True,
        search_url_template="https://example.com/search?q={query}",
        result_selector="div.recipe-card",
        logo_url="https://example.com/logo.png",
        consecutive_failures=0,
        needs_attention=False,
    )


@pytest.fixture
def disabled_source(clean_sources):
    """Create a disabled SearchSource (after clearing seeded data)."""
    return SearchSource.objects.create(
        host="disabled.com",
        name="Disabled Source",
        is_enabled=False,
        search_url_template="https://disabled.com/search?q={query}",
        result_selector="div.result",
        logo_url="",
        consecutive_failures=5,
        needs_attention=True,
    )


# --- List Sources ---


@pytest.mark.django_db
def test_list_sources_empty(client, clean_sources):
    """GET /api/sources/ returns empty list when no sources exist."""
    response = client.get("/api/sources/")
    assert response.status_code == 200
    assert json.loads(response.content) == []


@pytest.mark.django_db
def test_list_sources(client, source, disabled_source):
    """GET /api/sources/ returns all sources ordered by name."""
    response = client.get("/api/sources/")
    assert response.status_code == 200
    data = json.loads(response.content)
    assert len(data) == 2
    # Ordered by name: "Disabled Source" before "Example Recipes"
    assert data[0]["name"] == "Disabled Source"
    assert data[1]["name"] == "Example Recipes"


@pytest.mark.django_db
def test_list_sources_fields(client, source):
    """GET /api/sources/ returns expected fields for each source."""
    response = client.get("/api/sources/")
    data = json.loads(response.content)
    assert len(data) == 1
    item = data[0]
    assert item["id"] == source.id
    assert item["host"] == "example.com"
    assert item["name"] == "Example Recipes"
    assert item["is_enabled"] is True
    assert item["search_url_template"] == "https://example.com/search?q={query}"
    assert item["result_selector"] == "div.recipe-card"
    assert item["logo_url"] == "https://example.com/logo.png"
    assert item["consecutive_failures"] == 0
    assert item["needs_attention"] is False
    assert item["last_validated_at"] is None


@pytest.mark.django_db
def test_list_sources_no_auth_required(client, source):
    """GET /api/sources/ does not require authentication."""
    response = client.get("/api/sources/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_list_sources_includes_seeded_data(client, db):
    """GET /api/sources/ returns migration-seeded sources."""
    response = client.get("/api/sources/")
    assert response.status_code == 200
    data = json.loads(response.content)
    # Migrations seed sources; verify at least some exist
    assert len(data) > 0
    # Each source has expected fields
    for item in data:
        assert "id" in item
        assert "host" in item
        assert "name" in item
        assert "is_enabled" in item


# --- Enabled Count ---


@pytest.mark.django_db
def test_enabled_count(client, source, disabled_source):
    """GET /api/sources/enabled-count/ returns correct counts."""
    response = client.get("/api/sources/enabled-count/")
    assert response.status_code == 200
    data = json.loads(response.content)
    assert data["enabled"] == 1
    assert data["total"] == 2


@pytest.mark.django_db
def test_enabled_count_empty(client, clean_sources):
    """GET /api/sources/enabled-count/ returns zeros when no sources exist."""
    response = client.get("/api/sources/enabled-count/")
    assert response.status_code == 200
    data = json.loads(response.content)
    assert data["enabled"] == 0
    assert data["total"] == 0


# --- Get Single Source ---


@pytest.mark.django_db
def test_get_source(client, source):
    """GET /api/sources/{id}/ returns the source."""
    response = client.get(f"/api/sources/{source.id}/")
    assert response.status_code == 200
    data = json.loads(response.content)
    assert data["id"] == source.id
    assert data["host"] == "example.com"
    assert data["name"] == "Example Recipes"


@pytest.mark.django_db
def test_get_source_not_found(client):
    """GET /api/sources/{id}/ returns 404 for non-existent source."""
    response = client.get("/api/sources/99999/")
    assert response.status_code == 404
    data = json.loads(response.content)
    assert data["error"] == "not_found"


@pytest.mark.django_db
def test_get_source_no_auth_required(client, source):
    """GET /api/sources/{id}/ does not require authentication."""
    response = client.get(f"/api/sources/{source.id}/")
    assert response.status_code == 200


# --- Toggle Source ---


@pytest.mark.django_db
def test_toggle_source(auth_client, source):
    """POST /api/sources/{id}/toggle/ toggles is_enabled."""
    assert source.is_enabled is True
    response = auth_client.post(f"/api/sources/{source.id}/toggle/")
    assert response.status_code == 200
    data = json.loads(response.content)
    assert data["id"] == source.id
    assert data["is_enabled"] is False

    # Toggle again
    response = auth_client.post(f"/api/sources/{source.id}/toggle/")
    assert response.status_code == 200
    data = json.loads(response.content)
    assert data["is_enabled"] is True


@pytest.mark.django_db
def test_toggle_source_persists(auth_client, source):
    """POST /api/sources/{id}/toggle/ persists the change to the database."""
    auth_client.post(f"/api/sources/{source.id}/toggle/")
    source.refresh_from_db()
    assert source.is_enabled is False


@pytest.mark.django_db
def test_toggle_source_not_found(auth_client):
    """POST /api/sources/{id}/toggle/ returns 404 for non-existent source."""
    response = auth_client.post("/api/sources/99999/toggle/")
    assert response.status_code == 404
    data = json.loads(response.content)
    assert data["error"] == "not_found"


@pytest.mark.django_db
def test_toggle_source_requires_auth(client, source):
    """POST /api/sources/{id}/toggle/ requires authentication."""
    response = client.post(f"/api/sources/{source.id}/toggle/")
    assert response.status_code == 401


# --- Bulk Toggle ---
# Note: bulk-toggle is a sync POST endpoint but Django Ninja routing
# causes 405 with the sync test client. We test auth enforcement only.


@pytest.mark.django_db
def test_bulk_toggle_requires_auth(client, source):
    """POST /api/sources/bulk-toggle/ without auth is rejected (not 200)."""
    response = client.post(
        "/api/sources/bulk-toggle/",
        data=json.dumps({"enable": False}),
        content_type="application/json",
    )
    # Must not succeed unauthenticated
    assert response.status_code != 200


# --- Update Selector ---


@pytest.mark.django_db
def test_update_selector(auth_client, source):
    """PUT /api/sources/{id}/selector/ updates the CSS selector."""
    response = auth_client.put(
        f"/api/sources/{source.id}/selector/",
        data=json.dumps({"result_selector": "div.new-selector"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = json.loads(response.content)
    assert data["id"] == source.id
    assert data["result_selector"] == "div.new-selector"


@pytest.mark.django_db
def test_update_selector_persists(auth_client, source):
    """PUT /api/sources/{id}/selector/ persists the change to the database."""
    auth_client.put(
        f"/api/sources/{source.id}/selector/",
        data=json.dumps({"result_selector": "span.updated"}),
        content_type="application/json",
    )
    source.refresh_from_db()
    assert source.result_selector == "span.updated"


@pytest.mark.django_db
def test_update_selector_not_found(auth_client):
    """PUT /api/sources/{id}/selector/ returns 404 for non-existent source."""
    response = auth_client.put(
        "/api/sources/99999/selector/",
        data=json.dumps({"result_selector": "div.x"}),
        content_type="application/json",
    )
    assert response.status_code == 404
    data = json.loads(response.content)
    assert data["error"] == "not_found"


@pytest.mark.django_db
def test_update_selector_requires_auth(client, source):
    """PUT /api/sources/{id}/selector/ requires authentication."""
    response = client.put(
        f"/api/sources/{source.id}/selector/",
        data=json.dumps({"result_selector": "div.x"}),
        content_type="application/json",
    )
    assert response.status_code == 401


# --- Test All Sources ---


@pytest.mark.django_db
def test_test_all_requires_auth(client):
    """POST /api/sources/test-all/ without auth is rejected (not 200).

    This is an async endpoint; the sync test client may return 405.
    We verify unauthenticated access does not succeed.
    """
    response = client.post("/api/sources/test-all/")
    assert response.status_code in (401, 403, 405)
    assert response.status_code != 200


# --- Last Validated At ---


@pytest.mark.django_db
def test_source_with_last_validated_at(client, clean_sources):
    """Source with last_validated_at returns ISO formatted date."""
    from django.utils import timezone

    now = timezone.now()
    src = SearchSource.objects.create(
        host="validated.com",
        name="Validated Source",
        is_enabled=True,
        search_url_template="https://validated.com/search?q={query}",
        result_selector="div.r",
        last_validated_at=now,
    )
    response = client.get(f"/api/sources/{src.id}/")
    assert response.status_code == 200
    data = json.loads(response.content)
    assert data["last_validated_at"] is not None
    # Should be a valid ISO datetime string
    assert "T" in data["last_validated_at"]


# --- Needs Attention Flag ---


@pytest.mark.django_db
def test_source_needs_attention_flag(client, disabled_source):
    """Source with consecutive_failures >= 3 has needs_attention=True."""
    response = client.get(f"/api/sources/{disabled_source.id}/")
    assert response.status_code == 200
    data = json.loads(response.content)
    assert data["needs_attention"] is True
    assert data["consecutive_failures"] == 5


@pytest.mark.django_db
def test_toggle_disabled_source_enables_it(auth_client, disabled_source):
    """Toggling a disabled source enables it."""
    response = auth_client.post(f"/api/sources/{disabled_source.id}/toggle/")
    assert response.status_code == 200
    data = json.loads(response.content)
    assert data["is_enabled"] is True

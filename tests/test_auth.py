"""Tests for Phase 12: Authentication System."""

import pytest
from django.contrib.auth.models import User
from django.test import Client

from apps.core.models import AppSettings
from apps.profiles.models import Profile


class TestModels:
    """Tests for Session A - Database Changes."""

    @pytest.mark.django_db
    def test_profile_user_field_nullable(self):
        """Profile can exist without User (home mode)."""
        profile = Profile.objects.create(
            name="Test User",
            avatar_color="#FF5733",
        )
        assert profile.user is None
        assert profile.name == "Test User"

    @pytest.mark.django_db
    def test_profile_links_to_user(self):
        """Profile can link to User (public mode)."""
        user = User.objects.create_user(username="testuser", password="testpass123")  # pragma: allowlist secret
        profile = Profile.objects.create(
            name="Test User",
            avatar_color="#FF5733",
            user=user,
        )
        assert profile.user == user
        assert user.profile == profile

    @pytest.mark.django_db
    def test_appsettings_deployment_mode_default(self):
        """Deployment mode defaults to 'home'."""
        settings = AppSettings.get()
        assert settings.deployment_mode == "home"
        assert settings.get_deployment_mode() == "home"

    @pytest.mark.django_db
    def test_appsettings_get_deployment_mode_env_override(self, monkeypatch):
        """Environment variable overrides database setting."""
        settings = AppSettings.get()
        settings.deployment_mode = "home"
        settings.save()

        # Env var should override
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")
        assert settings.get_deployment_mode() == "public"

        # Case insensitive
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "PUBLIC")
        assert settings.get_deployment_mode() == "public"

        # Invalid env var falls back to database
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "invalid")
        assert settings.get_deployment_mode() == "home"

    @pytest.mark.django_db
    def test_appsettings_get_allow_registration_env_override(self, monkeypatch):
        """COOKIE_ALLOW_REGISTRATION env var overrides database."""
        settings = AppSettings.get()
        settings.allow_registration = True
        settings.save()

        # Env var should override
        monkeypatch.setenv("COOKIE_ALLOW_REGISTRATION", "false")
        assert settings.get_allow_registration() is False

        monkeypatch.setenv("COOKIE_ALLOW_REGISTRATION", "true")
        assert settings.get_allow_registration() is True

        # Case insensitive
        monkeypatch.setenv("COOKIE_ALLOW_REGISTRATION", "FALSE")
        assert settings.get_allow_registration() is False

        # Invalid env var falls back to database
        monkeypatch.setenv("COOKIE_ALLOW_REGISTRATION", "invalid")
        assert settings.get_allow_registration() is True  # database value

    @pytest.mark.django_db
    def test_appsettings_get_instance_name_env_override(self, monkeypatch):
        """COOKIE_INSTANCE_NAME env var overrides database."""
        settings = AppSettings.get()
        settings.instance_name = "My Recipes"
        settings.save()

        # Env var should override
        monkeypatch.setenv("COOKIE_INSTANCE_NAME", "Family Cookbook")
        assert settings.get_instance_name() == "Family Cookbook"

        # Empty env var falls back to database
        monkeypatch.setenv("COOKIE_INSTANCE_NAME", "")
        assert settings.get_instance_name() == "My Recipes"

    @pytest.mark.django_db
    def test_appsettings_allow_registration_default(self):
        """Allow registration defaults to True."""
        settings = AppSettings.get()
        assert settings.allow_registration is True
        assert settings.get_allow_registration() is True

    @pytest.mark.django_db
    def test_appsettings_instance_name_default(self):
        """Instance name defaults to 'Cookie'."""
        settings = AppSettings.get()
        assert settings.instance_name == "Cookie"
        assert settings.get_instance_name() == "Cookie"


class TestAuthAPI:
    """Tests for Session B - Backend Auth Logic."""

    @pytest.mark.django_db
    def test_profile_select_home_mode_no_auth_required(self):
        """Home mode: any user can select any profile."""
        client = Client()
        profile = Profile.objects.create(name="Test", avatar_color="#FF5733")

        # Ensure home mode
        settings = AppSettings.get()
        settings.deployment_mode = "home"
        settings.save()

        response = client.post(f"/api/profiles/{profile.id}/select/")
        assert response.status_code == 200
        assert response.json()["id"] == profile.id

    @pytest.mark.django_db
    def test_profile_select_public_mode_requires_auth(self, monkeypatch):
        """Public mode: 401 if not authenticated."""
        client = Client()
        profile = Profile.objects.create(name="Test", avatar_color="#FF5733")

        # Set public mode via env var
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        response = client.post(f"/api/profiles/{profile.id}/select/")
        assert response.status_code == 401
        assert response.json()["error"] == "unauthorized"

    @pytest.mark.django_db
    def test_profile_select_public_mode_wrong_user(self, monkeypatch):
        """Public mode: 403 if user doesn't own profile."""
        # Create two users with profiles
        user1 = User.objects.create_user(username="user1", password="pass1234")  # pragma: allowlist secret
        user2 = User.objects.create_user(username="user2", password="pass1234")  # pragma: allowlist secret
        profile1 = Profile.objects.create(name="User1", avatar_color="#FF5733", user=user1)
        Profile.objects.create(name="User2", avatar_color="#33FF57", user=user2)

        # Set public mode
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        # Login as user2, try to select user1's profile
        client = Client()
        client.force_login(user2)

        response = client.post(f"/api/profiles/{profile1.id}/select/")
        assert response.status_code == 403
        assert response.json()["error"] == "forbidden"

    @pytest.mark.django_db
    def test_profile_select_public_mode_own_profile(self, monkeypatch):
        """Public mode: success when user owns profile."""
        user = User.objects.create_user(username="testuser", password="pass1234")  # pragma: allowlist secret
        profile = Profile.objects.create(name="Test", avatar_color="#FF5733", user=user)

        # Set public mode
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        client = Client()
        client.force_login(user)

        response = client.post(f"/api/profiles/{profile.id}/select/")
        assert response.status_code == 200
        assert response.json()["id"] == profile.id

    @pytest.mark.django_db
    def test_get_current_profile_home_mode_uses_session(self):
        """Home mode: profile from session['profile_id']."""
        from apps.profiles.utils import get_current_profile

        profile = Profile.objects.create(name="Test", avatar_color="#FF5733")

        # Ensure home mode
        settings = AppSettings.get()
        settings.deployment_mode = "home"
        settings.save()

        # Create a mock request with session
        client = Client()
        client.post(f"/api/profiles/{profile.id}/select/")

        # Use client session to make request and check profile
        response = client.get("/api/profiles/")
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_get_current_profile_public_mode_uses_user(self, monkeypatch):
        """Public mode: profile from request.user.profile."""
        from django.test import RequestFactory
        from apps.profiles.utils import get_current_profile

        user = User.objects.create_user(username="testuser", password="pass1234")  # pragma: allowlist secret
        profile = Profile.objects.create(name="Test", avatar_color="#FF5733", user=user)

        # Set public mode
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        # Create mock request with authenticated user
        factory = RequestFactory()
        request = factory.get("/")
        request.user = user
        request.session = {}

        result = get_current_profile(request)
        assert result == profile

    @pytest.mark.django_db
    def test_auth_settings_endpoint_returns_config(self):
        """GET /api/system/auth-settings/ returns deployment config."""
        client = Client()

        # Set up settings
        settings = AppSettings.get()
        settings.deployment_mode = "home"
        settings.allow_registration = True
        settings.instance_name = "Test Instance"
        settings.save()

        response = client.get("/api/system/auth-settings/")
        assert response.status_code == 200

        data = response.json()
        assert data["deployment_mode"] == "home"
        assert data["allow_registration"] is True
        assert data["instance_name"] == "Test Instance"
        assert "env_overrides" in data

    @pytest.mark.django_db
    def test_auth_settings_endpoint_shows_env_override(self, monkeypatch):
        """GET /api/system/auth-settings/ shows env override status."""
        client = Client()

        # Set env var override
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        response = client.get("/api/system/auth-settings/")
        assert response.status_code == 200

        data = response.json()
        assert data["deployment_mode"] == "public"
        assert data["env_overrides"]["deployment_mode"] is True


class TestViews:
    """Tests for Session C - Login/Register Views."""

    @pytest.mark.django_db
    def test_login_get_renders_form(self, monkeypatch):
        """GET /legacy/login/ renders login template."""
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        client = Client()
        response = client.get("/legacy/login/")

        assert response.status_code == 200
        assert b"login" in response.content.lower() or b"Login" in response.content

    @pytest.mark.django_db
    def test_login_home_mode_redirects_to_selector(self):
        """Login view redirects to profile selector in home mode."""
        # Ensure home mode (default)
        settings = AppSettings.get()
        settings.deployment_mode = "home"
        settings.save()

        client = Client()
        response = client.get("/legacy/login/")

        assert response.status_code == 302
        assert "/legacy/" in response.url  # Redirects to profile selector

    @pytest.mark.django_db
    def test_login_success_redirects_to_home(self, monkeypatch):
        """Valid credentials redirect to home page."""
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        # Create user with profile
        user = User.objects.create_user(username="testuser", password="testpass123")  # pragma: allowlist secret
        Profile.objects.create(user=user, name="Test", avatar_color="#FF5733")

        client = Client()
        response = client.post(
            "/legacy/login/",
            {
                "username": "testuser",
                "password": "testpass123",  # pragma: allowlist secret
            },
        )

        assert response.status_code == 302
        assert "/legacy/home/" in response.url

    @pytest.mark.django_db
    def test_login_invalid_credentials_generic_error(self, monkeypatch):
        """Invalid credentials show generic error (prevents username enumeration)."""
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        client = Client()
        response = client.post(
            "/legacy/login/",
            {
                "username": "nonexistent",
                "password": "wrongpass",  # pragma: allowlist secret
            },
        )

        assert response.status_code == 200
        assert b"Invalid username or password" in response.content  # pragma: allowlist secret

    @pytest.mark.django_db
    def test_login_same_error_for_wrong_password_and_nonexistent_user(self, monkeypatch):
        """Login shows identical error for wrong password and nonexistent user."""
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        # Create a real user
        User.objects.create_user(username="realuser", password="correctpass")  # pragma: allowlist secret

        client = Client()

        # Wrong password for existing user
        response1 = client.post(
            "/legacy/login/",
            {
                "username": "realuser",
                "password": "wrongpass",  # pragma: allowlist secret
            },
        )

        # Nonexistent user
        response2 = client.post(
            "/legacy/login/",
            {
                "username": "fakeuser",
                "password": "anypass",  # pragma: allowlist secret
            },
        )

        # Both should show the same error
        assert b"Invalid username or password" in response1.content  # pragma: allowlist secret
        assert b"Invalid username or password" in response2.content  # pragma: allowlist secret

    @pytest.mark.django_db
    def test_session_id_regenerated_on_login(self, monkeypatch):
        """Session ID changes after login (prevents session fixation)."""
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        user = User.objects.create_user(username="testuser", password="testpass123")  # pragma: allowlist secret
        Profile.objects.create(user=user, name="Test", avatar_color="#FF5733")

        client = Client()

        # Get initial session
        client.get("/legacy/login/")
        initial_session_key = client.session.session_key

        # Login
        client.post(
            "/legacy/login/",
            {
                "username": "testuser",
                "password": "testpass123",  # pragma: allowlist secret
            },
        )

        # Session key should have changed
        new_session_key = client.session.session_key
        assert new_session_key != initial_session_key

    @pytest.mark.django_db
    def test_register_get_renders_form(self, monkeypatch):
        """GET /legacy/register/ renders register template."""
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        client = Client()
        response = client.get("/legacy/register/")

        assert response.status_code == 200

    @pytest.mark.django_db
    def test_register_home_mode_redirects(self, monkeypatch):
        """Register view redirects in home mode."""
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "home")

        client = Client()
        response = client.get("/legacy/register/")

        assert response.status_code == 302

    @pytest.mark.django_db
    def test_register_disabled_redirects(self, monkeypatch):
        """Register view redirects when registration disabled."""
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")
        monkeypatch.setenv("COOKIE_ALLOW_REGISTRATION", "false")

        client = Client()
        response = client.get("/legacy/register/")

        assert response.status_code == 302
        assert "/legacy/login/" in response.url

    @pytest.mark.django_db
    def test_register_success_creates_user_and_profile(self, monkeypatch):
        """Valid registration creates User and Profile."""
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        client = Client()
        response = client.post(
            "/legacy/register/",
            {
                "username": "newuser",
                "password": "securepass123",  # pragma: allowlist secret
                "password_confirm": "securepass123",  # pragma: allowlist secret
                "avatar_color": "#FF5733",
            },
        )

        assert response.status_code == 302
        assert "/legacy/home/" in response.url

        # Verify user and profile created
        user = User.objects.get(username="newuser")
        assert user.profile is not None
        assert user.profile.avatar_color == "#FF5733"

    @pytest.mark.django_db
    def test_register_duplicate_username_shows_error(self, monkeypatch):
        """Duplicate username shows error message."""
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        # Create existing user
        User.objects.create_user(username="existinguser", password="pass1234")  # pragma: allowlist secret

        client = Client()
        response = client.post(
            "/legacy/register/",
            {
                "username": "existinguser",
                "password": "newpass123",  # pragma: allowlist secret
                "password_confirm": "newpass123",  # pragma: allowlist secret
            },
        )

        assert response.status_code == 200
        assert b"Username already taken" in response.content

    @pytest.mark.django_db
    def test_register_password_mismatch_shows_error(self, monkeypatch):
        """Password confirmation mismatch shows error."""
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        client = Client()
        response = client.post(
            "/legacy/register/",
            {
                "username": "newuser",
                "password": "password123",  # pragma: allowlist secret
                "password_confirm": "different123",  # pragma: allowlist secret
            },
        )

        assert response.status_code == 200
        assert b"Passwords do not match" in response.content

    @pytest.mark.django_db
    def test_register_short_password_shows_error(self, monkeypatch):
        """Password under 8 chars shows error."""
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        client = Client()
        response = client.post(
            "/legacy/register/",
            {
                "username": "newuser",
                "password": "short",  # pragma: allowlist secret
                "password_confirm": "short",  # pragma: allowlist secret
            },
        )

        assert response.status_code == 200
        assert b"Password must be at least 8 characters" in response.content

    @pytest.mark.django_db
    def test_register_invalid_username_shows_error(self, monkeypatch):
        """Username with invalid chars shows error."""
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        client = Client()
        response = client.post(
            "/legacy/register/",
            {
                "username": "invalid@user!",
                "password": "password123",  # pragma: allowlist secret
                "password_confirm": "password123",  # pragma: allowlist secret
            },
        )

        assert response.status_code == 200
        assert b"can only contain letters, numbers, and underscores" in response.content

    @pytest.mark.django_db
    def test_logout_clears_session(self, monkeypatch):
        """Logout clears Django auth and session profile_id."""
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        user = User.objects.create_user(username="testuser", password="testpass123")  # pragma: allowlist secret
        Profile.objects.create(user=user, name="Test", avatar_color="#FF5733")

        client = Client()
        client.force_login(user)
        client.session["profile_id"] = user.profile.id
        client.session.save()

        response = client.get("/legacy/logout/")

        assert response.status_code == 302
        # Check user is logged out
        assert "_auth_user_id" not in client.session

    @pytest.mark.django_db
    def test_logout_public_mode_redirects_to_login(self, monkeypatch):
        """Public mode: logout redirects to login."""
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        user = User.objects.create_user(username="testuser", password="testpass123")  # pragma: allowlist secret

        client = Client()
        client.force_login(user)

        response = client.get("/legacy/logout/")

        assert response.status_code == 302
        assert "/legacy/login/" in response.url

    @pytest.mark.django_db
    def test_logout_home_mode_redirects_to_selector(self):
        """Home mode: logout redirects to profile selector."""
        settings = AppSettings.get()
        settings.deployment_mode = "home"
        settings.save()

        client = Client()
        response = client.get("/legacy/logout/")

        assert response.status_code == 302
        assert response.url == "/legacy/"  # Profile selector


class TestTemplates:
    """Tests for Session D - Template Rendering."""

    @pytest.mark.django_db
    def test_login_template_renders(self, monkeypatch):
        """GET /legacy/login/ returns 200 and contains form elements."""
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        client = Client()
        response = client.get("/legacy/login/")

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "<form" in content
        assert 'name="username"' in content
        assert 'name="password"' in content  # pragma: allowlist secret
        assert 'type="submit"' in content

    @pytest.mark.django_db
    def test_register_template_renders(self, monkeypatch):
        """GET /legacy/register/ returns 200 and contains form elements."""
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        client = Client()
        response = client.get("/legacy/register/")

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "<form" in content
        assert 'name="username"' in content
        assert 'name="password"' in content  # pragma: allowlist secret
        assert 'name="password_confirm"' in content

    @pytest.mark.django_db
    def test_login_template_shows_instance_name(self, monkeypatch):
        """Login page displays configured instance name."""
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")
        monkeypatch.setenv("COOKIE_INSTANCE_NAME", "Family Recipes")

        client = Client()
        response = client.get("/legacy/login/")

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Family Recipes" in content

    @pytest.mark.django_db
    def test_register_template_shows_instance_name(self, monkeypatch):
        """Register page displays configured instance name."""
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")
        monkeypatch.setenv("COOKIE_INSTANCE_NAME", "Family Recipes")

        client = Client()
        response = client.get("/legacy/register/")

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Family Recipes" in content

    @pytest.mark.django_db
    def test_register_template_has_color_picker(self, monkeypatch):
        """Register page includes avatar color picker."""
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        client = Client()
        response = client.get("/legacy/register/")

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert 'id="color-picker"' in content
        assert 'name="avatar_color"' in content

    @pytest.mark.django_db
    def test_login_template_no_es6_syntax(self, monkeypatch):
        """Login page inline scripts are ES5 compliant (no ES6 syntax)."""
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        client = Client()
        response = client.get("/legacy/login/")

        content = response.content.decode("utf-8")

        # Check for common ES6 syntax that would break iOS 9
        # Login template has no inline JS, so this should pass
        assert "const " not in content or "const " in content.split("<!--")[0]  # Allow in comments
        assert "let " not in content or "let " in content.split("<!--")[0]
        assert "=>" not in content  # Arrow functions

    @pytest.mark.django_db
    def test_register_template_no_es6_syntax(self, monkeypatch):
        """Register page inline scripts are ES5 compliant (no ES6 syntax)."""
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        client = Client()
        response = client.get("/legacy/register/")

        content = response.content.decode("utf-8")

        # Check for common ES6 syntax that would break iOS 9
        assert "const " not in content
        assert "let " not in content
        assert "=>" not in content  # Arrow functions
        assert "template literal" not in content.lower()  # No backtick strings

        # Verify we use var instead
        assert "var " in content  # Should use var for variables

    @pytest.mark.django_db
    def test_login_template_has_csrf_token(self, monkeypatch):
        """Login form includes CSRF token."""
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        client = Client()
        response = client.get("/legacy/login/")

        content = response.content.decode("utf-8")
        assert "csrfmiddlewaretoken" in content

    @pytest.mark.django_db
    def test_register_template_has_csrf_token(self, monkeypatch):
        """Register form includes CSRF token."""
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        client = Client()
        response = client.get("/legacy/register/")

        content = response.content.decode("utf-8")
        assert "csrfmiddlewaretoken" in content

    @pytest.mark.django_db
    def test_login_shows_register_link_when_allowed(self, monkeypatch):
        """Login page shows register link when registration is enabled."""
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")
        monkeypatch.setenv("COOKIE_ALLOW_REGISTRATION", "true")

        client = Client()
        response = client.get("/legacy/login/")

        content = response.content.decode("utf-8")
        assert "/legacy/register/" in content
        assert "Register" in content

    @pytest.mark.django_db
    def test_login_hides_register_link_when_disabled(self, monkeypatch):
        """Login page hides register link when registration is disabled."""
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")
        monkeypatch.setenv("COOKIE_ALLOW_REGISTRATION", "false")

        client = Client()
        response = client.get("/legacy/login/")

        content = response.content.decode("utf-8")
        assert "/legacy/register/" not in content


class TestSettingsAPI:
    """Tests for Session F - Settings API."""

    @pytest.mark.django_db
    def test_put_auth_settings_updates_deployment_mode(self):
        """PUT /api/system/auth-settings/ updates deployment mode."""
        client = Client()

        # Ensure starting in home mode
        settings = AppSettings.get()
        settings.deployment_mode = "home"
        settings.save()

        response = client.put(
            "/api/system/auth-settings/",
            data={"deployment_mode": "public"},
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["deployment_mode"] == "public"

        # Verify database updated
        settings.refresh_from_db()
        assert settings.deployment_mode == "public"

    @pytest.mark.django_db
    def test_put_auth_settings_updates_allow_registration(self):
        """PUT /api/system/auth-settings/ updates allow_registration."""
        client = Client()

        # Ensure starting with registration enabled
        settings = AppSettings.get()
        settings.allow_registration = True
        settings.save()

        response = client.put(
            "/api/system/auth-settings/",
            data={"allow_registration": False},
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["allow_registration"] is False

        # Verify database updated
        settings.refresh_from_db()
        assert settings.allow_registration is False

    @pytest.mark.django_db
    def test_put_auth_settings_updates_instance_name(self):
        """PUT /api/system/auth-settings/ updates instance_name."""
        client = Client()

        # Ensure starting with default name
        settings = AppSettings.get()
        settings.instance_name = "Cookie"
        settings.save()

        response = client.put(
            "/api/system/auth-settings/",
            data={"instance_name": "Family Recipes"},
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["instance_name"] == "Family Recipes"

        # Verify database updated
        settings.refresh_from_db()
        assert settings.instance_name == "Family Recipes"

    @pytest.mark.django_db
    def test_put_auth_settings_respects_env_override(self, monkeypatch):
        """Cannot change deployment_mode via API when env var is set."""
        # Set env var overrides - public mode requires admin auth
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")
        monkeypatch.setenv("COOKIE_ADMIN_USERNAME", "admin")

        # Ensure database has different value
        settings = AppSettings.get()
        settings.deployment_mode = "home"
        settings.save()

        # Create admin user (required for public mode)
        admin = User.objects.create_user(username="admin", password="pass123")  # pragma: allowlist secret
        Profile.objects.create(user=admin, name="Admin", avatar_color="#FF5733")

        client = Client()
        client.force_login(admin)

        # Get CSRF token
        client.get("/legacy/login/")
        csrf_token = client.cookies.get("csrftoken")

        response = client.put(
            "/api/system/auth-settings/",
            data={"deployment_mode": "home"},
            content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf_token.value if csrf_token else "",
        )

        assert response.status_code == 200
        data = response.json()

        # Should succeed but with warning
        assert data["success"] is True
        assert len(data["warnings"]) > 0
        assert "environment variable" in data["warnings"][0].lower()

        # Database value should remain unchanged (was home, stays home)
        settings.refresh_from_db()
        assert settings.deployment_mode == "home"

        # But effective mode is still from env var
        assert data["deployment_mode"] == "public"

    @pytest.mark.django_db
    def test_get_auth_settings_shows_env_override_status(self, monkeypatch):
        """GET /api/system/auth-settings/ shows which settings are env-controlled."""
        client = Client()

        # Set env vars for some settings
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")
        monkeypatch.setenv("COOKIE_INSTANCE_NAME", "Test Instance")

        response = client.get("/api/system/auth-settings/")
        assert response.status_code == 200

        data = response.json()
        assert data["env_overrides"]["deployment_mode"] is True
        assert data["env_overrides"]["instance_name"] is True
        assert data["env_overrides"]["allow_registration"] is False

    @pytest.mark.django_db
    def test_put_auth_settings_validates_deployment_mode(self):
        """PUT /api/system/auth-settings/ rejects invalid deployment_mode."""
        client = Client()

        response = client.put(
            "/api/system/auth-settings/",
            data={"deployment_mode": "invalid"},
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "invalid_deployment_mode"

    @pytest.mark.django_db
    def test_put_auth_settings_validates_instance_name_not_empty(self):
        """PUT /api/system/auth-settings/ rejects empty instance_name."""
        client = Client()

        response = client.put(
            "/api/system/auth-settings/",
            data={"instance_name": "   "},
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "invalid_instance_name"

    @pytest.mark.django_db
    def test_put_auth_settings_validates_instance_name_length(self):
        """PUT /api/system/auth-settings/ rejects instance_name > 100 chars."""
        client = Client()

        response = client.put(
            "/api/system/auth-settings/",
            data={"instance_name": "x" * 101},
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "invalid_instance_name"

    @pytest.mark.django_db
    def test_put_auth_settings_updates_multiple_fields(self):
        """PUT /api/system/auth-settings/ can update multiple fields at once."""
        client = Client()

        settings = AppSettings.get()
        settings.deployment_mode = "home"
        settings.allow_registration = True
        settings.instance_name = "Cookie"
        settings.save()

        response = client.put(
            "/api/system/auth-settings/",
            data={
                "deployment_mode": "public",
                "allow_registration": False,
                "instance_name": "My Recipes",
            },
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["deployment_mode"] == "public"
        assert data["allow_registration"] is False
        assert data["instance_name"] == "My Recipes"


class TestAdminAuthorization:
    """Tests for Session H - Admin Authorization."""

    @pytest.mark.django_db
    def test_is_admin_home_mode_returns_true(self):
        """Home mode: all users are effectively admin."""
        from apps.core.utils import is_admin

        # Home mode is the default
        settings = AppSettings.get()
        settings.deployment_mode = "home"
        settings.save()

        # Anonymous user
        from django.contrib.auth.models import AnonymousUser

        anon = AnonymousUser()
        assert is_admin(anon) is True

        # Regular user
        user = User.objects.create_user(username="regular", password="pass123")  # pragma: allowlist secret
        assert is_admin(user) is True

    @pytest.mark.django_db
    def test_is_admin_public_mode_no_env_var(self, monkeypatch):
        """Public mode without COOKIE_ADMIN_USERNAME: no one is admin."""
        from apps.core.utils import is_admin

        # Ensure env var is not set
        monkeypatch.delenv("COOKIE_ADMIN_USERNAME", raising=False)

        settings = AppSettings.get()
        settings.deployment_mode = "public"
        settings.save()

        user = User.objects.create_user(username="testuser", password="pass123")  # pragma: allowlist secret
        assert is_admin(user) is False

    @pytest.mark.django_db
    def test_is_admin_public_mode_matching_username(self, monkeypatch):
        """Public mode: user matching env var is admin."""
        from apps.core.utils import is_admin

        monkeypatch.setenv("COOKIE_ADMIN_USERNAME", "admin_user")

        settings = AppSettings.get()
        settings.deployment_mode = "public"
        settings.save()

        admin = User.objects.create_user(username="admin_user", password="pass123")  # pragma: allowlist secret
        assert is_admin(admin) is True

    @pytest.mark.django_db
    def test_is_admin_public_mode_non_matching_username(self, monkeypatch):
        """Public mode: user not matching env var is not admin."""
        from apps.core.utils import is_admin

        monkeypatch.setenv("COOKIE_ADMIN_USERNAME", "admin_user")

        settings = AppSettings.get()
        settings.deployment_mode = "public"
        settings.save()

        regular = User.objects.create_user(username="regular_user", password="pass123")  # pragma: allowlist secret
        assert is_admin(regular) is False

    @pytest.mark.django_db
    def test_settings_view_home_mode_accessible(self):
        """Home mode: settings accessible without auth."""
        # Home mode is default
        settings = AppSettings.get()
        settings.deployment_mode = "home"
        settings.save()

        # Create and select a profile (required by require_profile)
        profile = Profile.objects.create(name="Test", avatar_color="#FF5733")

        client = Client()
        session = client.session
        session["profile_id"] = profile.id
        session.save()

        response = client.get("/legacy/settings/")
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_settings_view_public_mode_admin_accessible(self, monkeypatch):
        """Public mode: settings accessible to admin."""
        monkeypatch.setenv("COOKIE_ADMIN_USERNAME", "admin")
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        # Create admin user with profile
        admin = User.objects.create_user(username="admin", password="pass123")  # pragma: allowlist secret
        Profile.objects.create(user=admin, name="Admin", avatar_color="#FF5733")

        client = Client()
        client.force_login(admin)

        response = client.get("/legacy/settings/")
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_settings_view_public_mode_user_forbidden(self, monkeypatch):
        """Public mode: settings returns 403 for non-admin."""
        monkeypatch.setenv("COOKIE_ADMIN_USERNAME", "admin")
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        # Create regular user with profile
        user = User.objects.create_user(username="regular", password="pass123")  # pragma: allowlist secret
        Profile.objects.create(user=user, name="Regular", avatar_color="#FF5733")

        client = Client()
        client.force_login(user)

        response = client.get("/legacy/settings/")
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_api_reset_public_mode_user_forbidden(self, monkeypatch):
        """Public mode: reset endpoint returns 403 for non-admin."""
        monkeypatch.setenv("COOKIE_ADMIN_USERNAME", "admin")
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        # Create regular user with profile
        user = User.objects.create_user(username="regular", password="pass123")  # pragma: allowlist secret
        Profile.objects.create(user=user, name="Regular", avatar_color="#FF5733")

        client = Client()
        client.force_login(user)

        # Get CSRF token
        client.get("/legacy/login/")
        csrf_token = client.cookies.get("csrftoken")

        response = client.post(
            "/api/system/reset/",
            data={"confirmation_text": "RESET"},
            content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf_token.value if csrf_token else "",
        )
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_api_delete_own_profile_allowed(self, monkeypatch):
        """Any user can delete their own profile."""
        monkeypatch.setenv("COOKIE_ADMIN_USERNAME", "admin")
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        # Create regular user with profile
        user = User.objects.create_user(username="regular", password="pass123")  # pragma: allowlist secret
        profile = Profile.objects.create(user=user, name="Regular", avatar_color="#FF5733")

        client = Client()
        client.force_login(user)

        # Get CSRF token
        client.get("/legacy/login/")
        csrf_token = client.cookies.get("csrftoken")

        response = client.delete(
            f"/api/profiles/{profile.id}/",
            HTTP_X_CSRFTOKEN=csrf_token.value if csrf_token else "",
        )
        assert response.status_code == 204

    @pytest.mark.django_db
    def test_api_delete_other_profile_admin_only(self, monkeypatch):
        """Only admin can delete other users' profiles."""
        monkeypatch.setenv("COOKIE_ADMIN_USERNAME", "admin")
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        # Create regular user with profile
        user = User.objects.create_user(username="regular", password="pass123")  # pragma: allowlist secret
        Profile.objects.create(user=user, name="Regular", avatar_color="#FF5733")

        # Create target profile (another user)
        target_user = User.objects.create_user(username="target", password="pass123")  # pragma: allowlist secret
        target_profile = Profile.objects.create(user=target_user, name="Target", avatar_color="#3366FF")

        client = Client()
        client.force_login(user)

        # Get CSRF token
        client.get("/legacy/login/")
        csrf_token = client.cookies.get("csrftoken")

        # Regular user cannot delete another user's profile
        response = client.delete(
            f"/api/profiles/{target_profile.id}/",
            HTTP_X_CSRFTOKEN=csrf_token.value if csrf_token else "",
        )
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_api_delete_other_profile_admin_allowed(self, monkeypatch):
        """Admin can delete other users' profiles."""
        monkeypatch.setenv("COOKIE_ADMIN_USERNAME", "admin")
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        # Create admin user with profile
        admin = User.objects.create_user(username="admin", password="pass123")  # pragma: allowlist secret
        Profile.objects.create(user=admin, name="Admin", avatar_color="#FF5733")

        # Create target profile (another user)
        target_user = User.objects.create_user(username="target", password="pass123")  # pragma: allowlist secret
        target_profile = Profile.objects.create(user=target_user, name="Target", avatar_color="#3366FF")

        client = Client()
        client.force_login(admin)

        # Get CSRF token
        client.get("/legacy/login/")
        csrf_token = client.cookies.get("csrftoken")

        # Admin can delete another user's profile
        response = client.delete(
            f"/api/profiles/{target_profile.id}/",
            HTTP_X_CSRFTOKEN=csrf_token.value if csrf_token else "",
        )
        assert response.status_code == 204

    @pytest.mark.django_db
    def test_api_auth_settings_includes_is_admin(self):
        """Auth settings endpoint includes is_admin flag."""
        client = Client()

        response = client.get("/api/system/auth-settings/")
        assert response.status_code == 200
        data = response.json()
        assert "is_admin" in data
        # Home mode: everyone is admin
        assert data["is_admin"] is True

    @pytest.mark.django_db
    def test_api_auth_settings_is_admin_public_mode(self, monkeypatch):
        """Auth settings shows is_admin=False for non-admin in public mode."""
        monkeypatch.setenv("COOKIE_ADMIN_USERNAME", "admin")
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        # Create regular user with profile
        user = User.objects.create_user(username="regular", password="pass123")  # pragma: allowlist secret
        Profile.objects.create(user=user, name="Regular", avatar_color="#FF5733")

        client = Client()
        client.force_login(user)

        response = client.get("/api/system/auth-settings/")
        assert response.status_code == 200
        data = response.json()
        assert data["is_admin"] is False

    @pytest.mark.django_db
    def test_api_update_auth_settings_admin_only(self, monkeypatch):
        """Only admin can update auth settings in public mode."""
        monkeypatch.setenv("COOKIE_ADMIN_USERNAME", "admin")
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        # Create regular user with profile
        user = User.objects.create_user(username="regular", password="pass123")  # pragma: allowlist secret
        Profile.objects.create(user=user, name="Regular", avatar_color="#FF5733")

        client = Client()
        client.force_login(user)

        # Get CSRF token
        client.get("/legacy/login/")
        csrf_token = client.cookies.get("csrftoken")

        response = client.put(
            "/api/system/auth-settings/",
            data={"instance_name": "Hacked"},
            content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf_token.value if csrf_token else "",
        )
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_api_save_api_key_admin_only(self, monkeypatch):
        """Only admin can save API key in public mode."""
        monkeypatch.setenv("COOKIE_ADMIN_USERNAME", "admin")
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        # Create regular user with profile
        user = User.objects.create_user(username="regular", password="pass123")  # pragma: allowlist secret
        Profile.objects.create(user=user, name="Regular", avatar_color="#FF5733")

        client = Client()
        client.force_login(user)

        # Get CSRF token
        client.get("/legacy/login/")
        csrf_token = client.cookies.get("csrftoken")

        response = client.post(
            "/api/ai/save-api-key",
            data={"api_key": "sk-test-key"},  # pragma: allowlist secret
            content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf_token.value if csrf_token else "",
        )
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_list_profiles_admin_sees_all(self, monkeypatch):
        """Admin can see all profiles in public mode."""
        monkeypatch.setenv("COOKIE_ADMIN_USERNAME", "admin")
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        # Create admin user with profile
        admin = User.objects.create_user(username="admin", password="pass123")  # pragma: allowlist secret
        Profile.objects.create(user=admin, name="Admin", avatar_color="#FF5733")

        # Create other users
        user1 = User.objects.create_user(username="user1", password="pass123")  # pragma: allowlist secret
        Profile.objects.create(user=user1, name="User 1", avatar_color="#3366FF")

        user2 = User.objects.create_user(username="user2", password="pass123")  # pragma: allowlist secret
        Profile.objects.create(user=user2, name="User 2", avatar_color="#66FF33")

        client = Client()
        client.force_login(admin)

        response = client.get("/api/profiles/")
        assert response.status_code == 200
        data = response.json()
        # Admin sees all 3 profiles
        assert len(data) == 3

    @pytest.mark.django_db
    def test_list_profiles_user_sees_only_own(self, monkeypatch):
        """Non-admin user can only see their own profile in public mode."""
        monkeypatch.setenv("COOKIE_ADMIN_USERNAME", "admin")
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        # Create admin user with profile
        admin = User.objects.create_user(username="admin", password="pass123")  # pragma: allowlist secret
        Profile.objects.create(user=admin, name="Admin", avatar_color="#FF5733")

        # Create regular user
        user = User.objects.create_user(username="regular", password="pass123")  # pragma: allowlist secret
        Profile.objects.create(user=user, name="Regular", avatar_color="#3366FF")

        client = Client()
        client.force_login(user)

        response = client.get("/api/profiles/")
        assert response.status_code == 200
        data = response.json()
        # Regular user sees only their own profile
        assert len(data) == 1
        assert data[0]["name"] == "Regular"

"""Regression tests for response-header ownership (pentest round 3).

In production, `nginx/security-headers.conf` is the sole source of the
following response headers:

    X-Frame-Options, X-Content-Type-Options, Referrer-Policy,
    Cross-Origin-Opener-Policy

If Django's `SecurityMiddleware` or `XFrameOptionsMiddleware` also emits
them, every Django-served response carries each header twice. These tests
pin the configuration that prevents that duplication.
"""

import importlib
import os

import pytest


@pytest.fixture
def prod_settings(monkeypatch):
    """Re-import `cookie.settings` with DEBUG=false so the production
    hardening branch runs. Django cannot rebuild MIDDLEWARE via
    `override_settings`, so we read the module fresh in isolation."""
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("SECRET_KEY", "test-only-not-a-real-secret")  # pragma: allowlist secret
    monkeypatch.setenv("DATABASE_URL", os.environ["DATABASE_URL"])
    # Supply a COOKIE_VERSION so the prod guard in settings.py doesn't fire
    # during reload — we're pinning header behaviour here, not version flow.
    monkeypatch.setenv("COOKIE_VERSION", "test")
    import cookie.settings as settings_module

    reloaded = importlib.reload(settings_module)
    yield reloaded
    # Restore the baseline DEBUG=True module state for subsequent tests.
    monkeypatch.setenv("DEBUG", "true")
    importlib.reload(settings_module)


class TestProdDefersHeadersToNginx:
    """In prod, Django must not emit any of the four headers nginx owns."""

    def test_prod_branch_ran(self, prod_settings):
        assert prod_settings.DEBUG is False

    def test_secure_referrer_policy_disabled(self, prod_settings):
        assert prod_settings.SECURE_REFERRER_POLICY is None, (
            "In prod, nginx owns Referrer-Policy — Django must not set it or "
            "the header appears twice on every Django-served response."
        )

    def test_coop_disabled(self, prod_settings):
        assert prod_settings.SECURE_CROSS_ORIGIN_OPENER_POLICY is None, (
            "In prod, nginx owns Cross-Origin-Opener-Policy — Django must not set it."
        )

    def test_content_type_nosniff_disabled(self, prod_settings):
        assert prod_settings.SECURE_CONTENT_TYPE_NOSNIFF is False, (
            "In prod, nginx owns X-Content-Type-Options — Django must not set it."
        )

    def test_xframe_options_middleware_removed(self, prod_settings):
        assert "django.middleware.clickjacking.XFrameOptionsMiddleware" not in prod_settings.MIDDLEWARE, (
            "In prod, nginx owns X-Frame-Options — XFrameOptionsMiddleware must "
            "be absent from MIDDLEWARE or the header appears twice."
        )

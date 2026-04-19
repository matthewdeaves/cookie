"""Regression tests for the COOKIE_VERSION resolution pipeline.

Prior to v1.45.0 the version shown in the UI could silently fall back to
the string "dev" in production because:

  1. `Dockerfile.prod` never baked the version into the image.
  2. `docker-compose.prod.yml` had `COOKIE_VERSION=${COOKIE_VERSION:-dev}`,
     making the container env literally "dev" when the deployer forgot to
     set it.
  3. `cookie/settings.py` had a hardcoded fallback that the compose env
     then overrode anyway.

These tests pin each link of the chain so a regression in any one is
caught in CI, not on the production dashboard.
"""

from __future__ import annotations

import importlib
import os
import re
from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestDockerfileBakesVersion:
    """Dockerfile.prod must accept COOKIE_VERSION as an ARG, expose it as
    ENV, and attach it as an OCI LABEL so the manifest carries the version."""

    @pytest.fixture
    def dockerfile(self) -> str:
        return (REPO_ROOT / "Dockerfile.prod").read_text()

    def test_declares_build_arg(self, dockerfile):
        assert re.search(r"^ARG\s+COOKIE_VERSION\b", dockerfile, re.MULTILINE), (
            "Dockerfile.prod must declare `ARG COOKIE_VERSION` so the CD "
            "pipeline can pass the release version at build time."
        )

    def test_exposes_env(self, dockerfile):
        assert re.search(r"^ENV\s+COOKIE_VERSION=\$\{COOKIE_VERSION\}", dockerfile, re.MULTILINE), (
            "Dockerfile.prod must promote the build ARG to an ENV so the "
            "runtime settings loader sees it with no deploy-time fallback."
        )

    def test_declares_oci_version_label(self, dockerfile):
        assert re.search(
            r"LABEL\s+org\.opencontainers\.image\.version=\$\{COOKIE_VERSION\}",
            dockerfile,
        ), (
            "Dockerfile.prod must attach an OCI `image.version` LABEL so the "
            "pushed image manifest can be audited against the git tag."
        )


class TestCdWorkflowPassesVersion:
    """The CD workflow must pass COOKIE_VERSION as a build-arg derived from
    the git tag (strip leading `v`), falling back to a deterministic
    sha-based value for non-tag runs."""

    @pytest.fixture
    def cd_workflow(self) -> str:
        return (REPO_ROOT / ".github" / "workflows" / "cd.yml").read_text()

    def test_resolves_version_step(self, cd_workflow):
        # Match the shell step that derives COOKIE_VERSION from GITHUB_REF.
        assert re.search(r"GITHUB_REF_NAME#v", cd_workflow), (
            "cd.yml must strip the leading `v` from the tag ref so the "
            "COOKIE_VERSION baked into the image is clean semver (e.g. 1.45.0)."
        )
        assert re.search(r"GITHUB_REF_TYPE.*=.*tag", cd_workflow), (
            "cd.yml must differentiate tag runs from workflow_dispatch so "
            "non-tag builds do not bake a production-looking semver."
        )

    def test_build_step_consumes_version(self, cd_workflow):
        assert re.search(
            r"build-args:\s*\|[^|]*COOKIE_VERSION=\$\{\{\s*steps\.cookie_version\.outputs\.value\s*\}\}",
            cd_workflow,
            re.DOTALL,
        ), "docker/build-push-action must receive COOKIE_VERSION via build-args from the resolved step output."


class TestComposeDoesNotOverrideVersion:
    """docker-compose.prod.yml must NOT re-inject COOKIE_VERSION with a
    fallback — doing so masks build-pipeline bugs and was the original
    source of the "dev" sighting in production."""

    @pytest.fixture
    def compose(self) -> str:
        return (REPO_ROOT / "docker-compose.prod.yml").read_text()

    def test_no_cookie_version_env_with_dev_fallback(self, compose):
        assert "COOKIE_VERSION=${COOKIE_VERSION:-dev}" not in compose, (
            "docker-compose.prod.yml must not default COOKIE_VERSION to 'dev' — "
            "the image ENV baked by Dockerfile.prod is the sole source of truth."
        )

    def test_no_unconditional_cookie_version_env(self, compose):
        # Any COOKIE_VERSION= line in the environment list would override
        # the image-baked ENV. The comment form is fine (and documented).
        for line in compose.splitlines():
            stripped = line.strip()
            if stripped.startswith("-") and "COOKIE_VERSION=" in stripped:
                pytest.fail(
                    f"docker-compose.prod.yml must not set COOKIE_VERSION in the "
                    f"environment list (found: {line.strip()!r}). The image ENV owns it."
                )


class TestSettingsRefusesDevFallbackInProd:
    """cookie/settings.py must refuse a missing/empty COOKIE_VERSION in
    production — silent "dev" was the reason this whole fix exists."""

    def _reload_settings(self, monkeypatch, *, debug: str, version: str | None) -> object:
        monkeypatch.setenv("DEBUG", debug)
        monkeypatch.setenv("SECRET_KEY", "test-only-not-a-real-secret")  # pragma: allowlist secret
        monkeypatch.setenv("DATABASE_URL", os.environ["DATABASE_URL"])
        if version is None:
            monkeypatch.delenv("COOKIE_VERSION", raising=False)
        else:
            monkeypatch.setenv("COOKIE_VERSION", version)
        import cookie.settings as settings_module

        return importlib.reload(settings_module)

    @pytest.fixture(autouse=True)
    def _restore_settings(self, monkeypatch):
        yield
        # Put the module back to dev defaults so later tests aren't affected.
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.delenv("COOKIE_VERSION", raising=False)
        import cookie.settings as settings_module

        importlib.reload(settings_module)

    def test_prod_missing_version_raises(self, monkeypatch):
        with pytest.raises(ImproperlyConfigured, match="COOKIE_VERSION"):
            self._reload_settings(monkeypatch, debug="false", version=None)

    def test_prod_empty_version_raises(self, monkeypatch):
        with pytest.raises(ImproperlyConfigured, match="COOKIE_VERSION"):
            self._reload_settings(monkeypatch, debug="false", version="")

    def test_prod_whitespace_version_raises(self, monkeypatch):
        with pytest.raises(ImproperlyConfigured, match="COOKIE_VERSION"):
            self._reload_settings(monkeypatch, debug="false", version="   ")

    def test_prod_semver_accepted(self, monkeypatch):
        reloaded = self._reload_settings(monkeypatch, debug="false", version="1.45.0")
        assert reloaded.COOKIE_VERSION == "1.45.0"

    def test_dev_missing_version_falls_back(self, monkeypatch):
        reloaded = self._reload_settings(monkeypatch, debug="true", version=None)
        assert reloaded.COOKIE_VERSION == "dev"

    def test_dev_explicit_version_wins(self, monkeypatch):
        reloaded = self._reload_settings(monkeypatch, debug="true", version="2.0.0-rc1")
        assert reloaded.COOKIE_VERSION == "2.0.0-rc1"

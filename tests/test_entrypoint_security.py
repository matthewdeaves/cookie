"""
Security checks for production entrypoint script.

Split from `test_nginx_security.py` to keep every test file under the
constitutional 500-line limit.
"""

from pathlib import Path

import pytest

ENTRYPOINT_PROD = Path(__file__).parent.parent / "entrypoint.prod.sh"


class TestEntrypointSecurity:
    """Security checks for production entrypoint script."""

    @pytest.fixture
    def entrypoint(self):
        return ENTRYPOINT_PROD.read_text()

    def test_no_secrets_in_cron_config(self, entrypoint):
        """Entrypoint must not write SECRET_KEY or DATABASE_URL to cron files.

        After 015-security-review-fixes, supercronic inherits env from the
        entrypoint process. No secrets are written to disk.
        """
        assert "/etc/cron.d/cookie-cleanup" not in entrypoint, (
            "Entrypoint must not write /etc/cron.d/cookie-cleanup — use supercronic with inherited env"
        )
        assert "supercronic" in entrypoint, "Entrypoint must launch supercronic as the scheduler"

    def test_secret_key_file_permissions(self, entrypoint):
        """Generated secret key file must be owner-only."""
        assert "chmod 600" in entrypoint, "SECRET_KEY file must have restrictive permissions"

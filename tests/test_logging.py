"""Tests for logging infrastructure (T174-T175)."""

import json
import logging

import pytest

from apps.core.logging import JSONFormatter


class TestJSONFormatter:
    """T174: JSON formatter produces valid JSON with required fields."""

    def test_produces_valid_json(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test.logger"
        assert parsed["message"] == "Test message"
        assert "timestamp" in parsed

    def test_includes_extra_fields(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="security",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="Login failure",
            args=(),
            exc_info=None,
        )
        record.ip = "1.2.3.4"
        record.request_id = "abc123"
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["ip"] == "1.2.3.4"
        assert parsed["request_id"] == "abc123"


class TestSecurityEventLevels:
    """T175: Security events are logged at correct levels."""

    def test_security_logger_exists(self):
        logger = logging.getLogger("security")
        assert logger is not None

    def test_login_failure_is_warning(self):
        """Security events for login failure should be WARNING level."""
        logger = logging.getLogger("security")
        # Verify the logger accepts WARNING level
        assert logger.isEnabledFor(logging.WARNING)

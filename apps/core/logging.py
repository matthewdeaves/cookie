"""JSON log formatter for production."""

import json
import logging
from datetime import UTC, datetime


class JSONFormatter(logging.Formatter):
    """Produces JSON log lines for machine parsing in production."""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
        }

        # Add request_id if available
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id

        # Add extra fields
        for key in ("username", "ip", "path", "reason", "endpoint", "action", "target_username"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)

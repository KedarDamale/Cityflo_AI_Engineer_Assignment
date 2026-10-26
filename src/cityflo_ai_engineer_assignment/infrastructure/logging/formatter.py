"""Privacy-preserving structured application log formatter."""

import json
import logging
from datetime import datetime, timezone

from ...core.events import EVENTS


class SafeJSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        # Unknown/free-text messages and arbitrary extras are intentionally omitted.
        event = record.msg if isinstance(record.msg, str) and record.msg in EVENTS else "application.log"
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "event": event,
        }
        for key in ("duration_ms", "failed_count"):
            value = getattr(record, key, None)
            if type(value) in (int, float):
                payload[key] = value
        status = getattr(record, "status", None)
        if status in ("ok", "error"):
            payload["status"] = status
        # Do not format exc_info: database errors can contain SQL and data values.
        return json.dumps(payload, allow_nan=False)

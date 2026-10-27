"""Privacy-preserving structured application log formatter."""

import json
import logging
import re
from datetime import datetime, timezone

from ...core.events import EVENTS
from ...core.config import MCP_PATH


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
        if event == "server.connection":
            transport = getattr(record, "transport", None)
            if transport in ("http", "stdio"):
                payload.update(transport=transport, authentication="none")
            host = getattr(record, "connection_host", None)
            port = getattr(record, "connection_port", None)
            # Only accept host/port, never arbitrary URLs, headers, or credentials.
            if (transport == "http" and isinstance(host, str)
                    and re.fullmatch(r"[A-Za-z0-9.:-]+", host)
                    and type(port) is int and 0 < port < 65536):
                host = {"0.0.0.0": "127.0.0.1", "::": "::1"}.get(host, host)
                authority = f"[{host}]" if ":" in host else host
                url = f"http://{authority}:{port}{MCP_PATH}"
                payload["url"] = url
                payload["client_config"] = {
                    "mcpServers": {"kedar_cityflow_mcp": {"url": url}}
                }
        # Do not format exc_info: database errors can contain SQL and data values.
        return json.dumps(payload, allow_nan=False)

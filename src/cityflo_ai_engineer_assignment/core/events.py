"""Allowed telemetry vocabulary; never use user input as event labels."""

EVENTS = frozenset({
    "server.started", "server.stopping", "server.stopped", "server.shutdown.complete",
    "server.shutdown.requested", "duckdb.connect", "duckdb.query", "duckdb.close",
    "mcp.get_10th_marks", "observability.publish_failed", "application.log",
})

OBSERVATIONS = EVENTS - {"application.log", "observability.publish_failed", "server.shutdown.complete", "server.shutdown.requested"}

TASK_NAME = "cityflo.record_observation"

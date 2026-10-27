"""Allowed telemetry vocabulary; never use user input as event labels."""

EVENTS = frozenset({
    "server.started", "server.connection", "server.stopping", "server.stopped", "server.shutdown.complete",
    "server.shutdown.requested", "duckdb.connect", "duckdb.query", "duckdb.close",
    "mcp.get_personal_info", "mcp.get_user_skills", "mcp.get_work_experiance",
    "mcp.get_personal_projects", "mcp.get_personal_achievements", "mcp.inspect_session",
    "observability.publish_failed", "application.log",
})

OBSERVATIONS = EVENTS - {"application.log", "observability.publish_failed", "server.shutdown.complete", "server.shutdown.requested", "server.connection"}

TASK_NAME = "cityflo.record_observation"

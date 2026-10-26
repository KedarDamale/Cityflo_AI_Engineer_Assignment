"""SQLite schema and idempotent event persistence owned by the worker."""

import sqlite3
import math
import uuid
from contextlib import closing
from datetime import datetime
from pathlib import Path

from ...core.events import OBSERVATIONS


class SQLiteObservationStore:
    """Every operation owns and closes its SQLite connection."""

    def __init__(self, path: Path):
        self.path = path

    def initialize(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path, timeout=10)) as connection:
            connection.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS observations (
                    event_id TEXT PRIMARY KEY,
                    occurred_at TEXT NOT NULL,
                    event TEXT NOT NULL,
                    status TEXT NOT NULL CHECK (status IN ('ok', 'error')),
                    duration_ms REAL NOT NULL
                );
                CREATE VIEW IF NOT EXISTS metrics AS
                SELECT event, COUNT(*) AS calls,
                       SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) AS failures,
                       AVG(duration_ms) AS average_duration_ms,
                       MAX(duration_ms) AS max_duration_ms
                FROM observations GROUP BY event;
            """)
            connection.commit()

    def write(self, event: dict):
        expected = {"event_id", "occurred_at", "event", "status", "duration_ms"}
        if set(event) != expected or event["event"] not in OBSERVATIONS:
            raise ValueError("Unsupported observation fields or event.")
        if event["status"] not in ("ok", "error"):
            raise ValueError("Unsupported observation status.")
        uuid.UUID(event["event_id"])
        datetime.fromisoformat(event["occurred_at"])
        duration = event["duration_ms"]
        if type(duration) not in (int, float) or not math.isfinite(duration) or duration < 0:
            raise ValueError("Invalid observation duration.")
        # Worker startup creates the schema; each task closes its own connection.
        with closing(sqlite3.connect(self.path, timeout=10)) as connection:
            with connection:
                connection.execute(
                    "INSERT OR IGNORE INTO observations VALUES (?, ?, ?, ?, ?)",
                    [event[key] for key in ("event_id", "occurred_at", "event", "status", "duration_ms")],
                )

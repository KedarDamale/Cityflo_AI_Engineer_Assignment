import io
import json
import tempfile
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path

import duckdb

from cityflo_ai_engineer_assignment.factories import DuckDBFactory, LoggingFactory
from cityflo_ai_engineer_assignment.infrastructure.observability.sqlite import SQLiteObservationStore


class FactoriesTest(unittest.TestCase):
    def test_owned_connections_parameters_and_read_only(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "test.duckdb"
            database = DuckDBFactory.create(path, read_only=False)
            with database:
                database.query("CREATE TABLE sample(value VARCHAR)")
                database.query("INSERT INTO sample VALUES (?)", ["a'quoted value"])
                self.assertEqual(database.query("SELECT value FROM sample").rows, [("a'quoted value",)])
            self.assertFalse(database.connected)
            database.close()
            with self.assertRaises(RuntimeError):
                database.query("SELECT 1")
            with DuckDBFactory.create(path) as reader:
                with self.assertRaises(duckdb.Error):
                    reader.query("DELETE FROM sample")
                self.assertEqual(reader.query("SELECT COUNT(*) FROM sample").rows, [(1,)])

    def test_logs_exclude_free_text_query_values_and_exceptions(self):
        stream = io.StringIO()
        logger = LoggingFactory.create("test." + uuid.uuid4().hex, stream=stream)
        private = "private-test-payload"
        try:
            raise RuntimeError(private)
        except RuntimeError:
            logger.error(private, extra={"sql": private, "parameters": private}, exc_info=True)
        logger.info("duckdb.query", extra={"status": "ok", "duration_ms": 1.5})
        records = [json.loads(line) for line in stream.getvalue().splitlines()]
        self.assertEqual(records[0]["event"], "application.log")
        self.assertEqual(records[1]["duration_ms"], 1.5)
        self.assertNotIn(private, stream.getvalue())

    def test_sqlite_writes_are_idempotent_and_reject_extra_data(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "obs.sqlite"
            store = SQLiteObservationStore(path)
            store.initialize()
            event = {"event_id": str(uuid.uuid4()), "occurred_at": datetime.now(timezone.utc).isoformat(),
                     "event": "duckdb.query", "status": "ok", "duration_ms": 2.0}
            store.write(event)
            store.write(event)
            with self.assertRaises(ValueError):
                store.write({**event, "raw_result": "private-test-payload"})
            with sqlite3.connect(path) as connection:
                self.assertEqual(connection.execute("SELECT calls FROM metrics").fetchone(), (1,))

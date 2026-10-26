"""Prove that an independent real Celery worker persists events after MCP exit."""

import json
import os
import select
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]


class ObservabilityIntegrationTest(unittest.TestCase):
    def test_persistence_after_server_exit(self):
        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder)
            duckdb.connect(str(data / "cityflo.duckdb")).close()
            env = dict(os.environ, CITYFLO_DATA_DIR=str(data))
            server = subprocess.Popen(
                [sys.executable, "-m", "cityflo_ai_engineer_assignment", "--transport", "stdio"],
                cwd=ROOT, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True,
            )
            try:
                def call(payload):
                    server.stdin.write(json.dumps(payload) + "\n")
                    server.stdin.flush()
                    self.assertTrue(select.select([server.stdout], [], [], 15)[0])
                    result = json.loads(server.stdout.readline())
                    self.assertIn("result", result)
                    return result["result"]

                call({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
                    "protocolVersion": "2025-06-18", "capabilities": {},
                    "clientInfo": {"name": "persistence-test", "version": "1"}}})
                server.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
                result = call({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
                    "name": "get_10th_marks", "arguments": {"name": "pravin"}}})
                self.assertFalse(result.get("isError", False))
                server.terminate()
                self.assertEqual(server.wait(timeout=10), 0)
                self.assertIn('"event": "server.shutdown.complete"', server.stderr.read())
            finally:
                if server.poll() is None:
                    server.kill()
                    server.wait(timeout=5)
                for pipe in (server.stdin, server.stdout, server.stderr):
                    pipe.close()

            with sqlite3.connect(data / "obs.sqlite") as connection:
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM observations").fetchone(), (0,))
            self.assertGreater(len(list((data / "celery/queue").glob("*.msg"))), 0)

            with (data / "worker.log").open("w+") as log:
                worker = subprocess.Popen(
                    [sys.executable, "-m", "celery", "-A", "cityflo_ai_engineer_assignment.workers.observability:app",
                     "worker", "--pool=solo", "--concurrency=1", "--loglevel=WARNING",
                     "--without-heartbeat", "--without-gossip", "--without-mingle"],
                    cwd=ROOT, env=env, stdout=log, stderr=log,
                )
                try:
                    deadline = time.monotonic() + 20
                    while True:
                        with sqlite3.connect(data / "obs.sqlite") as connection:
                            counts = dict(connection.execute("SELECT event, COUNT(*) FROM observations GROUP BY event"))
                        if counts.get("server.stopped") == 1 and len(counts) == 6:
                            break
                        self.assertIsNone(worker.poll(), "Celery worker exited early")
                        if time.monotonic() > deadline:
                            log.seek(0)
                            self.fail("Celery did not persist observations: " + log.read())
                        time.sleep(0.1)
                    worker.terminate()
                    self.assertEqual(worker.wait(timeout=10), 0)
                finally:
                    if worker.poll() is None:
                        worker.kill()
                        worker.wait(timeout=5)

            self.assertEqual(counts, {"duckdb.connect": 1, "duckdb.close": 1, "server.started": 1,
                                      "server.stopping": 1, "server.stopped": 1, "mcp.get_10th_marks": 1})
            (ROOT / "outputs/observability-validation.json").write_text(json.dumps({
                "verified": True, "real_celery_worker": True, "server_exited_before_worker_started": True,
                "server_exit_code": 0, "worker_exit_code": 0, "persisted_events": counts,
                "broker": "filesystem", "sqlite": "obs.sqlite",
            }, indent=2) + "\n")

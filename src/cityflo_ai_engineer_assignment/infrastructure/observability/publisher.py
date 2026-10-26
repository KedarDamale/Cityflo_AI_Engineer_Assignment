"""Non-blocking application queue and background Celery task publication."""

import queue
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

from ...core.events import OBSERVATIONS, TASK_NAME


class Observability:
    def __init__(self, app, logger):
        self.app = app
        self.logger = logger
        self._queue = queue.Queue()
        self._lock = threading.Lock()
        self._closed = False
        self._failures = 0
        self._publisher = threading.Thread(target=self._publish, name="observation-publisher", daemon=True)
        self._publisher.start()

    def record(self, event: str, *, status="ok", duration_ms=0.0) -> str:
        if event not in OBSERVATIONS or status not in ("ok", "error"):
            raise ValueError("Unsupported observation event or status.")
        payload = {"event_id": str(uuid.uuid4()), "occurred_at": datetime.now(timezone.utc).isoformat(),
                   "event": event, "status": status, "duration_ms": round(duration_ms, 3)}
        with self._lock:
            if self._closed:
                raise RuntimeError("Observability is closed.")
            self._queue.put_nowait(payload)
        self.logger.info(event, extra={"status": status, "duration_ms": duration_ms})
        return payload["event_id"]

    @contextmanager
    def track(self, event: str):
        started = time.perf_counter()
        status = "ok"
        try:
            yield
        except BaseException:
            status = "error"
            raise
        finally:
            self.record(event, status=status, duration_ms=(time.perf_counter() - started) * 1000)

    def _publish(self):
        while True:
            payload = self._queue.get()
            try:
                if payload is None:
                    return
                self.app.send_task(TASK_NAME, args=[payload], task_id=payload["event_id"],
                                   argsrepr="(<safe-observation>,)", ignore_result=True)
            except Exception:
                self._failures += 1
                self.logger.error("observability.publish_failed", extra={"failed_count": self._failures})
            finally:
                self._queue.task_done()

    def close(self):
        with self._lock:
            if self._closed:
                return
            self._closed = True
            self._queue.put_nowait(None)
        # Only wait for durable publication, not for the independent worker.
        self._publisher.join()
        self.app.close()
        if self._failures:
            raise RuntimeError(f"Failed to publish {self._failures} observations.")

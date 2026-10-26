"""Owned, serialized DuckDB connection and parameterized query adapter."""

import threading
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass
from pathlib import Path

import duckdb


@dataclass(frozen=True)
class QueryResult:
    columns: tuple[str, ...]
    rows: list[tuple]


class DuckDBDatabase:
    def __init__(self, path: Path, *, read_only: bool, observer=None):
        self.path = path
        self.read_only = read_only
        self.observer = observer
        self._connection = None
        self._lock = threading.RLock()

    def _track(self, event):
        return self.observer.track(event) if self.observer else nullcontext()

    def connect(self):
        with self._lock:
            if self._connection is None:
                with self._track("duckdb.connect"):
                    self._connection = duckdb.connect(str(self.path), read_only=self.read_only)
        return self

    @property
    def connected(self):
        with self._lock:
            return self._connection is not None

    @contextmanager
    def connection(self):
        with self._lock:
            if self._connection is None:
                raise RuntimeError("DuckDB is not connected.")
            yield self._connection

    def query(self, sql: str, parameters=None) -> QueryResult:
        # Never log SQL, parameters, result rows, or exception messages.
        with self._track("duckdb.query"), self.connection() as connection:
            cursor = connection.execute(sql, parameters if parameters is not None else [])
            return QueryResult(tuple(item[0] for item in cursor.description), cursor.fetchall())

    def close(self):
        with self._lock:
            if self._connection is not None:
                try:
                    with self._track("duckdb.close"):
                        self._connection.close()
                finally:
                    self._connection = None

    def __enter__(self):
        return self.connect()

    def __exit__(self, *exc):
        self.close()

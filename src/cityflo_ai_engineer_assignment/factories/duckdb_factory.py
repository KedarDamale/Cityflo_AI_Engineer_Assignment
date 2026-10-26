"""Build the query adapter; callers explicitly own its lifecycle."""

from pathlib import Path

from ..core.config import get_data_dir
from ..infrastructure.database.duckdb import DuckDBDatabase, QueryResult


class DuckDBFactory:
    @staticmethod
    def create(path: Path | str | None = None, *, read_only=True, observer=None) -> DuckDBDatabase:
        database = Path(path) if path is not None else get_data_dir() / "cityflo.duckdb"
        return DuckDBDatabase(database.resolve(), read_only=read_only, observer=observer)

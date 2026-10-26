"""Assemble the SQLite store schema, Celery producer, and observation publisher."""

from pathlib import Path

from ..core.config import get_data_dir
from ..infrastructure.observability.publisher import Observability
from ..infrastructure.observability.sqlite import SQLiteObservationStore
from .celery_factory import CeleryFactory
from .logging_factory import LoggingFactory


class ObservabilityFactory:
    @staticmethod
    def create(data_dir: Path | None = None, *, logger=None) -> Observability:
        folder = data_dir or get_data_dir()
        SQLiteObservationStore(folder / "obs.sqlite").initialize()
        return Observability(CeleryFactory.create(folder), logger or LoggingFactory.create("cityflo.observability"))

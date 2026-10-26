"""Run separately: celery -A cityflo_ai_engineer_assignment.worker:app worker --pool=solo."""

import sqlite3

from ..factories.celery_factory import CeleryFactory
from ..core.events import TASK_NAME
from ..infrastructure.observability.sqlite import SQLiteObservationStore
from ..core.config import get_data_dir

app = CeleryFactory.create()
store = SQLiteObservationStore(get_data_dir() / "obs.sqlite")
store.initialize()


@app.task(name=TASK_NAME, ignore_result=True, acks_late=True,
          autoretry_for=(sqlite3.OperationalError,), retry_backoff=True,
          retry_kwargs={"max_retries": 5})
def record_observation(event: dict):
    store.write(event)

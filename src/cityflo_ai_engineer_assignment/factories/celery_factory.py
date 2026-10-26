"""A persistent local filesystem broker; no external broker service required."""

from pathlib import Path

from celery import Celery

from ..core.config import get_data_dir
from ..core.events import TASK_NAME



class CeleryFactory:
    @staticmethod
    def create(data_dir: Path | None = None) -> Celery:
        folder = (data_dir or get_data_dir()) / "celery"
        for child in ("queue", "processed", "control"):
            (folder / child).mkdir(parents=True, exist_ok=True)
        app = Celery("cityflo_observability", broker="filesystem://")
        app.conf.update(
            imports=("cityflo_ai_engineer_assignment.workers.observability",),
            broker_transport_options={
                "data_folder_in": str(folder / "queue"),
                "data_folder_out": str(folder / "queue"),
                "processed_folder": str(folder / "processed"),
                "control_folder": str(folder / "control"),
                "store_processed": False,
                "polling_interval": 0.1,
            },
            task_default_queue="observability",
            task_default_delivery_mode="persistent",
            task_serializer="json",
            accept_content=["json"],
            task_ignore_result=True,
            task_always_eager=False,
            task_acks_late=True,
            worker_prefetch_multiplier=1,
            worker_hijack_root_logger=False,
            worker_redirect_stdouts=False,
            task_publish_retry_policy={"max_retries": 2, "interval_start": 0, "interval_step": 0.1, "interval_max": 0.2},
        )
        return app

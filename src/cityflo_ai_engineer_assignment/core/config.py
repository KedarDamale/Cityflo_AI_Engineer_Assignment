"""Shared paths for the server and its independent observability worker."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def get_data_dir() -> Path:
    path = Path(os.environ.get("CITYFLO_DATA_DIR", ROOT / "data")).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path

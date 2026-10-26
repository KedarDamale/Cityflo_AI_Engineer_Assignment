"""Compatibility entrypoint for the independent Celery worker."""

from .workers.observability import app

__all__ = ["app"]

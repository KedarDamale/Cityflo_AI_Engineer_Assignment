"""Configure application loggers with safe JSON on stderr."""

import logging
import sys

from ..infrastructure.logging.formatter import SafeJSONFormatter


class LoggingFactory:
    @staticmethod
    def create(name: str = "cityflo", *, stream=None) -> logging.Logger:
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        logger.propagate = False
        if not logger.handlers:
            handler = logging.StreamHandler(stream if stream is not None else sys.stderr)
            handler.setFormatter(SafeJSONFormatter())
            logger.addHandler(handler)
        return logger

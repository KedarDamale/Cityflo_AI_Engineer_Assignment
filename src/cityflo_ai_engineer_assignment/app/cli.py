"""Command-line parsing; application composition remains separate."""

import argparse
import asyncio
import logging
import sys

from fastmcp import FastMCP

from .runtime import serve
from .server import create_server


def nonnegative_seconds(value: str) -> int:
    seconds = int(value)
    if seconds < 0:
        raise argparse.ArgumentTypeError("Shutdown timeout must be zero or greater.")
    return seconds


def main(server: FastMCP | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run Cityflo Assignment MCP.")
    parser.add_argument("--transport", choices=("http", "stdio"), default="http")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--shutdown-timeout",
        type=nonnegative_seconds,
        default=10,
        help="Seconds to drain HTTP requests before cancellation (default: 10).",
    )
    args = parser.parse_args()

    # stdout belongs exclusively to JSON-RPC when running over stdio.
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    try:
        asyncio.run(serve(server if server is not None else create_server(), args))
    except KeyboardInterrupt:
        # Also keep an interrupt during startup free of a Python traceback.
        pass

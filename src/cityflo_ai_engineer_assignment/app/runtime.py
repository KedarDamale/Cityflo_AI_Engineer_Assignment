"""HTTP/stdio transport supervision and graceful process signals."""

import argparse
import asyncio
import signal
from contextlib import contextmanager

import uvicorn
from fastmcp import FastMCP

from ..factories.logging_factory import LoggingFactory
from ..infrastructure.transports.stdio import run_stdio

logger = LoggingFactory.create("cityflo.server")


@contextmanager
def shutdown_signals(request_stop):
    """Restore prior handlers and absorb Uvicorn's post-cleanup signal replay."""
    previous = {}
    try:
        for signum in (signal.SIGINT, signal.SIGTERM):
            previous[signum] = signal.signal(signum, lambda sig, frame: request_stop())
        yield
    finally:
        for signum, handler in previous.items():
            signal.signal(signum, handler)


async def serve(mcp: FastMCP, args: argparse.Namespace) -> None:
    if args.transport == "http":
        server = uvicorn.Server(
            uvicorn.Config(
                mcp.http_app(path="/cityflo_mcp"),
                host=args.host,
                port=args.port,
                lifespan="on",
                timeout_graceful_shutdown=args.shutdown_timeout,
                ws="websockets-sansio",
            )
        )
        # Uvicorn drains requests and shuts down the ASGI/MCP lifespan. Its
        # signal replay reaches this handler, allowing a clean process exit.
        with shutdown_signals(lambda: setattr(server, "should_exit", True)):
            await server.serve()
    else:
        task = asyncio.create_task(run_stdio(mcp))
        stopping = False

        def request_stop():
            nonlocal stopping
            if not stopping:
                stopping = True
                logger.info("server.shutdown.requested")
                task.cancel()

        with shutdown_signals(request_stop):
            try:
                await task
            except asyncio.CancelledError:
                if not stopping:
                    raise

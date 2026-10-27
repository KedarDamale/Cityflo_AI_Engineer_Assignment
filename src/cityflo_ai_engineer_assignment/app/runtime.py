"""HTTP/stdio transport supervision and graceful process signals."""

import argparse
import asyncio
import signal
from contextlib import contextmanager

import uvicorn
from fastmcp import FastMCP

from ..factories.logging_factory import LoggingFactory
from ..core.config import MCP_PATH
from ..infrastructure.transports.stdio import run_stdio

logger = LoggingFactory.create("cityflo.server")


class ConnectionLoggingServer(uvicorn.Server):
    async def startup(self, sockets=None) -> None:
        await super().startup(sockets=sockets)
        if self.started:
            # Log only after the listener is bound; port 0 reports its real port.
            port = self.servers[0].sockets[0].getsockname()[1]
            logger.info("server.connection", extra={
                "transport": "http", "connection_host": self.config.host,
                "connection_port": port,
            })


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
        server = ConnectionLoggingServer(
            uvicorn.Config(
                mcp.http_app(path=MCP_PATH),
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
        logger.info("server.connection", extra={"transport": "stdio"})
        loop = asyncio.get_running_loop()
        task = asyncio.create_task(run_stdio(mcp))
        stopping = False

        def request_stop():
            nonlocal stopping
            if not stopping:
                stopping = True
                logger.info("server.shutdown.requested")
                # signal.signal can run while the loop is blocked in select.
                # Wake its self-pipe as well as scheduling cancellation.
                loop.call_soon_threadsafe(task.cancel)

        with shutdown_signals(request_stop):
            try:
                await task
            except asyncio.CancelledError:
                if not stopping:
                    raise

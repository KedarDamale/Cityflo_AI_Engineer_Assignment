"""Acquire shared resources at startup and close them in reverse order."""

import asyncio
from contextlib import asynccontextmanager

from fastmcp import FastMCP

from ..factories import DuckDBFactory, LoggingFactory, ObservabilityFactory, PersonalInfoFactory

logger = LoggingFactory.create("cityflo.server")


@asynccontextmanager
async def server_lifespan(server: FastMCP):
    """Keep resource teardown in the lifespan, after transport shutdown."""
    observer = await asyncio.to_thread(ObservabilityFactory.create, logger=logger)
    database = DuckDBFactory.create(observer=observer)
    try:
        personal_info = await asyncio.to_thread(PersonalInfoFactory.create)
        await asyncio.to_thread(database.connect)
        observer.record("server.started")
        yield {"database": database, "observability": observer, "personal_info": personal_info}
    finally:
        observer.record("server.stopping")
        try:
            await asyncio.to_thread(database.close)
        finally:
            try:
                observer.record("server.stopped")
            finally:
                # The independent worker owns queued SQLite writes after exit.
                await asyncio.to_thread(observer.close)
        logger.info("server.shutdown.complete")

"""Cancellable POSIX stdin reader with the SDK's JSON-RPC transport."""

import asyncio
import os
import sys

from mcp.server.stdio import stdio_server
from fastmcp.server.context import reset_transport, set_transport


async def run_stdio(server):
    # SDK AsyncFile reads run in shielded worker threads and can block shutdown
    # until the peer closes stdin. A pipe reader permits immediate cancellation.
    reader = asyncio.StreamReader(limit=16 * 1024 * 1024)
    pipe = os.fdopen(os.dup(sys.stdin.fileno()), "rb", buffering=0)
    transport = None
    context_token = set_transport("stdio")
    try:
        transport, _ = await asyncio.get_running_loop().connect_read_pipe(
            lambda: asyncio.StreamReaderProtocol(reader), pipe
        )
        # These two FastMCP hooks are isolated here and covered by real protocol
        # and signal tests against the locked SDK version.
        async with server._lifespan_manager():
            async with stdio_server(stdin=reader) as (incoming, outgoing):
                await server._mcp_server.run(
                    incoming, outgoing, server._mcp_server.create_initialization_options()
                )
    finally:
        reset_transport(context_token)
        if transport is not None:
            transport.close()
        else:
            pipe.close()

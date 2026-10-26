"""Composition root: construct MCP and register its tool modules."""

from fastmcp import FastMCP

from .lifecycle import server_lifespan
from ..tools.student_marks import register_tools


def create_server() -> FastMCP:
    server = FastMCP(
        "Cityflo Assignment MCP",
        lifespan=server_lifespan,
        instructions=(
            "Student academic-record lookup for Class 10 / 10th standard / tenth / SSC "
            "examination marks in the connected sample database. Use get_10th_marks "
            "when a user asks how much a student scored, even without mentioning "
            "Cityflo, MCP, or a database. Exact matches return stored marks. Possible "
            "spelling matches are suggestions only: ask the user to confirm the name "
            "before looking up a different student. Scores have no declared unit in "
            "this dataset; do not assume a percentage or total. This server currently "
            "provides student marks, not route or trip analysis."
        ),
    )
    register_tools(server)
    return server

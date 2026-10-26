"""MCP schema and transport adapter for the student marks service."""

from typing import Annotated

from fastmcp import Context, FastMCP
from pydantic import Field

from ..services.student_marks import lookup_marks


def get_10th_marks(
    name: Annotated[
        str,
        Field(
            min_length=1,
            max_length=200,
            description="Student name as provided by the user, for example Pravin or Parveen.",
        ),
    ],
    ctx: Context,
) -> dict:
    """Return exact marks or unconfirmed spelling suggestions, never both."""
    with ctx.lifespan_context["observability"].track("mcp.get_10th_marks"):
        return lookup_marks(name)


def register_tools(server: FastMCP) -> None:
    server.tool(
        title="Look up a student's Class 10 marks",
        description=(
            "Look up a student's Class 10 / 10th standard / tenth / SSC examination "
            "marks by name in the connected sample student database. Use for questions "
            "such as 'How much did Pravin score in 10th?' or 'What are Parveen's SSC "
            "marks?', even if the user does not name Cityflo or this MCP. Ignores "
            "capitalization and surrounding/repeated whitespace. Returns stored marks "
            "only for an exact normalized name. Otherwise returns up to three possible "
            "name matches without marks; ask the user to confirm a suggested name "
            "before another lookup. Similarity scores are spelling similarity, not "
            "identity confidence. Unknown students return not_found; never invent a "
            "result or assume marks are percentages."
        ),
        annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
    )(get_10th_marks)

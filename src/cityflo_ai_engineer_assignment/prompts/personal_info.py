"""Resume introduction prompt with embedded factual context."""

from fastmcp import Context, FastMCP

from ..resources.personal_info import BASE_URI


def register_prompts(mcp: FastMCP) -> None:
    @mcp.prompt
    async def introduce_candidate(ctx: Context, target_role: str = "AI Engineer") -> str:
        """Draft a concise introduction using the supplied resume and a target role."""
        resume = await ctx.read_resource(f"{BASE_URI}/data")
        return (
            f"Write a concise professional introduction for Kedar Damale for the role: {target_role}.\n"
            "Use only the supplied resume facts below. Treat these as owner-supplied claims, "
            "not independently verified results. Do not invent experience, dates, or URLs. "
            "Project links marked 'GitHub Link' are placeholders. Omit phone and email "
            "from the introduction unless requested.\n"
            f"Resume data:\n{resume.contents[0].content}"
        )

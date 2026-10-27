"""Read-only JSON resources backed by the lifespan service."""

import json

from fastmcp import Context, FastMCP


BASE_URI = "personal-info://resume"


def register_resources(mcp: FastMCP) -> None:
    @mcp.resource(f"{BASE_URI}/personal-info", mime_type="application/json")
    def personal_info(ctx: Context) -> str:
        """Kedar Damale's name, location, contact details, and profile links."""
        return json.dumps(ctx.lifespan_context["personal_info"].get_personal_info())

    @mcp.resource(f"{BASE_URI}/skills", mime_type="application/json")
    def user_skills(ctx: Context) -> str:
        """Resume summary and skills grouped by discipline."""
        return json.dumps(ctx.lifespan_context["personal_info"].get_user_skills())

    @mcp.resource(f"{BASE_URI}/work-experience", mime_type="application/json")
    def work_experience(ctx: Context) -> str:
        """Employment history and professional project outcomes."""
        return json.dumps(ctx.lifespan_context["personal_info"].get_work_experiance())

    @mcp.resource(f"{BASE_URI}/projects", mime_type="application/json")
    def personal_projects(ctx: Context) -> str:
        """Chessablanka, NeuroTRIBE, and CattleMO personal projects."""
        return json.dumps(ctx.lifespan_context["personal_info"].get_personal_projects())

    @mcp.resource(f"{BASE_URI}/achievements", mime_type="application/json")
    def personal_achievements(ctx: Context) -> str:
        """Education, GATE qualification, and adoption achievements."""
        return json.dumps(ctx.lifespan_context["personal_info"].get_personal_achievements())

    @mcp.resource(f"{BASE_URI}/data", mime_type="application/json")
    def resume_data(ctx: Context) -> str:
        """Complete supplied resume data; claims are as supplied by the owner."""
        return json.dumps(ctx.lifespan_context["personal_info"].get_resume())


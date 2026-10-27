"""Class-based MCP adapters with resource references and safe context updates."""

import json

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from mcp.types import ResourceLink, TextContent

from ..resources.personal_info import BASE_URI


class PersonalInfoTools:
    async def _read(self, ctx: Context, *, section: str, event: str) -> ToolResult:
        with ctx.lifespan_context["observability"].track(event):
            # Log only fixed event labels, never contact details or resume text.
            await ctx.info(f"{event}.started", logger_name="cityflo.personal_info")
            await ctx.report_progress(0, 1, "Reading resume resource")
            resource = await ctx.read_resource(f"{BASE_URI}/{section}")
            data = json.loads(resource.contents[0].content)
            await ctx.report_progress(1, 1, "Resume resource ready")
            await ctx.info(f"{event}.completed", logger_name="cityflo.personal_info")
            return ToolResult(
                structured_content=data,
                content=[
                    TextContent(type="text", text=json.dumps(data)),
                    ResourceLink(type="resource_link", uri=f"{BASE_URI}/{section}",
                                name=section, mime_type="application/json"),
                ],
            )

    async def get_personal_info(self, ctx: Context) -> ToolResult:
        """Get Kedar Damale's name, location, phone, email, and profile links."""
        return await self._read(ctx, section="personal-info", event="mcp.get_personal_info")

    async def get_user_skills(self, ctx: Context) -> ToolResult:
        """Get Kedar Damale's resume summary and categorized technical skills."""
        return await self._read(ctx, section="skills", event="mcp.get_user_skills")

    async def get_work_experiance(self, ctx: Context) -> ToolResult:
        """Get Kedar Damale's work experience, employers, dates, and project outcomes."""
        return await self._read(ctx, section="work-experience", event="mcp.get_work_experiance")

    async def get_personal_projects(self, ctx: Context) -> ToolResult:
        """Get Kedar Damale's Chessablanka, NeuroTRIBE, and CattleMO projects."""
        return await self._read(ctx, section="projects", event="mcp.get_personal_projects")

    async def get_personal_achievements(self, ctx: Context) -> ToolResult:
        """Get Kedar Damale's education, GATE DA qualification, and achievements."""
        return await self._read(ctx, section="achievements", event="mcp.get_personal_achievements")

    async def inspect_session(self, ctx: Context) -> dict:
        """Inspect this MCP request's identifiers, transport, and protocol version."""
        with ctx.lifespan_context["observability"].track("mcp.inspect_session"):
            return {
                "session_id": ctx.session_id,
                "request_id": ctx.request_id,
                "transport": ctx.transport,
                "protocol_version": getattr(ctx.request_context, "protocol_version", ""),
            }


def register_tools(mcp: FastMCP) -> None:
    tools = PersonalInfoTools()
    response_fields = {
        "get_personal_info": {"personal_info": {"type": "object"}},
        "get_user_skills": {"summary": {"type": "string"}, "skills": {"type": "object"}},
        "get_work_experiance": {"work_experience": {"type": "array", "items": {"type": "object"}}},
        "get_personal_projects": {"projects": {"type": "array", "items": {"type": "object"}}},
        "get_personal_achievements": {"education_and_achievements": {"type": "array", "items": {"type": "string"}}},
        "inspect_session": {
            "session_id": {"type": "string"}, "request_id": {"type": "string"},
            "transport": {"type": "string"}, "protocol_version": {"type": "string"},
        },
    }
    for method in (
        tools.get_personal_info, tools.get_user_skills, tools.get_work_experiance,
        tools.get_personal_projects, tools.get_personal_achievements, tools.inspect_session,
    ):
        fields = response_fields[method.__name__]
        mcp.tool(output_schema={
            "type": "object", "properties": fields, "required": list(fields),
            "additionalProperties": False,
        }, annotations={
            "readOnlyHint": True, "idempotentHint": method != tools.inspect_session,
            "openWorldHint": False,
        })(method)

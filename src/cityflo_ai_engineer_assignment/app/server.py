"""Composition root: construct MCP and register its tool modules."""

from fastmcp import FastMCP

from .lifecycle import server_lifespan
from ..tools.personal_info import register_tools
from ..resources.personal_info import register_resources
from ..prompts.personal_info import register_prompts
from ..route_analysis import make_server as make_route_server


def create_server() -> FastMCP:
    server = FastMCP(
        "Kedar Cityflow MCP",
        lifespan=server_lifespan,
        instructions=(
            "Kedar Damale's supplied resume: use get_personal_info for contact and links, "
            "get_user_skills for summary and skills, get_work_experiance for employment "
            "history, get_personal_projects for projects, and get_personal_achievements "
            "for education and achievements. JSON resources live under personal-info://resume/; "
            "personal-info://resume/data is the complete JSON resume. Tools include links "
            "to the matching section resources. The "
            "introduce_candidate prompt provides resume-grounded writing context. "
            "inspect_session reports only current MCP request metadata, not chat history. "
            "Claims are supplied by the owner; do not invent missing project URLs. "
            "Route delay tools provide exploratory timetable-based analysis."
        ),
    )
    register_resources(server)
    register_tools(server)
    register_prompts(server)
    server.mount(make_route_server())
    return server

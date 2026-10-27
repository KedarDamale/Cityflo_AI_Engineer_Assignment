"""Exercise resume discovery, context, resources, and prompts over real stdio."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

import duckdb
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from cityflo_ai_engineer_assignment.factories import PersonalInfoFactory


ROOT = Path(__file__).resolve().parents[1]
RESUME = ROOT / "src/cityflo_ai_engineer_assignment/my_resume"
BASE_URI = "personal-info://resume"
CASES = {
    "get_personal_info": ("personal-info", ["personal_info"]),
    "get_user_skills": ("skills", ["summary", "skills"]),
    "get_work_experiance": ("work-experience", ["work_experience"]),
    "get_personal_projects": ("projects", ["projects"]),
    "get_personal_achievements": ("achievements", ["education_and_achievements"]),
}


class PersonalInfoTest(unittest.TestCase):
    def test_returned_data_cannot_mutate_service(self):
        service = PersonalInfoFactory.create()
        data = service.get_resume()
        data["personal_info"]["name"] = "modified"
        data["skills"]["programming_and_data"].clear()
        self.assertEqual(service.get_personal_info()["personal_info"]["name"], "Kedar Damale")
        self.assertIn("Python", service.get_user_skills()["skills"]["programming_and_data"])


class PersonalInfoMCPTest(unittest.IsolatedAsyncioTestCase):
    async def test_tools_resources_prompts_and_context(self):
        source = json.loads((RESUME / "personal_info.json").read_text())
        logs, progress = [], []

        async def on_log(message):
            logs.append(message.data["msg"])

        async def on_progress(value, total, message):
            progress.append({"progress": value, "total": total, "message": message})

        evidence = {"transport": "stdio subprocess", "calls": []}
        with tempfile.TemporaryDirectory() as folder:
            duckdb.connect(str(Path(folder) / "cityflo.duckdb")).close()
            transport = StdioTransport(
                command=sys.executable,
                args=["-m", "cityflo_ai_engineer_assignment.main", "--transport", "stdio"],
                cwd=str(ROOT), env={"CITYFLO_DATA_DIR": folder}, keep_alive=False,
            )
            async with Client(transport, init_timeout=20, timeout=15, log_handler=on_log) as client:
                self.assertIn("Kedar Damale", client.instructions)
                tools = await client.list_tools()
                self.assertEqual({t.name for t in tools}, set(CASES) | {"inspect_session"})
                evidence["tools"] = [t.model_dump(mode="json", by_alias=True, exclude_none=True) for t in tools]
                resources = await client.list_resources()
                self.assertEqual({str(r.uri) for r in resources},
                                 {f"{BASE_URI}/{section}" for section, _ in CASES.values()} |
                                 {f"{BASE_URI}/data"})
                evidence["resources"] = [{"uri": str(r.uri), "mime_type": r.mime_type} for r in resources]

                for name, (section, keys) in CASES.items():
                    with self.subTest(tool=name):
                        tool = next(t for t in tools if t.name == name)
                        self.assertEqual(tool.input_schema.get("properties", {}), {})
                        self.assertEqual(tool.output_schema["required"], keys)
                        self.assertTrue(tool.annotations.read_only_hint)
                        before = len(progress)
                        result = await client.call_tool(
                            name, {}, progress_handler=on_progress,
                            meta={"io.modelcontextprotocol/logLevel": "info"},
                        )
                        expected = {key: source[key] for key in keys}
                        self.assertFalse(result.is_error)
                        self.assertEqual(result.structured_content, expected)
                        self.assertEqual(json.loads(result.content[0].text), expected)
                        links = {str(c.uri) for c in result.content if c.type == "resource_link"}
                        self.assertEqual(links, {f"{BASE_URI}/{section}"})
                        resource = await client.read_resource(f"{BASE_URI}/{section}")
                        self.assertEqual(resource[0].mime_type, "application/json")
                        self.assertEqual(json.loads(resource[0].text), expected)
                        self.assertEqual([p["progress"] for p in progress[before:]], [0, 1])
                        evidence["calls"].append({"tool": name, "result_keys": keys, "matches_source": True})

                complete = await client.read_resource(f"{BASE_URI}/data")
                self.assertEqual(json.loads(complete[0].text), source)

                session = (await client.call_tool("inspect_session", {})).structured_content
                self.assertTrue(session["session_id"])
                self.assertTrue(session["request_id"])
                self.assertEqual(session["transport"], "stdio")
                self.assertTrue(session["protocol_version"])
                evidence["session_inspection"] = {"keys": list(session), "verified": True}

                prompts = await client.list_prompts()
                self.assertEqual([p.name for p in prompts], ["introduce_candidate"])
                for arguments, role in [({}, "AI Engineer"), ({"target_role": "Data Engineer"}, "Data Engineer")]:
                    prompt = await client.get_prompt("introduce_candidate", arguments)
                    text = prompt.messages[0].content.text
                    self.assertIn(role, text)
                    self.assertIn("Do not invent", text)
                    embedded = text.split("Resume data:\n", 1)[1]
                    self.assertEqual(json.loads(embedded), source)
                evidence["prompt"] = {"name": "introduce_candidate", "default_and_custom_role": True}

                # An obsolete marks name must no longer resolve.
                missing = await client.call_tool("get_10th_marks", {}, raise_on_error=False)
                self.assertTrue(missing.is_error)

        for name in CASES:
            self.assertIn(f"mcp.{name}.started", logs)
            self.assertIn(f"mcp.{name}.completed", logs)
        for private in (source["personal_info"]["phone"], source["personal_info"]["email"]):
            self.assertNotIn(private, json.dumps(logs))
            self.assertNotIn(private, json.dumps(progress))
        evidence.update(verified=True, context_logs=logs, context_progress=progress)
        (ROOT / "outputs/personal-info-mcp-validation.json").write_text(json.dumps(evidence, indent=2) + "\n")


if __name__ == "__main__":
    unittest.main()

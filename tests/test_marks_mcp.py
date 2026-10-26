"""Verify discovery and name handling through an actual MCP subprocess."""

import json
import sys
import unittest
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import StdioTransport


ROOT = Path(__file__).resolve().parents[1]


class MarksMCPTest(unittest.IsolatedAsyncioTestCase):
    async def test_discovery_and_lookups(self):
        transport = StdioTransport(
            command=sys.executable,
            args=["-m", "cityflo_ai_engineer_assignment.main", "--transport", "stdio"],
            cwd=str(ROOT),
        )
        evidence = {"transport": "stdio subprocess", "calls": []}
        async with Client(transport, init_timeout=15, timeout=10) as client:
            instructions = client.instructions
            self.assertIn("Class 10", instructions)
            self.assertIn("confirm", instructions)
            evidence["instructions"] = instructions

            tools = await client.list_tools()
            tool = next(t for t in tools if t.name == "get_10th_marks")
            for term in ("Class 10", "10th standard", "SSC", "Parveen", "confirm"):
                self.assertIn(term, tool.description)
            self.assertIn("description", tool.input_schema["properties"]["name"])
            self.assertEqual(tool.input_schema["required"], ["name"])
            self.assertTrue(tool.annotations.read_only_hint)
            self.assertIsNotNone(tool.output_schema)
            evidence["tool"] = tool.model_dump(mode="json", by_alias=True, exclude_none=True)

            cases = [
                ("pravin", "found"),
                ("  PrAvIn  ", "found"),
                ("parveen", "confirmation_required"),
                ("pravi", "confirmation_required"),
                ("zzzzzz", "not_found"),
                ("pr", "not_found"),
            ]
            for name, expected_status in cases:
                with self.subTest(name=name):
                    result = await client.call_tool("get_10th_marks", {"name": name})
                    self.assertFalse(result.is_error)
                    record = result.data
                    self.assertEqual(record["status"], expected_status)
                    if expected_status == "found":
                        self.assertEqual(record["student_name"], "pravin")
                        self.assertEqual(record["marks"], 60.0)
                        self.assertEqual(record["marks_unit"], "unspecified")
                    else:
                        self.assertNotIn("marks", record)
                        self.assertLessEqual(len(record["suggestions"]), 3)
                        for candidate in record["suggestions"]:
                            self.assertNotIn("marks", candidate)
                        if name == "parveen":
                            self.assertEqual(record["suggestions"][0]["student_name"], "pravin")
                    evidence["calls"].append({"arguments": {"name": name}, "result": record})

            for arguments in ({"name": ""}, {"name": "   "}, {"name": 123}, {}):
                with self.subTest(invalid_arguments=arguments):
                    result = await client.call_tool(
                        "get_10th_marks", arguments, raise_on_error=False
                    )
                    self.assertTrue(result.is_error)
                    evidence["calls"].append({"arguments": arguments, "is_error": True})

        evidence["verified"] = True
        destination = ROOT / "outputs" / "mcp-discovery-validation.json"
        destination.parent.mkdir(exist_ok=True)
        destination.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()

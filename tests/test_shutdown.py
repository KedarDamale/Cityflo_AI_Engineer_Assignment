"""Exercise real process signals, stdio EOF, and an in-flight HTTP request."""

import asyncio
import json
import select
import signal
import socket
import subprocess
import sys
import threading
import time
import unittest
from pathlib import Path
from urllib.request import urlopen

from fastmcp import Client


ROOT = Path(__file__).resolve().parents[1]
HTTP_FIXTURE = """
import asyncio
import sys
from starlette.responses import PlainTextResponse
from cityflo_ai_engineer_assignment.main import mcp, main

async def slow_request(request):
    print('TEST_REQUEST_STARTED', file=sys.stderr, flush=True)
    await asyncio.sleep(0.5)
    return PlainTextResponse('finished')

mcp.custom_route('/test-inflight', methods=['GET'])(slow_request)
main()
"""


@unittest.skipUnless(sys.platform != "win32", "POSIX process signals required")
class ShutdownTest(unittest.TestCase):
    def start_server(self, transport, port=8000, *, direct_script=False):
        command = [sys.executable, "-u"]
        command += (
            ["-c", HTTP_FIXTURE]
            if transport == "http"
            else ([str(ROOT / "src/cityflo_ai_engineer_assignment/main.py")]
                  if direct_script else ["-m", "cityflo_ai_engineer_assignment.main"])
        )
        command += ["--transport", transport, "--port", str(port), "--shutdown-timeout", "2"]
        process = subprocess.Popen(
            command, cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True,
        )
        self.addCleanup(self.close_process, process)
        logs = []
        started = threading.Event()

        def read_logs():
            for line in process.stderr:
                logs.append(line)
                if "TEST_REQUEST_STARTED" in line:
                    started.set()

        reader = threading.Thread(target=read_logs, daemon=True)
        reader.start()
        return process, logs, started, reader

    @staticmethod
    def close_process(process):
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        for pipe in (process.stdin, process.stdout, process.stderr):
            if pipe and not pipe.closed:
                pipe.close()

    def send(self, process, payload):
        process.stdin.write(json.dumps(payload) + "\n")
        process.stdin.flush()

    def receive(self, process):
        self.assertTrue(select.select([process.stdout], [], [], 15)[0], "MCP reply timed out")
        result = json.loads(process.stdout.readline())
        while "id" not in result:
            result = json.loads(process.stdout.readline())
        return result

    def assert_clean_exit(self, process, logs, reader):
        try:
            code = process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.fail("Shutdown timed out. Server stderr:\n" + "".join(logs))
        self.assertEqual(code, 0)
        reader.join(timeout=2)
        text = "".join(logs)
        self.assertEqual(text.count('"event": "server.shutdown.complete"'), 1, text)
        self.assertNotIn("Traceback", text)
        self.assertNotIn("CancelledError", text)

    def test_shutdown(self):
        evidence = []
        for stop in (signal.SIGINT, signal.SIGTERM, "EOF"):
            with self.subTest(transport="stdio", stop=str(stop)):
                direct_script = stop == signal.SIGTERM
                process, logs, _, reader = self.start_server("stdio", direct_script=direct_script)
                self.send(process, {
                    "jsonrpc": "2.0", "id": 1, "method": "initialize",
                    "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                               "clientInfo": {"name": "shutdown-test", "version": "1"}},
                })
                self.assertIn("result", self.receive(process))
                self.send(process, {"jsonrpc": "2.0", "method": "notifications/initialized"})
                self.send(process, {
                    "jsonrpc": "2.0", "id": 2, "method": "tools/call",
                    "params": {"name": "get_user_skills", "arguments": {}},
                })
                self.assertFalse(self.receive(process)["result"].get("isError", False))
                if stop == "EOF":
                    process.stdin.close()
                else:
                    process.send_signal(stop)
                self.assert_clean_exit(process, logs, reader)
                if stop != "EOF":
                    self.assertIn("server.shutdown.requested", "".join(logs))
                self.assertEqual(process.stdout.read(), "")
                connection = next(json.loads(line) for line in logs
                                  if '"event": "server.connection"' in line)
                self.assertEqual(connection["transport"], "stdio")
                self.assertEqual(connection["authentication"], "none")
                self.assertNotIn("url", connection)
                evidence.append({"transport": "stdio", "stop": stop if stop == "EOF" else stop.name,
                                 "entrypoint": "direct file" if direct_script else "module",
                                 "exit_code": 0, "cleanup_completed_once": True})

        for stop in (signal.SIGINT, signal.SIGTERM):
            with self.subTest(transport="http", stop=stop.name):
                with socket.socket() as reserved:
                    reserved.bind(("127.0.0.1", 0))
                    port = reserved.getsockname()[1]
                # A dynamically assigned port must be advertised accurately too.
                process, logs, started, reader = self.start_server("http", 0 if stop == signal.SIGTERM else port)
                deadline = time.monotonic() + 15
                while not any('"event": "server.connection"' in line for line in logs):
                    self.assertIsNone(process.poll(), "HTTP server exited during startup")
                    self.assertLess(time.monotonic(), deadline, "Connection log timed out")
                    time.sleep(0.05)
                connection = next(json.loads(line) for line in logs
                                  if '"event": "server.connection"' in line)
                from urllib.parse import urlsplit
                port = urlsplit(connection["url"]).port
                self.assertEqual(connection["authentication"], "none")
                self.assertEqual(connection["transport"], "http")
                self.assertEqual(connection["client_config"]["mcpServers"]["kedar_cityflow_mcp"]["url"], connection["url"])

                async def verify_advertised_connection():
                    async with Client(connection["url"], timeout=10) as client:
                        result = await client.call_tool("inspect_session", {})
                        self.assertEqual(result.structured_content["transport"], "streamable-http")

                asyncio.run(verify_advertised_connection())
                while True:
                    try:
                        with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                            break
                    except OSError:
                        self.assertIsNone(process.poll(), "HTTP server exited during startup")
                        self.assertLess(time.monotonic(), deadline, "HTTP startup timed out")
                        time.sleep(0.05)

                responses = []

                def request():
                    try:
                        with urlopen(f"http://127.0.0.1:{port}/test-inflight", timeout=10) as response:
                            responses.append(response.read().decode())
                    except Exception as error:
                        responses.append(repr(error))

                requester = threading.Thread(target=request, daemon=True)
                requester.start()
                self.assertTrue(started.wait(timeout=5), "HTTP request did not begin")
                process.send_signal(stop)
                self.assert_clean_exit(process, logs, reader)
                requester.join(timeout=2)
                self.assertEqual(responses, ["finished"])
                with socket.socket() as probe:
                    self.assertNotEqual(probe.connect_ex(("127.0.0.1", port)), 0)
                evidence.append({"transport": "http", "stop": stop.name, "exit_code": 0,
                                 "advertised_url_mcp_call_verified": True,
                                 "in_flight_response_completed": True, "listener_closed": True,
                                 "cleanup_completed_once": True})

        (ROOT / "outputs" / "server-shutdown-validation.json").write_text(
            json.dumps({"verified": True, "cases": evidence}, indent=2) + "\n", encoding="utf-8"
        )

# Cityflo Assignment MCP

This server exposes Kedar Damale's supplied résumé through personal-info tools,
JSON resources, and a reusable introduction prompt. It owns a read-only DuckDB
connection, and sends safe operational observations to an independent Celery
worker that persists them in SQLite. Route analysis for the take-home is not
implemented.

## Source layout

```text
src/cityflo_ai_engineer_assignment/
  main.py                   # stable console/module entrypoint
  __main__.py               # python -m cityflo_ai_engineer_assignment
  worker.py                 # compatibility Celery entrypoint
  app/
    cli.py                  # CLI options
    server.py               # MCP construction and tool registration
    lifecycle.py            # resource acquisition and reverse-order cleanup
    runtime.py              # HTTP/stdio supervision and signals
  core/
    config.py               # shared paths and environment configuration
    events.py               # permitted telemetry vocabulary
  services/
    personal_info.py        # PersonalInfo access rules; no MCP or database dependency
  tools/
    personal_info.py        # PersonalInfoTools adapters and context notifications
  resources/
    personal_info.py        # @mcp.resource JSON sections
  prompts/
    personal_info.py        # @mcp.prompt introduce_candidate
  my_resume/
    personal_info.json      # single source of supplied résumé facts
  factories/
    duckdb_factory.py
    logging_factory.py
    observability_factory.py
    celery_factory.py
    personal_info_factory.py
  infrastructure/
    database/duckdb.py      # connection ownership and parameterized queries
    logging/formatter.py   # safe JSON formatting
    observability/
      publisher.py          # background task publisher
      sqlite.py             # SQLite schema and idempotent writes
    transports/stdio.py    # cancellable pipe reader using the real MCP SDK
  workers/
    observability.py        # Celery application and persistence task
```

Application composition connects factories, services, resources, and infrastructure.
Business rules do not import MCP or worker code. Add tools in `tools/`, their
business logic in `services/`, and register them in `app/server.py`. Factories
construct adapters; `app/lifecycle.py` owns their startup and cleanup.
`PersonalInfoFactory.create()` loads packaged JSON once during
startup. Resource handlers use that service from `ctx.lifespan_context`.
`PersonalInfoTools` reads its matching JSON resource through `ctx.read_resource`;
each result contains the requested structured data, readable JSON, and links to
the section resource. Service getters return copies so callers
cannot modify subsequent results. Each server gets its own service instance.

## Install and run

From the project root:

```bash
uv sync --locked
uv run cityflo-ai-engineer-assignment
```

The server expects `data/cityflo.duckdb` to exist. To process observations, start
the independent worker in another terminal:

```bash
uv run celery -A cityflo_ai_engineer_assignment.workers.observability:app worker --pool=solo --concurrency=1 --loglevel=WARNING --without-heartbeat --without-gossip --without-mingle
```

The worker can be started before or after MCP. Both use the same data directory;
set `CITYFLO_DATA_DIR` identically for both processes to override `data/`.
The local broker stores pending tasks in `data/celery/queue/`, so Redis is not
required for this single-host setup. The worker creates or uses `data/obs.sqlite`.

Connect a Streamable HTTP MCP client to
`http://127.0.0.1:8000/kedar_cityflow_mcp`. The host and port can be changed with
`--host` and `--port`. The equivalent module command is:

```bash
uv run python -m cityflo_ai_engineer_assignment.main
```

After HTTP startup succeeds, stderr contains a JSON `server.connection` log with
the actual MCP URL, `transport: "http"`, `authentication: "none"`, and a copyable
`client_config` object:

```json
{"mcpServers": {"kedar_cityflow_mcp": {"url": "http://127.0.0.1:8000/kedar_cityflow_mcp"}}}
```

This server requires no username, password, or bearer token. The URL uses your
selected host and port (including the assigned port with `--port 0`). Binding to
`0.0.0.0` or `::` displays a loopback URL for a client on the same machine; remote
clients must substitute the server's reachable hostname. Stdio startup logs its
transport and authentication status on stderr; it has no HTTP URL.

Direct file execution also works from the project root with the project's
virtual environment active:

```bash
python3 src/cityflo_ai_engineer_assignment/main.py
```

For clients that launch the server over stdio:

```bash
uv run cityflo-ai-engineer-assignment --transport stdio
```

A client configuration template follows. Set `cwd` to your checkout's absolute
path; it is a placeholder, not a command to run literally. Configuration field
support varies by client; clients without `cwd` can use uv's `--directory` flag.

```json
{
  "mcpServers": {
    "cityflo_assignment": {
      "command": "uv",
      "args": ["run", "cityflo-ai-engineer-assignment", "--transport", "stdio"],
      "cwd": "<absolute-path-to-your-checkout>"
    }
  }
}
```

## Discovery and calls

Server instructions describe the supplied résumé, available tools, and resource
URIs. All résumé tools take no arguments and have structured output schemas and
read-only annotations:

| Tool | Structured result keys | JSON resource |
| --- | --- | --- |
| `get_personal_info` | `personal_info` | `personal-info://resume/personal-info` |
| `get_user_skills` | `summary`, `skills` | `personal-info://resume/skills` |
| `get_work_experiance` | `work_experience` | `personal-info://resume/work-experience` |
| `get_personal_projects` | `projects` | `personal-info://resume/projects` |
| `get_personal_achievements` | `education_and_achievements` | `personal-info://resume/achievements` |

`get_work_experiance` intentionally preserves the requested method/tool spelling.
`PersonalInfo` is the business service; `PersonalInfoTools` is the MCP adapter.
Use `PersonalInfoFactory.create()` for Python callers.

The host application controls whether these descriptions enter the model's
context or its tool search index. Server descriptions help discovery but cannot
force tool selection. If you control the host, configure it to check connected
tools for relevant factual lookups before requesting missing information.
Restart the running server and reconnect or refresh the MCP client after changes
so it retrieves the new instructions and tool metadata.

Representative `tools/call` parameters:

```json
{"name": "get_user_skills", "arguments": {}}
```

The structured result is `{"summary": "...", "skills": {...}}`, matching the
supplied data exactly. Work experience contains both employers; projects contain
Chessablanka, NeuroTRIBE, and CattleMO. Project URLs supplied as `GitHub Link`
remain placeholders; résumé claims have not been independently verified.

Use `resources/list` to discover all six JSON resources. `resources/read` parameters:

```json
{"uri": "personal-info://resume/data"}
```

This returns the complete JSON résumé with MIME type `application/json`.
The supplied JSON is the résumé source; no image loading or parsing is required.

Use `prompts/list`, then `prompts/get`:

```json
{"name": "introduce_candidate", "arguments": {"target_role": "AI Engineer"}}
```

The prompt embeds the complete JSON data so the
model has factual context. `target_role` defaults to `AI Engineer`. Retrieving the
prompt does not run a model or generate the introduction by itself.

## Context, logs, and progress

Each résumé tool emits fixed start/completion messages through `ctx.info` and
progress 0/1 through `ctx.report_progress`. With MCP 2026-07-28, request info logs
using `_meta: {"io.modelcontextprotocol/logLevel": "info"}`; older clients use
`logging/setLevel`. Send a progress token to receive progress notifications.
Tools also retain the
existing Celery observation timings. Notifications and observations contain no
phone numbers, email addresses, or résumé text. Contact details appear only in
the explicitly requested résumé data/resources.

Call `inspect_session` with `{}` to see the current request ID, connection/session
ID, transport, and protocol version. It does not expose credentials or chat
history. With MCP 2026-07-28, a connection identifier may change per request;
it should not be treated as a persistent conversation identity.

Example real client (start the HTTP server first):

```python
import asyncio
from fastmcp import Client

async def on_log(message):
    print(message.data)  # fixed event labels only

async def on_progress(progress, total, message):
    print(progress, total, message)

async def main():
    async with Client("http://127.0.0.1:8000/kedar_cityflow_mcp", log_handler=on_log) as client:
        if client.protocol_version != "2026-07-28":
            await client.set_logging_level("info")
        result = await client.call_tool(
            "get_user_skills", {}, progress_handler=on_progress,
            meta={"io.modelcontextprotocol/logLevel": "info"},
        )
        print(result.structured_content)
        await client.read_resource("personal-info://resume/data")
        await client.get_prompt("introduce_candidate", {"target_role": "AI Engineer"})
        print((await client.call_tool("inspect_session", {})).structured_content)

asyncio.run(main())
```

Context/resource/prompt behavior follows the [FastMCP context documentation](https://gofastmcp.com/servers/context),
[resource documentation](https://gofastmcp.com/servers/resources), and
[prompt documentation](https://gofastmcp.com/servers/prompts), checked against the locked SDK.

## Verify the real MCP connection

```bash
uv run python -m unittest discover -s tests -v
```

The test launches a separate server process over stdio through a real FastMCP
client. It checks all five résumé payloads against the source JSON, tool metadata,
all JSON resource payloads, the prompt with default/custom role,
session inspection, client logs/progress, and removal of the old marks tool.
It writes safe metadata and validation results to
`outputs/personal-info-mcp-validation.json`. This verifies protocol integration;
automatic selection by a particular model still needs testing in that host.

## Graceful shutdown

Press Ctrl+C once in the server terminal, or send SIGTERM to the server process.
HTTP stops accepting connections, allows active HTTP requests up to 10 seconds
to finish, and then closes MCP sessions and runs lifespan cleanup. Configure
the request drain period with:

```bash
uv run cityflo-ai-engineer-assignment --shutdown-timeout 20
```

Stdio handles Ctrl+C and SIGTERM by cancelling the serving task and awaiting
transport/lifespan cleanup. Closing the client's stdin pipe also shuts it down.
Stdio calls may be cancelled during shutdown; the HTTP drain timeout does not
apply to stdio. Normal shutdown exits with code 0 and writes its completion
message to stderr, keeping stdout available for MCP JSON-RPC. The cancellable
pipe implementation is tested on POSIX and isolates internal FastMCP hooks
in `infrastructure/transports/stdio.py`; retest when changing the locked SDK.

On startup, the lifespan initializes the SQLite schema (then closes that setup
connection), starts the background publisher, loads the personal-info service,
and opens DuckDB. On shutdown it
closes DuckDB, records the final lifecycle observations, flushes publication to
the persistent Celery queue, and closes the Celery producer. The independent
worker continues processing pending observations after MCP exits. Each worker
task commits and closes its own SQLite connection; there is no open SQLite
connection left in the MCP process.

Stop the worker separately with Ctrl+C or SIGTERM when desired. A warm worker
shutdown finishes its active task; pending queue files remain for its next run.

## Query and observation factories

```python
from cityflo_ai_engineer_assignment.factories import DuckDBFactory, ObservabilityFactory

observer = ObservabilityFactory.create()
try:
    with DuckDBFactory.create(observer=observer) as database:
        result = database.query("SELECT COUNT(*) FROM trips WHERE route = ?", ["R-12"])
finally:
    observer.close()
```

MCP tools access the already-open database through
`ctx.lifespan_context["database"]`, rather than opening a connection for each call.
The personal-info tools use the packaged résumé service; their calls are timed
through the same observer.

Observations record only event IDs, timestamps, fixed event categories, status,
and duration. SQL text, parameters, result rows, exception messages, phone
numbers, and complaint text are excluded. Application logs use safe JSON on
stderr. SQLite provides `observations` and an aggregate `metrics` view:

```sql
SELECT event, calls, failures, average_duration_ms FROM metrics;
```

Requests enqueue observations in memory; a publisher thread performs broker I/O
and Celery performs SQLite writes. UUID generation, queueing, and stderr logging
still have a small cost. Graceful shutdown flushes the publisher before exit.
Forced termination before that flush can lose unpublished observations; the
filesystem broker is a local development transport, not a guarantee against
worker crashes or disk failure. Horizontal deployment would require a shared
broker and a suitable shared metrics backend. The DuckDB adapter serializes
access to its owned connection.

The integration suite verifies a real Celery worker processing queued events
after the MCP process exits. Evidence is in
`outputs/observability-validation.json`; signal/EOF evidence is in
`outputs/server-shutdown-validation.json`.

The CSV inputs are retained in `data/`. The raw ops log is excluded from Git;
its official retrieval path is recorded in `sources.json`.

## CSV inputs in DuckDB

Each CSV becomes a table named after the file: `trips` and `schedule_v2`.
All columns are stored as `VARCHAR` to retain original identifiers, timestamps,
offsets, and anomalies for later analysis; empty fields become SQL `NULL`.
Use explicit casts such as `TRY_CAST(scheduled_runtime_min AS DOUBLE)` in queries.
The existing database contains 5,292 trip rows and 2 timetable rows. Original
CSV hashes are in `sources.json`. The database, observability SQLite files,
and broker files are generated local artifacts excluded from Git.

If the database is absent, recreate it from the source CSVs with:

```python
from pathlib import Path
from cityflo_ai_engineer_assignment.factories import DuckDBFactory

with DuckDBFactory.create(read_only=False) as database:
    for source in sorted(Path("data").glob("*.csv")):
        table = '"' + source.stem.replace('"', '""') + '"'
        database.query(
            f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM read_csv(?, header=true, all_varchar=true)",
            [str(source)],
        )
```

For example, in DuckDB:

```sql
SELECT route, COUNT(*) AS trips
FROM trips
GROUP BY route
ORDER BY route;
```

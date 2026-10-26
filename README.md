# Cityflo Assignment MCP

This server exposes sample Class 10 marks lookups, owns a read-only DuckDB
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
    student_marks.py        # lookup rules; no MCP or database dependency
  tools/
    student_marks.py        # MCP schemas and service adapters
  factories/
    duckdb_factory.py
    logging_factory.py
    observability_factory.py
    celery_factory.py
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

Application composition connects factories, services, and infrastructure.
Business rules do not import MCP or worker code. Add tools in `tools/`, their
business logic in `services/`, and register them in `app/server.py`. Factories
construct adapters; `app/lifecycle.py` owns their startup and cleanup.

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
`http://127.0.0.1:8000/cityflo_mcp`. The host and port can be changed with
`--host` and `--port`. The equivalent module command is:

```bash
uv run python -m cityflo_ai_engineer_assignment.main
```

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

Server initialization supplies instructions explaining the available academic
records. `tools/list` exposes `get_10th_marks` with a description that includes
Class 10, 10th standard, tenth, SSC, and example questions. It also exposes a
described `name` parameter, structured output schema, and read-only annotations.
Users can ask "How much did Pravin score in 10th?" without naming the MCP.

The host application controls whether these descriptions enter the model's
context or its tool search index. Server descriptions help discovery but cannot
force tool selection. If you control the host, configure it to check connected
tools for relevant factual lookups before requesting missing information.
Restart the running server and reconnect or refresh the MCP client after changes
so it retrieves the new instructions and tool metadata.

Representative `tools/call` parameters:

```json
{"name": "get_10th_marks", "arguments": {"name": "Pravin"}}
```

The result has `status: "found"`, `student_name: "pravin"`, `standard: 10`,
`marks: 60.0`, and `marks_unit: "unspecified"`. The source data does not declare
whether its numbers are percentages or marks out of a particular total.
Capitalization and surrounding/repeated whitespace are normalized.

```json
{"name": "get_10th_marks", "arguments": {"name": "Parveen"}}
```

This returns `status: "confirmation_required"` and a suggestion for `pravin`,
with no marks. The agent should ask whether the user means Pravin before making
another lookup. Suggestions use RapidFuzz WRatio at a cutoff of 60/100, at most
three candidates, and alphabetical ordering before scoring for stable ties.
The cutoff is deliberately permissive for spelling suggestions, not an identity
decision; similarity is not a probability that two names identify one person.
Queries shorter than three characters receive no fuzzy suggestions.
Unknown names return `not_found`; blank names and invalid parameter types are
tool errors. Neither unsuccessful path dumps the database.

## Verify the real MCP connection

```bash
uv run python -m unittest discover -s tests -v
```

The test launches a separate server process over stdio through a real FastMCP
client. It checks initialization instructions, `tools/list` metadata, and
`tools/call` responses for exact names, capitalization, misspellings, unknown
names, and invalid input. It writes the observed metadata and results to
`outputs/mcp-discovery-validation.json`. This verifies protocol integration;
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
pipe implementation is tested on POSIX and isolates two internal FastMCP hooks
in `infrastructure/transports/stdio.py`; retest when changing the locked SDK.

On startup, the lifespan initializes the SQLite schema (then closes that setup
connection), starts the background publisher, and opens DuckDB. On shutdown it
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
The sample marks tool continues to use its sample student data; its calls are
timed through the same observer.

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

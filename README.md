# Cityflo Assignment MCP

This project provides an experimental route delay MCP server and also exposes Kedar Damale's supplied résumé through personal-info tools,
JSON resources, and a reusable introduction prompt. It owns a read-only DuckDB
connection, and sends safe operational observations to an independent Celery
worker that persists them in SQLite. The route analysis and decision remain conditional on identifying 4xx vehicles.

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

## Experimental route delay MCP server

Run separately from the résumé server:

```bash
uv run python -m cityflo_ai_engineer_assignment.route_analysis
```

Stdio client configuration: `{"command":"uv","args":["run","python","-m","cityflo_ai_engineer_assignment.route_analysis"]}` from the project root. Tools: `route_delays`, `worst_routes` (e.g. `{"limit":3,"method":"median"}`), `evaluate_methods`, and `route_evidence` (e.g. `{"route":"R-14"}`). This reads CSV files directly, not the potentially stale DuckDB copy. It never reads the raw ops log.

This is an exploratory implementation, not a finished decision. Scheduled departures are interpreted in Mumbai UTC+05:30; arrival offsets are interpreted as stamped, without assuming an incorrect device clock can be corrected automatically. Negative elapsed time and elapsed time above six hours are excluded as provisional plausibility bounds. Missing or malformed values are excluded. These bounds require further sensitivity analysis. Signed delays are retained. The 10-minute tail count is descriptive, not an agreed verdict threshold. The median ranking breaks ties by route code.

REC-114 is applied only to explicit numeric series 400–499 with an effective timetable row; missing applicable rows are excluded. The supplied data guide describes the series field as only the last two digits, so two-digit values cannot establish 4xx membership. The exported results therefore use the original runtime for those rows and are **not confirmed REC-114-compliant**. A mapping or documented assumption is needed before operational use. The current trips CSV differs from the recorded original SHA-256; it is preserved unchanged. The original blob is available in Git history and must be reconciled before finalizing results.

`evaluate_methods` compares all four rankings, 5%, 10%, and 20% trims, and median rankings after leaving out each day. It does not yet complete the agreed evaluation of excluded-record sensitivity, Huber parameter sensitivity, genuine extreme delays, and borderline operational costs. No final threshold or verdict has been selected.

The route server can also be started over HTTP with:

```bash
uv run python -c 'from cityflo_ai_engineer_assignment.route_analysis import make_server; make_server().run(transport="http", host="127.0.0.1", port=8025, show_banner=False)'
```

Connect a Streamable HTTP MCP client to `http://127.0.0.1:8025/mcp`. Route tools are also mounted in the existing server code, but an already-connected client must restart and rediscover tools. See `outputs/method-evaluation.md` for exploratory results and limitations.

## Data quality and limitations of robust summaries

The current analysis identifies **42 excluded rows**, not 43: 24 have an unparseable actual-arrival timestamp and 18 have an arrival five minutes before scheduled departure after applying the stated offset. The latter is physically inconsistent with the scheduled departure as an assumed departure time, but could also reflect an early departure or a clock problem; without actual departure, exclusion is a conservative assumption, not proof the records are wrong. A further included row has a nonstandard offset and is documented separately below.

| Trip | Route | Finding | Treatment |
|---|---|---|---|
| T1-00136 | R-01 | Actual arrival is not parseable | Excluded: delay cannot be calculated |
| T1-00352 | R-03 | Actual arrival is not parseable | Excluded: delay cannot be calculated |
| T1-00361 | R-03 | Arrival is 5 min before scheduled departure | Excluded by provisional elapsed-time rule |
| T1-00392 | R-04 | Arrival is 5 min before scheduled departure | Excluded by provisional elapsed-time rule |
| T1-00417 | R-04 | Arrival is 5 min before scheduled departure | Excluded by provisional elapsed-time rule |
| T1-00470 | R-04 | Actual arrival is not parseable | Excluded: delay cannot be calculated |
| T1-00673 | R-06 | Arrival is 5 min before scheduled departure | Excluded by provisional elapsed-time rule |
| T1-00734 | R-06 | Actual arrival is not parseable | Excluded: delay cannot be calculated |
| T1-01111 | R-09 | Arrival is 5 min before scheduled departure | Excluded by provisional elapsed-time rule |
| T1-01303 | R-11 | Arrival is 5 min before scheduled departure | Excluded by provisional elapsed-time rule |
| T1-01372 | R-11 | Actual arrival is not parseable | Excluded: delay cannot be calculated |
| T1-01419 | R-11 | Arrival is 5 min before scheduled departure | Excluded by provisional elapsed-time rule |
| T1-01691 | R-14 | Arrival is 5 min before scheduled departure | Excluded by provisional elapsed-time rule |
| T1-02034 | R-16 | Actual arrival is not parseable | Excluded: delay cannot be calculated |
| T1-02470 | R-19 | Actual arrival is not parseable | Excluded: delay cannot be calculated |
| T1-02488 | R-20 | Arrival is 5 min before scheduled departure | Excluded by provisional elapsed-time rule |
| T1-02585 | R-20 | Actual arrival is not parseable | Excluded: delay cannot be calculated |
| T1-02697 | R-21 | Arrival is 5 min before scheduled departure | Excluded by provisional elapsed-time rule |
| T1-02730 | R-21 | Arrival is 5 min before scheduled departure | Excluded by provisional elapsed-time rule |
| T1-02930 | R-23 | Actual arrival is not parseable | Excluded: delay cannot be calculated |
| T1-03142 | R-24 | Arrival is 5 min before scheduled departure | Excluded by provisional elapsed-time rule |
| T1-03274 | R-25 | Actual arrival is not parseable | Excluded: delay cannot be calculated |
| T1-03297 | R-26 | Actual arrival is not parseable | Excluded: delay cannot be calculated |
| T1-03377 | R-26 | Arrival is 5 min before scheduled departure | Excluded by provisional elapsed-time rule |
| T1-03396 | R-27 | Actual arrival is not parseable | Excluded: delay cannot be calculated |
| T1-03414 | R-27 | Actual arrival is not parseable | Excluded: delay cannot be calculated |
| T1-03490 | R-27 | Actual arrival is not parseable | Excluded: delay cannot be calculated |
| T1-03491 | R-27 | Arrival is 5 min before scheduled departure | Excluded by provisional elapsed-time rule |
| T1-03636 | R-28 | Arrival is 5 min before scheduled departure | Excluded by provisional elapsed-time rule |
| T1-03641 | R-28 | Actual arrival is not parseable | Excluded: delay cannot be calculated |
| T1-03669 | R-28 | Actual arrival is not parseable | Excluded: delay cannot be calculated |
| T1-03716 | R-29 | Actual arrival is not parseable | Excluded: delay cannot be calculated |
| T1-03733 | R-29 | Actual arrival is not parseable | Excluded: delay cannot be calculated |
| T1-03822 | R-29 | Actual arrival is not parseable | Excluded: delay cannot be calculated |
| T1-04337 | R-33 | Actual arrival is not parseable | Excluded: delay cannot be calculated |
| T1-04381 | R-34 | Arrival is 5 min before scheduled departure | Excluded by provisional elapsed-time rule |
| T1-04466 | R-34 | Actual arrival is not parseable | Excluded: delay cannot be calculated |
| T1-04540 | R-35 | Arrival is 5 min before scheduled departure | Excluded by provisional elapsed-time rule |
| T1-04646 | R-36 | Actual arrival is not parseable | Excluded: delay cannot be calculated |
| T1-04846 | R-38 | Actual arrival is not parseable | Excluded: delay cannot be calculated |
| T1-05210 | R-40 | Actual arrival is not parseable | Excluded: delay cannot be calculated |
| T1-05264 | R-40 | Arrival is 5 min before scheduled departure | Excluded by provisional elapsed-time rule |

**Additional offset case:** T1-02864 (R-23) is stamped `+00:00`, unlike the other rows. Interpreting the timestamp with that offset gives arrival at 07:02 Mumbai time and an arrival delay of −2 minutes. It is included, not counted as an excluded or proven faulty row. If the offset itself is misconfigured, the value may be wrong; verify the device clock before treating it as certain.

**Concentrated disruption on R-35:** On Wednesday 2026-08-05, all 19 included R-35 trips were more than 30 minutes late; their median delay was 52 minutes. T1-04521 was 61 minutes late, and T1-04508 and T1-04516 were 60 minutes late. Across the week R-35 has median 2.00 minutes, 10% trimmed mean 3.96, Huber 1.99 and ordinary mean 8.05. The robust measures all rank it outside the top three; the 10% trimmed mean ranks it fifth. This is a limitation if the review cares about a severe disruption affecting a minority of the week’s trips. The Wednesday operational notes are possible context, not proof that any particular trip was affected. Show the number and share of severely delayed trips and daily results alongside the weekly statistic; verify GPS/operations evidence before deciding whether the disruption was genuine.

**Other ranking limitations:** The median gives R-26 and R-31 the same 4-minute delay; its current route-code tie-break does not demonstrate that R-26 had worse service. R-26 has 4 of 103 included trips over 10 minutes late while R-31 has none of 112. The 5% trimmed mean ranks R-35 in the top three, while 10% and 20% do not; the choice of trim changes the decision. Huber tuning values 1, 1.5 and 2 preserve the same top three on this slice, but all three downweight R-35’s cluster. These are examples of tradeoffs, not evidence that a method is universally defective.

All results remain provisional: 4xx membership cannot be established from the two-digit series field, so REC-114 cannot yet be confidently applied. The current trip CSV differs byte-for-byte from its recorded original hash, but its parsed and whitespace-stripped records match the original Git blob in order. See `outputs/method-evaluation.md` for the comparison and sensitivity checks.

### Additional issues found in the current slice

- **R-14's late-trip frequency:** 28 of 118 included trips (23.7%) arrived more than 10 minutes late; its 90th-percentile delay was 14 minutes. Its weekly robust summaries all rank it worst, but the single summary does not tell Priya how many trips were affected. The 10-minute cutoff is an illustrative threshold, not an agreed Cityflo service standard.
- **R-26 versus R-31:** Both have a 4-minute weekly median, but 4 of 103 included R-26 trips were more than 10 minutes late versus 0 of 112 on R-31. The median ranking's route-code tie-break puts R-26 first without using that distinction. A tie-break using tail performance could make a different operational choice and must be specified in advance.
- **Scope of the R-35 finding:** Under the current calculation, R-35 is the only route with included trips more than 30 minutes late: 19 of 132 included trips, all on Wednesday. This is an observed pattern, not proof of its cause. The 30-minute cutoff is illustrative, not an agreed service standard.
- **Daily sensitivity:** Removing any one day retains R-14, R-33 and R-26 as the median top three, but changes the order of R-33 and R-26 when Tuesday, Friday or Saturday is removed. Rank order is therefore sensitive to the days included.
- **Excluded-record sensitivity:** Reintroducing the 18 parseable negative-elapsed records did not change the top three for median, 10% trimmed mean or Huber. This stress test does not validate those records. The 24 unparseable arrival timestamps cannot be assessed without corrected values.
- **Clock and timetable uncertainty:** The stamped offset is interpreted as supplied; a misconfigured device can still produce a parseable but incorrect time. The 4xx vehicle membership is unresolved from two-digit series values, so current results have not been verified against REC-114. Any operational ranking or route verdict could change after those issues are resolved.

To regenerate the conditional decision and its evidence from the current CSVs:

```bash
uv run python -m cityflo_ai_engineer_assignment.decision_report
```

See `DECISION.md` for the provisional review score, proposed verdicts and the timetable sensitivity scenario. The index combines the 10% trimmed delay with severe-trip exposure; it is a prioritization score, not an average trip delay. Ranking by `review_score` is available using `worst_routes`. Explicit 4xx trips before the effective date of a known revised timetable use the prior runtime; unknown-route 4xx trips are excluded pending timetable data.

With the HTTP server running, validate the generated decision against real MCP responses:

```bash
uv run python -m cityflo_ai_engineer_assignment.decision_report
uv run python -m cityflo_ai_engineer_assignment.check_routes http://127.0.0.1:8025/mcp
```

The check uses a real FastMCP client, calls all four route tools, and compares all route summaries and the review ranking against the generated JSON. The older résumé/observability test suite was not fully validated in the sandbox: its integration test timed out; rerun it in the target environment before publication.

# Cityflo AI Engineer — Friday route review

**Flag R-35, R-14 and R-33. Rank them in that order.** R-35 has 19 severe Wednesday failures; R-14 has recurring delay; R-33 narrowly crosses the intervention line. Read [DECISION.md](DECISION.md) for all 40 route verdicts, quantified lateness, operational costs, counterexamples and the evidence that would change each call.

The decision uses exported runtimes for unidentified two-digit vehicle classes. The candidate accepted that policy after confirming no verified class mapping is available. REC-114 is applied to identifiable 400–499 classes from the revision's effective date. Applying the revisions to every eligible trip on R-14/R-27 instead clears R-14 and changes the top three to R-35, R-33, R-26. That is a disclosed sensitivity scenario, not an inferred fleet mapping.

## Setup and reproduce

Use Python 3.12+ and [uv](https://docs.astral.sh/uv/). From the checkout root:

```bash
uv sync --locked
uv run python -m cityflo_ai_engineer_assignment.decision_report
uv run python -m cityflo_ai_engineer_assignment.check_routes --stdio
uv run python -m unittest discover -s tests -v
```

The analysis reads the two source CSVs directly. It needs no DuckDB database, Celery worker, credentials or remote service. The checks launch real MCP subprocesses; the full suite also opens local HTTP sockets. Run in an environment that permits those operations. `uv.lock` pins the tested dependency graph.

The report regenerates `DECISION.md` and these artifacts:

| Artifact | Purpose |
|---|---|
| `outputs/review-decision.json` | Every route, its verdict, statistics, frozen parameters, input hashes and timetable alternative |
| `outputs/route-evidence.json` | Trip IDs, calculated delays, runtime provenance for consequential routes; every excluded record |
| `outputs/decision-sensitivity.json` | Severity weights/cutoffs, flag thresholds, day removal, elapsed bounds, missing-record stress and estimator comparisons |
| `outputs/route-mcp-validation.json` | Real tool discovery/calls and agreement with the generated verdicts and ranking |
| `outputs/fresh-slice-validation.json` | Real MCP rehearsal with a separate synthetic slice and an explicit 4xx timetable |
| `outputs/readiness-validation.json` | Final setup, source integrity, ledger and transcript checks |

Earlier exploratory artifacts are retained under `outputs/archive/`; they do not define the final verdict.

## Run and connect the real MCP server

Standalone route server over stdio:

```bash
uv run python -m cityflo_ai_engineer_assignment.route_analysis
```

Client configuration, with a placeholder checkout path:

```json
{
  "mcpServers": {
    "cityflo_routes": {
      "command": "uv",
      "args": ["--directory", "<absolute-path-to-checkout>", "run", "python", "-m", "cityflo_ai_engineer_assignment.route_analysis"]
    }
  }
}
```

Available tools and representative `tools/call` parameters:

```json
{"name":"route_delays","arguments":{}}
{"name":"worst_routes","arguments":{"limit":3}}
{"name":"worst_routes","arguments":{"limit":10,"method":"huber"}}
{"name":"evaluate_methods","arguments":{}}
{"name":"route_evidence","arguments":{"route":"R-35"}}
```

`worst_routes` defaults to the operational `review_score`. Comparison methods are `median`, `trimmed_mean_10`, `huber`, and `mean`. Rankings use two-decimal scores descending, then route code ascending. A no-data route is reported as unassessable and is excluded from ranking.

`check_routes --stdio` starts a separate server process using the installed Python, discovers tools, calls all four through a real FastMCP client, and compares all route summaries and both default/explicit review rankings with the generated decision. This is protocol integration, not a direct Python call to tool functions.

For Streamable HTTP:

```bash
uv run python -c 'from cityflo_ai_engineer_assignment.route_analysis import make_server; make_server().run(transport="http", host="127.0.0.1", port=8025, show_banner=False)'
```

Connect to `http://127.0.0.1:8025/mcp`, then validate:

```bash
uv run python -m cityflo_ai_engineer_assignment.check_routes http://127.0.0.1:8025/mcp
```

## Rule and consequences

For each valid trip, arrival delay is actual arrival with its stamped offset minus scheduled departure in Mumbai time plus applicable runtime. Keep signed negative delays. Exclude malformed records, duplicate/missing IDs, negative departure-to-arrival elapsed time and elapsed above 360 minutes. The negative-elapsed screen is an assumption because actual departures are absent, not proof of bad GPS.

Score = 10% trimmed mean + 30 × fraction of trips more than 30 minutes late. Flag if the unrounded score is strictly above five. These are explicit operational judgments, not Cityflo policy; the score measures intervention priority rather than average passenger delay. Data on rider loads, refund amounts and depot incentives are unavailable.

The supplied slice has 5,292 rows: 5,250 included and 42 excluded (24 unparseable arrivals and 18 negative elapsed times). T1-02864's +00:00 stamp is interpreted as supplied and gives −2 minutes; no unsupported clock correction is applied. R-35's 19 severe trips contribute 975 bus-trip minutes, which robust weekly centers suppress. A single hypothetical correction can reverse R-35/R-14. R-26's clear flips under the extreme missing-record upper endpoint. These limits are defended explicitly in the decision, not hidden by the ranking.

## Fresh slice and live debrief

Use a separate directory containing `trips.csv` and `schedule_v2.csv` with the documented columns:

```bash
CITYFLO_ROUTE_DATA_DIR=/path/to/fresh-slice uv run python -m cityflo_ai_engineer_assignment.route_analysis
uv run python -m cityflo_ai_engineer_assignment.decision_report --data-dir /path/to/fresh-slice --output-dir outputs/fresh-slice
uv run python -m cityflo_ai_engineer_assignment.validate_fresh_slice
```

The override is intentionally separate from the supplementary server's `CITYFLO_DATA_DIR`. No original inputs are overwritten. The report prints fresh rankings and omits the original extract's narrative unless both CSV hashes match the official inputs. Parameters stay frozen until a new constraint is supplied; `summarize` accepts explicit severity weight/cutoff and flag tolerance for a justified scenario. `evaluate_methods` exposes those sensitivity sweeps through MCP.

In the live round, identify R-35/R-14 as the fragile order, R-14 as the timetable-sensitive verdict, and R-26 as the missingness-sensitive clear. Call `route_evidence` before changing a decision.

## Provenance, privacy and transcript

Original documents and CSVs are preserved, and all six hashes in `sources.json` were verified. The raw `data/ops_log.txt` is retained locally and excluded from Git. Official retrieval: [Cityflo ops log](https://careers.cityflo.com/takehomes/ai-engineer/data/ops_log.txt). The route analysis does not require it to reproduce numeric results. Weather/traffic categories are context only: the handoff calls the log last week's chatter and it has no trip join. It supplies no class mapping or independent device verification.

No rider phones or complaint wording belong in tools, traces, fixtures or public evidence. Route tools read only the CSVs. Complaint evidence is referenced by ticket/category if needed; the raw ops file is never dumped into tool output.

`decisions.jsonl` contains genuine candidate steering, including explicit acceptance of the unidentified-class policy. Quotes are checked against original Codex rollout filenames and line numbers. For a message containing an image, concatenate its text content blocks in order; the image binary is not a fabricated text quote. Agent-only analysis choices are described in the decision rather than invented as user overrides.

Unmodified native session files and the local manifest are kept under ignored `local-transcripts/`. Cityflo's upload service issued a PUT URL for `ai-engineer-raw-sessions.zip`; the archive preserves separate original JSONL files, their hashes and a manifest. It does not synthesize a combined conversation. Upload evidence and Cityflo's actual submission receipt remain local; no temporary upload URLs or raw logs are public. See [READINESS.md](READINESS.md) for final verification and remaining evidence limits.

## Supplementary server

The existing résumé tools, resources, prompt, DuckDB factory and Celery/SQLite observability implementation are preserved. They are separate from the standalone route-analysis path. Their detailed setup and architecture are in [docs/architecture-and-resume.md](docs/architecture-and-resume.md); historical analysis sections there are superseded by this README and the final decision.

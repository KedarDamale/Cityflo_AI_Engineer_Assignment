# Delivery guide: AI Engineer - Sage AI

## Assignment and current status

- Applied role: **AI Engineer - Sage AI**.
- Cityflo MCP `position_id`: **`ai-engineer`**. Use this exact value for transcript upload and submission.
- Official bundle: https://careers.cityflo.com/takehomes/ai-engineer/
- Timebox: **4-6 focused hours**.
- Goal: **Which routes were actually late this week, by how much, and which three were worst?**

This folder contains the original downloaded assignment documents and data, preparation notes, empty `src/` and `outputs/` work areas, and an empty steering ledger. Implementation and final decisions still need to be produced. The application, candidate profile, resume, and agent configuration were already submitted; the take-home deliverable has not been submitted.

`BRIEF.md`, `HANDOFF.md`, and `DATA_GUIDE.md` are the downloaded source documents. This delivery guide explains the workflow and a suggested project layout; suggested filenames and folders do not add grading requirements. Download URLs and original SHA-256 hashes are in `sources.json`.

## Where to put your work

Work in this Desktop folder as its own project and, when ready, its own repository. Suggested public repository name: `cityflo-ai-engineer-takehome`.

```text
Cityflo-AI-Engineer/
  BRIEF.md             # original assignment
  HANDOFF.md           # original ops request
  DATA_GUIDE.md        # original column reference
  data/                # original downloaded inputs
  src/                 # write your implementation here
  outputs/             # generated verdicts, ranking and safe evidence
  README.md            # add exact setup and run instructions
  DECISION.md          # add your final decision record
  decisions.jsonl      # starts empty; add real steering decisions
  delivery.md          # this guide
  sources.json         # original file download URLs and hashes
  local-transcripts/   # create locally for raw logs; ignored by Git
```

Choose a dependency file appropriate to your implementation, such as `pyproject.toml` or `requirements.txt`. The layout is a suggestion, not a framework requirement.

## What to do while solving

Start a dedicated coding-agent session in this folder so the solve and its raw transcript are easy to identify. Use your normal agent throughout; agent use is required. Record real user steering as it happens.

1. Read `HANDOFF.md`, `BRIEF.md`, and `DATA_GUIDE.md` before implementing your definition of lateness.
2. Build a small MCP server over the supplied trips, revised timetable, and ops log. Put implementation code in `src/` and dependency declarations in the project root.
3. Connect the server to a real MCP client/your coding agent and actually call its tools. Record the exact launch command and client configuration in your solution's `README.md`; remove credentials and machine-specific paths from the shared configuration.
4. Produce a defensible verdict for every route, quantify how late it was, and give one ranked worst-three. Include evidence that lets Priya trace consequential calls back to trip/route IDs.
5. Evaluate the handoff's privacy directive and REC-114 timetable convention explicitly. Document their treatment and supporting evidence in `DECISION.md`.
6. Keep raw rider phone numbers and verbatim complaint text out of tool responses, traces, logs, and public artifacts. Reference ticket IDs and categories. The original `data/ops_log.txt` is preserved locally and excluded from Git by the supplied `.gitignore`; document its official download URL if your public solution needs it.
7. Go beyond an unexamined mean-lateness ranking. Defend your ranking and borderline calls using your chosen reproducible rule and the actual data.

For each consequential call in `DECISION.md`, cover all four items:

1. **Rule:** a stranger can apply it to another extract and reproduce the call.
2. **Where your rule breaks:** cite a specific route, trip, or ping ID and explain why you keep the rule despite that case.
3. **Cost and who bears it:** quantify the operational impact from your numbers where possible.
4. **What would change your mind:** name the observation that would flip the call.

Write a committed decision that Priya can defend. The grading emphasis is judgment and its defense; parsing files and selecting a framework are only the starting point.

## Steering ledger and raw transcript

The supplied `decisions.jsonl` is empty intentionally. Each real entry must contain `decision`, `quote`, and `anchor`. The following is a schema illustration, not a real entry to submit:

```json
{"decision":"<the consequential decision>","quote":"<verbatim words the user actually sent>","anchor":"<matching turn or stable location in the raw transcript>"}
```

Copy quotes exactly and cross-check every anchor against the actual exported transcript. Agent proposals are not user overrides; if the user kept a proposal, record that honestly. There is no minimum count. Do not invent user messages or backfill fictional steering.

Keep the original raw solve-session transcript, including the actual messages and tool interactions. A hand-written summary, reconstructed conversation, or this delivery guide is not a transcript. Locate/export the genuine session file using your agent's session storage and verify it belongs to this assignment. If the solve spans sessions, preserve the original files and resolve the multi-session upload format with Cityflo rather than dropping part of the work. Keep raw logs out of the public Git repository; upload them through Cityflo's dedicated session-log URL.

## Deliverables to finish

- The runnable MCP server and its dependency file.
- `README.md`: setup, server launch command, how to connect a client, representative tool calls, and how to reproduce the final answer. Add instructions to obtain the locally retained ops log if needed.
- `DECISION.md`: one verdict per route, lateness amounts, ranked worst-three, and defended consequential calls. The brief explicitly requests this filename.
- `outputs/`: recommended location for machine-readable route verdicts, ranking, and safe evidence references. Filenames are your choice.
- `decisions.jsonl`: genuine steering decisions with verbatim user quotes and transcript anchors.
- The complete raw solve-session transcript, uploaded separately through Cityflo MCP.

## After solving: reproduce and publish the code

1. Rerun the commands in your solution's `README.md` from a fresh environment. Check that they regenerate the documented verdicts and ranking, and that the evidence references and steering anchors are correct.
2. Review the public files, dependencies, and any example client configuration. Keep credentials, local virtual environments, raw session logs, and machine-specific configuration out of Git. The included `.gitignore` provides a starting point.
3. Publish a separate public GitHub repository or gist containing this role's code, dependency declarations, decision record, steering ledger, run instructions, and the permitted inputs/fixtures needed for reproduction. For any input retained locally, document its official source and how to obtain it. GitHub is the simplest repository option; Cityflo accepts a repo/gist deliverable URL.
4. Confirm that someone who is not signed in to your account can open the URL, read the code and decisions, and follow the run instructions. A local Desktop path is not a submission URL.

If you use GitHub CLI, run these commands **only after the solution is ready to publish**, from this folder. They create a new public repository; change the name if it is already taken:

```bash
git init -b main
git add .
git commit -m "Complete Cityflo take-home"
gh repo create cityflo-ai-engineer-takehome --public --source . --remote origin --push
```

An existing repository may need a normal commit and push instead. Record the actual final URL for the next step.

## After publishing: upload the transcript and submit to Cityflo

These are **MCP calls for your agent**, not terminal commands. The exact submission order is:

1. Ask the agent to request a fresh session-log upload URL:

```json
{"tool":"get_session_log_upload_url","arguments":{"position_id":"ai-engineer","filename":"ai-engineer-session.jsonl"}}
```

2. Keep both returned values: `upload_url` and `session_log_key`. Upload the genuine raw transcript file with an HTTP PUT to that URL. For example, after setting `CITYFLO_UPLOAD_URL` to the returned URL and `CITYFLO_SESSION_FILE` to the real local file:

```bash
curl --fail --show-error --upload-file "$CITYFLO_SESSION_FILE" --write-out '\nHTTP %{http_code}\n' "$CITYFLO_UPLOAD_URL"
```

Confirm HTTP 200 before submitting. Request another URL if the short-lived URL expires. Never put the temporary upload URL in the public repository.

3. Ask the agent to submit this role's actual public URL and the key from the successful upload:

```json
{"tool":"submit_assignment","arguments":{"position_id":"ai-engineer","deliverable_url":"<actual public repository or gist URL>","session_log_key":"<key from the successful transcript upload>","notes":"<brief run instructions, final commit, and material limitations>"}}
```

4. Read the tool response and confirm Cityflo accepted the submission. A published repository alone is not a completed Cityflo submission. Repeat this process separately for the other role using its own URL, role ID, transcript, and upload key.

You can ask your connected agent: "Submit my completed AI Engineer - Sage AI take-home from this repository, using its genuine raw solve-session transcript." Provide the final repository URL and the session identity/file when needed.

## Prepare for the live round

In a 15-minute live debrief, run the MCP tool on a fresh data slice with one new constraint. Be ready to defend the worst-three, identify your least certain call, and explain the evidence that would change it.

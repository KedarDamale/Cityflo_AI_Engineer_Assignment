# Final requirement reconciliation — 2026-11-04

**Ready for submission under the candidate's explicit timetable policy.** The candidate confirmed no verified vehicle-class mapping is available and accepted exported runtimes for unidentified classes. This resolves the need for an operational call without inventing a mapping. Missing membership remains a material analytical limitation, with quantified REC-114 alternatives in the decision.

The final decision flags and ranks **R-35, R-14, R-33**. Its review scores are 8.28, 7.90, 5.42; trimmed delays are 3.96, 7.90, 5.42 minutes. The score measures intervention priority. These are service flags, not proof of operator fault or automatic cash deductions.

| Requirement | Verification |
|---|---|
| Runnable MCP server and locked setup | Fresh Python 3.12 environment installed all 78 packages with `uv sync --locked --offline`; no existing project virtual environment was reused. |
| Actual MCP use | Separate real stdio server/client; discovery and all four tools exercised. All 40 route summaries and default/explicit rankings match generated decision JSON. |
| Verdict per route and ranked worst three | Present in `DECISION.md` and `outputs/review-decision.json`; every Markdown row checked against implementation output. |
| Defended consequential calls | Rules, specific IDs, costs/bearers and change-of-mind evidence for R-35, R-14, R-33, R-26, R-37 and the REC-114 policy. |
| Decision-score sensitivity | Severity weights 0/10/15/30/60; severe cutoffs 20/30/45/60; flag lines 4/5/6; actual score after omitting each day; hypothetical correction of one severe trip; excluded-record endpoint scenarios. |
| Estimator and anomaly checks | Median, mean, 5/10/20% trims, Huber 1/1.5/2; elapsed caps 180/360/720; negative-elapsed stress. 5,292 rows reconcile to 5,250 included plus 42 excluded. |
| REC-114 | Applied to identifiable 400–499 classes at the correct effective date. Unidentified suffixes use the accepted export policy. All-eligible revision sensitivity clears R-14 and changes top three to R-35, R-33, R-26. |
| Input provenance | All six source hashes match `sources.json`; originals preserved. |
| Privacy | Route tools read only the CSVs. Raw ops file and native session files are ignored and absent from Git tracking/history checks. A limited historical exact-match audit is retained locally; no blanket claim of semantic review of every past message is made. |
| Genuine steering | All 19 ledger entries parse and decoded quotes match anchored original user messages. Image-message text blocks are concatenated in original order. No inferred vehicle mapping or agent-only choice is attributed to the user. |
| Genuine transcript | Five native Codex sessions located and preserved separately. Live sources retained; snapshots and hashes refreshed after validation. ZIP preserves unchanged JSONL files and a manifest, not a reconstructed conversation. |
| Multi-session upload path | Cityflo's upload API accepted the filename `ai-engineer-raw-sessions.zip` and returned a PUT URL naming that file. This verifies the archive upload path; it is not evidence that a grader has already unpacked/reviewed it. |
| Full suite | All 12 tests pass in the fresh environment with required local socket/subprocess access. Initial sandbox failures and the corrected stale tool-discovery assertion remain in genuine logs. |
| Fresh-slice live rehearsal | Separate seven-row synthetic slice through all four real MCP tools: explicit 4xx, date boundary, equivalent UTC, unknown class, malformed input, duplicate IDs, no-data routes and changed six-point tolerance verified. Original inputs untouched. |
| Publication and acceptance | Final changes must be committed/pushed, anonymously reproduced, raw archive PUT confirmed HTTP 200, and `submit_assignment` acceptance recorded. Actual receipt/status is retained locally after the submission flow. |

The machine-readable evidence is in `outputs/readiness-validation.json`, `outputs/route-mcp-validation.json`, `outputs/fresh-slice-validation.json` and the suite's validation artifacts. The README gives exact commands and credential-free client configuration.

Remaining uncertainty is explicit: R-14 can clear under verified REC-114 membership; R-35/R-14 reverse if one severe observation is corrected; R-26 clears under the chosen rule but flags at the extreme missing-record upper endpoint (5.22). No rider loads, refund amounts, monetary incentives, actual departure times or causal fault are inferred. The final decision chooses a line and says who bears its error costs.

Earlier exploratory outputs remain under `outputs/archive/`. Supplementary résumé/database/observability code is preserved separately. Completion time for this follow-up is recorded in the local manifest; historical cumulative focused solve time cannot be reconstructed reliably from elapsed session spans.

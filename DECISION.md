# Friday route-review decision

**Flag R-35, R-14, R-33 for lateness remediation; clear the other assessed routes.** Worst three: 1. **R-35** (score 8.28; trimmed delay 3.96 min); 2. **R-14** (score 7.90; trimmed delay 7.90 min); 3. **R-33** (score 5.42; trimmed delay 5.42 min). A clear means below this weekly intervention threshold, not that every trip was on time. No-data routes receive `insufficient_data`.

## Operational rule and its cost

Use the exported runtime for unidentified classes. The candidate accepted this policy after confirming that no verified class mapping is available; the exact acceptance is anchored in `decisions.jsonl`. This is an explicit assumption, not a finding that two-digit codes are outside 4xx. The service flags and remediation priorities stand now. Before an irreversible incentive deduction, request the class mapping and independent clock/arrival evidence: these observations do not establish operator fault or the amount of any penalty.

1. Scheduled departure is Mumbai UTC+05:30. Interpret arrival using its stamped offset. Delay = actual arrival − (scheduled departure + applicable runtime), in minutes. Retain negative signed delays.
2. Apply REC-114 to explicit numeric classes 400–499, using the latest route revision effective on departure date. Before a known future revision use the export runtime. Exclude explicit 4xx trips with no route schedule. For unidentified two-digit suffixes use the export runtime; never infer a hundreds digit from the route.
3. Exclude malformed data, missing/duplicate trip IDs, negative scheduled-departure-to-arrival elapsed time, and elapsed time over 360 minutes. Negative elapsed is a plausibility screen, not proof of a faulty row: actual departure is absent. Retain genuine extreme delays inside that range.
4. Remove floor(0.10 × n) trips from each tail to calculate the 10% trimmed mean. Severe means delay strictly over 30 minutes. **Review score = trimmed mean + 30 × severe-trip fraction.** Flag only if the unrounded score exceeds 5. Rank scores rounded to two decimals descending, then route code ascending. Keep raw trip evidence, median, ordinary mean, Huber, p90, positive trip-minutes and severe counts alongside it. A route with no usable observations is unassessable and is excluded from the ranking.

The five-minute tolerance and 30-minute severe-event weight are judgments for this review, not Cityflo policy or fitted ground truth. The trim limits individual timestamp influence. Median and Huber suppress concentrated disruption; the severity term gives a 10% severe-trip share three additional priority points. That deliberately counts part of the same harm twice. Accept that cost to keep half-hour failures visible after trimming, and publish the sensitivity rather than claim an optimal coefficient. The score measures intervention priority, **not average passenger lateness**. Freeze these parameters for next week's extract unless the review supplies a new constraint.

Signed means allow early arrivals to offset late ones. Positive bus-trip minutes expose the service cost that offsetting hides; they sum per-trip positive arrival delay, not passenger-minutes or money. Rider loads, refunds and incentive amounts are unavailable. A clear verdict does not close individual service-recovery cases.


The extract contains 5,292 records: 5,250 included and 42 excluded. Decisions and timetable alternatives are in `outputs/review-decision.json`; trip-level evidence and all exclusions in `outputs/route-evidence.json`; daily and parameter sensitivity in `outputs/decision-sensitivity.json`. Evidence includes input hashes.

## One verdict per route

| Route | Included trips | 10% trimmed delay (min) | Trips >30 min | Review score | Verdict |
|---|---:|---:|---:|---:|---|
| R-01 | 153 | 0.76 | 0 | 0.76 | clear |
| R-02 | 105 | 1.42 | 0 | 1.42 | clear |
| R-03 | 103 | 1.67 | 0 | 1.67 | clear |
| R-04 | 144 | 0.11 | 0 | 0.11 | clear |
| R-05 | 105 | 2.40 | 0 | 2.40 | clear |
| R-06 | 117 | -1.54 | 0 | -1.54 | clear |
| R-07 | 147 | 2.67 | 0 | 2.67 | clear |
| R-08 | 126 | 2.58 | 0 | 2.58 | clear |
| R-09 | 146 | 2.29 | 0 | 2.29 | clear |
| R-10 | 126 | 1.07 | 0 | 1.07 | clear |
| R-11 | 137 | 2.05 | 0 | 2.05 | clear |
| R-12 | 112 | 1.62 | 0 | 1.62 | clear |
| R-13 | 133 | -0.91 | 0 | -0.91 | clear |
| R-14 | 118 | 7.90 | 0 | 7.90 | flag |
| R-15 | 119 | 2.64 | 0 | 2.64 | clear |
| R-16 | 146 | -0.14 | 0 | -0.14 | clear |
| R-17 | 147 | 2.87 | 0 | 2.87 | clear |
| R-18 | 154 | 2.00 | 0 | 2.00 | clear |
| R-19 | 125 | 2.38 | 0 | 2.38 | clear |
| R-20 | 145 | 1.97 | 0 | 1.97 | clear |
| R-21 | 124 | 2.04 | 0 | 2.04 | clear |
| R-22 | 112 | 1.92 | 0 | 1.92 | clear |
| R-23 | 132 | 0.17 | 0 | 0.17 | clear |
| R-24 | 146 | 0.75 | 0 | 0.75 | clear |
| R-25 | 139 | 1.38 | 0 | 1.38 | clear |
| R-26 | 103 | 4.52 | 0 | 4.52 | clear |
| R-27 | 143 | 2.56 | 0 | 2.56 | clear |
| R-28 | 151 | 0.66 | 0 | 0.66 | clear |
| R-29 | 151 | -0.94 | 0 | -0.94 | clear |
| R-30 | 147 | -0.46 | 0 | -0.46 | clear |
| R-31 | 112 | 3.73 | 0 | 3.73 | clear |
| R-32 | 133 | 1.17 | 0 | 1.17 | clear |
| R-33 | 104 | 5.42 | 0 | 5.42 | flag |
| R-34 | 124 | 2.55 | 0 | 2.55 | clear |
| R-35 | 132 | 3.96 | 19 | 8.28 | flag |
| R-36 | 132 | 0.39 | 0 | 0.39 | clear |
| R-37 | 105 | 4.27 | 0 | 4.27 | clear |
| R-38 | 146 | 1.44 | 0 | 1.44 | clear |
| R-39 | 154 | 1.83 | 0 | 1.83 | clear |
| R-40 | 152 | 2.65 | 0 | 2.65 | clear |

## Consequential calls on the supplied extract

**R-35 — flag, priority 1.** Apply the frozen score: 8.28, with trimmed delay 3.96 minutes. Nineteen of 132 included trips exceeded 30 minutes, contributing **975 bus-trip minutes** of delay, all on Wednesday 2026-08-05; their median was 52 minutes. T1-04521 was 61 minutes late; T1-04508 and T1-04516 were 60 minutes late. The rule breaks on genuine T1-04521-like extremes because trimming suppresses their magnitude and a count treats 31 and 61 minutes alike. Keep that limited influence to avoid letting one questionable timestamp determine the week, but preserve actual severe minutes in the evidence. Riders on those 19 trips bear the cost if cleared; a common clock fault could instead expose the depot head to an unjustified incentive loss. This is the **least certain rank order**: a severity weight below roughly 27.3 makes R-14 first, and correcting even one of those severe trips to 2 minutes moves R-35 below R-14. Removing Wednesday removes it from the top three; keep Wednesday because a real bad day belongs in the week. Independent arrival/device evidence invalidating the cluster would change the flag; validated correction of even one severe trip can change the order. Prioritize verifying that cluster and recovering service now.

**R-14 — flag, priority 2; least certain timetable verdict.** The score and trimmed delay are 7.90 minutes; 28 of 118 trips exceeded 10 minutes and the route accumulated 952 positive bus-trip minutes. T1-01691 is excluded because its stamped arrival precedes scheduled departure by five minutes. That exclusion breaks if the bus actually left early; retain it because the export cannot distinguish that from a clock problem. The more consequential break is unknown class membership: applying the revision to every eligible R-14 trip lowers its score to 2.89 and clears it. Riders bear recurring delay if wrongly cleared; the depot head bears a false-flag risk if these buses were actually eligible for REC-114. **Keep the service flag against the only identified trip-specific timetable, while withholding an inference of fault.** A verified vehicle mapping that puts enough affected trips under REC-114, or corrected arrivals bringing the score to 5 or below, flips this verdict. No verified mapping was available when the candidate accepted this policy.

**R-33 — flag, priority 3.** Score/trimmed delay 5.42 minutes, eight of 104 trips over 10 minutes, 575 positive bus-trip minutes. T1-04337 has an unparseable arrival and is excluded: a genuine severe failure can be hidden there, or an early arrival can bias the summary upward. Keep the parseability rule instead of inventing an arrival. The flag margin is only 0.42; a six-point tolerance clears R-33 and protects its depot head at the cost of leaving those eight rider-facing failures below the intervention line. Keep five uniformly rather than tune it to save a particular incentive. Verified arrival or schedule corrections moving the unrounded score to 5 or below change the verdict. Imputing all excluded records at either elapsed-time endpoint does not change R-33's flag at the chosen threshold.

**R-26 — clear, closest below the line.** Score 4.52, four of 103 trips over 10 minutes, 482 positive bus-trip minutes. T1-03377 has negative elapsed time and is excluded; a genuinely early departure is a counterexample to the plausibility screen. The weekly clear also breaks on those four late trips: their riders still need recovery. Keep the common five-point line rather than impose a depot penalty 0.48 below it, but retain the affected trips for support follow-up. This clear is **not robust to adverse missingness**: assigning every excluded trip a 360-minute elapsed time raises R-26 to 5.22 and makes it flag, while assigning zero elapsed leaves it clear. Neither imputation is observed. Corrected missing/negative-elapsed trip data lifting its score above five changes the call. If verified REC-114 membership clears R-14, R-26 enters the worst three even while remaining below the flag line; ranking and flagging are distinct decisions.

**R-37 — clear, next below the line.** Score 4.27, five of 105 trips over 10 minutes, 474 positive bus-trip minutes. T1-04787 was 13 minutes late, a specific counterexample to describing the whole route as on time. Riders on the five affected trips bear that cost. A four-point threshold would flag R-37 and R-26, increasing potential depot penalties from three routes to five; retain five to avoid retroactively tuning the tolerance. Verified timestamp/runtime corrections lifting its score above five change this verdict. Clearing the route does not dismiss the individual late trips.

**REC-114 — apply only to identifiable classes, not an inferred fleet.** R-14 and R-27 are the only supplied revision routes. Two-digit codes 01–40 do not recover a hundreds digit, and the ops log contains no vehicle mapping. R-14's 7.90-to-2.89 score change is the specific route where the unidentified-class policy can fail if the buses were 4xx. Retain the policy because a route-level revision does not prove trip eligibility, and silent reassignment would invent evidence. In the alternate scenario apply the latest revision to every eligible trip on each revised route, on/after its effective date: the worst three become **R-35, R-33, R-26**, and only R-35 and R-33 flag. R-27's “no change” note is not a computational guarantee: compare each exported runtime with 45 minutes. Priya bears the political risk; depot heads and riders bear the opposite error costs quantified above. A verified membership/effective-date correction changes the policy's application. Keep the alternate numbers visible; do not present them as a recovered mapping.

## Evidence limits and privacy

There are 24 unparseable arrivals and 18 negative-elapsed rows, all listed by ID and reason. Reintroducing the 18 parseable negative-elapsed records preserves the chosen top three and flags but does not validate those records. Assigning all 42 exclusions elapsed 0 or 360 minutes preserves the top three but the upper endpoint additionally flags R-26. This stress exposes the cost of potentially nonrandom missingness. All severe events fit even the 180-minute cap, so 180/360/720 caps preserve this ranking. Huber 1/1.5/2 preserves its comparison ranking; 5% versus 10% trimming changes whether R-35 is in the estimator top three. None establishes ground truth.

The weather/traffic and Wednesday categories in the ops log are context only. The handoff describes that file as last week's chatter, it has no trip-level join, and it cannot validate this week's severe-delay cluster or justify a clock correction. No phone numbers or complaint wording are quoted; complaint evidence is limited to ticket IDs/categories if needed. Route tools do not read the raw log. Original sources and provenance remain untouched; `sources.json` records the private ops file's official retrieval path.

T1-02864 (R-23) is included as −2 minutes under its +00:00 stamp. A clock misconfiguration could still make a parseable observation wrong; changing an offset without independent evidence would manufacture a correction. Missing actual departures, unknown class eligibility, common device faults, rider loads and causal responsibility remain uncertain. All six original source-file hashes were verified against `sources.json`. The numbers are verified calculations under the explicit policy, not verified causation.

## Live debrief

Run on a separate slice using `CITYFLO_ROUTE_DATA_DIR`; generate into a separate `--output-dir`. Keep the frozen rule unless the new constraint expressly changes it. Name R-35 versus R-14 as the fragile ordering, R-14 as the fragile timetable verdict, and R-26 as the missingness-sensitive clear. Retrieve the trip evidence and show the observation that would change each before proposing a revised ranking.


## Sensitivity results

| Change | Top three | Flagged routes |
|---|---|---|
| severity_weight = 0 | R-14, R-33, R-26 | R-14, R-33 |
| severity_weight = 10 | R-14, R-33, R-35 | R-14, R-33, R-35 |
| severity_weight = 15 | R-14, R-35, R-33 | R-14, R-33, R-35 |
| severity_weight = 30 | R-35, R-14, R-33 | R-14, R-33, R-35 |
| severity_weight = 60 | R-35, R-14, R-33 | R-14, R-33, R-35 |
| severe_threshold = 20 | R-35, R-14, R-33 | R-14, R-33, R-35 |
| severe_threshold = 30 | R-35, R-14, R-33 | R-14, R-33, R-35 |
| severe_threshold = 45 | R-14, R-35, R-33 | R-14, R-33, R-35 |
| severe_threshold = 60 | R-14, R-33, R-26 | R-14, R-33 |
| flag_threshold = 4 | R-35, R-14, R-33 | R-14, R-26, R-33, R-35, R-37 |
| flag_threshold = 5 | R-35, R-14, R-33 | R-14, R-33, R-35 |
| flag_threshold = 6 | R-35, R-14, R-33 | R-14, R-35 |

The JSON additionally sweeps elapsed caps 180/360/720 minutes, Huber tuning 1/1.5/2, trim fractions 5/10/20%, and omission of each day for the actual review score. Reintroducing parseable negative-elapsed rows is stress only. The excluded-record endpoints assign every recoverable excluded trip elapsed 0 or 360 minutes: these are neither observed corrections nor confidence intervals. Read the resulting rankings and per-route verdicts before using this on another slice.

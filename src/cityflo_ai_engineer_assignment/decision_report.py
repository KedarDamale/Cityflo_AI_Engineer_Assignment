"""Generate a conditional review decision and a timetable sensitivity scenario."""
import json
from collections import defaultdict
from pathlib import Path
from .route_analysis import ROOT, load, read_csv, summarize

def build():
    rows, excluded = load(ROOT/'data')
    baseline = summarize(rows)
    original = {r['trip_id']:r for r in read_csv(ROOT/'data'/'trips.csv')}
    schedules = {r['route']:r for r in read_csv(ROOT/'data'/'schedule_v2.csv')}
    alternate=[]
    for row in rows:
        adjusted=row.copy(); sch=schedules.get(row['route'])
        if sch and row['date'] >= sch['effective_date']:
            adjusted['delay'] += float(original[row['trip_id']]['scheduled_runtime_min']) - float(sch['revised_runtime_min'])
        alternate.append(adjusted)
    def ranking(items): return sorted(items, key=lambda x:(-x['review_score_min'], x['route']))
    baseline=ranking(baseline); alternate=ranking(summarize(alternate))
    out={'status':'conditional: 4xx membership unknown', 'review_score_rule':'10% trimmed mean plus 30 minutes times share of included trips with delay >30 minutes; flag if unrounded score >5 minutes; rank by displayed score then route code', 'baseline':baseline, 'scenario_all_scheduled_routes_4xx':alternate, 'excluded':excluded}
    (ROOT/'outputs'/'review-decision-conditional.json').write_text(json.dumps(out,indent=2)+'\n')
    table=['| Route | Included trips | 10% trimmed delay (min) | Trips >30 min | Review score | Verdict |','|---|---:|---:|---:|---:|---|']
    for x in sorted(baseline,key=lambda v:v['route']):
        table.append(f"| {x['route']} | {x['trips']} | {x['trimmed_mean_10_min']:.2f} | {x['severe_over_30_count']} | {x['review_score_min']:.2f} | {x['review_verdict']} |")
    report='''# Conditional route review decision

**Decision for review, subject to vehicle-series identification:** Flag routes with review score above 5 minutes, and rank R-35, R-14, R-33 as the worst three under the baseline assumption below. Do not use these results for incentives until REC-114 membership is resolved: the supplied series field gives only two-digit suffixes. The alternate timetable scenario below changes the ranking substantially.

## Rule and assumptions

For every valid trip calculate actual arrival, interpreting its stamped offset, minus scheduled departure in Mumbai time plus applicable planned runtime. Negative delays are retained. Exclude unparseable data and arrivals earlier than scheduled departure or more than 360 minutes afterward. Since actual departures are missing, the former is an assumption, not proof of an impossible journey; the upper bound is provisional. Excluded rows and route/trip IDs are in `outputs/review-decision-conditional.json`.

Baseline assumes no two-digit series is verified as 4xx and uses the export runtime for those rows. Explicit 400–499 IDs use the latest applicable revised schedule. This assumption is not evidence of vehicle class. Alternative scenario applies the revised schedule on or after its effective date to every trip on R-14 and R-27; it is a sensitivity bound on those routes, not proof that all vehicles are 4xx. Resolve membership with Cityflo and rerun.

Per route calculate the 10% trimmed mean of included signed delays (remove floor(0.10*n) trips from each tail). A severe trip has delay strictly greater than 30 minutes. Review score = trimmed mean + 30 × severe-trip fraction. Flag if the unrounded score is greater than 5; otherwise clear. Rank by score rounded to two decimals, then route code ascending. The score is a priority index in minutes, not average rider lateness. The 30-minute threshold, weighting and 5-minute flag threshold are operational judgments, not established Cityflo policy. This score consciously values a concentrated disruption as well as typical service; it may double-count severe incidents. It does not establish whether delays were caused by operators.

## Route decisions

'''+'\n'.join(table)+'''

## Consequential calls

**1. R-35, priority 1 (score 8.28; trimmed delay 3.96 minutes):** Nineteen of 132 included trips exceeded 30 minutes; all 19 occurred Wednesday, whose median was 52 minutes. T1-04521 was 61 minutes late. The weekly median is only 2 minutes and the ordinary 10% trimmed mean ranks this route fifth, so the added severity term gives the affected riders weight. The rule breaks if a stuck or misconfigured device caused the cluster: a depot head could face an unwarranted incentive loss. If real, riders on 19 trips bore delays over 30 minutes; we cannot infer rider counts or refunds. A verified independent arrival record or device diagnosis that removes or validates that cluster would change this call.

**2. R-14, priority 2 (score 7.90; trimmed delay 7.90):** 28 of 118 trips were over 10 minutes late; riders bear recurring delay. T1-01691 is excluded because its stamped arrival precedes scheduled departure by five minutes: if the bus actually departed early, excluding it can bias the route upward. Keeping the rule prevents an unknown departure/device event from silently influencing the verdict. The 4xx mapping is decisive: applying the revised timetable to all eligible R-14 trips lowers the score to 2.89 and clears it, protecting the depot head from a potential false flag. Verified 4xx IDs and device data would change the call.

**3. R-33, priority 3 (score 5.42; trimmed delay 5.42):** Eight of 104 trips were over 10 minutes late. T1-04337 has an unparseable arrival and is excluded; a genuinely late unrecorded trip would make the rider impact worse, while invalid timestamps can also conceal an early trip. The narrow 0.42-minute margin over the 5-minute threshold risks a depot incentive loss for a marginal or noisy result; clearing risks continued rider delay. A corrected timestamp or verified schedule moving the score to 5 or below changes the verdict.

**Borderline R-26 (clear, score 4.52):** Four of 103 included trips exceeded 10 minutes. T1-03377 was excluded because its arrival precedes scheduled departure; an early departure could make that exclusion incorrect. Riders on those four trips bear the downside of clearing; flagging a route 0.48 minutes below the threshold could cost a depot incentive. Corrected trip or timetable data that lifts its score above 5 changes the verdict.

## Verified versus uncertain

The calculations and counts are reproducible from the current CSV under the stated assumptions. They do not establish actual departure time, true device offsets, rider counts, monetary incentive amounts, refunds, or whether a disruption was avoidable. The Wednesday ops note is consistent with possible disruption, not a trip-level join or proof of causation. The original CSV hash differs from the working copy, but parsed whitespace-normalized records match the original Git blob. The raw ops log must never be emitted by a tool or published. Privacy uses ticket IDs and categories only where complaint evidence is needed.

**Timetable sensitivity:** When both revised-route timetables are applied to every eligible trip on R-14 and R-27, the top three become R-35, R-33 and R-26. This is an illustrative scenario; the true result depends on 4xx membership. Full route statistics and exclusions for both scenarios are in the generated JSON. This unresolved input limits the reliability of this decision.
'''
    (ROOT/'DECISION.md').write_text(report)
    print('baseline:', [(r['route'],r['review_score_min']) for r in baseline[:3]], 'scenario:', [(r['route'],r['review_score_min']) for r in alternate[:3]])

if __name__ == '__main__': build()

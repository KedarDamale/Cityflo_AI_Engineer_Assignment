"""Reproduce the operational decision, trip evidence and policy sensitivity."""
import argparse
import hashlib
import json
from pathlib import Path
from .route_analysis import ROOT, POLICY, evaluation, get_route_data_dir, load, ranked, read_csv, summarize


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')


def build(data_dir=None, output_dir=None, decision_path=None):
    data_dir=Path(data_dir) if data_dir is not None else get_route_data_dir()
    output_dir=Path(output_dir) if output_dir is not None else ROOT/'outputs'
    output_dir.mkdir(parents=True,exist_ok=True)
    decision_path=Path(decision_path) if decision_path else ROOT/'DECISION.md'
    rows, excluded=load(data_dir)
    all_routes={r['route'] for r in rows+excluded}
    baseline=ranked(summarize(rows,all_routes=all_routes))
    schedules=read_csv(data_dir/'schedule_v2.csv')
    alternate=[]
    for row in rows:
        adjusted=row.copy()
        candidates=[s for s in schedules if s['route']==row['route'] and s['effective_date']<=row['date']]
        if candidates:
            schedule=max(candidates,key=lambda s:s['effective_date'])
            runtime=float(schedule['revised_runtime_min'])
            adjusted.update(delay=row['delay']+row['runtime_min']-runtime,runtime_min=runtime,
                            timetable_source='stress: all eligible revised-route trips are 4xx')
        alternate.append(adjusted)
    alternate=ranked(summarize(alternate,all_routes=all_routes))
    assessed=[r for r in baseline if r['trips']]
    top=assessed[:3]
    flagged=[r['route'] for r in assessed if r['review_verdict']=='flag']
    clear=sorted((r for r in assessed if r['review_verdict']=='clear'),key=lambda r:-r['review_score_min'])
    consequential={r['route'] for r in top+clear[:2]}|set(flagged)
    sensitivity=evaluation(rows,data_dir)
    hashes={name:hashlib.sha256((data_dir/name).read_bytes()).hexdigest() for name in ('trips.csv','schedule_v2.csv')}
    out={'status':'operational decision under explicit unidentified-class policy','timetable_policy':POLICY,
         'unverified_assumption':'Two-digit codes cannot establish 4xx membership. No class mapping is inferred.',
         'parameters':{'trim_fraction_each_tail':0.1,'severe_delay_strictly_over_min':30,'severity_weight_min':30,
                       'flag_score_strictly_over':5,'max_elapsed_min':360},
         'ranking_rule':'two-decimal score descending, then route code ascending; no-data routes unranked',
         'baseline':baseline,'scenario_all_scheduled_routes_4xx':alternate,'excluded':excluded,'input_sha256':hashes}
    write_json(output_dir/'review-decision.json',out)
    write_json(output_dir/'decision-sensitivity.json',sensitivity)
    write_json(output_dir/'route-evidence.json',{'timetable_policy':POLICY,'input_sha256':hashes,
               'routes':sorted(consequential),'trips':[r for r in rows if r['route'] in consequential],'excluded':excluded})
    table=['| Route | Included trips | 10% trimmed delay (min) | Trips >30 min | Review score | Verdict |',
           '|---|---:|---:|---:|---:|---|']
    for x in sorted(baseline,key=lambda r:r['route']):
        if x['trips']:
            table.append(f"| {x['route']} | {x['trips']} | {x['trimmed_mean_10_min']:.2f} | {x['severe_over_30_count']} | {x['review_score_min']:.2f} | {x['review_verdict']} |")
        else:
            table.append(f"| {x['route']} | 0 | — | — | — | insufficient_data |")
    ranking='; '.join(f"{i}. **{r['route']}** (score {r['review_score_min']:.2f}; trimmed delay {r['trimmed_mean_10_min']:.2f} min)" for i,r in enumerate(top,1))
    rule=Path(__file__).with_name('decision_rule.md').read_text(encoding='utf-8')
    report=f"# Friday route-review decision\n\n**Flag {', '.join(flagged) or 'no routes'} for lateness remediation; clear the other assessed routes.** Worst three: {ranking}. A clear means below this weekly intervention threshold, not that every trip was on time. No-data routes receive `insufficient_data`.\n\n"+rule
    report+=f"\n\nThe extract contains {len(rows)+len(excluded):,} records: {len(rows):,} included and {len(excluded)} excluded. Decisions and timetable alternatives are in `outputs/review-decision.json`; trip-level evidence and all exclusions in `outputs/route-evidence.json`; daily and parameter sensitivity in `outputs/decision-sensitivity.json`. Evidence includes input hashes.\n\n## One verdict per route\n\n"+'\n'.join(table)
    original_hash='1c4d5bfe7ff229dfd52da8bb288b4b80fff71e00ab5369d339cdb7585cabb201'
    schedule_hash='b31e4e430ae1fcbaa2b7ea83259d4ca394019babdb07edc8ff707686da1dcc3a'
    if hashes['trips.csv']==original_hash and hashes['schedule_v2.csv']==schedule_hash:
        report+='\n\n'+Path(__file__).with_name('decision_calls.md').read_text(encoding='utf-8')
    else:
        report+='\n\n## Fresh-slice consequential cases\n\nThe original extract\'s narrative is intentionally omitted; do not reuse its trip IDs or conclusions on a new slice.\n\n'
        for item in top+clear[:2]:
            route=item['route']; trips=[r for r in rows if r['route']==route]; extreme=max(trips,key=lambda r:r['delay'])
            report+=f"**{route}: {item['review_verdict']}, score {item['review_score_min']:.2f}.** Apply the frozen rule. Counterexample: {extreme['trip_id']} had delay {extreme['delay']:.2f} minutes, which a weekly summary can conceal. Riders bear {item['positive_delay_trip_minutes']:.2f} positive bus-trip minutes; a false flag risks the depot head's unquantified incentive. Keep one rule rather than tune to a route. Verified timestamp/runtime corrections crossing the 5-point line or changing the ranking would change this call.\n\n"
    report+='\n\n## Sensitivity results\n\n| Change | Top three | Flagged routes |\n|---|---|---|\n'
    for family in ('severity_weight','severe_threshold','flag_threshold'):
        for parameter,value in sensitivity['decision_sensitivity'][family].items():
            report+=f"| {family} = {parameter} | {', '.join(value['top_three'])} | {', '.join(value['flagged_routes']) or 'none'} |\n"
    report+='\nThe JSON additionally sweeps elapsed caps 180/360/720 minutes, Huber tuning 1/1.5/2, trim fractions 5/10/20%, and omission of each day for the actual review score. Reintroducing parseable negative-elapsed rows is stress only. The excluded-record endpoints assign every recoverable excluded trip elapsed 0 or 360 minutes: these are neither observed corrections nor confidence intervals. Read the resulting rankings and per-route verdicts before using this on another slice.\n'
    decision_path.write_text(report,encoding='utf-8')
    print('Decision:',[(r['route'],r['review_score_min']) for r in top],'; flagged:',flagged)
    return out


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path)
    parser.add_argument('--output-dir',type=Path)
    args=parser.parse_args()
    build(args.data_dir,args.output_dir,args.output_dir/'DECISION.md' if args.output_dir else None)

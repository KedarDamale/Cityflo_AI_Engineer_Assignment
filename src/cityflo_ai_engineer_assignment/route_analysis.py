"""Timetable-based arrival delay analysis; never reads or emits raw ops chatter."""
import csv
import math
import os
import statistics as st
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastmcp import FastMCP

ROOT = Path(__file__).resolve().parents[2]
LOCAL = timezone(timedelta(hours=5, minutes=30))
POLICY = 'Export runtime for unidentified classes; REC-114 for explicit 400–499 classes from its effective date.'

def get_route_data_dir():
    """A separate override keeps fresh-slice route analysis independent of DuckDB."""
    return Path(os.environ.get('CITYFLO_ROUTE_DATA_DIR', ROOT/'data')).resolve()

def read_csv(path):
    with path.open(newline='', encoding='utf-8-sig') as f:
        return [{k.strip(): (v or '').strip() for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]

def offset(value):
    if len(value) != 6 or value[0] not in '+-' or value[3] != ':':
        raise ValueError('invalid offset')
    h, m = int(value[1:3]), int(value[4:6])
    if h > 14 or m > 59 or (h == 14 and m):
        raise ValueError('invalid offset')
    return timezone((1 if value[0] == '+' else -1) * timedelta(hours=h, minutes=m))

def load(data_dir, max_elapsed_min=360, include_negative_elapsed=False):
    schedules = defaultdict(list)
    for row in read_csv(data_dir / 'schedule_v2.csv'):
        schedules[row['route']].append((datetime.fromisoformat(row['effective_date']).date(), float(row['revised_runtime_min'])))
    rows, excluded = [], []
    source_rows = read_csv(data_dir / 'trips.csv')
    ids = Counter(r.get('trip_id', '') for r in source_rows)
    for r in source_rows:
        try:
            if not r.get('trip_id') or ids[r['trip_id']] > 1:
                raise ValueError('missing or duplicate trip id')
            departure = datetime.fromisoformat(r['scheduled_departure']).replace(tzinfo=LOCAL)
            arrival = datetime.fromisoformat(r['actual_arrival']).replace(tzinfo=offset(r['tz_offset']))
            runtime = float(r['scheduled_runtime_min'])
            original_runtime = runtime
            timetable_source = 'export: class unidentified' if len(r['vehicle_series']) <= 2 else 'export'
            if not math.isfinite(runtime) or runtime <= 0:
                raise ValueError('invalid runtime')
            series = int(r['vehicle_series'])
            if 400 <= series <= 499:
                candidates = [s for s in schedules[r['route']] if s[0] <= departure.date()]
                if candidates:
                    runtime = max(candidates)[1]
                    timetable_source = 'REC-114 revised timetable'
                elif not schedules[r['route']]:
                    raise ValueError('missing applicable revised timetable')
            delay = (arrival - (departure + timedelta(minutes=runtime))).total_seconds() / 60
            # Flag negative scheduled-departure-to-arrival intervals and extreme intervals;
            # retain unusually late but plausible journeys for sensitivity checks.
            elapsed = delay + runtime
            if (elapsed < 0 and not include_negative_elapsed) or elapsed > max_elapsed_min:
                raise ValueError('implausible elapsed time')
            rows.append({'trip_id': r['trip_id'], 'route': r['route'], 'date': str(departure.date()), 'delay': delay, 'series': series,
                         'elapsed_min': elapsed, 'runtime_min': runtime, 'export_runtime_min': original_runtime,
                         'timetable_source': timetable_source})
        except (ValueError, OverflowError, KeyError) as e:
            reason = str(e) if str(e) in ('invalid offset','invalid runtime','missing applicable revised timetable','implausible elapsed time','missing or duplicate trip id') else 'invalid input'
            excluded.append({'trip_id': r.get('trip_id',''), 'route': r.get('route',''), 'reason': reason})
    return rows, excluded

def trimmed(x, fraction):
    x = sorted(x); n = int(len(x)*fraction)
    return st.mean(x[n:len(x)-n] if n else x)

def huber(x, c=1.5):
    mu = st.median(x); scale = 1.4826 * st.median(abs(v-mu) for v in x)
    if scale == 0:
        return mu
    for _ in range(100):
        weights = [min(1, c*scale/abs(v-mu)) if v != mu else 1 for v in x]
        new = sum(v*w for v,w in zip(x,weights))/sum(weights)
        if abs(new-mu) < 1e-8: return new
        mu = new
    return mu

def summarize(rows, severity_weight=30, severe_threshold=30, flag_threshold=5, all_routes=()):
    groups = defaultdict(list)
    for route in all_routes:
        groups[route] = []
    for row in rows: groups[row['route']].append(row['delay'])
    out=[]
    for route, x in sorted(groups.items()):
        if not x:
            out.append({'route':route, 'trips':0, 'review_verdict':'insufficient_data', 'review_score_min':None})
            continue
        sx=sorted(x)
        severe = sum(v > severe_threshold for v in x)
        score = trimmed(x, .1) + severity_weight * severe / len(x)
        out.append({'review_score_min':round(score, 2), 'severe_over_30_count':sum(v > 30 for v in x),
                    'severe_count_at_threshold':severe, 'review_verdict': 'flag' if score > flag_threshold else 'clear',
                    'route':route,'trips':len(x),'median_min':round(st.median(x),2),'trimmed_mean_10_min':round(trimmed(x,.1),2),'huber_min':round(huber(x),2),'mean_min':round(st.mean(x),2),'late_over_10_count':sum(v>10 for v in x),'p90_min':round(sx[math.ceil(.9*len(sx))-1],2),
                    'positive_delay_trip_minutes':round(sum(max(0,v) for v in x),2),
                    'severe_delay_trip_minutes':round(sum(v for v in x if v > 30),2)})
    return out

def ranked(items, key='review_score_min'):
    return sorted(items, key=lambda r:(r.get(key) is None, -(r.get(key) or 0), r['route']))

def evaluation(rows, data_dir=None):
    base=summarize(rows); dates=sorted({r['date'] for r in rows})
    def rank(rs,key): return [r['route'] for r in sorted(rs,key=lambda r:(-r[key],r['route']))[:3]]
    top={key:rank(base,key) for key in ('median_min','trimmed_mean_10_min','huber_min','mean_min')}
    leave={d:rank(summarize([r for r in rows if r['date']!=d]),'median_min') for d in dates}
    params={str(p):[r for r,_ in sorted(((route,trimmed([x['delay'] for x in rows if x['route']==route],p)) for route in {x['route'] for x in rows}),key=lambda x:(-x[1],x[0]))[:3]] for p in (.05,.1,.2)}
    def result(items):
        return {'top_three':[r['route'] for r in ranked(items)[:3]],
                'flagged_routes':[r['route'] for r in items if r['review_verdict']=='flag'],
                'consequential_routes':[r for r in items if r['route'] in ('R-14','R-26','R-33','R-35','R-37')]}
    sensitivities = {
        'severity_weight':{str(w):result(summarize(rows,severity_weight=w)) for w in (0,10,15,30,60)},
        'severe_threshold':{str(t):result(summarize(rows,severe_threshold=t)) for t in (20,30,45,60)},
        'flag_threshold':{str(t):result(summarize(rows,flag_threshold=t)) for t in (4,5,6)},
        'review_score_leave_one_day_out':{d:result(summarize([r for r in rows if r['date']!=d])) for d in dates},
        'huber_tuning':{str(c):[r for r,_ in sorted(
            ((route,huber([x['delay'] for x in rows if x['route']==route],c)) for route in {x['route'] for x in rows}),
            key=lambda x:(-round(x[1],2),x[0]))[:3]] for c in (1,1.5,2)},
    }
    severe_rows=[r for r in rows if r['delay']>30]
    if severe_rows:
        extreme=max(severe_rows,key=lambda r:(r['delay'],r['trip_id']))
        typical=st.median(r['delay'] for r in rows if r['route']==extreme['route'])
        corrected=[dict(r,delay=typical) if r['trip_id']==extreme['trip_id'] else r for r in rows]
        sensitivities['one_extreme_corrected_to_route_median']={
            **result(summarize(corrected)), 'trip_id':extreme['trip_id'],'hypothetical_delay_min':typical,
            'note':'Hypothetical correction only; not evidence that the observed timestamp is wrong.'}
    if data_dir is not None:
        for cap in (180,360,720):
            stress,_=load(data_dir,max_elapsed_min=cap)
            sensitivities.setdefault('elapsed_cap',{})[str(cap)]=result(summarize(stress))
        stress,_=load(data_dir,include_negative_elapsed=True)
        sensitivities['include_negative_elapsed_stress_only']=result(summarize(stress))
        _, excluded=load(data_dir)
        excluded_ids={r['trip_id'] for r in excluded if r['reason']!='missing or duplicate trip id'}
        for endpoint in (0,360):
            imputed=[]
            schedules=read_csv(data_dir/'schedule_v2.csv')
            for r in read_csv(data_dir/'trips.csv'):
                if r['trip_id'] not in excluded_ids:
                    continue
                try:
                    runtime=float(r['scheduled_runtime_min'])
                    date=str(datetime.fromisoformat(r['scheduled_departure']).date())
                    if not math.isfinite(runtime) or runtime <= 0:
                        continue
                    if 400 <= int(r['vehicle_series']) <= 499:
                        candidates=[s for s in schedules if s['route']==r['route'] and s['effective_date']<=date]
                        if candidates:
                            runtime=float(max(candidates,key=lambda s:s['effective_date'])['revised_runtime_min'])
                        elif not any(s['route']==r['route'] for s in schedules):
                            continue
                    imputed.append({'trip_id':r['trip_id'],'route':r['route'],'date':date,'delay':endpoint-runtime})
                except (ValueError,KeyError):
                    continue
            sensitivities.setdefault('excluded_imputation_endpoints',{})[str(endpoint)]={
                **result(summarize(rows+imputed)), 'imputed_count':len(imputed),
                'note':'Stress only: assign every recoverable excluded record this elapsed time; not observed or corrected data.'}
    daily=[]
    for d in dates:
        for route in sorted({r['route'] for r in rows}):
            x=[r['delay'] for r in rows if r['route']==route and r['date']==d]
            if x: daily.append({'route':route,'date':d,'trips':len(x),'median_min':st.median(x),'severe_over_30_count':sum(v>30 for v in x),'positive_delay_trip_minutes':sum(max(0,v) for v in x)})
    return {'rankings':top,'median_leave_one_day_out':leave,'trimmed_parameter_rankings':params,
            'decision_sensitivity':sensitivities,'daily':daily,
            'note':'Sensitivity measures policy dependence; it does not establish ground truth or Cityflo service policy.'}

def make_server(data_dir=None):
    server=FastMCP('Cityflo route delay analysis')
    data_dir=Path(data_dir) if data_dir is not None else get_route_data_dir()
    @server.tool
    async def route_delays() -> dict:
        """Return per-route arrival delay statistics and data-quality counts."""
        rows, excluded=load(data_dir)
        routes={r['route'] for r in rows+excluded}
        return {'routes':summarize(rows,all_routes=routes),'excluded_count':len(excluded),'excluded_by_reason':dict(Counter(x['reason'] for x in excluded)), 'timetable_policy':POLICY,
                'warning':'Unidentified vehicle classes use export runtimes by explicit operational choice; class mapping remains unverified.'}
    @server.tool
    async def worst_routes(limit: int = 3, method: str = 'review_score') -> dict:
        """Rank by the operational review_score; median, trimmed_mean_10, huber, and mean are comparison methods."""
        keys={'review_score':'review_score_min','median':'median_min','trimmed_mean_10':'trimmed_mean_10_min','huber':'huber_min','mean':'mean_min'}
        if method not in keys or not 1 <= limit <= 1000: return {'error':'Choose a supported method and limit 1 to 1000.'}
        rows,excluded=load(data_dir)
        return {'method':method,'routes':ranked(summarize(rows),keys[method])[:limit],
                'unassessable_routes':sorted({r['route'] for r in excluded}-{r['route'] for r in rows}),
                'status':'operational decision under documented timetable policy' if method == 'review_score' else 'estimator comparison',
                'timetable_policy':POLICY}
    @server.tool
    async def evaluate_methods() -> dict:
        """Compare rankings, trim parameters, and leave-one-day-out median rankings."""
        rows,_=load(data_dir); return evaluation(rows,data_dir)
    @server.tool
    async def route_evidence(route: str) -> dict:
        """Return trip identifiers and calculated delays for a route, including excluded record reasons."""
        rows,excluded=load(data_dir); return {'trips':[r for r in rows if r['route']==route], 'excluded':[r for r in excluded if r['route']==route]}
    return server

if __name__ == '__main__':
    import asyncio
    from cityflo_ai_engineer_assignment.infrastructure.transports.stdio import run_stdio
    asyncio.run(run_stdio(make_server()))

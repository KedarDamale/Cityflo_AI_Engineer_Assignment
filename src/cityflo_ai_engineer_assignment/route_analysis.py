"""Timetable-based arrival delay analysis; never reads or emits raw ops chatter."""
import csv
import math
import statistics as st
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastmcp import FastMCP

ROOT = Path(__file__).resolve().parents[2]
LOCAL = timezone(timedelta(hours=5, minutes=30))

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

def load(data_dir):
    schedules = defaultdict(list)
    for row in read_csv(data_dir / 'schedule_v2.csv'):
        schedules[row['route']].append((datetime.fromisoformat(row['effective_date']).date(), float(row['revised_runtime_min'])))
    rows, excluded = [], []
    for r in read_csv(data_dir / 'trips.csv'):
        try:
            departure = datetime.fromisoformat(r['scheduled_departure']).replace(tzinfo=LOCAL)
            arrival = datetime.fromisoformat(r['actual_arrival']).replace(tzinfo=offset(r['tz_offset']))
            runtime = float(r['scheduled_runtime_min'])
            if not math.isfinite(runtime) or runtime <= 0:
                raise ValueError('invalid runtime')
            series = int(r['vehicle_series'])
            if 400 <= series <= 499:
                candidates = [s for s in schedules[r['route']] if s[0] <= departure.date()]
                if candidates:
                    runtime = max(candidates)[1]
                elif not schedules[r['route']]:
                    raise ValueError('missing applicable revised timetable')
            delay = (arrival - (departure + timedelta(minutes=runtime))).total_seconds() / 60
            # Flag negative scheduled-departure-to-arrival intervals and extreme intervals;
            # retain unusually late but plausible journeys for sensitivity checks.
            elapsed = delay + runtime
            if elapsed < 0 or elapsed > 360:
                raise ValueError('implausible elapsed time')
            rows.append({'trip_id': r['trip_id'], 'route': r['route'], 'date': str(departure.date()), 'delay': delay, 'series': series})
        except (ValueError, OverflowError, KeyError) as e:
            reason = str(e) if str(e) in ('invalid offset','invalid runtime','missing applicable revised timetable','implausible elapsed time') else 'invalid input'
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

def summarize(rows):
    groups = defaultdict(list)
    for row in rows: groups[row['route']].append(row['delay'])
    out=[]
    for route, x in sorted(groups.items()):
        sx=sorted(x)
        severe = sum(v > 30 for v in x)
        score = trimmed(x, .1) + 30 * severe / len(x)
        out.append({'review_score_min':round(score, 2), 'severe_over_30_count':severe, 'review_verdict': 'flag' if score > 5 else 'clear', 'route':route,'trips':len(x),'median_min':round(st.median(x),2),'trimmed_mean_10_min':round(trimmed(x,.1),2),'huber_min':round(huber(x),2),'mean_min':round(st.mean(x),2),'late_over_10_count':sum(v>10 for v in x),'p90_min':round(sx[math.ceil(.9*len(sx))-1],2)})
    return out

def evaluation(rows):
    base=summarize(rows); dates=sorted({r['date'] for r in rows})
    def rank(rs,key): return [r['route'] for r in sorted(rs,key=lambda r:(-r[key],r['route']))[:3]]
    top={key:rank(base,key) for key in ('median_min','trimmed_mean_10_min','huber_min','mean_min')}
    leave={d:rank(summarize([r for r in rows if r['date']!=d]),'median_min') for d in dates}
    params={str(p):[r for r,_ in sorted(((route,trimmed([x['delay'] for x in rows if x['route']==route],p)) for route in {x['route'] for x in rows}),key=lambda x:(-x[1],x[0]))[:3]] for p in (.05,.1,.2)}
    return {'rankings':top,'median_leave_one_day_out':leave,'trimmed_parameter_rankings':params,'note':'Inspect excluded trips, tail counts and close rankings before making a final verdict; sensitivity does not establish ground truth.'}

def make_server():
    server=FastMCP('Cityflo route delay analysis')
    @server.tool
    async def route_delays() -> dict:
        """Return per-route arrival delay statistics and data-quality counts."""
        rows, excluded=load(ROOT/'data')
        return {'routes':summarize(rows),'excluded_count':len(excluded),'excluded_by_reason':dict(Counter(x['reason'] for x in excluded)), 'warning':'Vehicle series may be encoded as two digits; 4xx membership cannot be inferred from those values.'}
    @server.tool
    async def worst_routes(limit: int = 3, method: str = 'median') -> dict:
        """Rank routes by review_score, median, trimmed_mean_10, huber, or mean; default is exploratory median."""
        keys={'review_score':'review_score_min','median':'median_min','trimmed_mean_10':'trimmed_mean_10_min','huber':'huber_min','mean':'mean_min'}
        if method not in keys or not 1 <= limit <= 40: return {'error':'Choose a supported method and limit 1 to 40.'}
        rows,_=load(ROOT/'data'); return {'method':method,'routes':sorted(summarize(rows),key=lambda r:(-r[keys[method]],r['route']))[:limit], 'status':'exploratory, not a final operational verdict'}
    @server.tool
    async def evaluate_methods() -> dict:
        """Compare rankings, trim parameters, and leave-one-day-out median rankings."""
        rows,_=load(ROOT/'data'); return evaluation(rows)
    @server.tool
    async def route_evidence(route: str) -> dict:
        """Return trip identifiers and calculated delays for a route, including excluded record reasons."""
        rows,excluded=load(ROOT/'data'); return {'trips':[r for r in rows if r['route']==route], 'excluded':[r for r in excluded if r['route']==route]}
    return server

if __name__ == '__main__':
    import asyncio
    from cityflo_ai_engineer_assignment.infrastructure.transports.stdio import run_stdio
    asyncio.run(run_stdio(make_server()))

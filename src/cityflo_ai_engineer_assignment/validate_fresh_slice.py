"""Rehearse a separate fresh slice through a real MCP subprocess."""
import asyncio
import csv
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from .decision_report import build
from .route_analysis import ROOT


async def main():
    with tempfile.TemporaryDirectory(prefix='cityflo-fresh-') as folder:
        data=Path(folder)
        (data/'schedule_v2.csv').write_text(
            'route,revised_runtime_min,effective_date,note\nR-51,45,2026-08-05,synthetic\n')
        headers=['trip_id','route','vehicle_series','scheduled_departure',
                 'scheduled_runtime_min','actual_arrival','tz_offset']
        cases=[
            ['before','R-51','451','2026-08-04 09:00','30','2026-08-04 09:40','+05:30'],
            ['after','R-51','451','2026-08-05 09:00','30','2026-08-05 10:10','+05:30'],
            ['utc','R-51','451','2026-08-05 09:00','30','2026-08-05 04:40','+00:00'],
            ['border','R-52','02','2026-08-05 09:00','30','2026-08-05 09:35:30','+05:30'],
            ['invalid','R-53','03','2026-08-05 09:00','30','not-a-time','+05:30'],
            ['duplicate','R-54','04','2026-08-05 09:00','30','2026-08-05 09:35','+05:30'],
            ['duplicate','R-54','04','2026-08-05 09:00','30','2026-08-05 09:35','+05:30'],
        ]
        with (data/'trips.csv').open('w',newline='') as f:
            writer=csv.writer(f); writer.writerow(headers); writer.writerows(cases)
        output=data/'generated'
        expected=build(data,output,output/'DECISION.md')
        assert 'T1-04521' not in (output/'DECISION.md').read_text()
        transport=StdioTransport(command=sys.executable,
            args=['-m','cityflo_ai_engineer_assignment.route_analysis'],cwd=str(ROOT),
            env={'CITYFLO_ROUTE_DATA_DIR':str(data)},keep_alive=False)
        async with Client(transport,init_timeout=30,timeout=30) as client:
            summary=(await client.call_tool('route_delays',{})).structured_content
            ranks=(await client.call_tool('worst_routes',{})).structured_content
            evidence=(await client.call_tool('route_evidence',{'route':'R-51'})).structured_content
            evaluation=(await client.call_tool('evaluate_methods',{})).structured_content
            assert sorted(summary['routes'],key=lambda r:r['route'])==sorted(expected['baseline'],key=lambda r:r['route'])
            assert [r['route'] for r in ranks['routes']]==['R-51','R-52']
            assert ranks['unassessable_routes']==['R-53','R-54']
            assert {r['trip_id']:r['delay'] for r in evidence['trips']}=={'before':10,'after':25,'utc':25}
            assert summary['excluded_count']==3
            baseline_flags=[r['route'] for r in summary['routes'] if r['review_verdict']=='flag']
            new_flags=evaluation['decision_sensitivity']['flag_threshold']['6']['flagged_routes']
            assert baseline_flags==['R-51','R-52'] and new_flags==['R-51']
        result={'verified_at':datetime.now(timezone.utc).isoformat(),'synthetic_slice':True,
            'transport':'real MCP stdio subprocess','original_inputs_overwritten':False,
            'input_rows':len(cases),'included':4,'excluded':3,
            'verified':['effective-date boundary','explicit 4xx timetable','equivalent UTC arrival',
                        'unidentified class uses export','no-data routes not silently cleared',
                        'duplicate IDs excluded','fresh report excludes original narrative',
                        'all four real MCP tools','6-point constraint clears borderline R-52'],
            'ranking':['R-51','R-52'],'default_flags':baseline_flags,'six_point_constraint_flags':new_flags}
        (ROOT/'outputs/fresh-slice-validation.json').write_text(json.dumps(result,indent=2)+'\n')
        print('Fresh-slice MCP rehearsal passed:',json.dumps(result))


if __name__=='__main__':
    asyncio.run(main())

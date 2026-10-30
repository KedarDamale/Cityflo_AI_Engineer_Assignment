import csv
import tempfile
import unittest
from pathlib import Path
from cityflo_ai_engineer_assignment.route_analysis import load, summarize

class RouteDecisionTest(unittest.TestCase):
 def test_revised_timetable_effective_date(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)
   (p/'schedule_v2.csv').write_text('route,revised_runtime_min,effective_date,note\nR-14,60,2026-08-05,test\n')
   (p/'trips.csv').write_text('trip_id,route,vehicle_series,scheduled_departure,scheduled_runtime_min,actual_arrival,tz_offset\na,R-14,414,2026-08-04 08:00,40,2026-08-04 09:10,+05:30\nb,R-14,414,2026-08-05 08:00,40,2026-08-05 09:10,+05:30\nc,R-14,414,2026-08-05 08:00,40,2026-08-05 03:40,+00:00\n')
   rows,ex=load(p)
   self.assertEqual(ex,[])
   self.assertEqual([r['delay'] for r in rows],[30,10,10])
 def test_severity_contributes_to_flag(self):
  rows=[{'route':'R-35','delay':0} for _ in range(80)]+[{'route':'R-35','delay':45} for _ in range(20)]
  r=summarize(rows)[0]
  self.assertEqual(r['severe_over_30_count'],20)
  self.assertEqual(r['review_verdict'],'flag')

if __name__=='__main__': unittest.main()

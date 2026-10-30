import unittest
from datetime import datetime
from cityflo_ai_engineer_assignment.route_analysis import offset, trimmed, huber, load, ROOT

class RouteAnalysisTest(unittest.TestCase):
    def test_timezone_equivalence(self):
        a=datetime.fromisoformat('2026-08-03 01:32').replace(tzinfo=offset('+00:00'))
        b=datetime.fromisoformat('2026-08-03 07:02').replace(tzinfo=offset('+05:30'))
        self.assertEqual(a,b)
    def test_robust_estimates(self):
        self.assertEqual(trimmed([0,1,1,1,100],.2),1)
        self.assertEqual(huber([1,1,1,1,100]),1)
    def test_input_records_are_accounted_for(self):
        rows,excluded=load(ROOT/'data')
        self.assertEqual(len(rows)+len(excluded),5292)

if __name__=='__main__': unittest.main()

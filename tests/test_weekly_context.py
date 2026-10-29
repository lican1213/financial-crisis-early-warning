"""Reconcile six-module weekly risk grades without a spurious technical downgrade."""
import json
import unittest
from datetime import date
from pathlib import Path

from fcews.core import Observation, decide

class WeeklyGradeTests(unittest.TestCase):
    def test_broader_weekly_orange_is_not_a_technical_green(self):
        path=Path(__file__).resolve().parents[1]/"data/weekly_baseline.json"
        weekly=json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(weekly["weekly_report"]["global_risk_grade"],"orange")
        self.assertEqual(weekly["weekly_report"]["composite_score"],66)
        self.assertEqual(weekly["severity"],"unknown")
        self.assertEqual(weekly["model_comparability"],"not_calibrated")
        now=date(2026,10,29)
        def ob(code,v):
            return Observation(code,"2026-10-27",v,"https://fred.stlouisfed.org/","2026-10-29T00:00:00Z")
        rows={"VIXCLS":ob("VIXCLS",18),"STLFSI4":ob("STLFSI4",-1),
              "BAMLH0A0HYM2":ob("BAMLH0A0HYM2",3)}
        state={}
        for _ in range(5):
            result=decide(rows,state,weekly,[],now)
            state=result["next_state"]
            self.assertNotIn("sustained_recovery",result["reasons"])
            self.assertNotIn("above_weekly_baseline",result["reasons"])

if __name__=="__main__":
    unittest.main()

"""Euro-area CISS official CSV parsing, source outages and persistence."""
import tempfile
import unittest
from pathlib import Path
from datetime import datetime,timezone
from fcews.ecb import parse_ecb_csv,refresh

class ECBTests(unittest.TestCase):
    def test_parse_and_choose_latest(self):
        raw="TIME_PERIOD,OBS_VALUE,OBS_STATUS\n2026-10-26,0.1,A\n2026-10-27,0.17,A\n"
        r=parse_ecb_csv(raw,"now")
        self.assertEqual(r["date"],"2026-10-27")
        self.assertEqual(r["value"],0.17)
        self.assertEqual(r["purpose"],"cross_region_context_only")

    def test_schema_drift_rejected(self):
        with self.assertRaises(ValueError):
            parse_ecb_csv("DATE,VALUE\n2026-10-27,0.5\n","now")

    def test_daily_cache(self):
        with tempfile.TemporaryDirectory() as folder:
            time=datetime(2026,10,29,1,0,tzinfo=timezone.utc)
            counter=[0]
            def f(url,timeout):
                counter[0]+=1
                return "TIME_PERIOD,OBS_VALUE\n2026-10-28,0.5\n"
            first=refresh(Path(folder),time,f)
            second=refresh(Path(folder),time,f)
            self.assertEqual(first,second)
            self.assertEqual(counter[0],1)

    def test_feed_down_not_zero(self):
        with tempfile.TemporaryDirectory() as folder:
            time=datetime(2026,10,29,1,0,tzinfo=timezone.utc)
            result=refresh(Path(folder),time,lambda u,t:(_ for _ in ()).throw(TimeoutError("down")))
            self.assertEqual(result["status"],"error")
            self.assertNotIn("observation",result)

if __name__=="__main__":
    unittest.main()

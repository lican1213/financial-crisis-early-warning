"""OFR public repo time-series integrity and daily rate-limit tests."""
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from fcews.stfm import parse_ofr_stfm, refresh

NOW = datetime(2026, 10, 29, 1, 0, tzinfo=timezone.utc)

class OfficialSTFMTests(unittest.TestCase):
    def test_official_array_pairs(self):
        data='[["2026-10-27",3.92],["2026-10-28",3.96],["2026-10-29",null]]'
        result = parse_ofr_stfm(data, NOW.isoformat())
        self.assertEqual(result["value"], 3.96)
        self.assertEqual(result["date"], "2026-10-28")
        self.assertEqual(result["purpose"], "context_only")

    def test_no_numeric_entries_fail(self):
        with self.assertRaises(ValueError):
            parse_ofr_stfm(json.dumps([["2026-10-28",None]]), NOW.isoformat())

    def test_same_day_does_not_refetch(self):
        with tempfile.TemporaryDirectory() as p:
            count=[0]
            def fake(url, timeout):
                count[0]+=1
                return '[["2026-10-28",3.96]]'
            a=refresh(Path(p),NOW,fetcher=fake)
            b=refresh(Path(p),NOW,fetcher=fake)
            self.assertEqual(count[0],1)
            self.assertEqual(a,b)

    def test_outage_does_not_forge_zero(self):
        with tempfile.TemporaryDirectory() as p:
            result=refresh(Path(p),NOW,fetcher=lambda url,timeout: (_ for _ in ()).throw(TimeoutError("down")))
            self.assertEqual(result["status"],"error")
            self.assertNotIn("observation",result)

if __name__=="__main__":
    unittest.main()

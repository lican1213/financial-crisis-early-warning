"""Actual-data ex-post diagnostics are labeled non-predictive and source-dated."""
import tempfile
import unittest
from pathlib import Path
from fcews.expost import collect_historical, generate, parse_history, checkpoints


class ExPostIntegrityTests(unittest.TestCase):
    def test_fred_history_parse_and_observation_lag(self):
        csv="DATE,VIXCLS\n2008-09-12,25\n2008-09-15,42\n2008-09-16,.\n"
        result=parse_history("VIXCLS",csv)
        self.assertEqual(result[0]["first_available_at_utc"],"2008-09-13T00:00:00Z")
        self.assertEqual(len(result),2)
        self.assertIn("EXPOST",result[0]["availability_basis"])

    def test_fake_html_is_not_data(self):
        with self.assertRaises(ValueError):
            parse_history("VIXCLS","<html>blocked</html>")

    def test_replay_report_warns_about_revisions(self):
        values={
            "VIXCLS":"DATE,VIXCLS\n2026-10-20,16\n",
            "BAMLH0A0HYM2":"DATE,BAMLH0A0HYM2\n2026-10-20,3.1\n",
            "NFCI":"DATE,NFCI\n2026-10-20,-0.5\n",
            "STLFSI4":"DATE,STLFSI4\n2026-10-20,-0.5\n",
        }
        def fetch(url,timeout):
            import urllib.parse
            key=urllib.parse.parse_qs(urllib.parse.urlparse(url).query)["id"][0]
            return values[key]
        def coll(start,end):
            return collect_historical(start,end,fetcher=fetch)
        with tempfile.TemporaryDirectory() as d:
            result=generate(Path(d),"2026-10-20","2026-10-23",coll)
            self.assertIn("NOT A POINT-IN-TIME",result["label"])
            self.assertIn("latest revised",result["experimental_controls"]["leakage_risk"])
            self.assertEqual(result["strategies"]["fcews"]["alerts"],0)
            self.assertTrue((Path(d)/"reports"/"expost_latest.json").exists())

if __name__=="__main__":
    unittest.main()

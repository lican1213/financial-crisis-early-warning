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

    def test_proxy_threshold_precrisis_only(self):
        from datetime import date,timedelta
        points=[]
        for i in range(130):
            dt=(date(2000,1,1)+timedelta(days=i)).isoformat()
            points.append({"series":"BAA10Y","observation_date":dt,
                           "first_available_at_utc":(date.fromisoformat(dt)+timedelta(days=1)).isoformat()+"T00:00:00Z",
                           "value":str(1+i/1000),"source_url":"https://fred.stlouisfed.org/series/BAA10Y",
                           "availability_basis":"EXPOST_latest_revised_proxy_lag"})
        points.append({"series":"BAA10Y","observation_date":"2026-10-20",
                       "first_available_at_utc":"2026-10-21T00:00:00Z","value":"99",
                       "source_url":"https://fred.stlouisfed.org/series/BAA10Y",
                       "availability_basis":"EXPOST_latest_revised_proxy_lag"})
        def coll(start,end):
            return points,{"BAA10Y":{"first":"2000-01-01","last":"2026-10-20","records":len(points)}}
        with tempfile.TemporaryDirectory() as p:
            result=generate(Path(p),"2026-10-20","2026-10-23",coll)
            proxy=result["baa_credit_proxy_sensitivity"]
            self.assertLess(proxy["training_q95_percent"],2)
            self.assertGreater(proxy["train_observation_count"],100)
            self.assertIn("NOT HY OAS",proxy["indicator"])

    def test_fake_html_is_not_data(self):
        with self.assertRaises(ValueError):
            parse_history("VIXCLS","<html>blocked</html>")

    def test_replay_report_warns_about_revisions(self):
        values={
            "VIXCLS":"DATE,VIXCLS\n2026-10-20,16\n",
            "BAMLH0A0HYM2":"DATE,BAMLH0A0HYM2\n2026-10-20,3.1\n",
            "NFCI":"DATE,NFCI\n2026-10-20,-0.5\n",
            "STLFSI4":"DATE,STLFSI4\n2026-10-20,-0.5\n",
            "BAA10Y":"DATE,BAA10Y\n2026-10-20,1.5\n",
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

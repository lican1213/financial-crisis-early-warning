"""Adversarial tests proving no modern-data fallback can pass historical PIT gate."""
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from fcews.alfred_public import (
    parse_asof_batch, fetch_batch, collect, weekly_asof,
    decision_checkpoints, evaluate_history, run, BASIS,
)
from fcews.benchmarks import evaluate


class AlfredPublicTests(unittest.TestCase):
    def test_vintage_headers_must_match_exact_request(self):
        # ALFRED can silently return today's vintage when query is malformed.
        with self.assertRaisesRegex(ValueError,"vintage mismatch"):
            parse_asof_batch("DATE,VIXCLS_20261028\n2008-09-12,40\n",
                             "VIXCLS",["2008-09-12"],"https://alfred.stlouisfed.org")

    def test_multiple_vintage_dates_produce_distinct_features(self):
        text=("DATE,VIXCLS_20080912,VIXCLS_20080919\n"
              "2008-09-05,20,20\n"
              "2008-09-12,30,34\n"
              "2008-09-16,,42\n"
              "2008-09-19,,39\n")
        rows, checksum = parse_asof_batch(text,"VIXCLS",["2008-09-12","2008-09-19"],"url")
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[0]["value"],"30.0")
        self.assertEqual(rows[1]["value"],"39.0")
        self.assertEqual(rows[0]["first_available_at_utc"],"2008-09-13T00:00:00Z")
        self.assertEqual(rows[1]["first_available_at_utc"],"2008-09-20T00:00:00Z")
        self.assertEqual(rows[0]["availability_basis"], BASIS)
        self.assertEqual(len(checksum),64)

    def test_alternate_official_date_header(self):
        rows,_=parse_asof_batch("observation_date,VIXCLS_20201002\n2020-10-02,28\n",
                               "VIXCLS",["2020-10-02"],"url")
        self.assertEqual(len(rows),1)

    def test_future_observation_inside_past_snapshot_never_included(self):
        rows,_=parse_asof_batch("DATE,VIXCLS_20080912\n"
                               "2008-09-10,30\n2008-09-15,99\n",
                               "VIXCLS",["2008-09-12"],"url")
        self.assertEqual(rows[0]["value"],"30.0")
        self.assertEqual(rows[0]["observation_date"],"2008-09-10")

    def test_missing_series_in_2008_is_not_a_fake_zero(self):
        rows,_=parse_asof_batch("DATE,STLFSI4_20080912\n2008-09-05,.\n",
                               "STLFSI4",["2008-09-12"],"url")
        self.assertEqual(rows,[])

    def test_batch_rejects_header_order_mismatch(self):
        with self.assertRaisesRegex(ValueError,"vintage mismatch"):
            parse_asof_batch("DATE,VIXCLS_20080919,VIXCLS_20080912\n2008-09-12,30,33\n",
                             "VIXCLS",["2008-09-12","2008-09-19"],"url")

    def test_fetch_repeats_series_id_for_each_date(self):
        requested=[]
        def stub(url):
            requested.append(url)
            return "DATE,VIXCLS_20080912,VIXCLS_20080919\n2008-09-12,20,23\n"
        rows,_=fetch_batch("VIXCLS",["2008-09-12","2008-09-19"],fetch=stub)
        params=parse_qs(urlsplit(requested[0]).query)
        self.assertEqual(params["id"],["VIXCLS,VIXCLS"])
        self.assertEqual(params["vintage_date"],["2008-09-12,2008-09-19"])
        self.assertEqual(len(rows),2)

    def test_pit_guard_accepts_verified_public_asof_basis(self):
        items=[{"series":code,"observation_date":"2026-10-26","value":str(value),
                "first_available_at_utc":"2026-10-27T00:00:00Z",
                "availability_basis":BASIS,"source_url":"https://alfred.stlouisfed.org/"}
               for code,value in (("VIXCLS",40),("BAMLH0A0HYM2",7))]
        result=evaluate(items,[{"decision_at_utc":"2026-10-27T12:00:00Z"}],[],mode="pit")
        self.assertEqual(result["strategies"]["fcews"]["alerts"],1)

    def test_weekly_fridays_and_monday_decisions(self):
        days=weekly_asof("2020-03-01","2020-03-20")
        self.assertEqual(days,["2020-03-06","2020-03-13","2020-03-20"])
        decisions=decision_checkpoints(days)
        self.assertEqual(decisions[1]["decision_at_utc"],"2020-03-16T12:00:00Z")

    def test_recovery_of_missing_vintage_does_not_promote_unverified_data(self):
        def fake(code,chunk):
            if code=="STLFSI4":
                raise ValueError("ALFRED returned today's fallback vintage")
            raw="DATE,"+",".join(code+"_"+d.replace("-","") for d in chunk)+"\n"
            raw+="2008-09-05,"+",".join(["20"]*len(chunk))+"\n"
            return parse_asof_batch(raw,code,chunk,"url")
        dates=["2008-09-12","2008-09-19"]
        rows, stats=collect(dates, codes=("VIXCLS","STLFSI4"), fetch=fake, sleep_seconds=0)
        self.assertEqual(len(rows),2)
        self.assertEqual(stats["STLFSI4"]["snapshots_accepted"],0)
        self.assertEqual(len(stats["STLFSI4"]["errors"]),1)

    def test_strict_fail_on_silent_fallback(self):
        with self.assertRaisesRegex(RuntimeError,"ALFRED source failure"):
            collect(["2008-09-12"], codes=("VIXCLS",),fetch=lambda code,days: (_ for _ in ()).throw(ValueError("fallback")),
                    sleep_seconds=0, strict=True)

    def test_run_includes_holdout_and_source_hashes(self):
        def synthetic(days):
            entries=[]
            stats={}
            for code,value in (("VIXCLS",45),("BAMLH0A0HYM2",7),
                               ("NFCI",2),("STLFSI4",1.5)):
                stats[code]={"snapshots_accepted":len(days),"errors":[],
                             "csv_batch_hashes":["a"*64]}
                for asof in days:
                    entries.append({"series":code,"value":str(value),"observation_date":asof,
                        "requested_asof_date":asof,
                        "first_available_at_utc":(date.fromisoformat(asof).toordinal()+1),
                        "source_url":"https://alfred.stlouisfed.org/",
                        "availability_basis":BASIS})
            # Ensure valid timestamp format.
            from datetime import timedelta
            for x in entries:
                x["first_available_at_utc"]=(date.fromisoformat(x["observation_date"])+timedelta(days=1)).isoformat()+"T00:00:00Z"
            return entries,stats
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            result=run(root,smoke=True,collector=synthetic)
            self.assertTrue((root/"reports/alfred_smoke.json").exists())
            self.assertIn("holdout_2017on",result["evaluation"])
            self.assertEqual(result["diagnostics"]["minimum_source_coverage"],5)

    def test_duplicate_asof_dates_cannot_be_replayed(self):
        with self.assertRaisesRegex(ValueError,"unique"):
            collect(["2026-10-23","2026-10-23"],codes=(),sleep_seconds=0)


if __name__ == "__main__":
    unittest.main()

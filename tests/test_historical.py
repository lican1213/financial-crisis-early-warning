"""Challenge ALFRED vintage ingestion and holdout comparisons with future information."""
import tempfile
import unittest
from pathlib import Path

from fcews.pit_export import export_one
from fcews.benchmarks import evaluate

URL="https://fred.stlouisfed.org/series/"
def entry(code,value,observed="2026-10-25",public="2026-10-26T00:00:00Z",basis="publisher_timestamp_verified"):
    return {"series":code,"value":str(value),"observation_date":observed,
            "first_available_at_utc":public,"availability_basis":basis,
            "source_url":URL+code}

def time(day):
    return {"decision_at_utc":day+"T12:00:00Z"}

class HistoricalAdversarialTests(unittest.TestCase):
    def test_alfred_vintage_conservative_next_day(self):
        calls=[]
        def fake(params):
            calls.append(params)
            return {"count":1,"observations":[
                {"date":"2008-09-12","value":"38.3",
                 "realtime_start":"2008-09-15","realtime_end":"2008-09-15"}]}
        result=export_one("VIXCLS","fake-key","2007-01-01","2009-01-01",get=fake)
        self.assertEqual(result[0]["first_available_at_utc"],"2008-09-16T00:00:00Z")
        self.assertEqual(result[0]["vintage_date"],"2008-09-15")
        self.assertEqual(calls[0]["output_type"],3)

    def test_no_alfred_credential_no_fake_vintage(self):
        with self.assertRaisesRegex(ValueError,"FRED_API_KEY"):
            export_one("VIXCLS","","2007-01-01","2009-01-01")

    def test_unverified_availability_never_passes_pit(self):
        rows=[entry("VIXCLS",40,basis="guessed_weekly_lag")]
        with self.assertRaisesRegex(ValueError,"documented original-release"):
            evaluate(rows,[time("2026-10-27")],[],mode="pit")

    def test_dual_family_real_time_candidate_and_baselines(self):
        data=[entry("VIXCLS",40),entry("BAMLH0A0HYM2",7)]
        pts=[time("2026-10-26"),time("2026-10-27"),time("2026-10-28")]
        events=[{"event_id":"hypothetical","crisis_start_utc":"2026-10-28T12:00:00Z"}]
        result=evaluate(data,pts,events,mode="pit")
        self.assertEqual(result["strategies"]["fcews"]["alerts"],1)
        self.assertEqual(result["strategies"]["vix_only"]["alerts"],1)
        self.assertEqual(result["strategies"]["never_alert"]["alerts"],0)
        self.assertEqual(result["strategies"]["never_alert"]["missed_events"],["hypothetical"])
        self.assertEqual(result["strategies"]["fcews"]["lead_days_by_event"]["hypothetical"],2)

    def test_unreleased_credit_does_not_fake_dual_family(self):
        data=[entry("VIXCLS",40),
              entry("BAMLH0A0HYM2",7,public="2026-10-29T00:00:00Z")]
        result=evaluate(data,[time("2026-10-26"),time("2026-10-27")],[],mode="pit")
        self.assertEqual(result["strategies"]["fcews"]["alerts"],0)
        self.assertEqual(result["strategies"]["vix_only"]["alerts"],1)

    def test_downgrade_attributed_only_after_independent_data(self):
        data=[entry("VIXCLS",17),entry("STLFSI4",-1),entry("BAMLH0A0HYM2",3)]
        result=evaluate(data,[time("2026-10-26")],[],mode="pit")
        self.assertEqual(result["covered_by_three_families_share"],1)

    def test_expost_report_has_nonpredictive_label(self):
        data=[entry("VIXCLS",40,basis="latest_revised")]
        result=evaluate(data,[time("2026-10-27")],[],mode="expost")
        self.assertIn("NOT A POINT-IN-TIME",result["label"])

    def test_duplicate_checkpoints_rejected(self):
        with self.assertRaisesRegex(ValueError,"duplicate"):
            evaluate([], [time("2026-10-27"),time("2026-10-27")],[],mode="pit")

if __name__ == "__main__":
    unittest.main()

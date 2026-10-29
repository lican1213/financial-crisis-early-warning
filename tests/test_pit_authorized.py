"""Unauthorized vintage data must never produce publishable PIT accuracy."""
import csv
import tempfile
import unittest
from pathlib import Path

from fcews.pit_authorized import summary
from fcews.pit_export import FIELDS


class AuthorizedPITGateTests(unittest.TestCase):
    def test_missing_fred_key_rejected_without_creating_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with self.assertRaisesRegex(ValueError,"FRED_API_KEY"):
                summary(root,key="")
            self.assertFalse((root/"reports/alfred_authorized_pit.json").exists())

    def test_empty_vintage_export_rejected(self):
        def empty_export(path,start,end,key):
            path.parent.mkdir(parents=True,exist_ok=True)
            with path.open("w",newline="") as f:
                csv.DictWriter(f,FIELDS).writeheader()
            return {"series_counts":{"VIXCLS":0}}
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,"empty"):
                summary(Path(tmp),key="synthetic",exporter=empty_export)

    def test_authorized_fixture_outputs_only_aggregate_report(self):
        def fake_export(path,start,end,key):
            path.parent.mkdir(parents=True,exist_ok=True)
            rows=[
                {"series":code,"observation_date":"2026-10-26",
                 "first_available_at_utc":"2026-10-27T00:00:00Z",
                 "value":value,"source_url":"https://fred.stlouisfed.org/series/"+code,
                 "availability_basis":"ALFRED_vintage_date_plus_one_UTC_day",
                 "vintage_date":"2026-10-26"}
                for code,value in (("NFCI","1.8"),("VIXCLS","40"),("BAMLH0A0HYM2","7"))
            ]
            with path.open("w",newline="") as f:
                writer=csv.DictWriter(f,FIELDS)
                writer.writeheader()
                writer.writerows(rows)
            return {"type":"ALFRED_day_level_conservative",
                    "series_counts":{"NFCI":1,"VIXCLS":1,"BAMLH0A0HYM2":1}}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            output=summary(root,key="synthetic",start="2026-10-26",end="2026-10-28",exporter=fake_export)
            self.assertEqual(output["method"],"ALFRED_FRED_AUTHORIZED_DATE_LEVEL_PIT")
            self.assertTrue((root/"reports/alfred_authorized_pit.json").exists())
            self.assertIn("miss_quality",output["benchmark"])
            self.assertFalse((root/"reports/alfred_authorized_pit.json").read_text().find("synthetic")!=-1)
            self.assertTrue((root/"data/local/alfred_original_vintages.csv").exists())


if __name__=="__main__":
    unittest.main()

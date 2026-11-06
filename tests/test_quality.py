import unittest
from datetime import date

from fcews.core import Observation
from fcews.quality import elapsed_business_days, late_source_dates


def row(code, day):
    return Observation(code, day, 1.0, "https://official.example/", "2026-11-06T00:00:00Z")


class FreshnessTests(unittest.TestCase):
    def test_weekend_does_not_count_as_three_missing_days(self):
        self.assertEqual(elapsed_business_days(date(2026, 10, 30), date(2026, 11, 2)), 1)

    def test_old_daily_observation_is_flagged_not_called_financial_crisis(self):
        late = late_source_dates({"VIXCLS": row("VIXCLS", "2026-10-29")}, date(2026, 11, 6))
        self.assertEqual(late, {"VIXCLS": 6})

    def test_normal_weekly_publication_not_spuriously_stale(self):
        rows = {"STLFSI4": row("STLFSI4", "2026-10-30"),
                "NFCI": row("NFCI", "2026-10-30")}
        self.assertEqual(late_source_dates(rows, date(2026, 11, 6)), {})

    def test_future_observation_is_an_operational_data_error(self):
        self.assertEqual(late_source_dates({"SOFR": row("SOFR", "2026-11-07")},
                                           date(2026, 11, 6)), {"SOFR": -1})

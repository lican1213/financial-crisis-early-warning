"""Adversarial gates: research context may enrich explanations but NEVER authorize a crisis notification."""
import math
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

from fcews.core import Observation
from fcews.research import (
    CN_SERIES, US_SERIES, build_context, collect_us, evaluate_releases,
    housing_turning_point, official_url, validate_release,
)


def release(code, value, period="2026-09-30", published="2026-10-20", measure=None):
    authority, unit = CN_SERIES[code]
    return {
        "series": code, "authority": authority, "unit": unit, "value": value,
        "period_end": period, "published_date": published,
        "source_url": ("https://www.stats.gov.cn/sj/zxfb/official.html" if authority == "NBS"
                       else "https://www.pbc.gov.cn/goutongjiaoliu/official.html"),
        "definition": "Official statistical measure, not a guessed housing proxy",
        "measure_type": measure or ("monthly" if unit in ("cities", "index")
                                   else "stock_yoy" if "BALANCE" in code or "UNSOLD" in code
                                   else "cumulative_yoy"),
    }


class OfficialReleaseGates(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 11, 9)

    def test_source_hostname_boundary_and_credentials(self):
        self.assertTrue(official_url("https://www.stats.gov.cn/sj/tj.html", "NBS"))
        for bad in [
            "https://www.stats.gov.cn.evil.example/whatever",
            "http://www.stats.gov.cn/sj/tj.html",
            "https://www.stats.gov.cn@bad.example/sj/tj.html",
            "https://www.stats.gov.cn:8080/sj/tj.html",
            "https://stats.gov.cn",  # no document path
        ]:
            self.assertFalse(official_url(bad, "NBS"), bad)

    def test_future_release_rejected_not_backfilled(self):
        with self.assertRaises(ValueError):
            validate_release(release("NBS_PMI_NEW_ORDERS", 49, published="2026-11-10"), self.today)

    def test_period_cannot_postdate_publication(self):
        with self.assertRaises(ValueError):
            validate_release(release("NBS_PMI_NEW_ORDERS", 49, period="2026-11-30"), self.today)

    def test_wrong_loan_statistical_unit_and_authority_rejected(self):
        item = release("PBOC_MORTGAGE_BALANCE_YOY", -3)
        item["unit"] = "billion_cny"
        with self.assertRaises(ValueError):
            validate_release(item, self.today)
        item = release("NBS_DEVELOPER_MORTGAGE_FUNDS_YOY", -18)
        item["authority"] = "PBOC"
        with self.assertRaises(ValueError):
            validate_release(item, self.today)

    def test_nan_and_boolean_and_city_range_rejected(self):
        for number in [math.nan, True, float("inf"), None]:
            with self.assertRaises(ValueError):
                validate_release(release("NBS_PMI_MANUFACTURING", number), self.today)
        for number in [-1, 71, 5.25]:
            with self.assertRaises(ValueError):
                validate_release(release("NBS_USED_HOME_RISING_CITIES", number), self.today)

    def test_company_profit_not_accepted_as_demand(self):
        row = {
            "series": "COMPANY_RANDSTAD", "authority": "RANDSTAD",
            "unit": "net_profit_yoy_pct", "value": 25, "period_end": "2026-09-30",
            "published_date": "2026-10-21", "source_url": "https://www.randstad.com/investors/results",
            "definition": "Profit inflated by restructuring and exchange rate",
            "measure_type": "quarterly",
        }
        with self.assertRaises(ValueError):
            validate_release(row, self.today)
        row["unit"] = "organic_revenue_yoy_pct"
        self.assertEqual(validate_release(row, self.today)["value"], 25)

    def test_no_data_means_unknown_not_zero_or_previous_subjective_score(self):
        got = evaluate_releases([], self.today)
        self.assertIsNone(got["china_recovery_breadth_score"])
        self.assertIsNone(got["staffing_global_score"])
        self.assertEqual(got["housing_turning_point"]["status"], "unverified")

    def test_spoofed_primary_source_prevents_scoring(self):
        row = release("NBS_PMI_SMALL", 47)
        row["source_url"] = "https://stats.gov.cn.scam.test/pmi"
        got = evaluate_releases([row], self.today)
        self.assertEqual(got["status"], "needs_review")
        self.assertEqual(got["accepted_count"], 0)
        self.assertIsNone(got["china_recovery_breadth_score"])

    def test_duplicate_revision_requires_review(self):
        items = [release("NBS_PMI_SMALL", 48), release("NBS_PMI_SMALL", 49)]
        got = evaluate_releases(items, self.today)
        self.assertEqual(got["status"], "needs_review")
        self.assertEqual(len(got["rejected"]), 1)

    def test_single_used_home_city_improvement_not_turning_point(self):
        items = [
            release("NBS_USED_HOME_RISING_CITIES", 2, period="2026-08-31", published="2026-09-20"),
            release("NBS_USED_HOME_RISING_CITIES", 10),
        ]
        got = housing_turning_point(items, self.today)
        self.assertFalse(got["confirmed"])
        self.assertIsNone(got["improving_groups"])

    def test_two_demand_improvements_still_require_inventory(self):
        items = self._full_housing()
        items = [r for r in items if r["series"] != "NBS_RESIDENTIAL_UNSOLD_AREA_YOY"]
        self.assertFalse(housing_turning_point(items, self.today)["confirmed"])

    def test_inventory_worsens_blocks_turning_point(self):
        items = self._full_housing()
        for row in items:
            if row["series"] == "NBS_RESIDENTIAL_UNSOLD_AREA_YOY" and row["period_end"] == "2026-09-30":
                row["value"] = 3
        self.assertFalse(housing_turning_point(items, self.today)["confirmed"])

    def test_two_independent_groups_and_inventory_can_confirm(self):
        got = housing_turning_point(self._full_housing(), self.today)
        self.assertTrue(got["confirmed"])
        self.assertEqual(got["improving_groups"], 3)

    def test_inconsistent_period_blocks_turning_point(self):
        items = self._full_housing()
        for row in items:
            if row["series"] == "PBOC_MORTGAGE_BALANCE_YOY" and row["period_end"] == "2026-09-30":
                row["period_end"] = "2026-10-31"
        self.assertFalse(housing_turning_point(items, self.today)["confirmed"])

    def _full_housing(self):
        data = [
            ("NBS_USED_HOME_RISING_CITIES", 3, 10),
            ("NBS_RESIDENTIAL_SALES_AREA_YOY", -20, -12),
            ("PBOC_MORTGAGE_BALANCE_YOY", -5, -4),
            ("NBS_RESIDENTIAL_UNSOLD_AREA_YOY", 1, 0),
        ]
        items = []
        for code, old, new in data:
            items.append(release(code, old, period="2026-08-31", published="2026-09-20"))
            items.append(release(code, new))
        return items


class USContextGates(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 11, 9)

    def fake(self, code):
        return Observation(code, "2026-10-01" if US_SERIES[code][2] == "monthly" else "2026-11-05", 2.5,
                           "https://fred.stlouisfed.org/series/" + code,
                           "2026-11-09T01:00:00Z")

    def test_all_live_indicators_are_context_not_crisis(self):
        got = collect_us(self.fake, self.today)
        self.assertEqual(got["status"], "complete")
        self.assertEqual(set(got["observations"]), set(US_SERIES))

    def test_stale_monthly_and_wrong_codes_fail_closed(self):
        def wrong(code):
            day = "2025-01-01" if code == "TEMPHELPS" else ("2026-10-01" if US_SERIES[code][2] == "monthly" else "2026-11-05")
            return Observation(code, day, 1, "https://fred.stlouisfed.org",
                               "2026-11-09T01:00:00Z")
        got = collect_us(wrong, self.today)
        self.assertEqual(got["status"], "partial")
        self.assertIn("TEMPHELPS", got["missing"])
        def swapped(code):
            obj = self.fake(code)
            if code == "JTSJOL":
                return Observation("TEMPHELPS", obj.date, obj.value, obj.source, obj.retrieved_utc)
            return obj
        self.assertIn("JTSJOL", collect_us(swapped, self.today)["missing"])

    def test_missing_manual_evidence_keeps_public_repo_private_data_free(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            out = build_context(root, datetime(2026, 11, 9, tzinfo=timezone.utc), self.fake)
            self.assertFalse(out["notification_authorized"])
            self.assertIsNone(out["official_release_research"]["staffing_global_score"])
            self.assertEqual(out["model_comparability"], "not_calibrated")


if __name__ == "__main__":
    unittest.main()

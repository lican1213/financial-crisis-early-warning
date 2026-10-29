"""Falsification tests for licensed MOVE boundary and Cboe official term data."""
import unittest
from datetime import datetime, timezone

from fcews.volatility import (
    parse_index_history, parse_cfe_vx_settlement,
    parse_yield_history, realized_yield_vol, collect_context,
)

UTC = datetime(2026, 10, 29, 3, 0, tzinfo=timezone.utc)


def cboe_csv(code, day="2026-10-28", value=20):
    return f"DATE,OPEN,HIGH,LOW,CLOSE\n{day},18,21,17,{value}\n"


def fred_csv(code, n=28):
    from datetime import date, timedelta
    start=date(2026,9,8)
    rows = [f"{(start+timedelta(days=i)).isoformat()},{4+0.04*(i%7):.2f}"
            for i in range(n)]
    return "observation_date,"+code+"\n"+"\n".join(rows)


class VolatilityTests(unittest.TestCase):
    def test_cboe_native_month_day_year(self):
        items=parse_index_history("DATE,OPEN,HIGH,LOW,CLOSE\n10/27/2026,20,22,19,21\n10/28/2026,19,20,17,18\n","VIX")
        self.assertEqual(items[-1],("2026-10-28",18.0))

    def test_non_positive_or_na_rejected(self):
        with self.assertRaisesRegex(ValueError,"non-positive"):
            parse_index_history("DATE,CLOSE\n2026-10-28,-4\n","VIX3M")

    def test_missing_schema_rejected(self):
        with self.assertRaisesRegex(ValueError,"missing DATE"):
            parse_index_history("Time,Price\n2026-10-28,40\n","VIX")

    def test_index_single_series_tenor_values(self):
        self.assertEqual(parse_index_history("DATE,VIX6M\n2026-10-28,21.4\n","VIX6M"),[("2026-10-28",21.4)])

    def test_realized_rate_vol_correct_units(self):
        dates=[(f"2026-10-{i:02d}", float(i%4)/100+4) for i in range(1,23)]
        result=realized_yield_vol({"DGS10":dates})
        self.assertEqual(result["DGS10"]["window"],20)
        self.assertGreater(result["DGS10"]["std_daily_yield_change_bp_20d"],0)

    def test_rate_vol_sparse_has_no_fake_zero(self):
        self.assertEqual(realized_yield_vol({"DGS10":[("2026-10-28",4.8)]}),{})

    def test_cfe_monthly_vs_weekly_exclusion(self):
        raw=("Symbol,Expiration Date,Settlement Price\n"
             "VX44/X6,2026-11-04,40\n"
             "VX/X6,2026-11-18,20\n"
             "VX/Z6,2026-12-16,22\n"
             "VXM/X6,2026-11-18,19\n")
        result=parse_cfe_vx_settlement(raw,"2026-10-28")
        self.assertEqual(result["front"]["settlement"],20)
        self.assertEqual(result["f2_minus_f1"],2)
        self.assertFalse(result["backwardation"])

    def test_cfe_one_monthly_contract_rejected(self):
        with self.assertRaisesRegex(ValueError,"fewer than two"):
            parse_cfe_vx_settlement(
                "Symbol,Expiration Date,Settlement Price\nVX/X6,2026-11-18,22\n",
                "2026-10-28")

    def test_cfe_negative_price_not_included(self):
        with self.assertRaisesRegex(ValueError,"fewer than two"):
            parse_cfe_vx_settlement(
                "Symbol,Expiration Date,Settlement Price\n"
                "VX/X6,2026-11-18,-1\nVX/Z6,2026-12-16,20\n",
                "2026-10-28")

    def test_mismatched_cboe_dates_cannot_generate_slope(self):
        def fetch(url,timeout):
            if "VIX9D_History" in url:
                return cboe_csv("VIX9D",day="2026-10-27")
            if "History.csv" in url:
                return cboe_csv("VIX")
            return fred_csv(url.split("id=")[-1])
        result=collect_context(UTC,fetcher=fetch,include_futures=False)
        self.assertIsNone(result["context"]["equity_vol_index_term_structure"])
        self.assertIn("CBOE:TERM",result["errors"])

    def test_combined_term_and_treasury_context(self):
        v={"VIX9D":27,"VIX":24,"VIX3M":23,"VIX6M":22}
        def fetch(url,timeout):
            for code in v:
                if "/"+code+"_History.csv" in url:
                    return cboe_csv(code,value=v[code])
            return fred_csv(url.split("id=")[-1])
        result=collect_context(UTC,fetcher=fetch,include_futures=False)
        self.assertEqual(result["status"],"ok")
        self.assertTrue(result["context"]["equity_vol_index_term_structure"]["near_term_equity_implied_vol_higher"])
        self.assertEqual(result["context"]["equity_vol_index_term_structure"]["equity_index_spread_vix9d_minus_vix3m"],4)
        self.assertIsNone(result["context"]["move"]["value"])
        self.assertEqual(result["alert_role"],"context_only_no_independent_family_or_notification_gate")
        self.assertGreater(len(result["context"]["treasury_realized_yield_volatility"]),0)

    def test_outdated_history_causes_degraded_status(self):
        def fetch(url,timeout):
            if "History.csv" in url:
                return cboe_csv("VIX",day="2026-10-10")
            return fred_csv(url.split("id=")[-1])
        result=collect_context(UTC,fetcher=fetch,include_futures=False)
        self.assertEqual(result["status"],"degraded")
        self.assertTrue(any("stale" in error for error in result["errors"].values()))

    def test_no_move_proxy_promoted_to_move(self):
        def fetch(url,timeout):
            if "History.csv" in url:
                return cboe_csv("VIX")
            return fred_csv(url.split("id=")[-1])
        result=collect_context(UTC,fetcher=fetch,include_futures=False)
        self.assertEqual(result["context"]["move"]["status"],"license_required")
        self.assertIsNone(result["context"]["move"]["value"])

    def test_futures_source_failure_does_not_invent_futures(self):
        def fetch(url,timeout):
            if "settlement/csv" in url:
                raise TimeoutError("source down")
            if "History.csv" in url:
                return cboe_csv("VIX")
            return fred_csv(url.split("id=")[-1])
        result=collect_context(UTC,fetcher=fetch,include_futures=True)
        self.assertEqual(result["status"],"ok")
        self.assertNotIn("vx_futures",result["context"])
        self.assertIn("CFE:VX",result["errors"])


if __name__ == "__main__":
    unittest.main()

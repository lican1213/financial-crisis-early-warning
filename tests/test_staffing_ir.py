"""Issuer IR adversarial tests: measure definition, quarter and spoofed source."""
import unittest
from datetime import date, datetime,timezone

from fcews.staffing_ir import RELEASES, collect,extract,official_host

NOW=date(2026,11,9)


def report(code):
    core={
        "RANDSTAD": "21 October 2026 Q3 2026 org. revenue growth 3.9% Organic revenue increased 3.9% "
                    "Underlying EBITA margin 3.5%. Profit boosted by restructuring. ",
        "MANPOWERGROUP":"Oct. 15, 2026 ManpowerGroup Reports 3rd Quarter 2026 Results "
                     "Revenues of $4.8 billion (+4% as reported, +5% constant currency, +6% organic constant currency). "
                     "Continued cost actions improved profit. ",
        "KORN_FERRY":"Korn Ferry Announces First Quarter Fiscal 2027 Results of Operations. September 9, 2026. "
                     "Korn Ferry announced first quarter fee revenue of $756.5 million, an increase of 7% year-over-year at both actual and constant currency. "
                     "AMS acquisition and integration cost footnote. ",
        "HAYS":"Q1 27 Statistics Change in net fees for the quarter ended 30 September 2026 vs prior year. "
               "Group net fees down 3% with Temp & Contracting and Perm down 1% and 7% respectively. "
               "Momentum strategy delivered cost savings and workforce productivity initiatives. ",
        "PAGEGROUP":"Michael Page PLC 13 October 2026 THIRD QUARTER 2026 TRADING UPDATE "
                    "Group gross profit of £190.5m, +1.5% vs. Q3 2025; first quarter of growth since Q4 2022. "
                    "Constant currency excludes foreign exchange impact and UK remains negative. ",
    }
    return "<html><h1>"+core[code]+"</h1><p>Investment banking hiring context, final results cover demand fees not net income.</p></html>"


class StaffingIRTests(unittest.TestCase):
    def test_all_five_quarterly_demand_not_profit(self):
        expected={"RANDSTAD":3.9,"MANPOWERGROUP":6.0,"KORN_FERRY":7.0,
                  "HAYS":-3.0,"PAGEGROUP":1.5}
        for code,want in expected.items():
            with self.subTest(code=code):
                got=extract(code,report(code),NOW)
                self.assertEqual(got["value_pct"],want)
                self.assertEqual(got["period_end"],RELEASES[code]["period_end"])
                self.assertTrue(any(x in got["demand_measure"] for x in ("revenue", "net_fees", "gross_profit")))
                self.assertFalse(got["notification_authorized"])
                self.assertTrue(got["publication_date_in_document"] or code=="HAYS")

    def test_wrong_quarter_rejected(self):
        with self.assertRaises(ValueError):
            extract("RANDSTAD",report("RANDSTAD").replace("Q3 2026","Q2 2026"),NOW)
        with self.assertRaises(ValueError):
            extract("HAYS",report("HAYS").replace("30 September 2026","30 September 2025"),NOW)

    def test_profit_growth_not_equivalent_to_recruitment(self):
        raw=report("RANDSTAD").replace("org. revenue growth 3.9%","net profit growth 93%").replace("Organic revenue increased 3.9%","Operating profit increased 90%")
        with self.assertRaises(ValueError):
            extract("RANDSTAD",raw,NOW)

    def test_fake_recruiter_ir_hostname_rejected(self):
        for code in RELEASES:
            url=RELEASES[code]["url"]
            self.assertTrue(official_host(url,code))
            self.assertFalse(official_host(url.replace("https://","http://"),code))
            self.assertFalse(official_host("https://"+code.lower()+".evil.test/third-quarter",code))
        with self.assertRaises(ValueError):
            extract("PAGEGROUP",report("PAGEGROUP"),NOW,
                    "https://www.londonstockexchange.com.evil.example/en/news/PAGE/1")

    def test_stale_or_future_report_refused(self):
        with self.assertRaises(ValueError):
            extract("RANDSTAD",report("RANDSTAD"),date(2026,10,18))
        with self.assertRaises(ValueError):
            extract("RANDSTAD",report("RANDSTAD"),date(2027,5,1))

    def test_no_demand_metric_if_official_page_is_blocked(self):
        def fake(url,timeout):
            if "randstad.com" in url:
                return report("RANDSTAD")
            raise TimeoutError("source blocked")
        got=collect(datetime(2026,11,9,tzinfo=timezone.utc),fake)
        self.assertEqual(list(got["issuer_reports"]),["RANDSTAD"])
        self.assertEqual(len(got["missing"]),4)
        self.assertIsNone(got["positive_fee_revenue_direction_breadth_pct"])
        self.assertIsNone(got["staffing_global_score"])
        self.assertFalse(got["notification_authorized"])

    def test_full_firm_breadth_not_claimed_to_be_predictive_pulse(self):
        mapping={RELEASES[c]["url"]:report(c) for c in RELEASES}
        got=collect(datetime(2026,11,9,tzinfo=timezone.utc),
                    lambda url,timeout:mapping[url])
        self.assertEqual(got["status"],"complete")
        self.assertEqual(got["positive_fee_revenue_direction_breadth_pct"],80)
        self.assertIsNone(got["staffing_global_score"])
        self.assertIn("NOT",got["breadth_definition"])

    def test_earnings_only_cannot_pass(self):
        raw="<html>13 October 2026 THIRD QUARTER 2026 TRADING UPDATE "
        raw+="Net income up 500% after business disposal and currency accounting. "*5+"</html>"
        with self.assertRaises(ValueError):
            extract("PAGEGROUP",raw,NOW)


if __name__=="__main__":
    unittest.main()

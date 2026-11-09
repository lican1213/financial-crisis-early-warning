"""Issuer IR adversarial tests: measure definition, quarter and spoofed source."""
import unittest
from unittest.mock import patch
from datetime import date, datetime,timezone

from fcews.staffing_ir import RELEASES, collect,extract,official_host,fetch_official_pdf

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


    def test_verified_pdf_url_is_primary_issuer_not_lse_shell(self):
        url=RELEASES["PAGEGROUP"]["url"]
        self.assertTrue(url.startswith("https://investors.michaelpage.com/"))
        self.assertTrue(url.endswith(".pdf"))
        self.assertEqual(RELEASES["PAGEGROUP"]["basis"],"constant_currency_gross_profit_yoy_pct")

    def test_pdf_is_bounded_and_original_redirect_must_not_escape(self):
        url=RELEASES["PAGEGROUP"]["url"]
        class Response:
            def __init__(self,payload,final_url=None):
                self.payload,self.final_url=payload,final_url or url
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def geturl(self):return self.final_url
            def read(self,n):return self.payload[:n]
        text="13 October 2026\nTHIRD QUARTER 2026 TRADING UPDATE\nGroup gross profit of £190.5m, +1.5% vs. Q3 2025" + (" official issuer evidence "*10)
        class Page:
            def extract_text(self):return text
        class Reader:
            is_encrypted=False
            pages=[Page()]
        with patch("fcews.staffing_ir.urlopen",return_value=Response(b"%PDF-fake-proof")):
            with patch("pypdf.PdfReader",return_value=Reader()):
                extracted,sha=fetch_official_pdf(url)
        self.assertIn("Group gross profit of £190.5m",extracted)
        self.assertEqual(len(sha),64)
        self.assertEqual(extract("PAGEGROUP",extracted,NOW,source_sha256=sha)["value_pct"],1.5)
        for payload,redirect in ((b"<html>fake</html>",None),
                                 (b"%PDF-" + b"x"*2_000_000,None),
                                 (b"%PDF-fake","https://investors.michaelpage.com.evil.test/report.pdf")):
            with patch("fcews.staffing_ir.urlopen",return_value=Response(payload,redirect)):
                with self.assertRaises(ValueError):
                    fetch_official_pdf(url)

    def test_unreadable_pdf_is_operational_source_error(self):
        url=RELEASES["PAGEGROUP"]["url"]
        class Response:
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def geturl(self):return url
            def read(self,n):return b"%PDF-1.0\nInvalid document"
        with patch("fcews.staffing_ir.urlopen",return_value=Response()):
            with self.assertRaises(ValueError):
                fetch_official_pdf(url)

    def test_issuer_pdf_not_relabelled_as_a_hiring_volume(self):
        text="13 October 2026 THIRD QUARTER 2026 TRADING UPDATE Group gross profit of £190.5m, +1.5% vs. Q3 2025; Permanent 70% +1.1%, Temporary 30% +2.6%. "*3
        result=extract("PAGEGROUP",text,NOW,source_sha256="a"*64)
        self.assertEqual(result["demand_measure"],"constant_currency_gross_profit_yoy_pct")
        self.assertEqual(result["value_pct"],1.5)
        self.assertEqual(result["origin"],"original_issuer_IR_pdf")
        self.assertNotIn("hiring_volume",result["demand_measure"])

    def test_earnings_only_cannot_pass(self):
        raw="<html>13 October 2026 THIRD QUARTER 2026 TRADING UPDATE "
        raw+="Net income up 500% after business disposal and currency accounting. "*5+"</html>"
        with self.assertRaises(ValueError):
            extract("PAGEGROUP",raw,NOW)


if __name__=="__main__":
    unittest.main()

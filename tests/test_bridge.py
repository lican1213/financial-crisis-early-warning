import json
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from fcews.bridge import build_feed, publish

NOW=datetime(2026,10,29,2,0,tzinfo=timezone.utc)
PROJECT="https://github.com/lican1213/financial-crisis-early-warning/issues/"


class ChatGPTBridgeTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        (self.root/"data").mkdir()
        (self.root/"data/outbox.json").write_text('{"delivered":[],"pending":[]}')
        (self.root/"data/health.json").write_text('{"status":"partial"}')
        (self.root/"data/state.json").write_text('{"severity":"green"}')
        (self.root/"data/weekly_baseline.json").write_text(
            '{"severity":"unknown","model_comparability":"not_calibrated",'
            '"weekly_report":{"global_risk_grade":"orange"}}')

    def test_no_alert_when_no_candidates_even_if_orange_weekly(self):
        feed=build_feed(self.root,NOW)
        self.assertEqual(feed["candidate_count"],0)
        self.assertFalse(feed["should_send_user_notification"])
        self.assertEqual(feed["weekly_human_grade"],"orange")
        self.assertEqual(feed["current_technical_severity"],"green")
        self.assertFalse(feed["technical_model_comparable_to_weekly"])

    def test_partial_health_is_not_crisis(self):
        feed=build_feed(self.root,NOW)
        self.assertTrue(feed["health_not_financial_crisis"])
        self.assertFalse(feed["should_send_user_notification"])

    def test_receipt_yields_candidate_but_not_user_alert(self):
        row={"delivered":[{"id":"abc","issue_url":PROJECT+"21","issue_number":21,
                           "delivered_at_utc":NOW.isoformat()}],"pending":[]}
        (self.root/"data/outbox.json").write_text(json.dumps(row))
        feed=build_feed(self.root,NOW)
        self.assertEqual(feed["candidate_count"],1)
        self.assertEqual(feed["candidates"][0]["candidate_id"],"abc")
        self.assertFalse(feed["candidates"][0]["user_alert_authorized"])
        self.assertFalse(feed["should_send_user_notification"])

    def test_old_or_future_candidate_rejected(self):
        row={"delivered":[{"id":"expired","issue_url":PROJECT+"22","issue_number":22,
                           "delivered_at_utc":(NOW-timedelta(hours=73)).isoformat()},
                          {"id":"future","issue_url":PROJECT+"23","issue_number":23,
                           "delivered_at_utc":(NOW+timedelta(hours=1)).isoformat()}]}
        (self.root/"data/outbox.json").write_text(json.dumps(row))
        self.assertEqual(build_feed(self.root,NOW)["candidate_count"],0)

    def test_untrusted_issue_domain_rejected(self):
        row={"delivered":[{"id":"a","issue_url":"https://evil.example/issues/1",
                           "issue_number":1,"delivered_at_utc":NOW.isoformat()}]}
        (self.root/"data/outbox.json").write_text(json.dumps(row))
        self.assertEqual(build_feed(self.root,NOW)["candidate_count"],0)

    def test_missing_delivery_receipt_cannot_invent_notification(self):
        row={"delivered":[{"id":"a","issue_url":PROJECT+"2","issue_number":2}]}
        (self.root/"data/outbox.json").write_text(json.dumps(row))
        self.assertEqual(build_feed(self.root,NOW)["candidate_count"],0)

    def test_duplicate_receipts_not_duplicated(self):
        rec={"id":"same","issue_url":PROJECT+"10","issue_number":10,
             "delivered_at_utc":NOW.isoformat()}
        (self.root/"data/outbox.json").write_text(json.dumps({"delivered":[rec,rec]}))
        self.assertEqual(build_feed(self.root,NOW)["candidate_count"],1)

    def test_stable_hourly_output_and_no_timestamp_churn(self):
        first=publish(self.root,NOW)
        second=publish(self.root,NOW+timedelta(hours=1))
        self.assertTrue(first["changed"])
        self.assertFalse(second["changed"])
        self.assertEqual(first["fingerprint_sha256"],second["fingerprint_sha256"])


    def test_fresh_research_supplements_feed_but_cannot_authorize_alert(self):
        research={
            "as_of_date_utc":"2026-10-29",
            "us_labor_rates_credit":{"status":"complete","observations":{
                "TEMPHELPS":{"observation_date":"2026-10-01"}}},
            "official_release_research":{"china_recovery_breadth_score":100,
                                         "staffing_global_score":100},
            "notification_authorized":True,
        }
        (self.root/"data/research_context.json").write_text(json.dumps(research))
        feed=build_feed(self.root,NOW)
        self.assertEqual(feed["leading_research"]["status"],"fresh")
        self.assertEqual(feed["leading_research"]["us_observation_dates"]["TEMPHELPS"],"2026-10-01")
        self.assertIsNone(feed["leading_research"]["china_recovery_breadth_score"])
        self.assertIsNone(feed["leading_research"]["staffing_global_score"])
        self.assertFalse(feed["leading_research"]["authorizes_notification"])
        self.assertFalse(feed["should_send_user_notification"])
        self.assertEqual(feed["weekly_human_grade"],"orange")
        self.assertTrue(feed["weekly_human_grade_is_historical_paused"])
        self.assertFalse(feed["technical_model_comparable_to_weekly"])

    def test_stale_research_cannot_be_presented_as_current(self):
        (self.root/"data/research_context.json").write_text(json.dumps({
            "as_of_date_utc":"2026-10-23",
            "us_labor_rates_credit":{"status":"complete",
                                     "observations":{"JTSJOL":{"observation_date":"2026-08-01"}}}
        }))
        feed=build_feed(self.root,NOW)
        self.assertEqual(feed["leading_research"]["status"],"stale")
        self.assertEqual(feed["leading_research"]["us_observation_dates"],{})
        self.assertFalse(feed["leading_research"]["authorizes_notification"])

    def test_future_research_date_does_not_override_risk_gate(self):
        (self.root/"data/research_context.json").write_text(
            '{"as_of_date_utc":"2027-01-01"}')
        self.assertEqual(build_feed(self.root,NOW)["leading_research"]["status"],"stale")
        self.assertEqual(build_feed(self.root,NOW)["candidate_count"],0)


    def test_official_nbs_source_dates_never_grant_alerts_or_china_score(self):
        nbs={
            "schema":"fcews.nbs_official_pmi.v1", "status":"complete",
            "released_at_date":"2026-10-20",
            "source_url":"https://www.stats.gov.cn/sj/zxfbhjd/202610/t20261020_1965718.html",
            "observations":{"NBS_PMI_NEW_ORDERS":{"period_end":"2026-09-30", "value":99.0}},
            "alert_authorized":True, "score_authorized":True,
        }
        (self.root/"data/nbs_pmi_context.json").write_text(json.dumps(nbs))
        x=build_feed(self.root,NOW)
        self.assertEqual(x["nbs_pmi_research"]["published_date"],"2026-10-20")
        self.assertFalse(x["nbs_pmi_research"]["authorizes_notification"])
        self.assertIsNone(x["nbs_pmi_research"]["china_recovery_breadth_score"])
        self.assertFalse(x["should_send_user_notification"])

    def test_spoofed_nbs_source_not_forwarded(self):
        nbs={
            "schema":"fcews.nbs_official_pmi.v1","released_at_date":"2026-10-20",
            "source_url":"https://stats.gov.cn.evil.test/sj/zxfbhjd/202610/t20261020_1965718.html",
            "observations":{"NBS_PMI_NEW_ORDERS":{"period_end":"2026-09-30", "value":99}},
        }
        (self.root/"data/nbs_pmi_context.json").write_text(json.dumps(nbs))
        x=build_feed(self.root,NOW)
        self.assertEqual(x["nbs_pmi_research"]["status"],"missing_or_stale")
        self.assertFalse(x["should_send_user_notification"])

    def test_property_nbs_data_never_replaces_absent_pbc_mortgage_with_developer_cash(self):
        import json
        from datetime import date
        ctx={
            "schema":"fcews.nbs_property.v1","status":"complete",
            "as_of_date_utc":"2026-10-29",
            "latest_prices":{
                "period_end":"2026-09-30","source_url":"https://www.stats.gov.cn/sj/zxfb/202610/t20261019_1965609.html",
                "new":{"city_count":70,"mom_rising":17},
                "used":{"city_count":70,"mom_rising":9}},
            "latest_market":{
                "period_end":"2026-09-30","source_url":"https://www.stats.gov.cn/sj/zxfb/202610/t20261019_1965615.html",
                "developer_funding":{"developer_received_mortgages":{"cumulative_yoy_pct":100.0}}},
            "housing_turning_point_confirmed":True,
            "china_recovery_breadth_score":100,
            "directional_signals":{"used_price_rising_city_count_change":6},
        }
        (self.root/"data/nbs_property_context.json").write_text(json.dumps(ctx))
        feed=build_feed(self.root,NOW)
        got=feed["nbs_property_research"]
        self.assertEqual(got["used_city_rising_count"],9)
        self.assertTrue(got["needs_independent_pboc_mortgage_crosscheck"])
        self.assertFalse(got["turning_point_confirmed"])
        self.assertFalse(got["risk_alert_authorized"])
        self.assertIsNone(got["china_recovery_breadth_score"])
        self.assertFalse(feed["should_send_user_notification"])

    def test_stale_property_or_wrong_city_count_fail_closed(self):
        import json
        ctx={"schema":"fcews.nbs_property.v1","status":"complete",
             "as_of_date_utc":"2026-10-20",
             "latest_prices":{"period_end":"2026-09-30","new":{"city_count":69},
                              "used":{"city_count":70}},
             "latest_market":{"period_end":"2026-09-30"}}
        (self.root/"data/nbs_property_context.json").write_text(json.dumps(ctx))
        self.assertEqual(build_feed(self.root,NOW)["nbs_property_research"]["status"],"missing_or_stale")


    def test_stale_or_spoofed_staffing_does_not_invent_global_pulse(self):
        from fcews.staffing_ir import RELEASES
        reports={
            code:{"source_status":"issuer_document_parsed",
                  "published_date":v["published"],"period_end":v["period_end"],
                  "source_url":v["url"],"demand_measure":v["basis"],"value_pct":5}
            for code,v in RELEASES.items()}
        reports["HAYS"]["source_url"]="https://haysplc.com.evil.test/fake"
        research={"schema":"fcews.staffing_official_ir.v1",
                  "as_of_date_utc":"2026-10-29",
                  "issuer_reports":reports,
                  "positive_fee_revenue_direction_breadth_pct":100,
                  "staffing_global_score":100,"notification_authorized":True}
        (self.root/"data/staffing_ir_context.json").write_text(json.dumps(research))
        feed=build_feed(self.root,NOW)
        got=feed["staffing_issuer_research"]
        self.assertEqual(got["status"],"partial")
        self.assertIn("HAYS",got["missing_issuers"])
        self.assertIsNone(got["positive_fee_breadth_pct"])
        self.assertIsNone(got["staffing_global_score"])
        self.assertFalse(got["risk_alert_authorized"])
        self.assertFalse(feed["should_send_user_notification"])

    def test_complete_five_issuer_directions_not_equal_systemic_stress(self):
        from fcews.staffing_ir import RELEASES
        reports={
            code:{"source_status":"issuer_document_parsed",
                  "published_date":v["published"],"period_end":v["period_end"],
                  "source_url":v["url"],"demand_measure":v["basis"],
                  "value_pct":(-2 if code=="HAYS" else 3)}
            for code,v in RELEASES.items()}
        (self.root/"data/staffing_ir_context.json").write_text(json.dumps({
            "schema":"fcews.staffing_official_ir.v1",
            "as_of_date_utc":"2026-10-29", "issuer_reports":reports}))
        feed=build_feed(self.root,NOW)
        self.assertEqual(feed["staffing_issuer_research"]["status"],"complete")
        self.assertEqual(feed["staffing_issuer_research"]["positive_fee_breadth_pct"],80)
        self.assertFalse(feed["should_send_user_notification"])
        self.assertEqual(feed["current_technical_severity"],"green")
        self.assertEqual(feed["weekly_human_grade"],"orange")


    def test_pboc_mortgage_is_different_from_household_mlt_and_nbs_developer_funds(self):
        from fcews.pboc_credit import FINANCIAL,CREDIT
        provenance="official_shanghai_government_republication_of_PBOC_not_original_vintage"
        ctx={
            "schema":"fcews.pboc_official_republication.v1","status":"complete",
            "as_of_date_utc":"2026-10-29","period_end":"2026-09-30",
            "financial_statistics":{"period_end":"2026-09-30","source_url":FINANCIAL,
                                   "publication_provenance":provenance,
                                   "household_medium_long_ytd_flow_100m_cny":1062,
                                   "gov_bond_fraction_of_tsf_pct":37.51},
            "loan_allocation":{"period_end":"2026-09-30","source_url":CREDIT,
                               "publication_provenance":provenance,
                               "individual_mortgage_balance_yoy_pct":-4.1,
                               "individual_mortgage_ytd_net_change_trillion_cny":-1.10},
            "china_recovery_breadth_score":100,
            "housing_turning_point_confirmed":True,
        }
        (self.root/"data/pboc_credit_context.json").write_text(json.dumps(ctx))
        feed=build_feed(self.root,NOW)
        got=feed["pboc_credit_research"]
        self.assertEqual(got["household_mlt_ytd_flow_100m_cny"],1062)
        self.assertEqual(got["mortgage_balance_yoy_pct"],-4.1)
        self.assertEqual(got["mortgage_ytd_net_change_trillion_cny"],-1.10)
        self.assertEqual(got["government_bond_share_tsf_pct"],37.51)
        self.assertIsNone(got["original_first_published_at"])
        self.assertFalse(got["housing_turning_point_confirmed"])
        self.assertFalse(got["risk_alert_authorized"])
        self.assertIsNone(got["china_recovery_breadth_score"])
        self.assertFalse(feed["should_send_user_notification"])

    def test_forged_pboc_source_or_stale_record_is_not_live_evidence(self):
        from fcews.pboc_credit import FINANCIAL,CREDIT
        p="official_shanghai_government_republication_of_PBOC_not_original_vintage"
        ctx={"schema":"fcews.pboc_official_republication.v1","status":"complete",
             "as_of_date_utc":"2026-10-29","period_end":"2026-09-30",
             "financial_statistics":{"period_end":"2026-09-30","source_url":FINANCIAL,
                                    "publication_provenance":p},
             "loan_allocation":{"period_end":"2026-09-30",
                                "source_url":CREDIT.replace("jrj.sh.gov.cn","jrj.sh.gov.cn.evil.test"),
                                "publication_provenance":p}}
        (self.root/"data/pboc_credit_context.json").write_text(json.dumps(ctx))
        x=build_feed(self.root,NOW)
        self.assertEqual(x["pboc_credit_research"]["status"],"missing_or_stale")
        self.assertFalse(x["should_send_user_notification"])

    def test_last_fully_verified_staffing_is_separate_from_failed_current_poll(self):
        from fcews.staffing_ir import RELEASES
        latest={
            "schema":"fcews.staffing_official_ir.v1","status":"complete",
            "as_of_date_utc":"2026-10-29","positive_fee_revenue_direction_breadth_pct":80,
            "issuer_reports":{
                k:{"source_url":v["url"],"source_status":"issuer_document_parsed",
                   "demand_measure":v["basis"],"published_date":v["published"],
                   "value_pct":(-3 if k=="HAYS" else 3)}
                for k,v in RELEASES.items()}
        }
        current={**latest,"status":"partial",
                 "issuer_reports":{k:v for k,v in latest["issuer_reports"].items() if k!="MANPOWERGROUP"}}
        (self.root/"data/staffing_ir_context.json").write_text(json.dumps(current))
        (self.root/"data/staffing_last_verified.json").write_text(json.dumps(latest))
        feed=build_feed(self.root,NOW)
        self.assertEqual(feed["staffing_issuer_research"]["status"],"partial")
        self.assertEqual(feed["staffing_last_verified"]["issuer_count"],5)
        self.assertEqual(feed["staffing_last_verified"]["positive_fee_direction_breadth_pct"],80)
        self.assertFalse(feed["staffing_last_verified"]["is_current_run_evidence"])
        self.assertFalse(feed["staffing_last_verified"]["authorizes_notification"])
        self.assertFalse(feed["should_send_user_notification"])

    def test_forged_old_staffing_archive_never_passes(self):
        from fcews.staffing_ir import RELEASES
        last={
            "schema":"fcews.staffing_official_ir.v1","status":"complete",
            "as_of_date_utc":"2026-10-29","positive_fee_revenue_direction_breadth_pct":80,
            "issuer_reports":{
                k:{"source_url":v["url"],"source_status":"issuer_document_parsed",
                   "demand_measure":v["basis"],"published_date":v["published"],
                   "value_pct":(-3 if k=="HAYS" else 3)}
                for k,v in RELEASES.items()}
        }
        last["issuer_reports"]["MANPOWERGROUP"]["source_url"]="https://manpowergroup.com.evil.test/fake"
        (self.root/"data/staffing_last_verified.json").write_text(json.dumps(last))
        self.assertEqual(build_feed(self.root,NOW)["staffing_last_verified"]["status"],
                         "not_available_or_outdated")

    def test_no_webhook_claim_in_contract(self):
        feed=build_feed(self.root,NOW)
        self.assertEqual(feed["transport"],"ChatGPT_hourly_poll_not_GitHub_webhook")

if __name__=="__main__":
    unittest.main()

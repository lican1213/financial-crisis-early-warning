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

    def test_no_webhook_claim_in_contract(self):
        feed=build_feed(self.root,NOW)
        self.assertEqual(feed["transport"],"ChatGPT_hourly_poll_not_GitHub_webhook")

if __name__=="__main__":
    unittest.main()

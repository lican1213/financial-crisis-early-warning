"""Operational receipts must never imply financial alert authorization."""
import unittest
from datetime import datetime, timezone, timedelta

from fcews.heartbeat import receipt


class HeartbeatTests(unittest.TestCase):
    now = datetime(2026, 11, 16, 12, tzinfo=timezone.utc)

    def record(self, previous=None, event="schedule", results=None, health="healthy", now=None, evidence="abc", attempt="1"):
        return receipt(previous or {}, now=now or self.now, event=event,
                       run_id="123", run_attempt=attempt, health=health, evidence_sha=evidence,
                       results=results or dict(collect="success", persist="success", bridge="success"))

    def test_unchanged_evidence_still_records_poll(self):
        first=self.record()
        second=self.record(first, now=self.now+timedelta(hours=1))
        self.assertEqual(first["evidence_sha256"],second["evidence_sha256"])
        self.assertNotEqual(first["last_successful_scheduled_poll_utc"],second["last_successful_scheduled_poll_utc"])
        self.assertFalse(second["authorizes_notification"])

    def test_push_does_not_mask_missed_schedule(self):
        first=self.record()
        second=self.record(first,event="push",now=self.now+timedelta(hours=3))
        self.assertEqual(first["last_successful_scheduled_poll_utc"],second["last_successful_scheduled_poll_utc"])
        self.assertNotEqual(first["last_successful_poll_utc"],second["last_successful_poll_utc"])

    def test_retry_cannot_mask_missed_natural_schedule(self):
        first=self.record()
        retry=self.record(first,attempt="2",now=self.now+timedelta(hours=4))
        self.assertTrue(retry["evidence_stages_completed"])
        self.assertFalse(retry["natural_schedule_attempt"])
        self.assertEqual(first["last_successful_scheduled_poll_utc"],retry["last_successful_scheduled_poll_utc"])
        self.assertNotEqual(first["last_successful_poll_utc"],retry["last_successful_poll_utc"])

    def test_unattested_legacy_schedule_clock_not_carried_forward(self):
        previous={"last_successful_scheduled_poll_utc":self.now.isoformat()}
        self.assertIsNone(self.record(previous,event="push")["last_successful_scheduled_poll_utc"])

    def test_failed_stage_does_not_advance_success_clock(self):
        first=self.record()
        for failed in ("collect","persist","bridge"):
            with self.subTest(failed=failed):
                results=dict(collect="success",persist="success",bridge="success")
                results[failed]="failure"
                second=self.record(first,results=results,now=self.now+timedelta(hours=1))
                self.assertFalse(second["evidence_stages_completed"])
                self.assertEqual(first["last_successful_scheduled_poll_utc"],second["last_successful_scheduled_poll_utc"])

    def test_missing_evidence_or_degraded_health_does_not_count(self):
        for kwargs in (dict(evidence=None),dict(health="degraded"),dict(health="unknown")):
            result=self.record(**kwargs)
            self.assertFalse(result["evidence_stages_completed"])
            self.assertIsNone(result["last_successful_scheduled_poll_utc"])

    def test_partial_is_completed_but_not_healthy(self):
        result=self.record(health="partial")
        self.assertTrue(result["evidence_stages_completed"])
        self.assertEqual(result["monitor_health"],"partial")
        self.assertFalse(result["authorizes_notification"])

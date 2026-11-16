"""Boundary tests: source dates -> decision -> persistent outbox -> read-only feed."""
import json
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from fcews.bridge import build_feed, publish
from fcews.cli import read_json, run, fingerprint, write_if_changed
from fcews.core import Observation, decide, advance_state
from fcews.backtest import replay
from fcews.delivery import deliver_candidates
from fcews.heartbeat import receipt

NOW = datetime(2026, 10, 29, 12, tzinfo=timezone.utc)
DAY = NOW.date()
ISSUE = "https://github.com/lican1213/financial-crisis-early-warning/issues/42"


def ob(code, day, value, recent=()):
    return Observation(code, day, value, "https://fred.stlouisfed.org/series/" + code,
                       NOW.isoformat(), recent=recent)


def pair():
    return {
        code: ob(code, "2026-10-28", value, (ob(code, "2026-10-27", value),))
        for code, value in (("VIXCLS", 40), ("BAMLH0A0HYM2", 7))
    }


class IssueClient:
    def __init__(self):
        self.fail = True
        self.record = None

    def find_body_fingerprint(self, key):
        return self.record if self.record and ("FCEWS-FP:" + key) in self.record["body"] else None

    def create(self, title, body):
        if self.fail:
            raise TimeoutError("issue transport unavailable")
        self.record = {"number": 42, "html_url": ISSUE, "body": body}
        return self.record

    def get(self, number):
        return self.record


class CrossStageTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    def fetch(self, rows, now=NOW):
        return run(self.root, lambda: (rows, {}), now)

    def test_late_third_channel_is_preserved_through_failed_issue_and_retry(self):
        self.assertTrue(self.fetch(pair())["alert_candidate"])
        # Credit/volatility already active on latest common date 28th.
        first = read_json(self.root/"data/outbox.json", {})["pending"][0]["id"]
        later = {**pair(), "SOFR": ob("SOFR", "2026-10-27", 4.1),
                 "TGCR": ob("TGCR", "2026-10-27", 3.8)}
        now = NOW + timedelta(hours=1)
        self.assertTrue(self.fetch(later, now)["alert_candidate"])
        result = read_json(self.root/"data/outbox.json", {})
        candidate = result["pending"][1]
        key = candidate["id"]
        self.assertNotEqual(key, first)
        self.assertEqual(candidate["evidence"]["newly_confirmed_families"], ["funding"])
        self.assertEqual(set(candidate["evidence"]["confirmation_matches"]["2026-10-27"]),
                         {"credit", "volatility", "funding"})
        self.assertEqual(set(candidate["evidence"]["confirmation_matches"]["2026-10-28"]),
                         {"credit", "volatility"})
        # Stage 3 can read the candidate before Issue creation; feed is not permission.
        publish(self.root, now)
        client = IssueClient()
        with self.assertRaises(TimeoutError):
            deliver_candidates(self.root, client)
        feed = build_feed(self.root, now)
        self.assertEqual(feed["candidate_count"], 2)
        visible = next(c for c in feed["candidates"] if c["candidate_id"] == key)
        self.assertEqual(visible["github_issue_status"], "pending")
        self.assertEqual(visible["evidence"], candidate["evidence"])
        self.assertIsNone(visible["issue_url"])
        self.assertFalse(feed["should_send_user_notification"])
        self.assertFalse(visible["user_alert_authorized"])
        self.assertFalse(self.fetch(later, now)["alert_candidate"])
        # Acknowledge just the second record, simulating a completed prior delivery of first.
        result["pending"] = [candidate]
        write_if_changed(self.root/"data/outbox.json", result)
        client.fail = False
        with patch("fcews.delivery.datetime") as clock:
            clock.now.return_value = now
            self.assertEqual(deliver_candidates(self.root, client), 1)
            self.assertEqual(deliver_candidates(self.root, client), 0)
        acknowledged = build_feed(self.root, now)["candidates"][0]
        self.assertEqual(acknowledged["candidate_id"], key)
        self.assertEqual(acknowledged["github_issue_status"], "acknowledged")
        self.assertEqual(acknowledged["evidence"], visible["evidence"])
        self.assertFalse(acknowledged["user_alert_authorized"])
        self.assertFalse(self.fetch(later, now)["alert_candidate"])

    def test_recent_normal_discards_older_third_channel(self):
        self.fetch(pair())
        rows = {**pair(), "SOFR": ob("SOFR", "2026-10-28", 3.81, (ob("SOFR","2026-10-27",4.1),)),
                "TGCR": ob("TGCR", "2026-10-28", 3.8, (ob("TGCR","2026-10-27",3.8),))}
        self.assertFalse(self.fetch(rows, NOW+timedelta(hours=1))["alert_candidate"])
        snapshot = read_json(self.root/"data/latest_check.json", {})
        self.assertNotIn("funding", snapshot["confirmation_matches"]["2026-10-27"])

    def test_same_id_expiry_cannot_be_reset_by_late_issue_receipt(self):
        evidence = {"reasons":["independent_stress_families"]}
        key = fingerprint(evidence)[:20]
        row = {"id":key,"created_at_utc":(NOW-timedelta(hours=73)).isoformat(),
               "evidence":evidence,"issue_number":42,"issue_url":ISSUE,
               "delivered_at_utc":NOW.isoformat()}
        write_if_changed(self.root/"data/outbox.json",{"pending":[],"delivered":[row]})
        self.assertEqual(build_feed(self.root,NOW)["candidate_count"],0)

    def test_bad_payload_hash_is_not_forwarded(self):
        row = {"id":"tampered","created_at_utc":NOW.isoformat(),"evidence":{"reasons":["false"]}}
        write_if_changed(self.root/"data/outbox.json",{"pending":[row],"delivered":[]})
        self.assertEqual(build_feed(self.root,NOW)["candidate_count"],0)

    def test_pending_and_receipt_dedup_same_identity(self):
        evidence={"reasons":["test"]}
        row={"id":fingerprint(evidence)[:20],"created_at_utc":NOW.isoformat(),"evidence":evidence}
        received={**row,"issue_url":ISSUE,"issue_number":42,"delivered_at_utc":NOW.isoformat()}
        write_if_changed(self.root/"data/outbox.json",{"pending":[row],"delivered":[received]})
        feed=build_feed(self.root,NOW)
        self.assertEqual(feed["candidate_count"],1)
        self.assertEqual(feed["candidates"][0]["github_issue_status"],"acknowledged")

    def test_shared_transition_retains_active_state_under_low_coverage(self):
        before=decide(pair(),{}, {}, [], DAY)["next_state"]
        live=decide({},before,{},[],DAY)
        self.assertEqual(advance_state(before,live,False),before)
        # Newly observed normal values can resolve a channel even during an outage.
        next_day=DAY+timedelta(days=1)
        rows={"VIXCLS":ob("VIXCLS",next_day.isoformat(),20)}
        outcome=decide(rows,before,{},[],next_day)
        state=advance_state(before,outcome,False)
        self.assertEqual(state["active_confirmation_families"],["credit"])
        self.assertEqual(state["critical_families"],before["critical_families"])

    def test_replay_late_third_channel_respects_release_time(self):
        def row(code,day,value,released):
            return {"series":code,"observation_date":day,"value":value,
                    "source_url":"https://fred.stlouisfed.org/series/"+code,
                    "first_available_at_utc":released}
        features=[row(code,day,val,"2026-10-29T09:00:00Z")
                  for day in ("2026-10-27","2026-10-28")
                  for code,val in (("VIXCLS",40),("BAMLH0A0HYM2",7))]
        features += [row(code,"2026-10-27",val,"2026-10-29T10:00:00Z")
                     for code,val in (("SOFR",4.1),("TGCR",3.8))]
        result=replay(features,[{"decision_at_utc":"2026-10-29T"+x+"Z"}
                                for x in ("09:30:00","10:30:00","11:30:00")],[])
        self.assertEqual(result["alerts"],2)
        self.assertEqual(result["alerts_detail"][1]["newly_confirmed_families"],["funding"])

    def test_failed_issue_channel_not_certified_by_healthy_feed(self):
        r=receipt({},now=NOW,event="schedule",run_id="123",run_attempt="1",
                  results={"collect":"success","persist":"success","bridge":"success","delivery":"failure"},
                  health="healthy",evidence_sha="abc")
        self.assertTrue(r["evidence_stages_completed"])
        self.assertFalse(r["full_poll_completed"])
        self.assertIsNone(r["last_successful_scheduled_poll_utc"])
        self.assertFalse(r["authorizes_notification"])

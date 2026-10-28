"""Adversarial integration tests: missing sources, outbox replay, as-published histories."""
from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from fcews.backtest import as_published, replay, utc
from fcews.cli import read_json, run
from fcews.collect import (
    collect_all, parse_fred_csv, parse_fred_json, parse_nyfed_json, parse_ofr_csv,
)
from fcews.core import Observation
from fcews.delivery import deliver_candidates, reconcile_health


def ob(code, val, day="2026-10-28"):
    return Observation(code, day, val, "https://official.example/" + code, "2026-10-29T01:00:00Z")


class CollectorTests(unittest.TestCase):
    def test_fred_json_descending_order_and_missing(self):
        data = {"observations": [
            {"date": "2026-10-28", "value": "."},
            {"date": "2026-10-27", "value": "4.92"},
        ]}
        got = parse_fred_json("DGS10", json.dumps(data), "now")
        self.assertEqual((got.date, got.value), ("2026-10-27", 4.92))

    def test_nyfed_official_schema(self):
        sample = {"refRates": [
            {"effectiveDate": "2026-10-28", "percentRate": 3.92, "type": "SOFR"}
        ]}
        got = parse_nyfed_json("SOFR", json.dumps(sample), "now")
        self.assertEqual(got.value, 3.92)

    def test_nyfed_empty_rejected(self):
        with self.assertRaises(ValueError):
            parse_nyfed_json("SOFR", '{"refRates":[]}', "now")

    def test_ofr_header_and_latest_order(self):
        sample = "Date,OFR FSI,Credit\n2026-10-27,-1.2,0\n2026-10-28,-1.0,0\n"
        got = parse_ofr_csv(sample, "now")
        self.assertEqual((got.date, got.value), ("2026-10-28", -1.0))

    def test_ofr_schema_drift_explicit_error(self):
        with self.assertRaises(ValueError):
            parse_ofr_csv("date,NOT_FSI\n2026-10-28,0.5\n", "now")

    def test_fred_csv_rejects_html_instead_of_values(self):
        with self.assertRaises(ValueError):
            parse_fred_csv("VIXCLS", "<html>Cloudflare</html>", "now")

    def test_all_fred_down_nyfed_still_observed(self):
        def fake_fred(*args):
            raise TimeoutError("FRED unavailable")
        def fake_nyfed(series, timeout):
            return ob(series, 3.9)
        with patch("fcews.collect.fetch_fred", fake_fred), patch(
            "fcews.collect.fetch_nyfed", fake_nyfed
        ), patch("fcews.collect.fetch_ofr", lambda timeout: ob("OFR_FSI", -1)):
            rows, errors = collect_all(0.1)
        self.assertEqual(rows["SOFR"].value, 3.9)
        self.assertEqual(rows["OFR_FSI"].value, -1)
        self.assertEqual(len([k for k in errors if k.startswith("FRED:")]), 9)


class MonitorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "data").mkdir()
        self.now = datetime(2026, 10, 29, 1, 0, tzinfo=timezone.utc)

    def test_all_sources_down_is_degraded_not_green(self):
        result = run(self.root, lambda: ({}, {"FRED:SOFR": "TimeoutError: blocked"}), self.now)
        self.assertEqual(result["status"], "degraded")
        self.assertEqual(result["severity"], "unknown")
        self.assertFalse((self.root / "data/state.json").exists())
        self.assertEqual(read_json(self.root / "data/health.json", {})["missing_required_families"],
                         ["credit", "funding", "system", "volatility"])

    def test_two_families_stress_alert_once_and_cached(self):
        rows = {
            "VIXCLS": ob("VIXCLS", 39),
            "BAMLH0A0HYM2": ob("BAMLH0A0HYM2", 7),
        }
        first = run(self.root, lambda: (rows, {}), self.now)
        self.assertTrue(first["alert_candidate"])
        self.assertEqual(first["status"], "degraded")
        outbox = read_json(self.root / "data/outbox.json", {})
        self.assertEqual(len(outbox["pending"]), 1)
        second = run(self.root, lambda: ({}, {"FRED:VIXCLS": "TimeoutError: blocked"}), self.now)
        self.assertFalse(second["alert_candidate"])
        self.assertEqual(len(read_json(self.root / "data/outbox.json", {})["pending"]), 1)
        self.assertEqual(second["families"], ["credit", "volatility"])

    def test_identical_hourly_poll_preserves_original_retrieval_and_vintage(self):
        rows = {"STLFSI4": ob("STLFSI4", -0.5), "VIXCLS": ob("VIXCLS", 18),
                "BAMLH0A0HYM2": ob("BAMLH0A0HYM2", 3)}
        first = run(self.root, lambda: (rows, {}), self.now)
        baseline = (self.root / "data/observations.json").read_bytes()
        vintage = (self.root / "data/vintage_log.jsonl").read_bytes()
        reretrieved = {code: Observation(code, v.date, v.value, v.source,
                                        "2026-10-29T02:00:00Z") for code, v in rows.items()}
        second = run(self.root, lambda: (reretrieved, {}), self.now)
        self.assertFalse(second["alert_candidate"])
        self.assertEqual(baseline, (self.root / "data/observations.json").read_bytes())
        self.assertEqual(vintage, (self.root / "data/vintage_log.jsonl").read_bytes())
        self.assertEqual(first["evidence_sha256"], second["evidence_sha256"])

    def test_same_date_revision_is_logged(self):
        original = {"STLFSI4": ob("STLFSI4", -0.5)}
        run(self.root, lambda: (original, {}), self.now)
        updated = {"STLFSI4": ob("STLFSI4", -0.3)}
        run(self.root, lambda: (updated, {}), self.now)
        log = (self.root / "data/vintage_log.jsonl").read_text()
        self.assertIn('"previous_value": -0.5', log)
        self.assertEqual(read_json(self.root / "data/observations.json", {})["STLFSI4"]["value"], -0.3)

    def test_degraded_fetch_cannot_clear_previous_stress_regime(self):
        rows = {"VIXCLS": ob("VIXCLS", 39), "BAMLH0A0HYM2": ob("BAMLH0A0HYM2", 7)}
        run(self.root, lambda: (rows, {}), self.now)
        # Simulate unavailable sources by starting next poll beyond both source TTLs.
        late = datetime(2026, 11, 10, 1, 0, tzinfo=timezone.utc)
        r = run(self.root, lambda: ({}, {"FRED:VIXCLS": "TimeoutError: offline"}), late)
        self.assertEqual(r["status"], "degraded")
        self.assertEqual(read_json(self.root / "data/state.json", {})["critical_families"],
                         ["credit", "volatility"])

    def test_cache_stale_does_not_falsely_suggest_calm(self):
        rows = {
            "STLFSI4": ob("STLFSI4", -0.5, "2026-09-01"),
            "VIXCLS": ob("VIXCLS", 16, "2026-09-01"),
        }
        output = run(self.root, lambda: (rows, {}), self.now)
        self.assertEqual(output["status"], "degraded")
        self.assertEqual(output["families"], [])

    def test_three_fresh_independent_families_healthy(self):
        rows = {"STLFSI4": ob("STLFSI4", -0.5), "VIXCLS": ob("VIXCLS", 18),
                "BAMLH0A0HYM2": ob("BAMLH0A0HYM2", 3)}
        r = run(self.root, lambda: (rows, {}), self.now)
        self.assertEqual(r["status"], "healthy")
        self.assertEqual(r["severity"], "green")


class FakeClient:
    def __init__(self):
        self.records = {}
        self.next_id = 1
        self.error_after_post = False

    def issues(self):
        return list(self.records.values())

    def find_body_fingerprint(self, key):
        return next((r for r in self.issues() if "FCEWS-FP:" + key in (r.get("body") or "")), None)

    def create(self, title, body):
        i = self.next_id
        self.next_id += 1
        record = {"number": i, "state": "open", "html_url": "https://github.com/example/issues/" + str(i),
                  "title": title, "body": body}
        self.records[i] = record
        if self.error_after_post:
            self.error_after_post = False
            raise TimeoutError("response lost after GitHub accepted issue")
        return record

    def get(self, n):
        return self.records[n]

    def patch(self, n, changes):
        self.records[n].update(changes)
        return self.records[n]


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "data").mkdir()
        self.outbox = {"pending": [{
            "id": "abc123", "title": "FCEWS CANDIDATE abc123",
            "body": "Source dated evidence.\n<!-- FCEWS-FP:abc123 -->",
        }], "delivered": []}
        (self.root / "data/outbox.json").write_text(json.dumps(self.outbox), encoding="utf-8")
        self.client = FakeClient()

    def test_delivery_readback_and_receipt(self):
        self.assertEqual(deliver_candidates(self.root, self.client), 1)
        self.assertEqual(deliver_candidates(self.root, self.client), 0)
        saved = read_json(self.root / "data/outbox.json", {})
        self.assertEqual(len(saved["pending"]), 0)
        self.assertEqual(len(self.client.records), 1)

    def test_response_lost_after_create_replays_without_duplicate_issue(self):
        self.client.error_after_post = True
        with self.assertRaises(TimeoutError):
            deliver_candidates(self.root, self.client)
        self.assertEqual(len(self.client.records), 1)
        self.assertEqual(deliver_candidates(self.root, self.client), 1)
        self.assertEqual(len(self.client.records), 1)

    def test_health_issue_dedup_and_recovery(self):
        (self.root / "data/health.json").write_text(json.dumps({"status": "degraded"}), encoding="utf-8")
        self.assertEqual(reconcile_health(self.root, self.client), "opened")
        self.assertEqual(reconcile_health(self.root, self.client), "already_open")
        self.assertEqual(len(self.client.records), 1)
        (self.root / "data/health.json").write_text(json.dumps({"status": "healthy"}), encoding="utf-8")
        self.assertEqual(reconcile_health(self.root, self.client), "recovered")
        self.assertEqual(next(iter(self.client.records.values()))["state"], "closed")


class HistoricalTests(unittest.TestCase):
    def test_as_published_reject_future_revisions(self):
        features = [
            {"series": "VIXCLS", "observation_date": "2026-10-27", "first_available_at_utc": "2026-10-28T14:00:00Z",
             "value": "20", "source_url": "https://fred.stlouisfed.org/"},
            {"series": "VIXCLS", "observation_date": "2026-10-27", "first_available_at_utc": "2026-10-30T14:00:00Z",
             "value": "55", "source_url": "https://fred.stlouisfed.org/"},
        ]
        self.assertEqual(as_published(features, utc("2026-10-29T00:00:00Z"))["VIXCLS"].value, 20)
        self.assertEqual(as_published(features, utc("2026-10-31T00:00:00Z"))["VIXCLS"].value, 55)

    def test_before_first_publication_has_no_data(self):
        features = [{"series": "VIXCLS", "observation_date": "2026-10-28",
                     "first_available_at_utc": "2026-10-29T10:00:00Z", "value": 40,
                     "source_url": "https://fred.stlouisfed.org/"}]
        self.assertEqual(as_published(features, utc("2026-10-28T23:00:00Z")), {})

    def test_naive_timestamp_rejected(self):
        with self.assertRaises(ValueError):
            utc("2026-10-28T23:00:00")

    def test_no_peeking_and_no_fictitious_alert(self):
        features = [
            {"series": code, "observation_date": "2026-10-28",
             "first_available_at_utc": "2026-10-29T10:00:00Z",
             "value": value, "source_url": "https://fred.stlouisfed.org/"}
            for code, value in [("VIXCLS", 45), ("BAMLH0A0HYM2", 8)]
        ]
        summary = replay(features, [{"decision_at_utc": "2026-10-28T12:00:00Z"}],
                         [{"event_id": "synthetic", "crisis_start_utc": "2026-10-28T23:00:00Z"}])
        self.assertEqual(summary["alerts"], 0)
        self.assertEqual(summary["missed_event_ids"], ["synthetic"])


if __name__ == "__main__":
    unittest.main()

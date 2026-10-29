"""Hostile source claims cannot become systemic-risk alerts without document integrity."""
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from fcews.events import inspect_event, trusted_url, verify_events
from fcews.cli import run, read_json


NOW = datetime(2026, 10, 29, 1, 0, tzinfo=timezone.utc)
DOCUMENT = b"OFFICIAL DOCUMENT: supervised institution entering resolution on 2026-10-28"

def valid():
    return {
        "id": "fdic-case-001", "category": "bank",
        "primary_source_url": "https://www.fdic.gov/news/press-releases/2026/test-document",
        "source_sha256": hashlib.sha256(DOCUMENT).hexdigest(),
        "verified": True, "review_status": "approved", "verified_by": "reviewer-1",
        "published_at_utc": "2026-10-28T15:00:00Z",
        "verified_at_utc": "2026-10-28T20:00:00Z",
        "cross_market_mechanism": "Test hypothetical transmission via repo collateral haircuts.",
    }

class EventProvenanceAdversarialTests(unittest.TestCase):
    def test_known_primary_sources_only(self):
        self.assertTrue(trusted_url("https://www.fdic.gov/news/"))
        self.assertTrue(trusted_url("https://financialresearch.gov/financial-stress-index/"))
        for url in [
            "http://www.fdic.gov/news", "https://www.fdic.gov.evil.test/a",
            "https://fdic.gov@evil.test/a", "https://localhost/a",
            "https://127.0.0.1/a", "https://www.fdic.gov:8080/a",
            "https://www.fdic.gov/a#hidden",
        ]:
            with self.subTest(url=url):
                self.assertFalse(trusted_url(url))

    def test_valid_document_hash_and_reviewer(self):
        got = inspect_event(valid(), NOW, reader=lambda url: DOCUMENT)
        self.assertEqual(got["id"], "fdic-case-001")

    def test_changed_document_must_not_alert(self):
        with self.assertRaisesRegex(ValueError, "SHA256"):
            inspect_event(valid(), NOW, reader=lambda url: b"changed official publication")

    def test_html_claim_from_other_host_cannot_pass(self):
        event = valid()
        event["primary_source_url"] = "https://www.fdic.gov.evil.test/article"
        called = []
        def fake_reader(url):
            called.append(url)
            return DOCUMENT
        with self.assertRaisesRegex(ValueError, "primary-source"):
            inspect_event(event, NOW, reader=fake_reader)
        self.assertFalse(called)

    def test_false_approval_or_missing_reviewer(self):
        event = valid()
        event["verified"] = False
        with self.assertRaisesRegex(ValueError, "human-approved"):
            inspect_event(event, NOW, reader=lambda url: DOCUMENT)
        event = valid()
        event["verified_by"] = ""
        with self.assertRaisesRegex(ValueError, "reviewer"):
            inspect_event(event, NOW, reader=lambda url: DOCUMENT)

    def test_future_publication_rejected(self):
        event = valid()
        event["published_at_utc"] = "2026-10-30T00:00:00Z"
        with self.assertRaises(ValueError):
            inspect_event(event, NOW, reader=lambda url: DOCUMENT)

    def test_unapproved_claim_not_fetched(self):
        event = valid()
        event["review_status"] = "pending"
        called = []
        accepted, failures = verify_events([event], NOW, reader=lambda url: called.append(url))
        self.assertEqual((accepted, failures, called), ([], {}, []))

    def test_failed_source_integrity_not_forwarded_to_risk_engine(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data").mkdir()
            (root / "data/events.json").write_text(json.dumps([valid()]))
            with patch("fcews.events.retrieve_document", lambda url: b"not original"):
                # Inject a rejected source-check result, so even with 'verified': true
                # the engine cannot consume this forged record.
                with patch("fcews.cli.verify_events", return_value=([], {"fdic-case-001": "checksum mismatch"})):
                    result = run(root, collector=lambda: ({}, {}), now=NOW)
            self.assertFalse(result["alert_candidate"])
            self.assertEqual(read_json(root/"data/health.json", {})["reviewed_event_count"], 0)

if __name__ == "__main__":
    unittest.main()

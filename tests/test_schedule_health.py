"""Counterexamples for GitHub's best-effort cron cadence."""
import json
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit
from fcews.schedule_health import PAGE_SIZE, fetch_runs

from fcews.schedule_health import evaluate


class ScheduleHealthTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 6, 12, 0, tzinfo=timezone.utc)

    def run_at(self, minutes_ago, event="schedule", conclusion="success", attempt=1):
        when = self.now-timedelta(minutes=minutes_ago)
        return {"created_at": when.isoformat(), "event": event, "conclusion": conclusion, "run_attempt": attempt}

    def test_normal_hourly_cron_within_grace(self):
        runs = [self.run_at(i*60) for i in range(25)]
        result = evaluate(runs, self.now)
        self.assertEqual(result["status"], "on_time")
        self.assertEqual(result["successful_runs_in_window"], 25)
        self.assertEqual(result["max_observed_gap_minutes"], 60)

    def test_missing_scheduled_runs_are_not_hidden_by_latest_success(self):
        runs = [self.run_at(5), self.run_at(365), self.run_at(725),
                self.run_at(1085), self.run_at(1440)]
        result = evaluate(runs, self.now)
        self.assertEqual(result["status"], "late")
        self.assertGreaterEqual(result["max_observed_gap_minutes"], 360)
        self.assertTrue(result["monitoring_not_financial_crisis"])

    def test_push_runs_do_not_count_as_hourly_schedule(self):
        runs = [self.run_at(5, event="push"), self.run_at(130)]
        result = evaluate(runs, self.now)
        self.assertEqual(result["successful_runs_in_window"], 1)
        self.assertEqual(result["status"], "late")

    def test_failed_scheduled_run_does_not_certify_healthy_polling(self):
        runs = [self.run_at(i*60, conclusion="failure") for i in range(25)]
        result = evaluate(runs, self.now)
        self.assertIsNone(result["last_successful_run_utc"])
        self.assertEqual(result["status"], "late")

    def test_retry_and_unknown_attempt_never_certify_first_attempt(self):
        runs=[self.run_at(1,attempt=2),self.run_at(2,attempt=None),self.run_at(240)]
        result=evaluate(runs,self.now)
        self.assertEqual(result["successful_runs_in_window"],1)
        self.assertEqual(result["status"],"late")

    def test_timezone_naive_clock_rejected(self):
        with self.assertRaises(ValueError):
            evaluate([], datetime(2026, 11, 6, 12, 0))

    def test_paged_api_reads_all_records_without_truncation(self):
        class Response:
            def __init__(self, data): self.data=data
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def read(self,n): return self.data[:n]
        records=[dict(self.run_at(i*30),repository={"metadata":"X"*12000}) for i in range(45)]
        pages=[]
        def fake(request,timeout):
            q=parse_qs(urlsplit(request.full_url).query)
            self.assertEqual(q["created"],["2026-11-05..2026-11-06"])
            self.assertEqual(q["event"],["schedule"])
            self.assertEqual(q["per_page"],[str(PAGE_SIZE)])
            page=int(q["page"][0]); pages.append(page)
            return Response(json.dumps({"workflow_runs":records[(page-1)*PAGE_SIZE:page*PAGE_SIZE]}).encode())
        with patch("fcews.schedule_health.urlopen",side_effect=fake):
            result=fetch_runs("lican1213/financial-crisis-early-warning","token",self.now)
        self.assertEqual(len(result),45)
        self.assertEqual(pages,[1,2,3])

    def test_unreadable_api_response_cannot_certify_healthy(self):
        class Response:
            def __init__(self, data): self.data=data
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def read(self,n): return self.data[:n]
        for body in (b'{"workflow_runs":['+b' '*1_000_100,b'{"workflow_runs": broken}'):
            with self.subTest(size=len(body)):
                with patch("fcews.schedule_health.urlopen",return_value=Response(body)):
                    with self.assertRaises((ValueError,json.JSONDecodeError)):
                        fetch_runs("lican1213/financial-crisis-early-warning","token",self.now)

    def test_pagination_limit_is_failure_not_success(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def read(self,n):
                return json.dumps({"workflow_runs":[{"created_at":"2026-11-06T11:00:00Z"}]*PAGE_SIZE}).encode()[:n]
        with patch("fcews.schedule_health.urlopen",return_value=Response()):
            with self.assertRaisesRegex(ValueError,"pagination exceeded"):
                fetch_runs("lican1213/financial-crisis-early-warning","token",self.now)

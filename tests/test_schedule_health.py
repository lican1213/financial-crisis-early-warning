"""Counterexamples for GitHub's best-effort cron cadence."""
import unittest
from datetime import datetime, timedelta, timezone

from fcews.schedule_health import evaluate


class ScheduleHealthTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 6, 12, 0, tzinfo=timezone.utc)

    def run_at(self, minutes_ago, event="schedule", conclusion="success"):
        when = self.now-timedelta(minutes=minutes_ago)
        return {"created_at": when.isoformat(), "event": event, "conclusion": conclusion}

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

    def test_timezone_naive_clock_rejected(self):
        with self.assertRaises(ValueError):
            evaluate([], datetime(2026, 11, 6, 12, 0))

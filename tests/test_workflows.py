"""Workflow guard: production polling must not write data into feature branches."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class WorkflowSafetyTests(unittest.TestCase):
    def test_production_monitor_only_runs_on_main(self):
        content = (ROOT / ".github/workflows/check.yml").read_text(encoding="utf-8")
        self.assertIn("  push:\n    branches:\n      - main\n", content)
        self.assertIn("  monitor:\n    if: github.ref == 'refs/heads/main'\n", content)
        self.assertIn("git add -A data", content)  # A branch restriction guards a real write step.

    def test_research_workflow_never_posts_crisis_or_runs_on_feature_branch(self):
        content = (ROOT / ".github/workflows/research.yml").read_text(encoding="utf-8")
        self.assertIn("  official-research:\n    if: github.ref == 'refs/heads/main'", content)
        self.assertIn("branches: [main]", content)
        self.assertIn("continue-on-error: true", content)
        self.assertNotIn("fcews.delivery", content)
        self.assertNotIn("fcews.bridge", content)

    def test_dual_hourly_slots_are_only_best_effort(self):
        content = (ROOT / ".github/workflows/check.yml").read_text(encoding="utf-8")
        self.assertIn("cron: '13 * * * *'", content)
        self.assertIn("cron: '43 * * * *'", content)
        self.assertIn("git pull --rebase origin main", content)

    def test_paused_sunday_report_absent_from_active_cadence(self):
        content = (ROOT / "docs/operations/CADENCE.md").read_text(encoding="utf-8")
        self.assertIn("Paused ChatGPT", content)
        self.assertNotIn("| Sunday | **10:00** | Existing ChatGPT", content)

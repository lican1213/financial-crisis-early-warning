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
        # Bridge is allowed only to publish a read-only freshness snapshot.
        # It does not deliver an Issue or user-facing crisis notification.
        self.assertIn("PYTHONPATH=src python -m fcews.bridge", content)
        self.assertIn("git add data/chatgpt_feed.json", content)
        self.assertIn("git pull --ff-only origin main", content)
        self.assertLess(
            content.index("git add data/nbs_pmi_context.json"),
            content.index("PYTHONPATH=src python -m fcews.bridge"),
        )
        self.assertLess(
            content.index("PYTHONPATH=src python -m fcews.bridge"),
            content.index("git add data/chatgpt_feed.json"),
        )
        self.assertIn("id: property", content)
        self.assertIn("id: staffing", content)
        self.assertIn("if: always()", content)
        self.assertIn("steps.property.outcome == 'failure'", content)
        self.assertIn("steps.staffing.outcome == 'failure'", content)
        self.assertLess(content.index("git add data/staffing_ir_context.json"),
                        content.index("PYTHONPATH=src python -m fcews.bridge"))

    def test_dual_hourly_slots_are_only_best_effort(self):
        content = (ROOT / ".github/workflows/check.yml").read_text(encoding="utf-8")
        self.assertIn("cron: '13 * * * *'", content)
        self.assertIn("cron: '43 * * * *'", content)
        self.assertIn("git pull --rebase origin main", content)

    def test_standalone_sunday_task_stays_paused_but_hourly_task_has_research_branch(self):
        content = (ROOT / "docs/operations/CADENCE.md").read_text(encoding="utf-8")
        self.assertIn("Paused ChatGPT", content)
        self.assertIn("Sunday **10:00 Beijing time**", content)
        self.assertNotIn("| Sunday | **10:00** | Existing ChatGPT", content)

    def test_cboe_context_covers_friday_us_close_without_feature_branch_writes(self):
        content = (ROOT / ".github/workflows/volatility.yml").read_text(encoding="utf-8")
        # The existing 08:45 Beijing cadence runs five times weekly, after each US session.
        self.assertIn("cron: '45 0 * * 2-6'", content)
        self.assertNotIn("cron: '45 0 * * 1-5'", content)
        self.assertIn("  push:\n    branches: [main]\n", content)
        self.assertIn("  volatility:\n    if: github.ref == 'refs/heads/main'", content)
        self.assertNotIn("fcews.delivery", content)

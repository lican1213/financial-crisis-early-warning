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

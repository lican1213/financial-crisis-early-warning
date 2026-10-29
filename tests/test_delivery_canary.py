"""Non-crisis GitHub integration canary: exact-once issue and confirmed close."""
import unittest

from fcews.delivery import canary


class SimulatedGitHub:
    def __init__(self):
        self.issues = {}
        self.calls = 0

    def find_body_fingerprint(self, key):
        marker = "FCEWS-FP:" + key
        return next((a for a in self.issues.values() if marker in a.get("body", "")), None)

    def create(self, title, body):
        self.calls += 1
        item = {"number": self.calls, "title": title, "body": body, "state": "open",
                "html_url": "https://github.com/org/repo/issues/" + str(self.calls)}
        self.issues[self.calls] = item
        return item

    def get(self, n):
        return self.issues[n]

    def patch(self, n, body):
        self.issues[n].update(body)
        return self.issues[n]


class DeliveryCanaryTests(unittest.TestCase):
    def test_realistic_issue_readback_close_and_repeat(self):
        gh = SimulatedGitHub()
        first = canary(gh, "abcdef1234567890")
        again = canary(gh, "abcdef1234567890")
        self.assertEqual(first, again)
        self.assertEqual(gh.calls, 1)
        self.assertEqual(gh.issues[1]["state"], "closed")
        self.assertFalse(first["crisis_notification"])

    def test_missing_readback_does_not_claim_success(self):
        gh = SimulatedGitHub()
        gh.get = lambda n: {"number": n, "body": "", "state": "open"}
        with self.assertRaisesRegex(RuntimeError, "readback"):
            canary(gh, "abc")

if __name__ == "__main__":
    unittest.main()

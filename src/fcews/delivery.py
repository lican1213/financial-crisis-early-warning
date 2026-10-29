"""Idempotent candidate delivery and data-health incidents over authenticated GitHub REST."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

from .cli import ROOT, read_json, write_if_changed

HEALTH_TITLE = "FCEWS DATA-HEALTH: official market-data coverage degraded"


class GitHubClient:
    def __init__(self, repo: str, token: str):
        if not repo or "/" not in repo or not token:
            raise ValueError("GITHUB_REPOSITORY and GITHUB_TOKEN must be present")
        self.prefix = "https://api.github.com/repos/" + quote(repo, safe="/")

        self.token = token

    def request(self, method: str, path: str, body=None):
        encoded = json.dumps(body).encode("utf-8") if body is not None else None
        req = Request(
            self.prefix + path, method=method, data=encoded,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": "Bearer " + self.token,
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "FCEWS/0.3",
            },
        )
        with urlopen(req, timeout=12) as response:
            return json.loads(response.read(1_000_000))

    def issues(self):
        # GitHub issue listings include pull requests. Ignore those records.
        for page in range(1, 11):
            records = self.request("GET", f"/issues?state=all&per_page=100&page={page}")
            if not isinstance(records, list):
                raise ValueError("invalid GitHub issues listing")
            for record in records:
                if "pull_request" not in record:
                    yield record
            if len(records) < 100:
                break

    def find_body_fingerprint(self, key: str):
        marker = "FCEWS-FP:" + key
        return next((r for r in self.issues() if marker in (r.get("body") or "")), None)

    def create(self, title: str, body: str):
        return self.request("POST", "/issues", {"title": title, "body": body})

    def patch(self, number: int, body: dict):
        return self.request("PATCH", f"/issues/{number}", body)

    def get(self, number: int):
        return self.request("GET", f"/issues/{number}")


def deliver_candidates(root: Path, client: GitHubClient) -> int:
    outbox_path = root / "data/outbox.json"
    outbox = read_json(outbox_path, {"pending": [], "delivered": []})
    count = 0
    for candidate in list(outbox.get("pending", [])):
        key = candidate["id"]
        existing = client.find_body_fingerprint(key)
        if existing is not None:
            issue = existing
        else:
            issue = client.create(candidate["title"], candidate["body"])
        confirmed = client.get(int(issue["number"]))
        if "FCEWS-FP:" + key not in (confirmed.get("body") or ""):
            raise RuntimeError("GitHub issue readback failed; leave item pending")
        if any(item["id"] == key for item in outbox.get("delivered", [])):
            outbox["pending"] = [p for p in outbox["pending"] if p["id"] != key]
            continue
        outbox.setdefault("delivered", []).append({
            "id": key, "issue_number": int(confirmed["number"]),
            "issue_url": confirmed["html_url"],
            "delivered_at_utc": datetime.now(timezone.utc).isoformat(),
        })
        outbox["pending"] = [p for p in outbox["pending"] if p["id"] != key]
        write_if_changed(outbox_path, outbox)
        count += 1
    return count


def reconcile_health(root: Path, client: GitHubClient) -> str:
    health = read_json(root / "data/health.json", {})
    status = health.get("status", "degraded")
    matching = [r for r in client.issues() if r.get("title") == HEALTH_TITLE and r.get("state") == "open"]
    if status == "degraded":
        if matching:
            return "already_open"
        details = json.dumps(health, indent=2, sort_keys=True)
        client.create(HEALTH_TITLE,
                      "No valid source-family coverage. This is a **monitoring failure**, "
                      "not a confirmed market crisis.\n\n"
                      "Source diagnostics:\n\n\`\`\`json\n" + details + "\n\`\`\`\n\n"
                      "Review the latest Actions job and official feeds; do not infer market calm.")
        return "opened"
    if status in ("healthy", "partial"):
        for issue in matching:
            client.patch(issue["number"], {
                "state": "closed",
                "state_reason": "completed",
            })
        return "recovered" if matching else "not_applicable"
    return "unrecognized_health"


def run(root: Path, client: GitHubClient) -> dict:
    delivered = deliver_candidates(root, client)
    health = reconcile_health(root, client)
    return {"candidate_issues_confirmed": delivered, "health_issue": health}


def canary(client: GitHubClient, token: str) -> dict:
    """Real GitHub Issues create/read/close test; never a crisis warning."""
    key = "CANARY-" + token[:20].replace("/", "-")
    marker = "FCEWS-FP:" + key
    title = "FCEWS INTEGRATION-CANARY: delivery permissions test (not a crisis)"
    body = ("This is a controlled delivery/API readback test, NOT a market risk alert.\n"
            "<!-- " + marker + " -->\n")
    issue = client.find_body_fingerprint(key)
    if issue is None:
        issue = client.create(title, body)
    number = int(issue["number"])
    readback = client.get(number)
    if marker not in (readback.get("body") or ""):
        raise RuntimeError("canary issue body did not survive GitHub readback")
    if readback.get("state") != "closed":
        client.patch(number, {"state": "closed", "state_reason": "completed"})
    confirmed = client.get(number)
    if confirmed.get("state") != "closed":
        raise RuntimeError("canary issue did not close")
    return {"status": "verified", "issue_url": confirmed["html_url"],
            "issue_number": number, "crisis_notification": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--canary", action="store_true")
    options = parser.parse_args()
    client = GitHubClient(
        os.getenv("GITHUB_REPOSITORY", ""),
        os.getenv("GITHUB_TOKEN", ""),
    )
    if options.canary:
        outcome = canary(client, os.getenv("GITHUB_SHA", "manual-verified-test"))
    else:
        outcome = run(options.root, client)
    print(json.dumps(outcome, sort_keys=True))


if __name__ == "__main__":
    main()

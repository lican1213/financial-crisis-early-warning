"""Audit GitHub Actions schedule delivery independently of the market-risk gate.

GitHub cron is best-effort. A successful run says nothing about how many
scheduled executions were delayed or dropped between runs.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

WINDOW_HOURS = 24
MAX_GAP_MINUTES = 90  # hourly period plus a 30-minute grace period
PAGE_SIZE = 20  # GitHub includes large nested repository objects in each run.
MAX_PAGES = 8
MAX_RESPONSE_BYTES = 1_000_000


def utc_timestamp(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("GitHub run timestamp lacks timezone")
    return result.astimezone(timezone.utc)


def evaluate(runs: list[dict], now: datetime, window_hours: int = WINDOW_HOURS,
             max_gap_minutes: int = MAX_GAP_MINUTES) -> dict:
    if now.tzinfo is None or window_hours < 1 or max_gap_minutes < 1:
        raise ValueError("invalid schedule audit time or interval")
    now = now.astimezone(timezone.utc)
    start = now - timedelta(hours=window_hours)
    completed = sorted({utc_timestamp(r["created_at"]) for r in runs
                        if r.get("event") == "schedule" and r.get("conclusion") == "success"
                        and r.get("run_attempt") == 1
                        and utc_timestamp(r["created_at"]) <= now})
    current = [point for point in completed if point >= start]
    boundaries = [start, *current, now]
    gaps = [(right-left).total_seconds()/60 for left,right in zip(boundaries,boundaries[1:])]
    overdue = [round(gap, 1) for gap in gaps if gap > max_gap_minutes]
    return {
        "status": "late" if overdue else "on_time",
        "monitoring_not_financial_crisis": True,
        "checked_at_utc": now.isoformat(),
        "window_hours": window_hours,
        "grace_limit_minutes": max_gap_minutes,
        "successful_runs_in_window": len(current),
        "natural_first_attempt_only": True,
        "last_successful_run_utc": completed[-1].isoformat() if completed else None,
        "max_observed_gap_minutes": round(max(gaps), 1),
        "gaps_over_grace_minutes": overdue,
    }


def fetch_runs(repo: str, token: str, now: datetime | None = None) -> list[dict]:
    """Page the UTC 24-hour window; never silently truncate GitHub's JSON."""
    if len(repo.split("/")) != 2 or not all(repo.split("/")):
        raise ValueError("invalid repository name")
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("audit timestamp must be timezone-aware")
    now = now.astimezone(timezone.utc)
    start = now - timedelta(hours=WINDOW_HOURS)
    date_range = start.date().isoformat() + ".." + now.date().isoformat()
    prefix = ("https://api.github.com/repos/" + quote(repo, safe="/")
              + "/actions/workflows/check.yml/runs?event=schedule"
              + "&created=" + date_range + "&per_page=" + str(PAGE_SIZE))
    runs: list[dict] = []
    for page in range(1, MAX_PAGES + 1):
        request = Request(prefix + "&page=" + str(page), headers={
            "Accept": "application/vnd.github+json", "User-Agent": "FCEWS schedule audit",
            "X-GitHub-Api-Version": "2022-11-28",
            **({"Authorization": "Bearer " + token} if token else {}),
        })
        with urlopen(request, timeout=12) as response:
            payload = response.read(MAX_RESPONSE_BYTES + 1)
        if len(payload) > MAX_RESPONSE_BYTES:
            raise ValueError("GitHub schedule page exceeded bounded response size")
        data = json.loads(payload)
        page_runs = data.get("workflow_runs") if isinstance(data, dict) else None
        if not isinstance(page_runs, list) or len(page_runs) > PAGE_SIZE:
            raise ValueError("invalid GitHub workflow run response")
        runs.extend(page_runs)
        if len(page_runs) < PAGE_SIZE:
            return runs
    raise ValueError("GitHub schedule pagination exceeded audit page limit; cadence unverified")


def main() -> None:
    now = datetime.now(timezone.utc)
    result = evaluate(fetch_runs(os.environ["GITHUB_REPOSITORY"],
                                 os.getenv("GITHUB_TOKEN", ""), now), now)
    print(json.dumps(result, sort_keys=True))
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as output:
            output.write("\n### FCEWS hourly GitHub schedule audit (operational only)\n\n")
            output.write(f"- Status: **{result['status']}**; window: {WINDOW_HOURS} h\n")
            output.write(f"- Successful runs: {result['successful_runs_in_window']}\n")
            output.write(f"- Maximum observed gap: {result['max_observed_gap_minutes']} min "
                         f"(limit {MAX_GAP_MINUTES} min)\n")
    if result["status"] == "late":
        print("::warning::Hourly GitHub schedule exceeded its grace period. "
              "This is an operational coverage gap, not a financial-crisis alert.")


if __name__ == "__main__":
    main()

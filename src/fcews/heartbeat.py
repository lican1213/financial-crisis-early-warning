"""Operational poll receipt, separate from evidence fingerprints and market alerts."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from .cli import ROOT, read_json, write_if_changed

SCHEMA = "fcews.poll_heartbeat.v1"


def receipt(previous: dict, *, now: datetime, event: str, run_id: str,
            run_attempt: str, results: dict, health: str, evidence_sha: str | None) -> dict:
    if now.tzinfo is None or not run_id.isdigit() or not run_attempt.isdigit() or int(run_attempt) < 1:
        raise ValueError("invalid poll receipt identity")
    if event not in {"schedule", "push", "workflow_dispatch"}:
        raise ValueError("unexpected poll trigger")
    now = now.astimezone(timezone.utc)
    stamp = now.isoformat()
    successful = (all(results.get(k) == "success" for k in ("collect", "persist", "bridge"))
                  and health in {"healthy", "partial"} and bool(evidence_sha))
    # Issue channel is optional for feed availability but not full operational success.
    delivery_ok = results.get("delivery", "success") == "success"
    completed = successful and delivery_ok
    # A non-scheduled or failed poll cannot move the scheduled-success clock.
    last_poll = previous.get("last_successful_poll_utc")
    last_schedule = (previous.get("last_successful_scheduled_poll_utc")
                     if previous.get("natural_schedule_only") is True else None)
    natural = event == "schedule" and run_attempt == "1"
    if completed:
        last_poll = stamp
        if natural:
            last_schedule = stamp
    return {
        "schema": SCHEMA, "recorded_at_utc": stamp, "trigger": event,
        "run_id": run_id, "run_attempt": run_attempt,
        "natural_schedule_only": True, "natural_schedule_attempt": natural,
        "evidence_stages_completed": successful, "stage_outcomes": results,
        "full_poll_completed": completed,
        "monitor_health": health, "evidence_sha256": evidence_sha,
        "last_successful_poll_utc": last_poll,
        "last_successful_scheduled_poll_utc": last_schedule,
        "operational_only": True, "authorizes_notification": False,
    }


def main(root: Path = ROOT) -> None:
    target = root / "data/poll_heartbeat.json"
    health = read_json(root / "data/health.json", {})
    check = read_json(root / "data/latest_check.json", {})
    previous = read_json(target, {})
    value = receipt(
        previous, now=datetime.now(timezone.utc), event=os.environ["GITHUB_EVENT_NAME"],
        run_id=os.environ["GITHUB_RUN_ID"], run_attempt=os.environ["GITHUB_RUN_ATTEMPT"],
        results={key: os.environ.get("FCEWS_" + key.upper(), "unknown")
                 for key in ("collect", "persist", "bridge", "delivery")},
        health=health.get("status", "unknown"), evidence_sha=check.get("evidence_sha256"),
    )
    write_if_changed(target, value)


if __name__ == "__main__":
    main()

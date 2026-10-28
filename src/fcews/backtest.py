"""Point-in-time replay. Requires a first-public timestamp for every observation."""
from __future__ import annotations

import argparse
import csv
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from .core import Observation, decide


def utc(value: str) -> datetime:
    moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if moment.tzinfo is None:
        raise ValueError("timestamp needs UTC offset: " + value)
    return moment.astimezone(timezone.utc)


def load_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def as_published(rows: list[dict], decision_at: datetime) -> dict[str, Observation]:
    """Select the last revision actually public at decision time; never look ahead."""
    selected: dict[str, tuple[datetime, Observation]] = {}
    for row in rows:
        release = utc(row["first_available_at_utc"])
        period = date.fromisoformat(row["observation_date"])
        if release > decision_at or period > decision_at.date():
            continue
        value = float(row["value"])
        code = row["series"]
        candidate = Observation(
            code, row["observation_date"], value,
            row["source_url"], decision_at.isoformat(),
            release.isoformat(),
        )
        current = selected.get(code)
        score = (period, release)
        if current is None or score > (date.fromisoformat(current[1].date), current[0]):
            selected[code] = (release, candidate)
    return {key: value[1] for key, value in selected.items()}


def replay(features: list[dict], decisions: list[dict], events: list[dict],
           weekly: dict | None = None, pre_event_days: int = 14) -> dict:
    weekly = weekly or {}
    decision_list = sorted((utc(row["decision_at_utc"]) for row in decisions))
    if len(decision_list) != len(set(decision_list)):
        raise ValueError("duplicate decision checkpoints")
    windows = []
    for event in events:
        start = utc(event["crisis_start_utc"])
        windows.append((event["event_id"], start - timedelta(days=pre_event_days),
                        start + timedelta(days=2), start))
    state: dict = {}
    alerts = []
    false_alerts = []
    for point in decision_list:
        observed = as_published(features, point)
        outcome = decide(observed, state, weekly, [], point.date())
        state = outcome["next_state"]
        if outcome["alert"]:
            match = [name for name, left, right, start in windows if left <= point <= right]
            record = {"decision_at_utc": point.isoformat(), "severity": outcome["severity"],
                      "reasons": outcome["reasons"], "matched_events": match}
            alerts.append(record)
            if not match:
                false_alerts.append(record)
    missed = [name for name, left, right, start in windows
              if not any(name in a["matched_events"] for a in alerts)]
    lead_days = {}
    for name, left, right, start in windows:
        earliest = next((utc(a["decision_at_utc"]) for a in alerts if name in a["matched_events"]), None)
        lead_days[name] = round((start - earliest).total_seconds() / 86400, 2) if earliest else None
    n = len(decision_list)
    return {
        "label": "retrospective point-in-time replay (not trained crisis probability)",
        "checkpoints": n, "events": len(windows), "alerts": len(alerts),
        "false_alerts": len(false_alerts),
        "false_alerts_per_100_checks": round(100 * len(false_alerts) / n, 3) if n else None,
        "missed_event_ids": missed, "event_lead_days": lead_days,
        "alerts_detail": alerts,
    }


def main():
    parser = argparse.ArgumentParser(description="Replay explicitly time-stamped, as-published CSV inputs")
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--weekly", type=Path)
    args = parser.parse_args()
    base = json.loads(args.weekly.read_text()) if args.weekly else {}
    print(json.dumps(replay(load_csv(args.features), load_csv(args.decisions),
                            load_csv(args.events), base), indent=2))


if __name__ == "__main__":
    main()

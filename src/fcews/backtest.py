"""Point-in-time replay. Requires a first-public timestamp for every observation."""
from __future__ import annotations

import argparse
import csv
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from .core import DIRECT_CODES, DIRECT_CONFIRMATION_FAMILIES, Observation, advance_state, decide, fresh


def utc(value: str) -> datetime:
    moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if moment.tzinfo is None:
        raise ValueError("timestamp needs UTC offset: " + value)
    return moment.astimezone(timezone.utc)


def load_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def published_snapshots(rows: list[dict], decisions, registry=None):
    """One chronological release stream for replay, benchmarks and coverage."""
    releases = iter(sorted(rows, key=lambda row: utc(row["first_available_at_utc"])))
    pending = next(releases, None)
    selected = {}
    history = {}
    direct_codes = DIRECT_CODES | {code for code, (family, _) in (registry or {}).items()
                                  if family in DIRECT_CONFIRMATION_FAMILIES}
    for point in decisions:
        while pending is not None and utc(pending["first_available_at_utc"]) <= point:
            row, pending = pending, next(releases, None)
            release = utc(row["first_available_at_utc"])
            observed = date.fromisoformat(row["observation_date"])
            if observed > release.date():
                continue  # an observed economic period cannot precede its own date
            code = row["series"]
            ob = Observation(code, observed.isoformat(), float(row["value"]),
                             row["source_url"], point.isoformat(), release.isoformat())
            rank = (ob.date, release)
            if code not in selected or rank > selected[code][0]:
                selected[code] = (rank, ob)
            if code in direct_codes and fresh(ob, point.date()):
                daily = history.setdefault(ob.date, {})
                prior = daily.get(code)
                if prior is None or release > utc(prior.available_at_utc):
                    daily[code] = ob
        history = {day: {code: ob for code, ob in group.items() if fresh(ob, point.date())}
                   for day, group in history.items()}
        history = {day: group for day, group in history.items() if group}
        yield point, {code: pair[1] for code, pair in selected.items()}, history


def published_snapshot(rows: list[dict], decision_at: datetime):
    point, selected, history = next(published_snapshots(rows, [decision_at]))
    return selected, history


def as_published(rows: list[dict], decision_at: datetime) -> dict[str, Observation]:
    return published_snapshot(rows, decision_at)[0]


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
    for point, observed, history in published_snapshots(features, decision_list):
        outcome = decide(observed, state, weekly, [], point.date(), history=history)
        # Replay models as-published availability, not actual historical network outages.
        state = advance_state(state, outcome, len(outcome["present_families"]) >= 3)
        if outcome["alert"]:
            match = [name for name, left, right, start in windows if left <= point <= right]
            record = {"decision_at_utc": point.isoformat(), "severity": outcome["severity"],
                      "reasons": outcome["reasons"], "matched_events": match,
                      "confirmation_matches": outcome["confirmation_matches"],
                      "newly_confirmed_families": outcome["newly_confirmed_families"]}
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

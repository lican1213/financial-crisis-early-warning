"""Chronological indicator-family comparison with explicit provenance category.

A revised historical FRED dump is EX-POST, not a validated predictive backtest.
"""
from __future__ import annotations

import argparse
import json
from datetime import timedelta, datetime
from pathlib import Path

from .backtest import load_csv, published_snapshots, utc
from .core import advance_state, decide
from .coverage import observable_direct_families

PIT_CLASSES = {"publisher_timestamp_verified", "ALFRED_vintage_date_plus_one_UTC_day", "ALFRED_public_asof_plus_one_UTC_day"}


def evaluate(features: list[dict], checkpoints: list[dict], events: list[dict],
             *, mode: str = "pit", window_days: int = 14, registry=None) -> dict:
    if mode not in ("pit", "expost"):
        raise ValueError("mode must be pit or expost")
    if mode == "pit" and any(row.get("availability_basis") not in PIT_CLASSES for row in features):
        raise ValueError("PIT requires a documented original-release availability basis")
    points = sorted(utc(r["decision_at_utc"]) for r in checkpoints)
    if len(set(points)) != len(points):
        raise ValueError("duplicate decision timestamps")
    if not points:
        raise ValueError("empty backtest period")
    # Ex-post mode labels all reported results as revised-history diagnostics.
    event_ranges = []
    for event in events:
        origin = utc(event["crisis_start_utc"])
        left, right = origin - timedelta(days=window_days), origin + timedelta(days=2)
        if left <= points[-1] and right >= points[0]:
            event_ranges.append((event["event_id"], left, right, origin))
    state = {}
    alerted = {"fcews": [], "vix_only": [], "never_alert": []}
    prev_vix_trigger = False
    coverage = []
    direct_coverage = []
    for instant, rows, history in published_snapshots(features, points, registry=registry):
        model = decide(rows, state, {}, [], instant.date(), registry=registry, history=history)
        state = advance_state(state, model, len(model["present_families"]) >= 3)
        coverage.append(len(model["present_families"]))
        direct_coverage.append(len(observable_direct_families(history, instant.date(), registry)))
        if model["alert"]:
            alerted["fcews"].append(instant)
        vix = model["indicators"].get("VIXCLS")
        vix_trigger = bool(vix and vix["critical"])
        if vix_trigger and not prev_vix_trigger:
            alerted["vix_only"].append(instant)
        prev_vix_trigger = vix_trigger

    def score(timestamps: list[datetime]) -> dict:
        unmatched = [t for t in timestamps if not any(left <= t <= right for _, left, right, _ in event_ranges)]
        missed = [name for name, left, right, _ in event_ranges
                  if not any(left <= t <= right for t in timestamps)]
        leads = {}
        for name, left, right, start in event_ranges:
            hits = [t for t in timestamps if left <= t <= right]
            leads[name] = round((start - min(hits)).total_seconds() / 86400, 2) if hits else None
        return {
            "alerts": len(timestamps),
            "unmatched_alerts": len(unmatched),
            "false_alarms_per_100_checkpoints": round(100 * len(unmatched) / len(points), 3),
            "missed_events": missed,
            "lead_days_by_event": leads,
            "silent_share": round(1 - len(timestamps) / len(points), 5),
        }

    output = {
        "mode": mode,
        "label": ("SOURCE-DATED PIT: conservative release-time proxy; check source timestamps"
                  if mode == "pit" else "EX-POST REVISED SERIES: NOT A POINT-IN-TIME PREDICTIVE TEST"),
        "checkpoints": len(points),
        "first_decision_utc": points[0].isoformat(),
        "last_decision_utc": points[-1].isoformat(),
        "crisis_event_count": len(event_ranges),
        "covered_by_three_families_share": round(sum(n >= 3 for n in coverage) / len(coverage), 5),
        "coverage_basis": "legacy diagnostic groups and separately exact-date direct channels",
        "covered_by_two_direct_same_date_share": round(sum(n >= 2 for n in direct_coverage) / len(points), 5),
        "covered_by_three_direct_same_date_share": round(sum(n >= 3 for n in direct_coverage) / len(points), 5),
        "unmatched_alerts_are_not_validated_false_positives": True,
        "strategies": {name: score(timestamps) for name, timestamps in alerted.items()},
    }
    return output


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--features", required=True, type=Path)
    p.add_argument("--decisions", required=True, type=Path)
    p.add_argument("--events", required=True, type=Path)
    p.add_argument("--mode", choices=("pit", "expost"), required=True)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    result = evaluate(load_csv(args.features), load_csv(args.decisions), load_csv(args.events),
                      mode=args.mode)
    rendered = json.dumps(result, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()

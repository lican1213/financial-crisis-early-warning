"""Crisis-window observability audit: never call an unobservable event a model miss.

An event's true detection outcome is interpretable only when a minimum set
of independent indicator families could have been observed *as of the
historical decision timestamp*. The benchmark's raw miss list remains intact;
this audit explicitly separates coverage failures from model false negatives.
"""
from __future__ import annotations

from datetime import timedelta

from .backtest import as_published, utc
from .core import indicators


def audit_event_coverage(features: list[dict], checkpoints: list[dict],
                         events: list[dict], pre_event_days: int = 14) -> dict:
    points = sorted(utc(r["decision_at_utc"]) for r in checkpoints)
    result: dict[str, dict] = {}
    for item in events:
        event_id = str(item["event_id"])
        crisis_start = utc(item["crisis_start_utc"])
        left = crisis_start - timedelta(days=pre_event_days)
        right = crisis_start + timedelta(days=2)
        local = [p for p in points if left <= p <= right]
        coverage = []
        for instant in local:
            available = as_published(features, instant)
            measures = indicators(available, instant.date())
            fam = sorted({metric["family"] for metric in measures.values()})
            coverage.append({
                "decision_at_utc": instant.isoformat(),
                "independent_families": fam,
                "count": len(fam),
            })
        high = sum(v["count"] >= 3 for v in coverage)
        partial = sum(v["count"] >= 2 for v in coverage)
        if high:
            status = "at_least_one_three_family_checkpoint"
        elif partial:
            status = "partial_two_family_only"
        else:
            status = "unassessable_no_two_family_checkpoint"
        result[event_id] = {
            "status": status,
            "pre_event_window_days": pre_event_days,
            "checkpoints_in_window": len(local),
            "checkpoints_with_two_families": partial,
            "checkpoints_with_three_families": high,
            "checkpoints_detail": coverage,
        }
    return result


def classify_misses(reported_misses: list[str], event_audit: dict) -> dict:
    """Separates model misses from missing sufficient contemporaneous coverage."""
    missed, unassessable, partial = [], [], []
    for event_id in reported_misses:
        status = event_audit.get(event_id, {}).get("status", "unassessable")
        if status == "at_least_one_three_family_checkpoint":
            missed.append(event_id)
        elif status == "partial_two_family_only":
            partial.append(event_id)
        else:
            unassessable.append(event_id)
    return {
        "missed_with_three_family_coverage": missed,
        "missed_with_partial_two_family_coverage": partial,
        "unassessable_missing_independent_sources": unassessable,
        "interpretation": "Raw missed-event labels are not necessarily verified model errors when PIT source coverage is inadequate.",
    }

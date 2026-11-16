"""Bounded, observation-date keyed recent direct-source evidence.

Capture only actually fetched values (not interpolations); retrieval is not
original publication time. Live snapshots must not be used as historical PIT.
"""
from datetime import date
from .core import DIRECT_CODES, Observation, fresh


def recent_history(saved: dict, fetched: dict[str, Observation],
                   cached: dict[str, Observation], today: date) -> dict[str, dict[str, Observation]]:
    history = {}

    def add(ob):
        if not isinstance(ob, Observation) or ob.series not in DIRECT_CODES or not fresh(ob, today):
            return
        daily = history.setdefault(ob.date, {})
        prior = daily.get(ob.series)
        if prior is None or (prior.value, prior.source) != (ob.value, ob.source):
            daily[ob.series] = ob

    for day, series in saved.items():
        if not isinstance(series, dict):
            continue
        for code, row in series.items():
            try:
                if row["date"] != day or row["series"] != code:
                    continue
                add(Observation(code, day, float(row["value"]), row["source"],
                                row.get("retrieved_utc", ""), row.get("available_at_utc")))
            except (KeyError, TypeError, ValueError):
                continue
    for ob in cached.values():
        add(ob)
    for ob in fetched.values():
        if isinstance(ob, Observation):
            for recent in ob.recent:
                if recent.series == ob.series:
                    add(recent)
            add(ob)
    return history


def serialize(history):
    return {day: {code: ob.as_dict() for code, ob in sorted(rows.items())}
            for day, rows in sorted(history.items())}

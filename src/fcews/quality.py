"""Source age diagnostics kept separate from crisis-risk classification.

Business-day thresholds are operational grace bounds, not official release
timestamps, crisis thresholds or a replacement for source publication calendars.
"""
from __future__ import annotations

from datetime import date, timedelta

DAILY_CODES = frozenset({"OFR_FSI", "BAMLH0A0HYM2", "VIXCLS", "SOFR", "TGCR",
                         "BGCR", "DGS10", "DGS30"})
WEEKLY_CODES = frozenset({"STLFSI4", "NFCI", "ANFCI"})
DAILY_GRACE_BUSINESS_DAYS = 3
WEEKLY_GRACE_BUSINESS_DAYS = 8


def elapsed_business_days(observed: date, now: date) -> int:
    if observed > now:
        raise ValueError("observation is future dated")
    current = observed + timedelta(days=1)
    count = 0
    while current <= now:
        if current.weekday() < 5:
            count += 1
        current += timedelta(days=1)
    return count


def late_source_dates(rows, now: date) -> dict[str, int]:
    """Flag unusually old official observations for operator review only."""
    late = {}
    for code, observation in rows.items():
        bound = (DAILY_GRACE_BUSINESS_DAYS if code in DAILY_CODES
                 else WEEKLY_GRACE_BUSINESS_DAYS if code in WEEKLY_CODES else None)
        if bound is None:
            continue
        try:
            age = elapsed_business_days(date.fromisoformat(observation.date), now)
            if age > bound:
                late[code] = age
        except (TypeError, ValueError):
            late[code] = -1  # malformed/future date, never interpret as fresh data
    return late

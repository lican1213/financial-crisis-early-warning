"""Pure risk rules. Monitoring coverage is not a claim of crisis prediction."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

# Levels are ordinal only; not calibrated crisis probabilities.
LEVELS = {"unknown": -1, "green": 0, "yellow": 1, "orange": 2, "red": 3}
# Four independent families. Highly correlated readings inside a family count once.
SERIES = {
    "STLFSI4": ("system", 1.0),
    "NFCI": ("system", 1.0),
    "ANFCI": ("system", 1.0),
    "BAMLH0A0HYM2": ("credit", 6.0),  # FRED reports percent: 6.0 = 600 bp.
    "VIXCLS": ("volatility", 30.0),
    "SOFR_TGCR_SPREAD": ("funding", 0.15),  # Percentage points: 0.15 = 15 bp.
}
MAX_AGE_DAYS = {
    "STLFSI4": 15, "NFCI": 15, "ANFCI": 15,
    "BAMLH0A0HYM2": 7, "VIXCLS": 7, "SOFR": 7, "TGCR": 7,
}


@dataclass(frozen=True)
class Observation:
    series: str
    date: str
    value: float
    source: str
    retrieved_utc: str


def fresh(o: Observation | None, now: date) -> bool:
    if o is None or o.series not in MAX_AGE_DAYS:
        return False
    try:
        age = (now - date.fromisoformat(o.date)).days
        return 0 <= age <= MAX_AGE_DAYS[o.series]
    except (TypeError, ValueError):
        return False


def indicators(rows: dict[str, Observation], now: date) -> dict[str, dict[str, Any]]:
    result = {}
    for code, (family, cutoff) in SERIES.items():
        if code == "SOFR_TGCR_SPREAD":
            a, b = rows.get("SOFR"), rows.get("TGCR")
            if not (fresh(a, now) and fresh(b, now) and a.date == b.date):
                continue
            value = round(a.value - b.value, 5)
            day = a.date
        else:
            observation = rows.get(code)
            if not fresh(observation, now):
                continue
            value, day = observation.value, observation.date
        result[code] = {
            "family": family, "date": day, "value": value,
            "threshold": cutoff, "critical": value >= cutoff,
        }
    return result


def decide(
    rows: dict[str, Observation],
    previous: dict[str, Any],
    weekly: dict[str, Any],
    events: list[dict[str, Any]],
    now: date,
) -> dict[str, Any]:
    metrics = indicators(rows, now)
    families = sorted({r["family"] for r in metrics.values()})
    critical = sorted({r["family"] for r in metrics.values() if r["critical"]})

    # Primary-source verification is a HUMAN-REVIEWED input, never inferred from a URL.
    accepted = {
        str(e["id"]) for e in events
        if e.get("id")
        and e.get("verified") is True
        and str(e.get("primary_source_url", "")).startswith("https://")
        and e.get("cross_market_mechanism")
    }
    known = set(previous.get("seen_events", []))
    new_events = sorted(accepted - known)

    if len(critical) >= 3:
        severity = "red"
    elif len(critical) >= 2:
        severity = "orange"
    elif len(critical) == 1:
        severity = "yellow"
    elif len(families) >= 3:
        severity = "green"
    else:
        severity = "unknown"

    weekly_level = weekly.get("severity", "unknown")
    if weekly_level not in LEVELS:
        raise ValueError("Weekly baseline must use one of: " + ", ".join(LEVELS))

    # Never mistake repeated hourly processing of the same published values for
    # three days of recovery. Recovery requires three distinct observation dates.
    evidence_date = max((m["date"] for m in metrics.values()), default="")
    below_weekly = (
        severity != "unknown" and weekly_level != "unknown"
        and LEVELS[severity] < LEVELS[weekly_level] and len(families) >= 3
    )
    prior_count = int(previous.get("recovery_count", 0))
    prior_day = str(previous.get("last_recovery_date", ""))
    if below_weekly and evidence_date > prior_day:
        recovery_count = prior_count + 1
        recovery_date = evidence_date
    elif below_weekly:
        recovery_count, recovery_date = prior_count, prior_day
    else:
        recovery_count, recovery_date = 0, ""

    reasons = []
    # First-run severe evidence must still alert; no silent bootstrap blind spot.
    if len(critical) >= 2 and len(previous.get("critical_families", [])) < 2:
        reasons.append("independent_stress_families")
    if (
        severity != "unknown" and weekly_level != "unknown"
        and len(families) >= 3 and LEVELS[severity] > LEVELS[weekly_level]
        and previous.get("last_alert_severity") != severity
    ):
        reasons.append("above_weekly_baseline")
    if new_events:
        reasons.append("verified_contagion_candidate_event")
    if recovery_count >= 3 and not previous.get("recovery_alerted", False):
        reasons.append("sustained_recovery")

    alert = bool(reasons)
    next_state = {
        "severity": severity,
        "critical_families": critical,
        "seen_events": sorted(known | accepted),
        "recovery_count": recovery_count,
        "last_recovery_date": recovery_date,
        "recovery_alerted": bool(previous.get("recovery_alerted", False) or "sustained_recovery" in reasons) if below_weekly else False,
        "last_alert_severity": severity if alert else previous.get("last_alert_severity"),
    }
    return {
        "date": now.isoformat(), "severity": severity,
        "confidence": "moderate" if len(families) >= 3 else "limited",
        "present_families": families, "critical_families": critical,
        "indicators": metrics, "events": new_events,
        "reasons": reasons, "alert": alert, "next_state": next_state,
    }

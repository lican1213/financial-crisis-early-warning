"""Source-dated financial-stress decisions. Values are provisional rule cutoffs, not probabilities."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from math import isfinite
from typing import Any

LEVELS = {"unknown": -1, "green": 0, "yellow": 1, "orange": 2, "red": 3}
SERIES = {
    "STLFSI4": ("system", 1.0),
    "NFCI": ("system", 1.0),
    "ANFCI": ("system", 1.0),
    "OFR_FSI": ("system", 1.0),
    "BAMLH0A0HYM2": ("credit", 6.0),  # 6% means 600 basis points
    "VIXCLS": ("volatility", 30.0),
    "SOFR_TGCR_SPREAD": ("funding", 0.15),  # 15 basis points
}
MAX_AGE_DAYS = {
    "STLFSI4": 15, "NFCI": 15, "ANFCI": 15, "OFR_FSI": 7,
    "BAMLH0A0HYM2": 7, "VIXCLS": 7, "SOFR": 7, "TGCR": 7,
    "DGS10": 7, "DGS30": 7, "BGCR": 7,
}
CONTEXT_CODES = {"DGS10", "DGS30", "BGCR"}
MAX_FUTURE_SECONDS = 300


@dataclass(frozen=True)
class Observation:
    series: str
    date: str
    value: float
    source: str
    retrieved_utc: str
    available_at_utc: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "series": self.series, "date": self.date, "value": self.value,
            "source": self.source, "retrieved_utc": self.retrieved_utc,
            "available_at_utc": self.available_at_utc,
        }


def fresh(o: Observation | None, now: date) -> bool:
    if o is None or o.series not in MAX_AGE_DAYS:
        return False
    try:
        age = (now - date.fromisoformat(o.date)).days
        return 0 <= age <= MAX_AGE_DAYS[o.series] and isfinite(o.value)
    except (TypeError, ValueError):
        return False


def indicators(rows: dict[str, Observation], now: date) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for code, (family, threshold) in SERIES.items():
        if code == "SOFR_TGCR_SPREAD":
            a, b = rows.get("SOFR"), rows.get("TGCR")
            if not (fresh(a, now) and fresh(b, now) and a.date == b.date):
                continue
            value, observed = round(a.value - b.value, 5), a.date
        else:
            o = rows.get(code)
            if not fresh(o, now):
                continue
            value, observed = o.value, o.date
        output[code] = {
            "family": family, "value": value, "date": observed,
            "threshold": threshold, "critical": value >= threshold,
        }
    return output


def verified_event_ids(events: list[dict[str, Any]]) -> set[str]:
    """A review decision plus immutable evidence is required, not a boolean and arbitrary URL."""
    ids = set()
    for event in events:
        try:
            event_id = str(event["id"])
            url = str(event["primary_source_url"])
            approved = (
                event.get("review_status") == "approved"
                and event.get("verified") is True
                and str(event.get("verified_by", "")).strip() != ""
                and str(event.get("source_sha256", "")).isalnum()
                and len(str(event.get("source_sha256"))) == 64
                and str(event.get("cross_market_mechanism", "")).strip() != ""
                and url.startswith("https://")
                and "example.com" not in url
                and event.get("published_at_utc")
            )
            if approved and event_id.strip():
                ids.add(event_id)
        except (KeyError, TypeError, ValueError):
            pass
    return ids


def decide(
    rows: dict[str, Observation], previous: dict[str, Any],
    weekly: dict[str, Any], events: list[dict[str, Any]], now: date,
) -> dict[str, Any]:
    metrics = indicators(rows, now)
    present = sorted({v["family"] for v in metrics.values()})
    stressed = sorted({v["family"] for v in metrics.values() if v["critical"]})
    new_events = sorted(verified_event_ids(events) - set(previous.get("seen_events", [])))

    if len(stressed) >= 3:
        severity = "red"
    elif len(stressed) == 2:
        severity = "orange"
    elif len(stressed) == 1:
        severity = "yellow"
    elif len(present) >= 3:
        severity = "green"
    else:
        severity = "unknown"

    base = weekly.get("severity", "unknown")
    if base not in LEVELS:
        raise ValueError("invalid weekly baseline level: " + str(base))
    # A baseline without a source and date is intentionally UNKNOWN.
    if base != "unknown" and not (weekly.get("as_of") and weekly.get("source_url", "").startswith("https://")):
        base = "unknown"

    evidence_day = max((v["date"] for v in metrics.values()), default="")
    down = (
        base != "unknown" and severity != "unknown"
        and len(present) >= 3 and LEVELS[severity] < LEVELS[base]
    )
    previous_recovery_date = str(previous.get("last_recovery_date", ""))
    if down and evidence_day > previous_recovery_date:
        recovery_count = int(previous.get("recovery_count", 0)) + 1
        recovery_date = evidence_day
    elif down:
        recovery_count, recovery_date = int(previous.get("recovery_count", 0)), previous_recovery_date
    else:
        recovery_count, recovery_date = 0, ""

    reasons: list[str] = []
    if len(stressed) >= 2 and len(previous.get("critical_families", [])) < 2:
        reasons.append("independent_stress_families")
    if (
        base != "unknown" and severity != "unknown"
        and len(present) >= 3 and LEVELS[severity] > LEVELS[base]
        and previous.get("last_alert_severity") != severity
    ):
        reasons.append("above_weekly_baseline")
    if new_events:
        reasons.append("reviewed_contagion_event")
    if recovery_count >= 3 and not previous.get("recovery_alerted", False):
        reasons.append("sustained_recovery")

    # Missing families are never counted as recovered/normal; events remain actionable.
    state = {
        "severity": severity,
        "critical_families": stressed,
        "seen_events": sorted(set(previous.get("seen_events", [])) | verified_event_ids(events)),
        "recovery_count": recovery_count,
        "last_recovery_date": recovery_date,
        "recovery_alerted": bool(previous.get("recovery_alerted", False) or "sustained_recovery" in reasons) if down else False,
        "last_alert_severity": severity if reasons else previous.get("last_alert_severity"),
    }
    return {
        "date": now.isoformat(), "severity": severity,
        "confidence": "moderate" if len(present) >= 3 else "limited",
        "present_families": present, "critical_families": stressed,
        "indicators": metrics, "events": new_events,
        "reasons": reasons, "alert": bool(reasons), "next_state": state,
    }

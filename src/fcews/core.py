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
    "DGS10": 7, "DGS30": 7, "BGCR": 7, "BAA10Y": 7,
}
CONTEXT_CODES = {"DGS10", "DGS30", "BGCR"}
# Composite stress indices reuse underlying credit, volatility and funding measures.
# Keep the legacy diagnostic grade for historical comparability; require distinct
# direct channels on the same observation date for the automatic two-family gate.
DIRECT_CONFIRMATION_FAMILIES = frozenset({"credit", "volatility", "funding"})
DIRECT_CODES = frozenset({"BAMLH0A0HYM2", "VIXCLS", "SOFR", "TGCR"})
MAX_FUTURE_SECONDS = 300


@dataclass(frozen=True)
class Observation:
    series: str
    date: str
    value: float
    source: str
    retrieved_utc: str
    available_at_utc: str | None = None
    recent: tuple[Observation, ...] = ()  # transport-only; as_dict remains one dated value

    def as_dict(self) -> dict[str, Any]:
        return {
            "series": self.series, "date": self.date, "value": float(self.value),
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


def indicators(rows: dict[str, Observation], now: date, registry=None) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for code, (family, threshold) in (SERIES if registry is None else registry).items():
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
    registry=None, history: dict[str, dict[str, Observation]] | None = None,
) -> dict[str, Any]:
    metrics = indicators(rows, now, registry=registry)
    present = sorted({v["family"] for v in metrics.values()})
    stressed = sorted({v["family"] for v in metrics.values() if v["critical"]})
    # Inner join by exact observation date, using only data available to this
    # decision. A later normal reading invalidates an older breach for that channel.
    dated = {day: dict(items) for day, items in (history or {}).items()}
    for code, row in rows.items():
        if (code in DIRECT_CODES or (registry or {}).get(code, ("", 0))[0] in DIRECT_CONFIRMATION_FAMILIES) and fresh(row, now):
            dated.setdefault(row.date, {})[code] = row
    direct_by_date: dict[str, dict[str, dict]] = {}
    for day, items in sorted(dated.items()):
        daily = indicators({k: v for k, v in items.items() if v.date == day}, now, registry=registry)
        direct_by_date[day] = {
            v["family"]: dict(v, series=k, sources={
                code: items[code].source for code in
                (("SOFR", "TGCR") if k == "SOFR_TGCR_SPREAD" else (k,))
            }) for k, v in daily.items() if v["family"] in DIRECT_CONFIRMATION_FAMILIES
        }
    direct_metrics = {}
    for daily in direct_by_date.values():
        direct_metrics.update(daily)
    last_normal = {}
    for day, daily in direct_by_date.items():
        for family, metric in daily.items():
            if not metric["critical"]:
                last_normal[family] = day
    qualifying = {}
    for day, daily in direct_by_date.items():
        matched = {f: v for f, v in daily.items() if v["critical"]
                   and direct_metrics[f]["critical"] and day > last_normal.get(f, "")}
        if len(matched) >= 2:
            qualifying[day] = matched
    confirmation_date = max(qualifying, default=None)
    confirmation_evidence = qualifying.get(confirmation_date, {})
    confirming = sorted(confirmation_evidence)

    # Migration preserves a previously confirmed episode, without inventing
    # per-channel resolution history. Missing data is not a normal observation.
    prior = previous.get("active_confirmation_families")
    if prior is None:
        prior = previous.get("confirming_families")
    if prior is None:
        prior = sorted(set(previous.get("critical_families", [])) & DIRECT_CONFIRMATION_FAMILIES)
        if len(prior) < 2:
            prior = []
    active = dict(previous.get("active_confirmation_dates") or
                  {f: previous.get("active_confirmation_date") or "" for f in prior})
    for family in list(active):
        if last_normal.get(family, "") > active[family]:
            del active[family]
    new_confirmation = len(confirming) >= 2 and bool(set(confirming) - set(active))
    for family in confirming:
        active[family] = max(active.get(family, ""), confirmation_date)
    active_date = max(active.values(), default="")
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
    # A baseline explicitly marked uncalibrated is never comparable.
    if weekly.get("model_comparability") == "not_calibrated":
        base = "unknown"
    # A baseline without a source and date is intentionally UNKNOWN.
    if base != "unknown" and not (weekly.get("as_of") and weekly.get("source_url", "").startswith("https://")):
        base = "unknown"

    family_dates: dict[str, str] = {}
    for metric in metrics.values():
        family = metric["family"]
        family_dates[family] = max(family_dates.get(family, ""), metric["date"])
    evidence_day = max(family_dates.values(), default="")
    down = (
        base != "unknown" and severity != "unknown"
        and len(present) >= 3 and LEVELS[severity] < LEVELS[base]
    )
    prior_families = previous.get("recovery_family_dates", {})
    updated_families = [
        fam for fam, observed in family_dates.items()
        if observed > prior_families.get(fam, "")
    ]
    previous_recovery_date = str(previous.get("last_recovery_date", ""))
    # Require at least two independently updated families for a new recovery day.
    # A solitary daily VIX update cannot masquerade as broad recovery.
    if down and evidence_day > previous_recovery_date and len(updated_families) >= 2:
        recovery_count = int(previous.get("recovery_count", 0)) + 1
        recovery_date = evidence_day
        recovery_family_dates = family_dates
    elif down:
        recovery_count, recovery_date = int(previous.get("recovery_count", 0)), previous_recovery_date
        recovery_family_dates = prior_families
    else:
        recovery_count, recovery_date, recovery_family_dates = 0, "", {}

    reasons: list[str] = []
    if new_confirmation:
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
        "confirming_families": confirming,
        "active_confirmation_families": sorted(active),
        "active_confirmation_dates": active,
        "active_confirmation_date": active_date or None,
        "seen_events": sorted(set(previous.get("seen_events", [])) | verified_event_ids(events)),
        "recovery_count": recovery_count,
        "last_recovery_date": recovery_date,
        "recovery_family_dates": recovery_family_dates,
        "recovery_alerted": bool(previous.get("recovery_alerted", False) or "sustained_recovery" in reasons) if down else False,
        "last_alert_severity": severity if reasons else previous.get("last_alert_severity"),
    }
    return {
        "date": now.isoformat(), "severity": severity,
        "confidence": "moderate" if len(present) >= 3 else "limited",
        "present_families": present, "critical_families": stressed,
        "confirming_families": confirming, "confirmation_date": confirmation_date,
        "confirmation_evidence": confirmation_evidence,
        "indicators": metrics, "events": new_events,
        "reasons": reasons, "alert": bool(reasons), "next_state": state,
    }

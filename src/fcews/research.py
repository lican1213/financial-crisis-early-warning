"""Official leading-indicator research layer, deliberately outside four-family alert gates.

First principle: an observed data point is not its publication timestamp, and
a change in one proxy is not a crisis nor a housing turning point. The public
repository stores only official, source-dated observations; missing stays missing.
"""
from __future__ import annotations

import argparse
import json
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from .collect import fetch_fred
from .cli import ROOT, read_json, write_if_changed

# All FRED series have original US government producers except investment-grade
# OAS (ICE BofA licensed series hosted by FRED). Never present FRED as their publisher.
US_SERIES = {
    "TEMPHELPS": ("staffing", "thousand_persons", "monthly", "BLS"),
    "JTSJOL": ("staffing", "thousand_vacancies", "monthly", "BLS"),
    "ICSA": ("labor", "persons", "weekly", "US_DOL"),
    "T10Y3M": ("rates", "percentage_points", "daily", "FED"),
    "T10Y2Y": ("rates", "percentage_points", "daily", "FED"),
    "BAMLC0A0CM": ("credit_context", "percent", "daily", "ICE_BofA"),
}
MAX_AGE = {"daily": 8, "weekly": 20, "monthly": 75}

# Official release-based indicators not reliably obtainable from machine-readable
# endpoints are ingested as individually checked records, not inferred from news.
CN_SERIES = {
    "NBS_PMI_MANUFACTURING": ("NBS", "index"),
    "NBS_PMI_NEW_ORDERS": ("NBS", "index"),
    "NBS_PMI_SMALL": ("NBS", "index"),
    "NBS_PMI_NEW_EXPORT_ORDERS": ("NBS", "index"),
    "NBS_NEW_HOME_RISING_CITIES": ("NBS", "cities"),
    "NBS_USED_HOME_RISING_CITIES": ("NBS", "cities"),
    "NBS_RESIDENTIAL_SALES_AREA_YOY": ("NBS", "percent"),
    "NBS_RESIDENTIAL_SALES_VALUE_YOY": ("NBS", "percent"),
    "NBS_RESIDENTIAL_UNSOLD_AREA_YOY": ("NBS", "percent"),
    "NBS_DEVELOPER_MORTGAGE_FUNDS_YOY": ("NBS", "percent"),
    "NBS_DEVELOPER_DOMESTIC_LOANS_YOY": ("NBS", "percent"),
    "NBS_PRIVATE_INVESTMENT_YOY": ("NBS", "percent"),
    "NBS_RETAIL_SALES_YOY": ("NBS", "percent"),
    "NBS_SMALL_FIRM_ORDERS": ("NBS", "index"),
    "PBOC_HOUSEHOLD_MLT_FLOW": ("PBOC", "billion_cny"),
    "PBOC_HOUSEHOLD_MLT_CONSUMPTION_FLOW": ("PBOC", "billion_cny"),
    "PBOC_MORTGAGE_BALANCE_YOY": ("PBOC", "percent"),
    "PBOC_GOV_BONDS_TSF_FLOW": ("PBOC", "billion_cny"),
    "PBOC_TOTAL_TSF_FLOW": ("PBOC", "billion_cny"),
    "PBOC_CORPORATE_MLT_FLOW": ("PBOC", "billion_cny"),
    "PBOC_BILL_FINANCING_FLOW": ("PBOC", "billion_cny"),
}
COMPANY_DOMAINS = {
    "RANDSTAD": ("randstad.com",),
    "MANPOWERGROUP": ("manpowergroup.com",),
    "KORN_FERRY": ("kornferry.com",),
    "HAYS": ("haysplc.com", "hays.com"),
    "PAGEGROUP": ("page.com", "pagegroup.com"),
    "ADECCO": ("adeccogroup.com",),
    "RECRUIT_INDEED": ("recruit-holdings.com", "indeed.com", "hiringlab.org"),
    "ROBERT_HALF": ("roberthalf.com",),
}
# A financial-report item is a demand measure (not a net profit) with a
# clearly stated comparison basis. Unit and period are explicit.
COMPANY_UNITS = {"organic_revenue_yoy_pct", "lfl_net_fees_yoy_pct",
                 "constant_currency_gross_profit_yoy_pct", "contract_volume_yoy_pct",
                 "permanent_placements_yoy_pct", "rpo_orders_yoy_pct"}
AUTHORITY_DOMAINS = {
    "NBS": ("stats.gov.cn",),
    "PBOC": ("pbc.gov.cn",),
    **COMPANY_DOMAINS,
}


def official_url(url: str, authority: str) -> bool:
    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or "").lower().rstrip(".")
        # Reject embedded credentials and nonstandard ports, which can hide
        # impersonation, redirects or a local endpoint.
        return (parsed.scheme == "https" and parsed.username is None
                and parsed.password is None and parsed.port in (None, 443)
                and bool(parsed.path) and any(
                    host == root or host.endswith("." + root)
                    for root in AUTHORITY_DOMAINS[authority]))
    except (ValueError, KeyError, TypeError):
        return False


def validate_release(record: dict, today: date) -> dict:
    """Reject look-ahead releases, spoofed authorities, mixed units and fake zeros."""
    if not isinstance(record, dict):
        raise ValueError("release must be an object")
    code = record.get("series")
    if code in CN_SERIES:
        authority, unit = CN_SERIES[code]
    elif isinstance(code, str) and code.startswith("COMPANY_"):
        authority = code[len("COMPANY_"):]
        if authority not in COMPANY_DOMAINS:
            raise ValueError("unregistered company")
        unit = record.get("unit")
        if unit not in COMPANY_UNITS:
            raise ValueError("unregistered demand-side unit")
    else:
        raise ValueError("unregistered research series")
    if record.get("authority") != authority or record.get("unit") != unit:
        raise ValueError("authority or unit mismatch")
    published = date.fromisoformat(record["published_date"])
    period = date.fromisoformat(record["period_end"])
    if not period <= published <= today:
        raise ValueError("future/unpublished release")
    if not official_url(record.get("source_url", ""), authority):
        raise ValueError("non-primary or untrusted source URL")
    if not isinstance(record.get("definition"), str) or len(record["definition"].strip()) < 12:
        raise ValueError("missing statistical definition")
    value = record.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("missing/nonfinite numeric observation")
    if unit == "cities" and (int(value) != value or value < 0 or value > 70):
        raise ValueError("70-city numerator out of bounds")
    if unit == "index" and not 0 <= value <= 100:
        raise ValueError("PMI index out of bounds")
    if record.get("measure_type") not in {"monthly", "stock_yoy", "cumulative_yoy",
                                          "cumulative_flow", "quarterly", "other"}:
        raise ValueError("comparison basis missing")
    return dict(record)


def evaluate_releases(records: list[dict], today: date) -> dict:
    """Quality gate and narrow objective diagnostics; NO inferred aggregate score."""
    accepted, rejected = [], []
    for i, row in enumerate(records):
        try:
            accepted.append(validate_release(row, today))
        except (ValueError, KeyError, TypeError) as exc:
            rejected.append({"row_index": i, "reason": type(exc).__name__ + ": " + str(exc)})
    # No overwrites of contradictory releases. If a historical revision is
    # supplied, its updated publication must be separately reconciled.
    by_key = {}
    duplicates = []
    for row in accepted:
        key = (row["series"], row["period_end"])
        if key in by_key:
            duplicates.append({"series": key[0], "period_end": key[1]})
        by_key[key] = row
    if duplicates:
        rejected.append({"reason": "duplicate observation/revision requires adjudication",
                         "pairs": duplicates})
    # Never allow a contested revision into a turning-point determination.
    contested = {(d["series"], d["period_end"]) for d in duplicates}
    admissible = [row for row in accepted if (row["series"], row["period_end"]) not in contested]
    latest = {}
    for row in admissible:
        code = row["series"]
        if code not in latest or row["period_end"] > latest[code]["period_end"]:
            latest[code] = row
    # The decision is unknown unless independent evidence groups can be matched
    # on an identical observation period and comparison basis.
    home = housing_turning_point(admissible, today)
    return {
        "status": "needs_review" if rejected else ("partial" if not accepted else "valid"),
        "accepted_count": len(accepted), "rejected": rejected,
        "latest": latest, "housing_turning_point": home,
        "china_recovery_breadth_score": None,
        "staffing_global_score": None,
        "score_status": "not_calibrated_missing_component_coverage",
        "release_authority_status": "hostname_and_schema_checked_not_live_document_readback",
        "risk_alert_role": "context_only_no_automatic_systemic_alert",
    }


def housing_turning_point(records: list[dict], today: date) -> dict:
    """At least two of price breadth, transactions and mortgage momentum must improve.

    Inventory must independently not deteriorate. All comparisons MUST share a
    period and like-for-like methodology. Missing components -> not confirmed.
    """
    codes = ("NBS_USED_HOME_RISING_CITIES", "NBS_RESIDENTIAL_SALES_AREA_YOY",
             "PBOC_MORTGAGE_BALANCE_YOY", "NBS_RESIDENTIAL_UNSOLD_AREA_YOY")
    series = {c: sorted((r for r in records if r["series"] == c),
                        key=lambda x: x["period_end"]) for c in codes}
    changes = {}
    for code, history in series.items():
        if len(history) < 2:
            continue
        before, after = history[-2:]
        if before["measure_type"] != after["measure_type"]:
            continue
        if after["period_end"] <= before["period_end"]:
            continue
        if (today - date.fromisoformat(after["period_end"])).days > 100:
            continue
        changes[code] = (after["value"] - before["value"], after["period_end"])
    # Demand categories must share the same latest monthly observation period;
    # cumulative YOY and monthly YOY cannot masquerade as like-for-like.
    demands = [changes.get(c) for c in codes[:3]]
    valid_demand = [d for d in demands if d is not None]
    matching = len(valid_demand) >= 2 and len({d[1] for d in valid_demand}) == 1
    inventory = changes.get(codes[3])
    inventory_ok = inventory is not None and matching and inventory[1] == valid_demand[0][1] and inventory[0] <= 0
    improving = sum(d[0] > 0 for d in valid_demand) if matching else 0
    confirmed = bool(matching and inventory_ok and improving >= 2)
    return {
        "confirmed": confirmed, "status": "confirmed" if confirmed else "unverified",
        "improving_groups": improving if matching else None,
        "inventory_not_deteriorating": inventory_ok if inventory else None,
        "basis": "strict_same_period_two_of_three_plus_inventory_no_worsening",
        "note": "Changes in housing loan balances can include prepayments; this is a diagnostic, not causal attribution.",
    }


def collect_us(fetcher=fetch_fred, today: date | None = None) -> dict:
    today = today or datetime.now(timezone.utc).date()
    rows, errors = {}, {}
    with ThreadPoolExecutor(max_workers=6) as pool:
        tasks = {pool.submit(fetcher, code): code for code in US_SERIES}
        for future in as_completed(tasks):
            code = tasks[future]
            try:
                obs = future.result()
                if (obs.series != code or not math.isfinite(obs.value)
                    or obs.source != "https://fred.stlouisfed.org/series/" + code):
                    raise ValueError("wrong series, source or nonfinite value")
                observed = date.fromisoformat(obs.date)
                freq = US_SERIES[code][2]
                if freq == "monthly" and observed.day != 1:
                    raise ValueError("monthly series must use first day of observation month")
                if not 0 <= (today-observed).days <= MAX_AGE[freq]:
                    raise ValueError("future or stale observation")
                rows[code] = {
                    "value": obs.value, "observation_date": obs.date,
                    "retrieved_utc": obs.retrieved_utc, "source_url": obs.source,
                    "unit": US_SERIES[code][1], "frequency": freq,
                    "producer": US_SERIES[code][3],
                    "publication_date": None, "vintage_status": "latest_not_original_release",
                }
            except (ValueError, TypeError, KeyError, OSError) as exc:
                errors[code] = type(exc).__name__ + ": " + str(exc)[:120]
    return {
        "status": "complete" if len(rows) == len(US_SERIES) else "partial",
        "observations": dict(sorted(rows.items())), "errors": errors,
        "missing": sorted(set(US_SERIES)-set(rows)),
    }


def build_context(root: Path = ROOT, now: datetime | None = None, fetcher=fetch_fred) -> dict:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    today = now.astimezone(timezone.utc).date()
    manual = read_json(root / "data/research_evidence.json", {"releases": []})
    if not isinstance(manual, dict) or not isinstance(manual.get("releases"), list):
        raise ValueError("research evidence must contain releases array")
    us = collect_us(fetcher, today)
    cn = evaluate_releases(manual["releases"], today)
    return {
        "schema": "fcews.leading_research.v1", "as_of_date_utc": today.isoformat(),
        "us_labor_rates_credit": us, "official_release_research": cn,
        "technical_model_severity": "unchanged_independent",
        "model_comparability": "not_calibrated",
        "notification_authorized": False,
        "source_gate": "official_observation_date_and_publication_date_distinguished",
    }


def refresh(root: Path = ROOT, now: datetime | None = None, fetcher=fetch_fred) -> dict:
    value = build_context(root, now, fetcher)
    write_if_changed(root / "data/research_context.json", value)
    return value


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=ROOT)
    args = p.parse_args()
    out = refresh(args.root)
    print(json.dumps({
        "us_status": out["us_labor_rates_credit"]["status"],
        "cn_status": out["official_release_research"]["status"],
        "us_missing": out["us_labor_rates_credit"]["missing"],
        "release_rejections": out["official_release_research"]["rejected"],
        "notification_authorized": False,
    }, sort_keys=True))
    if out["us_labor_rates_credit"]["status"] != "complete" or out["official_release_research"]["rejected"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

"""Official Cboe volatility term structure and US Treasury rate-volatility context.

NOT the licensed ICE MOVE index. Cboe VIX9D/VIX/VIX3M/VIX6M are
equity IMPLIED volatility index tenors, not CFE futures prices. Realized yield
volatility is not implied bond volatility. Both remain CONTEXT ONLY until
historical validation; never fabricate a new independent stress family.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import re
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from .collect import read_url, FRED_GRAPH
from .cli import ROOT, write_if_changed

CBOE_BASE = "https://cdn.cboe.com/api/global/us_indices/daily_prices"
CBOE_TENORS = {"VIX9D": 9, "VIX": 30, "VIX3M": 90, "VIX6M": 180}
FRED_YIELDS = ("DGS2", "DGS5", "DGS10", "DGS30")
CFE_ENDPOINT = "https://www-api.cboe.com/us/futures/market_statistics/settlement/csv"
CFE_PAGE = "https://www.cboe.com/markets/us/futures/market-statistics/settlement/futures/daily"
MOVE_SOURCE = "https://developer.ice.com/fixed-income-data-services/catalog/ice-data-indices-move-index"


def parse_index_history(raw: str, code: str) -> list[tuple[str, float]]:
    """Parse official Cboe daily_prices CSV; rows are as-observed, not vintage archive."""
    if code not in CBOE_TENORS:
        raise ValueError("unrecognized Cboe index: " + code)
    reader = csv.DictReader(io.StringIO(raw.lstrip("\ufeff")))
    if reader.fieldnames is None:
        raise ValueError("empty index CSV")
    keymap = {key.strip().upper(): key for key in reader.fieldnames}
    daykey, valuekey = keymap.get("DATE"), keymap.get("CLOSE") or keymap.get(code)
    if daykey is None or valuekey is None:
        raise ValueError("Cboe index CSV missing DATE / CLOSE: " + code)
    rows = {}
    for row in reader:
        text_date, text_value = (row.get(daykey) or "").strip(), (row.get(valuekey) or "").strip()
        if not text_date or text_value in ("", ".", "NA"):
            continue
        # Native Cboe CSV uses MM/DD/YYYY, but ISO is also supported.
        try:
            day = date.fromisoformat(text_date).isoformat()
        except ValueError:
            day = datetime.strptime(text_date, "%m/%d/%Y").date().isoformat()
        value = float(text_value)
        if not math.isfinite(value) or value <= 0:
            raise ValueError("non-positive or non-finite Cboe volatility")
        rows[day] = value
    if not rows:
        raise ValueError("no numeric Cboe index rows")
    return sorted(rows.items())


def parse_yield_history(raw: str, code: str) -> list[tuple[str, float]]:
    reader = csv.DictReader(io.StringIO(raw.lstrip("\ufeff")))
    if not reader.fieldnames or code not in reader.fieldnames:
        raise ValueError("FRED yield CSV has no " + code)
    rows = []
    for row in reader:
        raw_value = (row.get(code) or "").strip()
        day = row.get("DATE") or row.get("observation_date")
        if day and raw_value not in ("", ".", "NaN"):
            value = float(raw_value)
            if math.isfinite(value):
                rows.append((date.fromisoformat(day).isoformat(), value))
    return sorted(set(rows))


def realized_yield_vol(histories: dict[str, list[tuple[str, float]]], window: int = 20) -> dict:
    """Sample stddev of daily yield changes in basis points by Treasury maturity."""
    if window < 5:
        raise ValueError("window too short")
    out = {}
    for series, history in histories.items():
        if len(history) < window + 1:
            continue
        recent = history[-(window + 1):]
        changes = [(b[1] - a[1]) * 100 for a, b in zip(recent, recent[1:])]
        out[series] = {
            "observation_date": recent[-1][0],
            "std_daily_yield_change_bp_20d": round(statistics.stdev(changes), 5),
            "window": window,
        }
    return out


def parse_cfe_vx_settlement(raw: str, settlement_date: str) -> dict:
    """Extract *standard monthly* VX contracts. Weekly VX43 contracts excluded.

    Cboe official download CSV headers may evolve. Reject unexpected shapes
    rather than mistake another product's price for VX. Expiration must be ISO
    or MM/DD/YYYY and strictly later than the settlement trade date.
    """
    reader = csv.DictReader(io.StringIO(raw.lstrip("\ufeff")))
    if not reader.fieldnames:
        raise ValueError("empty CFE settlement")
    normalized = {re.sub(r"[^a-z0-9]", "", col.lower()): col for col in reader.fieldnames}
    symbol_col = next((normalized[k] for k in ("symbol", "contract", "symbolexpirationdate") if k in normalized), None)
    exp_col = next((normalized[k] for k in ("expirationdate", "expiration", "expiry", "expdate") if k in normalized), None)
    price_col = next((normalized[k] for k in ("settlementprice", "settle", "settlement", "price") if k in normalized), None)
    if not symbol_col or not price_col or not exp_col:
        raise ValueError("CFE schema unknown: " + ",".join(reader.fieldnames))
    today = date.fromisoformat(settlement_date)
    contracts = []
    for row in reader:
        sym = (row.get(symbol_col) or "").strip()
        # Monthly canonical "VX/X6" only; exclude VXM, weeklies like VX44/X6
        if not re.match(r"^VX/[FGHJKMNQUVXZ][0-9]{1,2}$", sym):
            continue
        raw_exp = (row.get(exp_col) or "").strip()
        try:
            exp = date.fromisoformat(raw_exp)
        except ValueError:
            try:
                exp = datetime.strptime(raw_exp, "%m/%d/%Y").date()
            except ValueError:
                continue
        raw_price = (row.get(price_col) or "").strip().rstrip("*")
        if not raw_price:
            continue
        val = float(raw_price)
        if exp > today and math.isfinite(val) and val > 0:
            contracts.append({"symbol": sym, "expiration_date": exp.isoformat(), "settlement": val})
    contracts.sort(key=lambda x: x["expiration_date"])
    if len(contracts) < 2:
        raise ValueError("fewer than two standard monthly VX futures")
    first, second = contracts[:2]
    return {
        "settlement_date": today.isoformat(), "source_url": CFE_PAGE,
        "front": first, "second": second, "f2_minus_f1": round(second["settlement"] - first["settlement"], 5),
        "backwardation": second["settlement"] < first["settlement"],
        "contract_basis": "STANDARD_MONTHLY_VX_FUTURES",
    }


def _latest_exchange_day(now: datetime) -> date:
    et = now.astimezone(ZoneInfo("America/New_York"))
    day = et.date() if et.hour >= 19 else et.date() - timedelta(days=1)
    while day.weekday() >= 5:
        day -= timedelta(days=1)
    return day


def collect_context(now: datetime | None = None, fetcher=read_url, include_futures: bool = True) -> dict:
    now = now or datetime.now(timezone.utc)
    sources, errors, indexed, yields = {}, {}, {}, {}
    jobs = []
    for code in CBOE_TENORS:
        jobs.append(("CBOE:" + code, CBOE_BASE + "/" + code + "_History.csv"))
    for code in FRED_YIELDS:
        jobs.append(("FRED:" + code, FRED_GRAPH + "?id=" + code + "&cosd=2026-01-01"))
    as_of = _latest_exchange_day(now)
    # Official date-specific settlement CSV is explicitly labeled post-close.
    if include_futures:
        jobs.append(("CFE:VX", CFE_ENDPOINT + "?dt=" + as_of.isoformat()))
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(fetcher, url, 12): (key, url) for key, url in jobs}
        for future in as_completed(futures):
            key, url = futures[future]
            try:
                raw = future.result()
                if key.startswith("CBOE:"):
                    code = key.split(":")[1]
                    latest = parse_index_history(raw, code)[-1]
                    age = (now.date() - date.fromisoformat(latest[0])).days
                    if age < 0 or age > 7:
                        raise ValueError("stale or future Cboe source date: " + latest[0])
                    indexed[code] = {"date": latest[0], "value": latest[1],
                                     "tenor_days": CBOE_TENORS[code], "source_url": url}
                elif key.startswith("FRED:"):
                    code = key.split(":")[1]
                    yields[code] = parse_yield_history(raw, code)
                else:
                    sources["vx_futures"] = parse_cfe_vx_settlement(raw, as_of.isoformat())
            except (OSError, UnicodeError, ValueError, TypeError) as error:
                errors[key] = type(error).__name__ + ": " + str(error)[:160]
    term = None
    if all(c in indexed for c in ("VIX9D", "VIX", "VIX3M", "VIX6M")):
        # Never compare mismatched market sessions for term structure.
        dates = {indexed[c]["date"] for c in CBOE_TENORS}
        if len(dates) == 1:
            values = {c: indexed[c]["value"] for c in CBOE_TENORS}
            term = {
                "observation_date": dates.pop(),
                "equity_index_spread_vix9d_minus_vix3m": round(values["VIX9D"] - values["VIX3M"], 5),
                "equity_index_spread_vix_minus_vix3m": round(values["VIX"] - values["VIX3M"], 5),
                "near_term_equity_implied_vol_higher": values["VIX9D"] > values["VIX3M"],
                "instrument": "CBOE_EQUITY_IMPLIED_VOL_INDICES_NOT_VIX_FUTURES",
            }
        else:
            errors["CBOE:TERM"] = "mismatched observation dates among Cboe indices"
    coverage = len(indexed)
    sources.update({
        "indexes": indexed, "equity_vol_index_term_structure": term,
        "treasury_realized_yield_volatility": realized_yield_vol(yields),
        "move": {"status": "license_required", "origin": MOVE_SOURCE,
                 "unit": "MOVE_points", "value": None,
                 "reason": "ICE MOVE is proprietary; realized yield vol and VIX term are NOT MOVE"},
    })
    return {
        "status": "ok" if coverage >= 3 else "degraded",
        "as_of_date_utc": now.date().isoformat(),
        "source_status": {"cboe_index_count": coverage, "yield_maturities": sorted(yields)},
        "errors": errors, "context": sources,
        "alert_role": "context_only_no_independent_family_or_notification_gate",
    }


def refresh(root: Path = ROOT, now: datetime | None = None, fetcher=read_url) -> dict:
    result = collect_context(now, fetcher)
    write_if_changed(root / "data/volatility_context.json", result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    result = refresh(args.root)
    print(json.dumps({
        "status": result["status"],
        "sources": result["source_status"],
        "term": result["context"]["equity_vol_index_term_structure"],
        "vx_futures": result["context"].get("vx_futures"),
        "move": result["context"]["move"]["status"],
        "errors": result["errors"],
    }, sort_keys=True))
    if result["status"] == "degraded":
        raise SystemExit(2)


if __name__ == "__main__":
    main()

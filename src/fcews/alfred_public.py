"""Leakage-checked historical ALFRED as-of snapshots (public, no API key).

This is an *undocumented* ALFRED graph CSV URL. Every requested vintage MUST
appear exactly as requested in the returned column headers. Otherwise refuse
the data: ALFRED can silently fall back to modern observations on malformed
requests. Availability is CONSERVATIVELY bounded by as-of date + 1 UTC day;
it is not the actual publisher's intra-day release timestamp.

We persist hashes/diagnostics, not copyrighted bulk market-data raw records.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import time
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .benchmarks import evaluate
from .expost import EVENTS
from .cli import ROOT, write_if_changed

ALFRED_GRAPH = "https://alfred.stlouisfed.org/graph/alfredgraph.csv"
SERIES = ("VIXCLS", "BAMLH0A0HYM2", "NFCI", "STLFSI4")
BASIS = "ALFRED_public_asof_plus_one_UTC_day"
ALFRED_EXPLANATION = "https://alfred.stlouisfed.org/help/downloaddata"
FIELDS = ("series", "observation_date", "first_available_at_utc",
          "value", "source_url", "availability_basis", "requested_asof_date", "source_sha256")


def weekly_asof(start: str, end: str) -> list[str]:
    begin, finish = date.fromisoformat(start), date.fromisoformat(end)
    if finish < begin:
        raise ValueError("end precedes start")
    result = []
    current = begin
    while current <= finish:
        if current.weekday() == 4:  # Friday; snapshots known after the close.
            result.append(current.isoformat())
        current += timedelta(days=1)
    return result


def decision_checkpoints(asof_days: list[str]) -> list[dict]:
    # A Friday snapshot becomes conservatively usable Saturday UTC midnight.
    # Monday midday UTC is the actual decision checkpoint (3 days after Friday).
    return [{"decision_at_utc": (date.fromisoformat(day) + timedelta(days=3)).isoformat()+"T12:00:00Z"}
            for day in asof_days]


def parse_asof_batch(raw: str, code: str, days: list[str], url: str) -> tuple[list[dict], str]:
    if not days:
        raise ValueError("no requested vintage dates")
    # Strictly validate all headers, including order and count, to catch ALFRED
    # defaulting to current revisions when a query syntax is wrong.
    reader = csv.reader(io.StringIO(raw.lstrip("\ufeff")))
    try:
        header = next(reader)
    except StopIteration as error:
        raise ValueError("ALFRED returned empty data") from error
    expected = ["DATE"] + [code+"_"+d.replace("-","") for d in days]
    if len(header) != len(expected) or header[0] not in ("DATE", "observation_date") or header[1:] != expected[1:]:
        raise ValueError(f"ALFRED vintage mismatch: expected {expected}, got {header}")
    table = {day: None for day in days}
    for row in reader:
        if len(row) != len(expected):
            raise ValueError("ALFRED CSV row width mismatch")
        observed = date.fromisoformat(row[0])
        for i, asof in enumerate(days):
            if observed > date.fromisoformat(asof):
                # Never accidentally include an observation newer than its as-of date.
                continue
            value = row[i+1].strip()
            if not value or value in (".", "NaN", "#NA"):
                continue
            candidate = (observed.isoformat(), float(value))
            current = table[asof]
            if current is None or candidate[0] >= current[0]:
                table[asof] = candidate
    checksum = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    items = []
    for asof in days:
        hit = table[asof]
        if hit is None:
            continue
        observed, value = hit
        # State what can be guaranteed, not an invented exact publication time.
        conservative = date.fromisoformat(asof)+timedelta(days=1)
        items.append({
            "series": code, "observation_date": observed,
            "first_available_at_utc": conservative.isoformat()+"T00:00:00Z",
            "value": str(value), "source_url": ALFRED_EXPLANATION,
            "availability_basis": BASIS, "requested_asof_date": asof,
            "source_sha256": checksum,
        })
    return items, checksum


def fetch_batch(code: str, days: list[str], fetch=None, timeout: int = 20):
    if code not in SERIES or not days or len(days) > 8:
        raise ValueError("invalid ALFRED source or batch size")
    first = date.fromisoformat(days[0])
    last = date.fromisoformat(days[-1])
    url = ALFRED_GRAPH + "?" + urlencode({
        "id": ",".join([code]*len(days)),
        "vintage_date": ",".join(days),
        "cosd": (first - timedelta(days=90)).isoformat(),
        "coed": last.isoformat(),
    })
    if fetch is None:
        def fetch(url):
            request = Request(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; FCEWS historical source verification)",
                "Accept": "text/csv",
            })
            with urlopen(request, timeout=timeout) as response:
                data = response.read(2_500_001)
            if len(data) > 2_500_000:
                raise ValueError("ALFRED CSV too large")
            return data.decode("utf-8-sig")
    raw = fetch(url)
    return parse_asof_batch(raw, code, days, url)


def collect(days: list[str], codes=SERIES, fetch=fetch_batch,
            sleep_seconds: float = 0.65, strict: bool = False) -> tuple[list[dict], dict]:
    if len(days) != len(set(days)) or days != sorted(days):
        raise ValueError("as-of dates must be unique and ascending")
    records, stats = [], {}
    for code in codes:
        result = {"snapshots_requested": len(days), "snapshots_accepted": 0,
                  "csv_batch_hashes": [], "errors": [], "missing_vintages": []}
        batch = 1 if len(days) <= 10 and (date.fromisoformat(days[-1]) - date.fromisoformat(days[0])).days > 365 else 8
        for i in range(0, len(days), batch):
            chunk = days[i:i+batch]
            last_error = None
            for attempt in range(3):
                try:
                    items, checksum = fetch(code, chunk)
                    result["csv_batch_hashes"].append(checksum)
                    records.extend(items)
                    result["snapshots_accepted"] += len(items)
                    if len(items) != len(chunk):
                        present = {r["requested_asof_date"] for r in items}
                        result["missing_vintages"].extend(d for d in chunk if d not in present)
                    last_error = None
                    break
                except HTTPError as err:
                    if err.code == 404:
                        # No historical vintage for this interval. This can
                        # legitimately predate a series' first publication.
                        result["missing_vintages"].extend(chunk)
                        last_error = None
                        break
                    last_error = "HTTPError: " + str(err)[:120]
                    if attempt < 2 and err.code in (429,500,502,503,504):
                        time.sleep(0.5*(2**attempt))
                    else:
                        break
                except (URLError, OSError, ValueError) as err:
                    last_error = type(err).__name__ + ": " + str(err)[:120]
                    if attempt < 2:
                        time.sleep(0.5*(2**attempt))
            if last_error:
                result["errors"].append({"from": chunk[0], "to": chunk[-1], "error": last_error})
                # No in-place interpolation from modern revised data.
                if strict:
                    raise RuntimeError(f"ALFRED source failure for {code}: {last_error}")
            if sleep_seconds:
                time.sleep(sleep_seconds)
        stats[code] = result
    return records, stats


def evaluate_history(features: list[dict], dates: list[str]) -> dict:
    checks = decision_checkpoints(dates)
    # Real historical windows are split in time; no post-event parameter retuning.
    train = [r for r in checks if r["decision_at_utc"][:10] < "2017-01-01"]
    test = [r for r in checks if r["decision_at_utc"][:10] >= "2017-01-01"]
    events_before = [e for e in EVENTS if e["crisis_start_utc"][:10] < "2017-01-01"]
    events_after = [e for e in EVENTS if e["crisis_start_utc"][:10] >= "2017-01-01"]
    output = {
        "method": "ALFRED_PUBLIC_ASOF_SNAPSHOTS",
        "true_intraday_first_release_clocks": False,
        "point_in_time_rule": "as-of snapshot, next UTC day at 00:00 minimum; execute Monday 12:00 UTC",
        "parameters_tuned_on_training_period": False,
        "thresholds": "frozen v0.3 heuristic rules, no fitting",
        "full_period": evaluate(features,checks,EVENTS,mode="pit") if checks else {},
        "pre2017": evaluate(features,train,events_before,mode="pit") if train else {},
        "holdout_2017on": evaluate(features,test,events_after,mode="pit") if test else {},
    }
    return output


def run(root: Path = ROOT, start="2007-01-01", end="2026-10-28",
        smoke: bool = False, collector=collect):
    days = (["2008-09-12","2011-09-09","2020-03-13","2023-03-10","2026-10-23"]
            if smoke else weekly_asof(start,end))
    # Treat missing historical signal as missing, not as absence of financial stress.
    records, source_stats = collector(days)
    completeness = {code: source_stats.get(code,{}).get("snapshots_accepted",0) for code in SERIES}
    diag = {
        "asof_dates": len(days), "sources": source_stats,
        "minimum_source_coverage": min(completeness.values()) if completeness else 0,
        "source_model": BASIS,
        "asof_csv_endpoint": ALFRED_GRAPH,
        "source_diagnostics": "Official ALFRED graph CSV is undocumented; strict column and hash checks required.",
        "price_licensing": "No bulk ICE/Cboe copyrighted raw observations committed to public GitHub",
    }
    report = evaluate_history(records,days) if records else {}
    result = {
        "label": "HISTORICAL AS-OF ALFRED; CONSERVATIVE DAY-LEVEL PIT, NOT INTRADAY",
        "mode": "pit_conservative_alfred_public",
        "smoke": smoke, "time_span": [days[0],days[-1]], "diagnostics": diag,
        "evaluation": report,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    path = root / "reports" / ("alfred_smoke.json" if smoke else "alfred_pit_latest.json")
    write_if_changed(path,result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke",action="store_true")
    parser.add_argument("--root",type=Path,default=ROOT)
    parser.add_argument("--start",default="2007-01-01")
    parser.add_argument("--end",default="2026-10-28")
    options = parser.parse_args()
    out = run(options.root,options.start,options.end,options.smoke)
    print(json.dumps({"mode":out["mode"],"smoke":out["smoke"],
                      "sources":{k:{"accepted":v["snapshots_accepted"],"errors":len(v["errors"])}
                                 for k,v in out["diagnostics"]["sources"].items()},
                      "checkpoints":out["diagnostics"]["asof_dates"]}, sort_keys=True))
    if not any(v["snapshots_accepted"] for v in out["diagnostics"]["sources"].values()):
        raise SystemExit(2)


if __name__ == "__main__":
    main()

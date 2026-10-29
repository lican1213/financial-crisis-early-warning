"""Export ALFRED vintage observations; requires user's authorized FRED API key.

Publication dates returned by ALFRED are DATE-granular, not intraday.
Advance to the following UTC midnight for conservative leakage control.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API = "https://api.stlouisfed.org/fred/series/observations"
SERIES = ("NFCI", "ANFCI", "STLFSI4", "BAMLH0A0HYM2", "VIXCLS", "SOFR", "TGCR")
FIELDS = ("series", "observation_date", "first_available_at_utc",
          "value", "source_url", "vintage_date", "availability_basis")


def query_json(params: dict, timeout: int = 20) -> dict:
    request = Request(API + "?" + urlencode(params), headers={"User-Agent": "FCEWS/0.4 PIT exporter"})
    with urlopen(request, timeout=timeout) as response:
        raw = response.read(8_000_000)
    payload = json.loads(raw)
    if not isinstance(payload.get("observations"), list):
        raise ValueError("ALFRED output_type=3 response lacks observations")
    return payload


def export_one(code: str, key: str, start: str, end: str, get=query_json) -> list[dict]:
    if code not in SERIES:
        raise ValueError("unrecognized ALFRED series")
    if not key:
        raise ValueError("FRED_API_KEY is required for authorized vintage export")
    results: list[dict] = []
    offset = 0
    while True:
        payload = get({
            "series_id": code, "api_key": key, "file_type": "json",
            "output_type": 3, "realtime_start": start, "realtime_end": end,
            "observation_start": start, "observation_end": end,
            "sort_order": "asc", "limit": 100000, "offset": offset,
        })
        raw = payload["observations"]
        for row in raw:
            value = row.get("value")
            if value in (None, "", "."):
                continue
            vintage = row.get("realtime_start")
            if not vintage:
                raise ValueError("ALFRED observation missing vintage release date")
            # Conservative day-level availability: the released value is safe
            # from the START of the following UTC date, not same-day 00:00.
            next_utc_day = date.fromisoformat(vintage) + timedelta(days=1)
            results.append({
                "series": code, "observation_date": row["date"],
                "first_available_at_utc": next_utc_day.isoformat() + "T00:00:00Z",
                "value": value, "source_url": "https://fred.stlouisfed.org/series/" + code,
                "vintage_date": vintage,
                "availability_basis": "ALFRED_vintage_date_plus_one_UTC_day",
            })
        offset += len(raw)
        if len(raw) == 0 or offset >= int(payload.get("count", offset)):
            break
        if offset > 1_000_000:
            raise ValueError("ALFRED vintage export exceeded safety limit")
    return results


def run(output: Path, start: str, end: str, key: str) -> dict:
    if not key:
        raise RuntimeError("FRED_API_KEY not configured; no retroactively invented vintages")
    all_records = []
    counts = {}
    for code in SERIES:
        items = export_one(code, key, start, end)
        counts[code] = len(items)
        all_records.extend(items)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(all_records)
    manifest = {
        "type": "ALFRED_day_level_conservative",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "start": start, "end": end, "series_counts": counts,
        "vintage_release_time_precision": "day_only",
        "timing_rule": "following 00:00 UTC after vintage date",
        "accuracy_claim": "not yet validated against publisher-specific release clocks",
    }
    output.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, default=Path("data/local/alfred_pit.csv"))
    p.add_argument("--start", default="2007-01-01")
    p.add_argument("--end", default=date.today().isoformat())
    args = p.parse_args()
    print(json.dumps(run(args.output, args.start, args.end, os.getenv("FRED_API_KEY", "")), indent=2))


if __name__ == "__main__":
    main()

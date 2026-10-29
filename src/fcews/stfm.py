"""Daily official short-term funding context from the public OFR STFM API.

The series is collected for context; it is deliberately NOT counted as a new
independent stress family until historical calibration establishes a threshold.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

from .collect import read_url
from .cli import ROOT, write_if_changed

MNEMONIC = "REPO-DVP_AR_G30-P"
BASE = "https://data.financialresearch.gov/v1/series/timeseries"
OFFICIAL_DOC = "https://www.financialresearch.gov/short-term-funding-monitor/api-specs/api-data-single/"


def parse_ofr_stfm(payload: str, retrieved_at: str) -> dict:
    raw = json.loads(payload)
    if isinstance(raw, dict):
        raw = raw.get("data") or raw.get("observations")
    if not isinstance(raw, list):
        raise ValueError("OFR STFM: expected list of date/value pairs")
    pairs = []
    for item in raw:
        if isinstance(item, (list, tuple)) and len(item) == 2:
            day, value = item
        elif isinstance(item, dict):
            day, value = item.get("date"), item.get("value")
        else:
            continue
        if day is not None and value is not None:
            datetime.strptime(str(day), "%Y-%m-%d")
            pairs.append((str(day), float(value)))
    if not pairs:
        raise ValueError("OFR STFM: no dated numeric observations")
    day, value = max(pairs)
    return {
        "code": "OFR_REPO_DVP_G30", "mnemonic": MNEMONIC,
        "date": day, "value": value,
        "unit": "percent", "purpose": "context_only",
        "source_url": OFFICIAL_DOC, "retrieved_at_utc": retrieved_at,
    }


def refresh(root: Path = ROOT, now: datetime | None = None, fetcher=read_url) -> dict:
    now = now or datetime.now(timezone.utc)
    day = now.date().isoformat()
    path = root / "data/stfm_context.json"
    if path.exists():
        old = json.loads(path.read_text(encoding="utf-8"))
        if old.get("last_checked_utc_date") == day and old.get("status") == "ok":
            return old  # OFR says STFM data update no more than once a day.
    url = BASE + "?" + urlencode({"mnemonic": MNEMONIC, "start_date": "2026-01-01"})
    try:
        fetched = parse_ofr_stfm(fetcher(url, 10), now.isoformat())
        record = {"last_checked_utc_date": day, "status": "ok", "observation": fetched}
    except (OSError, ValueError, KeyError, TypeError) as error:
        record = {"last_checked_utc_date": day, "status": "error",
                  "error_type": type(error).__name__, "previous": old.get("observation") if path.exists() else None}
    write_if_changed(path, record)
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    result = refresh(args.root)
    print(json.dumps(result, sort_keys=True))
    if result["status"] != "ok":
        raise SystemExit(2)


if __name__ == "__main__":
    main()

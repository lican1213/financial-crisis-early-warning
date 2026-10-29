"""Authorized ALFRED original-vintage evaluation with no raw-data GitHub commit.

Requires a user-controlled FRED_API_KEY secret. Exposes uncertainty and
source-family coverage separately. The published result contains statistical
summaries and provenance, not protected historical quotations or API key.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .benchmarks import evaluate
from .coverage import audit_event_coverage, classify_misses
from .expost import checkpoints, EVENTS
from .pit_export import run as export_alfred, FIELDS
from .cli import ROOT, write_if_changed


def summary(root: Path = ROOT, key: str = "", start: str = "2007-01-01",
            end: str = "2026-10-28", exporter=export_alfred):
    if not key:
        raise ValueError("FRED_API_KEY secret is required; no simulated vintage data")
    local = root / "data/local/alfred_original_vintages.csv"
    manifest = exporter(local, start, end, key)
    with local.open(encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames or any(field not in reader.fieldnames for field in FIELDS):
            raise ValueError("original-vintage exporter schema mismatch")
        features = list(reader)
    if not features:
        raise ValueError("ALFRED original-vintage export is empty")
    pts = checkpoints(start, end)
    # The original vintage data is not a fitted model. Frozen gates are
    # evaluated chronologically with no present-day revised-market fallback.
    result = evaluate(features, pts, EVENTS, mode="pit")
    coverage = audit_event_coverage(features, pts, EVENTS)
    result["event_observability"] = coverage
    result["miss_quality"] = classify_misses(result["strategies"]["fcews"]["missed_events"], coverage)
    report = {
        "method": "ALFRED_FRED_AUTHORIZED_DATE_LEVEL_PIT",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_manifest": manifest,
        "weekly_baseline": "not applied; no calibrated comparability with six-module human grade",
        "model_thresholds": "frozen v0.3; no hindsight retuning",
        "original_publisher_intraday_timestamps": False,
        "benchmark": result,
        "run_limits": {
            "source_availability": "ALFRED vintage dates are day-level proxies for first public timestamp",
            "historical_events": "four selected U.S./EU stress events; not comprehensive labels",
            "no_portfolio_profit_claim": True,
            "no_direct_ICE_MOVE": True,
            "no_licensed_raw_data_committed": True,
        },
    }
    output = root / "reports/alfred_authorized_pit.json"
    write_if_changed(output, report)
    return report


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--start", default="2007-01-01")
    p.add_argument("--end", default="2026-10-28")
    args = p.parse_args()
    out = summary(args.root, os.getenv("FRED_API_KEY",""), args.start, args.end)
    print(json.dumps({
        "method": out["method"],
        "source_counts": out["source_manifest"]["series_counts"],
        "checkpoint_count": out["benchmark"]["checkpoints"],
        "miss_quality": out["benchmark"]["miss_quality"],
    }))


if __name__ == "__main__":
    main()

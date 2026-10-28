"""Hourly CLI: no new risk evidence => no notification or noisy commit."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .collect import collect_fred
from .core import decide

ROOT = Path(__file__).resolve().parents[2]


def read_json(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def write_if_changed(path: Path, value) -> bool:
    encoded = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == encoded:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(encoded, encoding="utf-8")
    return True


def run(root: Path = ROOT):
    old = read_json(root / "data/state.json", {})
    weekly = read_json(root / "data/weekly_baseline.json", {})
    events = read_json(root / "data/events.json", [])
    rows, errors = collect_fred()
    now = datetime.now(timezone.utc)
    outcome = decide(rows, old, weekly, events, now.date())
    # Omit retrieved_utc in committed snapshots: unchanged evidence stays unchanged.
    sources = {
        key: {"date": val.date, "value": val.value, "source": val.source}
        for key, val in sorted(rows.items())
    }
    evidence = json.dumps({"sources": sources, "errors": errors}, sort_keys=True)
    signature = hashlib.sha256(evidence.encode("utf-8")).hexdigest()
    old_check = read_json(root / "data/latest_check.json", {})
    snapshot = {
        "checked_date_utc": now.date().isoformat(),
        "evidence_sha256": signature,
        "severity": outcome["severity"], "confidence": outcome["confidence"],
        "present_families": outcome["present_families"],
        "critical_families": outcome["critical_families"],
        "sources": sources, "source_errors": errors,
        "alert": outcome["alert"], "reasons": outcome["reasons"],
    }
    # Repeated retrieval of the same observation set must not rewrite the repo.
    if (
        old_check.get("evidence_sha256") != signature
        or old_check.get("severity") != snapshot["severity"]
        or old_check.get("reasons") != snapshot["reasons"]
    ):
        write_if_changed(root / "data/latest_check.json", snapshot)
    write_if_changed(root / "data/state.json", outcome["next_state"])

    alert_path = root / "data/ALERT.md"
    if outcome["alert"]:
        report = [
            "# FCEWS — candidate risk alert", "",
            "As-of UTC: " + now.isoformat(),
            "Risk level: " + outcome["severity"],
            "Confidence: " + outcome["confidence"],
            "Triggers: " + ", ".join(outcome["reasons"]),
            "Critical independent families: " + ", ".join(outcome["critical_families"]),
            "New event IDs: " + ", ".join(outcome["events"]), "",
            "## Evidence",
        ]
        for k, v in outcome["indicators"].items():
            report.append(f"- {k}: {v['value']} on {v['date']} (threshold {v['threshold']}; family {v['family']})")
        report += ["", "## Next 72 hours", "1. HY OAS and CCC stress", "2. SOFR/TGCR and funding disruptions", "3. VIX/MOVE and Treasury liquidity", "",
                   "## Investor actions", "Preserve cash buffer; avoid leverage and impulsive liquidation.",
                   "Human source verification required before publishing as an actual crisis notification.", ""]
        alert_path.write_text("\n".join(report), encoding="utf-8")
    elif alert_path.exists():
        alert_path.unlink()

    result = {
        "alert": outcome["alert"], "severity": outcome["severity"],
        "reasons": outcome["reasons"], "source_error_count": len(errors),
        "evidence_sha256": signature,
    }
    if os.getenv("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as target:
            target.write("alert=" + ("true" if outcome["alert"] else "false") + "\n")
    print(json.dumps(result, ensure_ascii=False))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    run(args.root)


if __name__ == "__main__":
    main()

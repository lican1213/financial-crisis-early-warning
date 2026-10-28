"""Stateful monitoring CLI. Failed collection is not the same as no financial stress."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from .collect import collect_all
from .core import Observation, decide, fresh, indicators

ROOT = Path(__file__).resolve().parents[2]


def read_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_if_changed(path: Path, value) -> bool:
    content = json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def fingerprint(record: dict) -> str:
    return hashlib.sha256(json.dumps(record, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load_cache(path: Path) -> dict[str, Observation]:
    cache = read_json(path, {})
    result = {}
    for code, row in cache.items():
        try:
            result[code] = Observation(
                code, row["date"], float(row["value"]), row["source"],
                row.get("retrieved_utc", ""), row.get("available_at_utc"),
            )
        except (KeyError, TypeError, ValueError):
            continue
    return result


def report_body(outcome: dict, rows: dict[str, Observation], now: datetime) -> str:
    parts = [
        "# FCEWS candidate systemic-risk alert", "",
        f"Evaluated UTC: {now.isoformat()}",
        f"Risk: {outcome['severity']} (confidence: {outcome['confidence']})",
        "Trigger(s): " + ", ".join(outcome["reasons"]),
        "Stressed independent families: " + ", ".join(outcome["critical_families"]),
        "New reviewed events: " + ", ".join(outcome["events"]), "",
        "## Observation-date and origin evidence",
    ]
    for code, item in sorted(outcome["indicators"].items()):
        observation = rows.get(code)
        src = (observation.source if observation else "paired NYFed/FRED source")
        parts.append(
            f"- {code}: {item['value']} on {item['date']}; "
            f"threshold {item['threshold']}; family {item['family']}; source: {src}"
        )
    parts += [
        "", "## Most important next 72 hours",
        "1. HY/CCC OAS and credit spread breadth",
        "2. SOFR/TGCR/BGCR, SRF, and repo-market funding",
        "3. VIX/MOVE, Treasury liquidity and correlated forced sales",
        "", "## Immediate investor actions",
        "Maintain an adequate liquid buffer. Avoid leverage and impulse liquidations.",
        "", "## Verification status",
        "Rule-gate candidate only. Event verification requires the source record's "
        "review evidence; this GitHub Issue is not an end-user ChatGPT alert.",
        "",
    ]
    return "\n".join(parts)


def run(root: Path = ROOT, collector=collect_all, now: datetime | None = None):
    now = now or datetime.now(timezone.utc)
    old_state = read_json(root / "data/state.json", {})
    weekly = read_json(root / "data/weekly_baseline.json", {})
    events = read_json(root / "data/events.json", [])
    fetched, errors = collector()
    if not isinstance(fetched, dict) or not isinstance(errors, dict):
        raise ValueError("collector must return (observations, errors)")
    cached = load_cache(root / "data/observations.json")
    # Newer observations take precedence; failed network fetch cannot erase verified cache.
    merged = dict(cached)
    changed_observations = []
    for code, obs in fetched.items():
        if not isinstance(obs, Observation):
            continue
        prior = merged.get(code)
        # Identical observation date, value and source must not rewrite the repo
        # merely because retrieval happened an hour later.
        changed = prior is None or (
            obs.date > prior.date or
            (obs.date == prior.date and (obs.value != prior.value or obs.source != prior.source))
        )
        if changed:
            if prior is not None and obs.date < prior.date:
                continue
            merged[code] = obs
            changed_observations.append({
                "first_seen_utc": now.isoformat(), "series": code,
                "observation_date": obs.date, "value": obs.value, "source": obs.source,
                "previous_value": prior.value if prior and prior.date == obs.date else None,
            })
    if changed_observations:
        trail = root / "data/vintage_log.jsonl"
        trail.parent.mkdir(parents=True, exist_ok=True)
        with trail.open("a", encoding="utf-8") as stream:
            for entry in changed_observations:
                stream.write(json.dumps(entry, sort_keys=True) + "\n")
    # Cache only actual source observations. Never manufacture synthetic zeros.
    write_if_changed(
        root / "data/observations.json",
        {key: item.as_dict() for key, item in sorted(merged.items())},
    )

    outcome = decide(merged, old_state, weekly, events, now.date())
    present = outcome["present_families"]
    # A recent cache supports continuity of risk analysis but CANNOT prove the
    # current polling run is healthy if the official endpoints all failed.
    live_present = sorted({v["family"] for v in indicators(fetched, now.date()).values()})
    healthy = len(live_present) >= 3
    health_status = "healthy" if healthy and not errors else ("partial" if healthy else "degraded")
    health = {
        "status": health_status,
        "present_families": present,
        "live_families": live_present,
        "source_error_types": {key: message.split(":", 1)[0] for key, message in sorted(errors.items())},
        "last_observation_dates": {key: ob.date for key, ob in sorted(merged.items())},
        "missing_required_families": sorted({"system", "credit", "volatility", "funding"} - set(present)),
        "last_successful_data": bool(healthy),
    }
    write_if_changed(root / "data/health.json", health)

    # A risk gate can still fire from two independently observed families when the
    # remaining sources are degraded. But degraded confidence must remain explicit.
    if outcome["alert"]:
        outbox = read_json(root / "data/outbox.json", {"pending": [], "delivered": []})
        evidence = {
            "reasons": sorted(outcome["reasons"]),
            "family_days": sorted((v["family"], v["date"], v["value"]) for v in outcome["indicators"].values() if v["critical"]),
            "events": outcome["events"],
            "baseline": weekly.get("as_of", ""),
        }
        key = fingerprint(evidence)[:20]
        existing = {item["id"] for item in outbox.get("pending", [])}
        existing |= {item["id"] for item in outbox.get("delivered", [])}
        if key not in existing:
            outbox.setdefault("pending", []).append({
                "id": key, "created_at_utc": now.isoformat(),
                "title": f"FCEWS CANDIDATE {key}: {outcome['severity']} ({','.join(outcome['reasons'])})",
                "body": report_body(outcome, merged, now) + f"\n\n<!-- FCEWS-FP:{key} -->\n",
            })
        write_if_changed(root / "data/outbox.json", outbox)
    # Advance state only if there is usable evidence or a verified candidate event.
    # A transient loss of families must not erase the previous stress regime
    # and cause a repeated escalation issue when feeds recover.
    if healthy or outcome["alert"] or outcome["events"]:
        write_if_changed(root / "data/state.json", outcome["next_state"])

    stable_snapshot = {
        "status": health_status, "severity": outcome["severity"],
        "present_families": present,
        "critical_families": outcome["critical_families"],
        "source_errors": health["source_error_types"],
        "observations": {
            key: {"date": ob.date, "value": float(ob.value), "source": ob.source}
            for key, ob in sorted(merged.items()) if fresh(ob, now.date())
        },
    }
    snapshot_sha = fingerprint(stable_snapshot)
    previous_check = read_json(root / "data/latest_check.json", {})
    if previous_check.get("evidence_sha256") != snapshot_sha:
        write_if_changed(root / "data/latest_check.json", {
            "evidence_sha256": snapshot_sha,
            "first_recorded_utc": now.isoformat(),
            "alert_candidate": outcome["alert"],
            **stable_snapshot,
        })

    output = {
        "alert_candidate": outcome["alert"],
        "status": health_status, "severity": outcome["severity"],
        "confidence": outcome["confidence"], "families": present,
        "source_errors": len(errors), "evidence_sha256": snapshot_sha,
    }
    if os.getenv("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output_file:
            output_file.write(f"healthy={'true' if healthy else 'false'}\n")
            output_file.write(f"alert={'true' if outcome['alert'] else 'false'}\n")
            output_file.write(f"status={health_status}\n")
    print(json.dumps(output, sort_keys=True))
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--require-healthy", action="store_true", default=False)
    options = parser.parse_args()
    outcome = run(options.root)
    # Operational failure, NOT financial crisis alarm. Workflow files a data-health incident.
    if options.require_healthy and outcome["status"] == "degraded":
        sys.exit(2)


if __name__ == "__main__":
    main()

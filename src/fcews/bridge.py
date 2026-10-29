"""Read-only GitHub-to-ChatGPT polling feed; never a webhook or automatic crisis authorization.

The existing ChatGPT hourly condition-watch task may READ this public JSON.
It must independently verify any candidate against official primary sources and
the user's four strict conditions. No candidate => absolutely no notification.
The feed is stable across identical hourly polls and never contains user holdings.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

from .cli import ROOT, read_json, write_if_changed

PROJECT = "lican1213/financial-crisis-early-warning"
MAX_AGE_HOURS = 72


def utc(value: str) -> datetime:
    dt=datetime.fromisoformat(value.replace("Z","+00:00"))
    if dt.tzinfo is None:
        raise ValueError("timestamp must have timezone")
    return dt.astimezone(timezone.utc)


def build_feed(root: Path, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone aware")
    now = now.astimezone(timezone.utc)
    health = read_json(root/"data/health.json", {})
    check = read_json(root/"data/latest_check.json", {})
    state = read_json(root/"data/state.json", {})
    weekly = read_json(root/"data/weekly_baseline.json", {})
    outbox = read_json(root/"data/outbox.json", {"pending":[],"delivered":[]})
    candidates = []
    seen = set()
    for item in outbox.get("delivered", []):
        candidate_id = str(item.get("id",""))
        link = str(item.get("issue_url",""))
        timestamp = item.get("delivered_at_utc")
        if not timestamp or not candidate_id or candidate_id in seen:
            continue
        try:
            when = utc(timestamp)
            if not timedelta(0) <= now-when <= timedelta(hours=MAX_AGE_HOURS):
                continue
            path = urlsplit(link)
            prefix = "/"+PROJECT+"/issues/"
            if path.scheme!="https" or path.netloc!="github.com" or not path.path.startswith(prefix):
                continue
            number = int(path.path[len(prefix):])
            if number < 1 or number != int(item.get("issue_number",0)):
                continue
        except (TypeError,ValueError):
            continue
        seen.add(candidate_id)
        candidates.append({
            "candidate_id": candidate_id,
            "issue_url": link,
            "github_issue_number": number,
            "first_delivered_utc": when.isoformat(),
            "review_state": "needs_independent_primary_verification",
            "user_alert_authorized": False,
        })
    candidates.sort(key=lambda r: (r["first_delivered_utc"],r["candidate_id"]))
    latest_sources = check.get("observations",{})
    source_summary = {
        key: {"date": info.get("date"), "source": info.get("source")}
        for key,info in sorted(latest_sources.items()) if isinstance(info,dict)
    }
    payload = {
        "schema": "fcews.chatgpt.readonly.v1",
        "transport": "ChatGPT_hourly_poll_not_GitHub_webhook",
        "candidate_count": len(candidates),
        "candidates": candidates,
        "should_send_user_notification": False,
        "notification_decision": "ChatGPT_independent_primary_source_and_four_gate_review_required",
        "monitor_health": health.get("status","unknown"),
        "health_not_financial_crisis": True,
        "latest_evidence_sha256": check.get("evidence_sha256"),
        "current_technical_severity": state.get("severity","unknown"),
        "technical_model_comparable_to_weekly": weekly.get("model_comparability","not_calibrated")=="calibrated",
        "weekly_human_grade": weekly.get("weekly_report",{}).get("global_risk_grade"),
        "last_evidence_observation_dates": {k:v["date"] for k,v in source_summary.items() if v.get("date")},
        "source_url": "https://github.com/"+PROJECT,
        "contract": {
            "notify_only_on_four_user_conditions": True,
            "no_change": "true_silence",
            "verified_candidate_issue_is_not_sufficient_evidence": True,
            "never_conflate_data_health_with_financial_crisis": True,
            "no_exactly_once_chatgpt_receipt_without_chatgpt_writeback": True,
        },
    }
    fingerprint=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
    return {"fingerprint_sha256":fingerprint, **payload}


def publish(root: Path = ROOT, now: datetime | None = None) -> dict:
    feed=build_feed(root,now)
    changed=write_if_changed(root/"data/chatgpt_feed.json", feed)
    return {"changed":changed,"candidate_count":feed["candidate_count"],"fingerprint_sha256":feed["fingerprint_sha256"]}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    args=p.parse_args()
    print(json.dumps(publish(args.root),sort_keys=True))


if __name__ == "__main__":
    main()

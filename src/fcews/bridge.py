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



def research_summary(context: dict, now: datetime) -> dict:
    """Read-only research context; no numerical score or alert permission imported."""
    try:
        day = datetime.fromisoformat(context["as_of_date_utc"]).date()
        age = (now.date() - day).days
        if not 0 <= age <= 3:
            raise ValueError("research snapshot stale or future dated")
        fresh = True
    except (KeyError, ValueError, TypeError):
        fresh, day = False, None
    us = context.get("us_labor_rates_credit", {}) if fresh else {}
    rows = us.get("observations", {}) if isinstance(us, dict) else {}
    dates = {k: v.get("observation_date") for k, v in rows.items()
             if isinstance(v, dict) and isinstance(v.get("observation_date"), str)}
    return {
        "status": "fresh" if fresh else ("stale" if context else "missing"),
        "source_snapshot_date": day.isoformat() if day else context.get("as_of_date_utc"),
        "us_source_status": us.get("status", "unknown") if isinstance(us, dict) else "unknown",
        "us_observation_dates": dict(sorted(dates.items())),
        "china_source_status": "independent_original_document_verification_required",
        "staffing_firm_source_status": "independent_original_document_verification_required",
        "china_recovery_breadth_score": None,
        "staffing_global_score": None,
        "authorizes_notification": False,
    }



def nbs_pmi_summary(context: dict, now: datetime) -> dict:
    """Display source dates only; numeric claims still require original-source review."""
    from .nbs import valid_article
    try:
        if not isinstance(context, dict):
            raise ValueError("invalid NBS snapshot")
        url = context.get("source_url", "")
        pub = datetime.fromisoformat(context["released_at_date"]).date()
        if (context.get("schema") != "fcews.nbs_official_pmi.v1"
            or not valid_article(url) or not 0 <= (now.date()-pub).days <= 75):
            raise ValueError("missing, stale or non-primary NBS snapshot")
        return {
            "status": "source_snapshot_available_not_independent_vintage",
            "published_date": pub.isoformat(), "source_url": url,
            "observation_periods": {k:v.get("period_end") for k,v in
                                    context.get("observations", {}).items()
                                    if isinstance(v, dict)},
            "authorizes_notification": False,
            "china_recovery_breadth_score": None,
        }
    except (KeyError, ValueError, TypeError):
        return {
            "status": "missing_or_stale",
            "published_date": None, "source_url": None, "observation_periods": {},
            "authorizes_notification": False,
            "china_recovery_breadth_score": None,
        }



def property_summary(context: dict, now: datetime) -> dict:
    """Expose source/grain/breadth only; never blend developer receipts with PBOC lending."""
    unknown = {
        "status": "missing_or_stale", "source_period": None,
        "used_city_rising_count": None, "new_city_rising_count": None,
        "directional_signals": None, "turning_point_confirmed": False,
        "needs_independent_pboc_mortgage_crosscheck": True,
        "risk_alert_authorized": False, "china_recovery_breadth_score": None,
    }
    try:
        if not isinstance(context, dict) or context.get("schema") != "fcews.nbs_property.v1":
            return unknown
        price = context["latest_prices"]
        market = context["latest_market"]
        period = datetime.fromisoformat(price["period_end"]).date()
        asof = datetime.fromisoformat(context["as_of_date_utc"]).date()
        if (context.get("status") != "complete" or market["period_end"] != price["period_end"]
            or not 0 <= (now.date()-asof).days <= 3
            or not 0 <= (now.date()-period).days <= 80
            or price["new"]["city_count"] != 70 or price["used"]["city_count"] != 70):
            return unknown
        return {
            "status":"source_snapshot_available_not_original_vintage",
            "source_period":period.isoformat(),
            "new_city_rising_count":price["new"]["mom_rising"],
            "used_city_rising_count":price["used"]["mom_rising"],
            "new_price_source":price["source_url"], "developer_source":market["source_url"],
            "directional_signals":context.get("directional_signals"),
            "turning_point_confirmed":False,
            "needs_independent_pboc_mortgage_crosscheck":True,
            "risk_alert_authorized":False, "china_recovery_breadth_score":None,
        }
    except (KeyError, TypeError, ValueError):
        return unknown



def staffing_summary(context: dict, now: datetime) -> dict:
    """Only official issuer demand directions, never profits or uncalibrated scores."""
    from .staffing_ir import RELEASES
    empty = {
        "status":"missing_or_stale", "available_issuers":[], "missing_issuers":[],
        "demand_directions":{}, "positive_fee_breadth_pct":None,
        "staffing_global_score":None, "risk_alert_authorized":False,
    }
    if not isinstance(context,dict) or context.get("schema")!="fcews.staffing_official_ir.v1":
        return empty
    try:
        asof=datetime.fromisoformat(context["as_of_date_utc"]).date()
        if not 0<=(now.date()-asof).days<=3:
            return empty
        reports=context["issuer_reports"]
        if not isinstance(reports,dict):
            return empty
        allowed={"RANDSTAD","MANPOWERGROUP","KORN_FERRY","HAYS","PAGEGROUP"}
        verified={}
        for company,row in reports.items():
            if (company not in allowed or not isinstance(row,dict)
                or row.get("source_status")!="issuer_document_parsed"
                or row.get("source_url")!=RELEASES[company]["url"]
                or row.get("demand_measure")!=RELEASES[company]["basis"]):
                continue
            reported=datetime.fromisoformat(row["published_date"]).date()
            if not 0<=(now.date()-reported).days<=120:
                continue
            val=float(row["value_pct"])
            if val!=val or not -100<=val<=100:
                continue
            verified[company]={"basis":row["demand_measure"],
                               "direction":"positive" if val>0 else "negative" if val<0 else "flat",
                               "period_end":row["period_end"],"source_url":row["source_url"]}
        breadth=round(100*sum(v["direction"]=="positive" for v in verified.values())/5,2) if len(verified)==5 else None
        return {
            "status":"complete" if len(verified)==5 else "partial",
            "available_issuers":sorted(verified),
            "missing_issuers":sorted(allowed-set(verified)),
            "demand_directions":verified,
            "positive_fee_breadth_pct":breadth,
            "staffing_global_score":None,
            "risk_alert_authorized":False,
        }
    except (KeyError,TypeError,ValueError,OverflowError):
        return empty



def pboc_credit_summary(context: dict, now: datetime) -> dict:
    """Official government republication evidence, NEVER a calibrated recession score."""
    from .pboc_credit import FINANCIAL, CREDIT
    empty = {
        "status": "missing_or_stale", "report_period": None,
        "mortgage_balance_yoy_pct": None, "mortgage_ytd_net_change_trillion_cny": None,
        "household_mlt_ytd_flow_100m_cny": None, "government_bond_share_tsf_pct": None,
        "original_first_published_at": None, "source_urls": {},
        "housing_turning_point_confirmed": False,
        "risk_alert_authorized": False, "china_recovery_breadth_score": None,
    }
    try:
        if not isinstance(context,dict) or context.get("schema")!="fcews.pboc_official_republication.v1":
            return empty
        asof=datetime.fromisoformat(context["as_of_date_utc"]).date()
        period=context["period_end"]
        a,b=context["financial_statistics"],context["loan_allocation"]
        if (context.get("status")!="complete"
            or not 0<=(now.date()-asof).days<=3
            or a["source_url"] != FINANCIAL or b["source_url"] != CREDIT
            or a["period_end"]!=period or b["period_end"]!=period
            or a["publication_provenance"]!="official_shanghai_government_republication_of_PBOC_not_original_vintage"
            or b["publication_provenance"]!="official_shanghai_government_republication_of_PBOC_not_original_vintage"):
            return empty
        return {
            "status":"official_government_republication_not_original_vintage",
            "report_period":period,
            "mortgage_balance_yoy_pct":b["individual_mortgage_balance_yoy_pct"],
            "mortgage_ytd_net_change_trillion_cny":b["individual_mortgage_ytd_net_change_trillion_cny"],
            "household_mlt_ytd_flow_100m_cny":a["household_medium_long_ytd_flow_100m_cny"],
            "government_bond_share_tsf_pct":a["gov_bond_fraction_of_tsf_pct"],
            "original_first_published_at":None,
            "source_urls":{"mortgage":CREDIT,"financing":FINANCIAL},
            "housing_turning_point_confirmed":False,
            "risk_alert_authorized":False,"china_recovery_breadth_score":None,
        }
    except (ValueError,TypeError,KeyError):
        return empty


def build_feed(root: Path, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone aware")
    now = now.astimezone(timezone.utc)
    health = read_json(root/"data/health.json", {})
    check = read_json(root/"data/latest_check.json", {})
    state = read_json(root/"data/state.json", {})
    weekly = read_json(root/"data/weekly_baseline.json", {})
    research = read_json(root/"data/research_context.json", {})
    nbs_pmi = read_json(root/"data/nbs_pmi_context.json", {})
    nbs_property = read_json(root/"data/nbs_property_context.json", {})
    staffing_ir = read_json(root/"data/staffing_ir_context.json", {})
    pboc_credit = read_json(root/"data/pboc_credit_context.json", {})
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
        "weekly_human_report_date": weekly.get("weekly_report",{}).get("report_date"),
        "weekly_human_grade_is_historical_paused": True,
        "leading_research": research_summary(research, now),
        "nbs_pmi_research": nbs_pmi_summary(nbs_pmi, now),
        "nbs_property_research": property_summary(nbs_property, now),
        "staffing_issuer_research": staffing_summary(staffing_ir, now),
        "pboc_credit_research": pboc_credit_summary(pboc_credit, now),
        "last_evidence_observation_dates": {k:v["date"] for k,v in source_summary.items() if v.get("date")},
        "source_url": "https://github.com/"+PROJECT,
        "contract": {
            "notify_only_on_four_user_conditions": True,
            "no_change": "true_silence",
            "verified_candidate_issue_is_not_sufficient_evidence": True,
            "never_conflate_data_health_with_financial_crisis": True,
            "research_context_cannot_authorize_crisis_notification": True,
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

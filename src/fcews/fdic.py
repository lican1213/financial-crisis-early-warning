"""Official FDIC bank-failure intake. New records request review, never trigger crisis alerts."""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

from .cli import ROOT, read_json, write_if_changed
from .collect import read_url

FDIC_API = "https://api.fdic.gov/banks/failures"
FDIC_DOC = "https://api.fdic.gov/banks/docs/"
MIN_REVIEW_ASSETS_USD_M = 10000  # $10bn: an intake priority, NOT a systemic event threshold


def parse_failures(content: str) -> list[dict]:
    payload=json.loads(content)
    records=payload.get("data")
    if not isinstance(records,list):
        raise ValueError("FDIC bank-failure API missing data list")
    found=[]
    for outer in records:
        row=outer.get("data",outer)
        if not isinstance(row,dict):
            continue
        cert=row.get("CERT")
        rawdate=str(row.get("FAILDATE",""))
        name=str(row.get("NAME","")).strip()
        try:
            try:
                failed=date.fromisoformat(rawdate[:10])
            except ValueError:
                failed=datetime.strptime(rawdate,"%m/%d/%Y").date()
            assets_thousands=float(row.get("QBFASSET") or 0)
            if cert is None or not name:
                continue
        except (TypeError,ValueError):
            continue
        found.append({
            "event_id":str(cert)+"-"+failed.isoformat(),
            "cert":str(cert),
            "name":name,
            "date":failed.isoformat(),
            "assets_usd_m":round(assets_thousands/1000,2),
            "publisher":"FDIC",
            "source_url":FDIC_DOC,
            "review_status":"pending_primary_document",
            "is_crisis_alert":False,
        })
    # A failure record is NOT proof of cross-market contagion.
    return sorted(found,key=lambda x:(x["date"],x["event_id"]),reverse=True)


def refresh(root: Path=ROOT, now: datetime|None=None, fetcher=read_url, lookback_days=90):
    now=now or datetime.now(timezone.utc)
    query=urlencode({"limit":100,"sort_by":"FAILDATE","sort_order":"DESC",
                     "fields":"NAME,CERT,FAILDATE,QBFASSET"})
    old=read_json(root/"data/fdic_review.json",{"known_event_ids":[]})
    try:
        all_failures=parse_failures(fetcher(FDIC_API+"?"+query,12))
        cutoff=(now.date()-timedelta(days=lookback_days)).isoformat()
        recent=[r for r in all_failures if r["date"]>=cutoff]
        previous=set(old.get("known_event_ids",[]))
        new_queue=[r for r in recent if r["event_id"] not in previous
                   and r["assets_usd_m"]>=MIN_REVIEW_ASSETS_USD_M]
        pending={r["event_id"]:r for r in old.get("pending_review",[])}
        pending.update({r["event_id"]:r for r in new_queue})
        current={"status":"ok","checked_utc":now.isoformat(),
                 "known_event_ids":sorted(previous|{r["event_id"] for r in recent}),
                 "recent_count":len(recent),
                 "new_review_queue":new_queue,
                 "pending_review":list(pending.values()),
                 "posted_review_event_ids":old.get("posted_review_event_ids",[]),
                 "recent_cases":recent}
    except (OSError,ValueError,TypeError,KeyError) as error:
        # Failed fetch must not overwrite the known set.
        current=dict(old,status="error",checked_utc=now.isoformat(),
                     "error_type":type(error).__name__,
                     new_review_queue=[])
    write_if_changed(root/"data/fdic_review.json",current)
    return current


def file_review_issues(root: Path, client) -> dict:
    state=read_json(root/"data/fdic_review.json",{})
    if state.get("status")!="ok":
        raise ValueError("FDIC source not healthy")
    posted=[]
    for record in list(state.get("pending_review",[])):
        key="FDIC-"+record["event_id"]
        existing=client.find_body_fingerprint(key)
        if existing is None:
            title="[REVIEW ONLY] FDIC: "+record["name"]+" ("+record["date"]+")"
            body=("Official FDIC failure record: "+record["source_url"]+"\n\n"+
                  "Reported assets: $"+str(record["assets_usd_m"])+" million. "+
                  "Review original resolution order, depositor/funding exposures, "+
                  "and cross-market contagion before deciding whether any of "+
                  "the user's four financial-risk notification criteria applies.\n\n"+
                  "**This is NOT a financial crisis alert.**\n\n"+
                  "<!-- FCEWS-FP:"+key+" -->\n")
            existing=client.create(title,body)
        receipt=client.get(existing["number"])
        if "FCEWS-FP:"+key not in (receipt.get("body") or ""):
            raise RuntimeError("FDIC review issue readback failed")
        posted.append(receipt["html_url"])
        state["pending_review"]=[r for r in state["pending_review"] if r["event_id"]!=record["event_id"]]
        state["posted_review_event_ids"]=sorted(set(state.get("posted_review_event_ids",[]))|{record["event_id"]})
        write_if_changed(root/"data/fdic_review.json",state)
    return {"review_issues":posted,"count":len(posted),"financial_alerts":0}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--post-review",action="store_true")
    args=p.parse_args()
    if args.post_review:
        import os
        from .delivery import GitHubClient
        result=file_review_issues(args.root,GitHubClient(os.getenv("GITHUB_REPOSITORY",""),os.getenv("GITHUB_TOKEN","")))
    else:
        result=refresh(args.root)
    print(json.dumps(result,sort_keys=True))
    if result.get("status")=="error":
        raise SystemExit(2)


if __name__=="__main__":
    main()

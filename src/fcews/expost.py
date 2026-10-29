"""Public-source *ex-post* diagnostic, never represented as an ALFRED PIT backtest.

Uses latest revised FRED series as of execution, and conservative proxy lags.
Its numbers cannot establish forecasting accuracy or crisis lead time.
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import date, datetime, timedelta, timezone
from io import StringIO
from pathlib import Path
from urllib.parse import urlencode

from .benchmarks import evaluate
from .collect import FRED_GRAPH, read_url

CODES = ("VIXCLS", "BAMLH0A0HYM2", "NFCI", "STLFSI4", "BAA10Y")
SOURCE_INFO = {
    "VIXCLS": 1,
    "BAMLH0A0HYM2": 1,
    "NFCI": 5,
    "STLFSI4": 5,
    "BAA10Y": 1,
}
# First-party accounts of four distinct systemic-stress windows.
EVENTS = [
    {"event_id":"2008_Lehman", "crisis_start_utc":"2008-09-15T12:00:00Z",
     "source_url":"https://www.federalreservehistory.org/essays/support-for-specific-institutions"},
    {"event_id":"2011_ECB_dollar_liquidity", "crisis_start_utc":"2011-09-15T12:00:00Z",
     "source_url":"https://www.ecb.europa.eu/press/pr/date/2011/html/pr110915.en.html"},
    {"event_id":"2020_coordinated_dollar_liquidity", "crisis_start_utc":"2020-03-15T21:00:00Z",
     "source_url":"https://www.federalreserve.gov/newsevents/pressreleases/monetary20200315c.htm"},
    {"event_id":"2023_SVB_FDIC_resolution", "crisis_start_utc":"2023-03-10T16:00:00Z",
     "source_url":"https://www.fdic.gov/news/press-releases/2023/pr23016.html"},
]


def parse_history(series: str, raw: str) -> list[dict]:
    reader=csv.DictReader(StringIO(raw))
    if not reader.fieldnames or series not in reader.fieldnames:
        raise ValueError("FRED historical CSV missing " + series)
    records=[]
    for row in reader:
        observed=row.get("DATE") or row.get("observation_date")
        value=row.get(series)
        if not observed or value in ("", ".", None):
            continue
        try:
            float(value)
            available = date.fromisoformat(observed)+timedelta(days=SOURCE_INFO[series])
        except (ValueError, KeyError):
            continue
        records.append({
            "series":series,"observation_date":observed,
            "first_available_at_utc":available.isoformat()+"T00:00:00Z",
            "value":value,"source_url":"https://fred.stlouisfed.org/series/"+series,
            "availability_basis":"EXPOST_latest_revised_proxy_lag",
        })
    if not records:
        raise ValueError("no historical values for " + series)
    return records


def collect_historical(start="2007-01-01", end="2026-10-28", fetcher=read_url):
    rows,coverage=[],{}
    for code in CODES:
        url=FRED_GRAPH+"?"+urlencode({"id":code,"cosd":start,"coed":end})
        parsed=parse_history(code,fetcher(url,15))
        rows.extend(parsed)
        coverage[code]={"records":len(parsed),
                        "first":parsed[0]["observation_date"],
                        "last":parsed[-1]["observation_date"]}
    return rows,coverage


def checkpoints(start: str, end: str):
    d=date.fromisoformat(start)
    stop=date.fromisoformat(end)
    rows=[]
    while d<=stop:
        if d.weekday()<5:
            rows.append({"decision_at_utc":d.isoformat()+"T21:00:00Z"})
        d+=timedelta(days=1)
    return rows


def generate(root: Path, start="2007-01-01", end="2026-10-28",
             collector=collect_historical):
    # Download pre-crisis credit history ONLY for fixed-threshold training.
    # Do not use 2008+ crisis observations to choose the 2007+ cutoff.
    features,coverage=collector("2000-01-01",end)
    checks=checkpoints(start,end)
    result=evaluate(features,checks,EVENTS,mode="expost")
    training=sorted(float(f["value"]) for f in features
                    if f["series"]=="BAA10Y"
                    and "2000-01-01" <= f["observation_date"] < "2007-01-01")
    if len(training)>=100:
        position=(len(training)-1)*0.95
        left=int(position)
        cutoff=training[left]+(training[min(left+1,len(training)-1)]-training[left])*(position-left)
        # Baa minus 10Y Treasury is investment-grade credit and NOT HY OAS.
        # This is a separate model registry: no mutation of production thresholds.
        proxy_registry={
            "NFCI":("system",1.0),
            "STLFSI4":("system",1.0),
            "VIXCLS":("volatility",30.0),
            "BAA10Y":("credit",round(cutoff,4)),
        }
        proxy=evaluate(features,checks,EVENTS,mode="expost",registry=proxy_registry)
        result["baa_credit_proxy_sensitivity"]={
            "indicator":"BAA10Y — Moody's Baa minus 10Y Treasury, NOT HY OAS",
            "training_window":"2000-01-01 through 2006-12-31",
            "train_observation_count":len(training),
            "training_q95_percent":round(cutoff,4),
            "model":"fixed pre-2007 cutoff, same system/VIX family definitions",
            "comparison":proxy["strategies"],
            "coverage_share":proxy["covered_by_three_families_share"],
            "claim":"ex-post sensitivity only; no first-publication vintage",
        }
    else:
        result["baa_credit_proxy_sensitivity"]={"status":"insufficient pre-2007 training sample",
                                                 "training_observation_count":len(training)}
    result["data_coverage"]=coverage
    result["published_run_utc"]=datetime.now(timezone.utc).isoformat()
    result["experimental_controls"]={
        "training_or_calibration":"none — thresholds frozen, not selected from training sample",
        "leakage_risk":"latest revised FRED series, proxy release lag; not original ALFRED vintages",
        "event_labels":"selected four official-source dates, not comprehensive all-crisis taxonomy",
        "unmatched_alerts":"outside selected event windows; not proven false positive",
        "scope":"US monetary-financial proxies, not global private-credit or energy contagion",
        "hy_history_limit":"ICE OAS FRED public series restricted to latest ~3 years from April 2026; pre-2023 crises lack HY evidence",
        "baa_proxy":"Moody's Baa-Treasury spread is investment-grade proxy, not HY OAS and not a drop-in live signal",
    }
    dst=root/"reports"/"expost_latest.json"
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path.cwd())
    p.add_argument("--start",default="2007-01-01")
    p.add_argument("--end",default="2026-10-28")
    args=p.parse_args()
    result=generate(args.root,args.start,args.end)
    print(json.dumps({"label":result["label"],"sources":result["data_coverage"],
                      "models":result["strategies"],"checkpoints":result["checkpoints"]}))


if __name__=="__main__":
    main()

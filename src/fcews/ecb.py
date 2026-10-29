"""Official ECB CISS (Euro-area systemic stress) daily context, not an automatic alarm."""
from __future__ import annotations

import argparse
import csv
import json
from datetime import date, datetime, timezone
from io import StringIO
from pathlib import Path
from urllib.parse import urlencode

from .collect import read_url
from .cli import ROOT, write_if_changed

SERIES_KEY = "D.U2.Z0Z.4F.EC.SS_CIN.IDX"
ROOT_URL = "https://data-api.ecb.europa.eu/service/data/CISS/"
DOCUMENTATION = "https://data.ecb.europa.eu/data/datasets/CISS"


def parse_ecb_csv(content: str, retrieved: str) -> dict:
    reader = csv.DictReader(StringIO(content))
    if not reader.fieldnames:
        raise ValueError("ECB CISS empty CSV")
    headers = {name.strip().upper(): name for name in reader.fieldnames}
    if "TIME_PERIOD" not in headers or "OBS_VALUE" not in headers:
        raise ValueError("ECB CISS missing TIME_PERIOD/OBS_VALUE")
    rows = []
    for row in reader:
        date_raw, value_raw = row.get(headers["TIME_PERIOD"]), row.get(headers["OBS_VALUE"])
        if date_raw and value_raw not in (None,"","NaN","."):
            date.fromisoformat(date_raw)
            rows.append((date_raw,float(value_raw)))
    if not rows:
        raise ValueError("ECB CISS no numeric dated observations")
    day,value = max(rows)
    return {
        "code":"ECB_NEW_CISS_EUROAREA", "date":day, "value":value,
        "unit":"index_0_to_1", "family":"system_context",
        "source_url":DOCUMENTATION,"retrieved_utc":retrieved,
        "purpose":"cross_region_context_only",
    }


def refresh(root: Path = ROOT, now: datetime | None=None, fetcher=read_url) -> dict:
    now=now or datetime.now(timezone.utc)
    url=ROOT_URL+SERIES_KEY+"?"+urlencode({"lastNObservations":3,"format":"csvdata"})
    path=root/"data/ecb_ciss_context.json"
    old=json.loads(path.read_text()) if path.exists() else {}
    if old.get("checked_utc_date")==now.date().isoformat() and old.get("status")=="ok":
        return old
    try:
        observation=parse_ecb_csv(fetcher(url,12),now.isoformat())
        result={"checked_utc_date":now.date().isoformat(),"status":"ok",
                "observation":observation}
    except (OSError,ValueError,TypeError,KeyError) as error:
        result={"checked_utc_date":now.date().isoformat(),"status":"error",
                "error_type":type(error).__name__,"previous":old.get("observation")}
    write_if_changed(path,result)
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    args=p.parse_args()
    result=refresh(args.root)
    print(json.dumps(result,sort_keys=True))
    if result["status"]!="ok":
        raise SystemExit(2)


if __name__=="__main__":
    main()

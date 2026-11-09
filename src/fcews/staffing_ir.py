"""Five official recruitment demand reports, with per-issuer measurement contracts.

These are current Q3 2026 original issuer/stock-exchange releases, not
automatically revised historical vintages. A missing issuer must remain missing,
and earnings/profit from restructuring cannot masquerade as hiring demand.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import math
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from .cli import ROOT, write_if_changed
from .collect import read_url
from .nbs import VisibleText

SCHEMA="fcews.staffing_official_ir.v1"
# A complete, validated Q3 issuer document is a temporary pinned release
# until its official investor archive yields a newer filing. This does NOT
# promise that the fixed page is always the latest next quarter.
RELEASES={
    "RANDSTAD":{
        "url":"https://www.randstad.com/press/2026/q3-2026-continued-top-line-momentum-drives-double-digit-profit-growth/",
        "published":"2026-10-21","period_end":"2026-09-30","basis":"organic_revenue_yoy_pct",
        "label":"organic revenue", "roots":("randstad.com",)},
    "MANPOWERGROUP":{
        "url":"https://www.manpowergroup.com/en/news-releases/news/manpowergroup-reports-3rd-quarter-2026-results",
        "published":"2026-10-15","period_end":"2026-09-30","basis":"organic_constant_currency_revenue_yoy_pct",
        "label":"organic constant currency revenue", "roots":("manpowergroup.com","manpower.com",)},
    "KORN_FERRY":{
        "url":"https://ir.kornferry.com/news-events/press-releases/detail/733/korn-ferry-announces-first-quarter-fiscal-2027-results-of-operations",
        "published":"2026-09-09","period_end":"2026-07-31","basis":"constant_currency_fee_revenue_yoy_pct",
        "label":"constant currency fee revenue", "roots":("kornferry.com",)},
    "HAYS":{
        "url":"https://www.haysplc.com/investors/results-centre",
        "published":"2026-10-12","period_end":"2026-09-30","basis":"like_for_like_net_fees_yoy_pct",
        "label":"like-for-like net fees", "roots":("haysplc.com",)},
    "PAGEGROUP":{
        "url":"https://investors.michaelpage.com/~/media/Files/P/page-v2/ir/result-reports/2026/q3-2026-trading-statement.pdf",
        "published":"2026-10-13","period_end":"2026-09-30","basis":"constant_currency_gross_profit_yoy_pct",
        "label":"constant currency gross profit", "roots":("michaelpage.com",)},
}
# Scripts must NOT replace original statements with unverified press estimates.
PATTERNS={
    "RANDSTAD":[r"Q3\s*2026\s+org\.?\s+revenue\s+growth\s+([+-]?\d+(?:\.\d+)?)%",
                r"Organic revenue increased\s+(\d+(?:\.\d+)?)%"],
    "MANPOWERGROUP":[r"([+-]?\d+(?:\.\d+)?)%\s+organic constant currency",
                    r"organic constant currency\s+revenue\s+(?:growth|of)\s+([+-]?\d+(?:\.\d+)?)%"],
    "KORN_FERRY":[r"fee revenue of\s+\$756\.5\s+million,\s+an increase of\s+(\d+(?:\.\d+)?)%\s+year.over.year\s+at both actual and constant currency"],
    "HAYS":[r"Group net fees down\s+(\d+(?:\.\d+)?)%\s+with Temp"],
    "PAGEGROUP":[r"Group\s+gross\s+profit\s+of\s*(?:£\s*)?190\.5\s*m\s*,?\s*\+(\d+(?:\.\d+)?)\s*%\s+vs\.?\s*Q3\s*2025",
                r"Gross\s+Profit\s+of\s*(?:£\s*)?190\.5\s*m\s*,?\s*\+(\d+(?:\.\d+)?)\s*%"],
}
PUBLISHED_TOKENS={
    "RANDSTAD":("21 October 2026",),
    "MANPOWERGROUP":("Oct. 15, 2026","October 15, 2026"),
    "KORN_FERRY":("September 9, 2026",),
    "HAYS":(),
    "PAGEGROUP":("13 October 2026",),
}


def official_host(url: str, company: str) -> bool:
    try:
        x=urlsplit(url)
        return x.scheme=="https" and x.username is None and x.password is None and x.port in (None,443) and bool(x.path) and any(
            x.hostname==root or (x.hostname or "").endswith("."+root)
            for root in RELEASES[company]["roots"])
    except (ValueError,KeyError,TypeError):
        return False


def fetch_official_pdf(url: str, timeout: float = 12) -> tuple[str, str]:
    """Read issuer original PDF, not the LSE JS-shell landing page.

    Enforce a bounded download, HTTPS official host (also after redirect),
    a PDF magic header, a text-bearing document, and original-document hash.
    """
    if url != RELEASES["PAGEGROUP"]["url"] or not official_host(url, "PAGEGROUP"):
        raise ValueError("not exact authorised Michael Page investor PDF")
    req=Request(url, headers={
        "User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/123.0.0.0 Safari/537.36",
        "Accept":"application/pdf", "X-Project-Source":"FCEWS public IR research",
    })
    with urlopen(req, timeout=timeout) as response:
        if response.geturl() != url:
            raise ValueError("issuer PDF redirect not pinned to original source")
        raw=response.read(2_000_001)
    if not raw.startswith(b"%PDF-") or len(raw)>2_000_000:
        raise ValueError("invalid/oversized original issuer PDF")
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError
    try:
        pdf=PdfReader(io.BytesIO(raw))
        if pdf.is_encrypted or not 1<=len(pdf.pages)<=10:
            raise ValueError("encrypted/unexpected issuer PDF page count")
        text="\n".join((page.extract_text() or "") for page in pdf.pages)
    except (PdfReadError,IndexError,KeyError,TypeError) as exc:
        raise ValueError("original issuer PDF unreadable") from exc
    if len(text)<150:
        raise ValueError("issuer PDF contains no accessible text")
    return text, hashlib.sha256(raw).hexdigest()


def visible_html(raw: str)->str:
    p=VisibleText()
    p.feed(raw)
    return re.sub(r"\s+"," "," ".join(p.parts))


def extract(code: str,html: str,today: date,url: str|None=None,source_sha256: str|None=None)->dict:
    if code not in RELEASES:
        raise ValueError("unregistered global recruiter")
    release=RELEASES[code]
    url=url or release["url"]
    if not official_host(url,code):
        raise ValueError("spoofed or unofficial company source")
    published=date.fromisoformat(release["published"])
    period=date.fromisoformat(release["period_end"])
    if not period<=published<=today or (today-published).days>120:
        raise ValueError("future/stale current issuer report")
    text=visible_html(html)
    if len(text)<150:
        raise ValueError("empty/truncated issuer response")
    if code=="RANDSTAD" and not re.search(r"Q3\s*2026",text,re.I):
        raise ValueError("Randstad report quarter not proven")
    if code=="MANPOWERGROUP" and not re.search(r"3rd Quarter 2026|third quarter 2026",text,re.I):
        raise ValueError("ManpowerGroup quarter not proven")
    if code=="KORN_FERRY" and not re.search(r"First Quarter Fiscal 2027|Q1 FY.?27",text,re.I):
        raise ValueError("Korn Ferry fiscal quarter not proven")
    if code=="HAYS" and not re.search(r"quarter ended 30 September 2026",text,re.I):
        raise ValueError("Hays Q1 FY27 quarter not proven")
    if code=="PAGEGROUP" and not re.search(r"THIRD QUARTER 2026 TRADING UPDATE",text,re.I):
        raise ValueError("Michael Page quarter not proven")
    verified_date=any(token.lower() in text.lower() for token in PUBLISHED_TOKENS[code])
    if PUBLISHED_TOKENS[code] and not verified_date:
        raise ValueError("issuer document publication date not found")
    hits=[]
    for pattern in PATTERNS[code]:
        matches=re.findall(pattern,text,re.I)
        if matches:
            if len({float(v) for v in matches})>1:
                raise ValueError("ambiguous demand growth rate in issuer original")
            hits.append(float(matches[0]))
    if not hits or any(abs(v)>100 for v in hits):
        if code=="PAGEGROUP":
            k=text.lower().find("gross profit")
            excerpt=text[max(0,k-30):k+150] if k>=0 else "[no gross profit heading]"
            raise ValueError("missing PAGEGROUP official gross-fee metric, excerpt: "+excerpt[:160])
        raise ValueError("missing/invalid employer demand growth rate")
    if len(set(hits))>1:
        raise ValueError("contradictory demand growth measures")
    value=hits[0]
    if code=="HAYS":
        value=-abs(value)
    # Observe reported restructuring/FX/acquisition effects, but never
    # use net profit to classify demand.
    caution_terms={
        "cost_reductions": bool(re.search(r"cost action|cost sav|restructur|productivity initiatives",text,re.I)),
        "m_and_a": bool(re.search(r"acquisition|acquired|merger|business disposals",text,re.I)),
        "currency":bool(re.search(r"constant currenc|foreign exchange|FX\b",text,re.I)),
    }
    return {
        "company":code,"period_end":period.isoformat(),
        "published_date":published.isoformat(),
        "publication_date_in_document":verified_date,
        "source_url":url,"origin":"original_issuer_IR_pdf" if code=="PAGEGROUP" else "issuer_IR",
        "document_sha256":source_sha256,
        "demand_measure":release["basis"],"value_pct":value,
        "measurement_label":release["label"],"effects_to_review":caution_terms,
        "other_reported_demand_measures":"not_extracted_unverified",
        "historical_vintage_status":"current_issuer_snapshot_not_original_asof_archive",
        "source_status":"issuer_document_parsed", "notification_authorized":False,
    }


def collect(now:datetime|None=None,fetcher=read_url)->dict:
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("timezone-aware run required")
    today=now.astimezone(timezone.utc).date()
    accepted,errors={},{}
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures={}
        for code in RELEASES:
            url=RELEASES[code]["url"]
            # In tests, a supplied fake fetcher acts as the controlled HTML/text
            # fixture. Production fetches the one actual issuer PDF.
            if code=="PAGEGROUP" and fetcher is read_url:
                future=pool.submit(fetch_official_pdf,url,12)
            else:
                future=pool.submit(fetcher,url,12)
            futures[future]=code
        for fut in as_completed(futures):
            code=futures[fut]
            try:
                fetched=fut.result()
                if code=="PAGEGROUP" and fetcher is read_url:
                    doc, sha=fetched
                else:
                    doc, sha=fetched, None
                accepted[code]=extract(code,doc,today,source_sha256=sha)
            except (OSError,UnicodeError,ValueError,KeyError,TypeError) as exc:
                errors[code]=type(exc).__name__+": "+str(exc)[:180]
    complete=len(accepted)==5
    # This is breadth of positive reported fee/revenue direction only,
    # NOT a calibrated global staffing pulse or a crisis forecast.
    breadth=(100*sum(r["value_pct"]>0 for r in accepted.values())/5
             if complete else None)
    return {
        "schema":SCHEMA,"as_of_date_utc":today.isoformat(),
        "status":"complete" if complete else "partial",
        "issuer_reports":dict(sorted(accepted.items())),
        "missing":sorted(set(RELEASES)-set(accepted)), "errors":errors,
        "positive_fee_revenue_direction_breadth_pct":breadth,
        "breadth_definition":"simple 5-issuer positive comparable direction share, NOT demand-volume weighting or forecast-calibrated",
        "staffing_global_score":None, "staffing_global_score_status":"not_calibrated",
        "notification_authorized":False, "risk_alert_role":"context_only",
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    args=p.parse_args()
    output=collect()
    write_if_changed(args.root/"data/staffing_ir_context.json",output)
    print(json.dumps({"status":output["status"],"available":list(output["issuer_reports"]),
                      "missing":output["missing"],"errors":output["errors"],
                      "breadth_pct":output["positive_fee_revenue_direction_breadth_pct"],
                      "notification_authorized":False},sort_keys=True))
    # Keep partial real evidence without falsifying five-of-five coverage.
    # Research workflow can still process other sources; missing IR is an
    # operational data-quality incident, not a systemic crisis.
    if not output["issuer_reports"]:
        raise SystemExit(2)


if __name__=="__main__":
    main()

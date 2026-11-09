"""PBOC 2026Q3 credit from official Shanghai-government PBOC report republications.

These copies are official-government distribution, NOT the PBOC's first
original release/vintage. Never confuse mortgage balance (stock), household
long-term flow, nonmortgage consumption balance, developer-received mortgages
or government bonds within total TSF. One Q3 point is not a private-credit impulse.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from .cli import ROOT, write_if_changed
from .collect import read_url
from .nbs import VisibleText

FINANCIAL="https://jrj.sh.gov.cn/SCGK194/20261015/24a15f78c09947de9eb58a48c2fdb451.html"
CREDIT="https://jrj.sh.gov.cn/SCDT197/20261029/ef0635afddcd4b73a684a2c1e10ec846.html"
ORIGINS={"financial":FINANCIAL,"credit":CREDIT}
SCHEMA="fcews.pboc_official_republication.v1"


def exact_source(url: str,kind: str)->bool:
    try:
        p=urlsplit(url)
        return (url==ORIGINS[kind] and p.scheme=="https" and p.hostname=="jrj.sh.gov.cn"
                and p.username is None and p.password is None and p.port in (None,443))
    except (ValueError,KeyError,TypeError):
        return False


def compact(raw: str)->str:
    p=VisibleText()
    p.feed(raw)
    return re.sub(r"\s+","", "".join(p.parts).replace("\u3000",""))


def strict_one(text:str,pattern:str)->float:
    matches=re.findall(pattern,text)
    if not matches or len({float(v) for v in matches})!=1:
        raise ValueError("PBOC metric missing or ambiguous: "+pattern[:80])
    return float(matches[0])


def meta(text:str,kind:str,today:date)->date:
    if "信息来源：中国人民银行" not in text:
        raise ValueError("not an official government republication of PBOC")
    m=re.search(r"发布时间[:：](20\d{2})-(\d{2})-(\d{2})",text)
    if not m:
        raise ValueError("republication date missing")
    pub=date(*map(int,m.groups()))
    if not date(2026,9,30)<=pub<=today:
        raise ValueError("PBOC source not published at evaluation date")
    title=("2026年前三季度金融统计数据报告" if kind=="financial"
           else "2026年三季度金融机构贷款投向统计报告")
    if title not in text:
        raise ValueError("wrong PBOC original report title")
    return pub


def parse_financial(raw:str,today:date,url:str=FINANCIAL)->dict:
    if not exact_source(url,"financial"):
        raise ValueError("untrusted government financial statistics URL")
    text=compact(raw)
    published=meta(text,"financial",today)
    cut=text[text.index("五、前三季度人民币贷款增加11.52万亿元"):]
    household=strict_one(cut,r"住户贷款减少(\d+(?:\.\d+)?)万亿元")
    short=strict_one(cut,r"短期贷款减少(\d+(?:\.\d+)?)万亿元")
    mlt=strict_one(cut,r"中长期贷款增加(\d+(?:\.\d+)?)亿元")
    company_mlt=strict_one(cut,r"企（事）业单位贷款增加\d+(?:\.\d+)?万亿元，其中，短期贷款增加\d+(?:\.\d+)?万亿元，中长期贷款增加(\d+(?:\.\d+)?)万亿元")
    bill=strict_one(cut,r"票据融资增加(\d+(?:\.\d+)?)万亿元")
    tsf=strict_one(text,r"社会融资规模增量累计为(\d+(?:\.\d+)?)万亿元")
    gov=strict_one(text,r"政府债券净融资(\d+(?:\.\d+)?)万亿元")
    loans=strict_one(text,r"对实体经济发放的人民币贷款增加(\d+(?:\.\d+)?)万亿元")
    if min(tsf,gov,loans,mlt,short,household,company_mlt,bill)<0 or gov>=tsf:
        raise ValueError("impossible PBOC credit mix")
    if abs((-household)-(-short+mlt/10000))>0.05:
        raise ValueError("PBOC household tenor flows do not reconcile")
    return {
        "source_url":url,"republication_date":published.isoformat(),
        "period_end":"2026-09-30","frequency":"2026_year_to_date",
        "household_total_ytd_flow_trillion_cny":-household,
        "household_short_ytd_flow_trillion_cny":-short,
        "household_medium_long_ytd_flow_100m_cny":mlt,
        "corporate_medium_long_ytd_flow_trillion_cny":company_mlt,
        "corporate_bill_financing_ytd_flow_trillion_cny":bill,
        "total_social_financing_ytd_flow_trillion_cny":tsf,
        "gov_bond_social_financing_ytd_flow_trillion_cny":gov,
        "rmb_lending_to_real_economy_ytd_flow_trillion_cny":loans,
        "gov_bond_fraction_of_tsf_pct":round(100*gov/tsf,2),
        "private_credit_impulse":None,
        "original_PBOC_publication_timestamp":None,
        "publication_provenance":"official_shanghai_government_republication_of_PBOC_not_original_vintage",
    }


def parse_credit(raw:str,today:date,url:str=CREDIT)->dict:
    if not exact_source(url,"credit"):
        raise ValueError("untrusted PBOC loan allocation source")
    text=compact(raw)
    published=meta(text,"credit",today)
    start=text.index("六、房地产贷款有所放缓")
    end=text.index("七、贷款支持科创企业",start)
    block=text[start:end]
    mort=re.search(r"个人住房贷款余额(\d+(?:\.\d+)?)万亿元，同比下降(\d+(?:\.\d+)?)%，前三季度减少(\d+(?:\.\d+)?)万亿元",block)
    dev=re.search(r"房地产开发贷款余额(\d+(?:\.\d+)?)万亿元，同比下降(\d+(?:\.\d+)?)%，前三季度减少(\d+(?:\.\d+)?)亿元",block)
    if mort is None or dev is None:
        raise ValueError("PBOC personal mortgage/developer loan breakdown missing")
    hh=text[text.index("八、住户经营性贷款同比小幅增长"):]
    business=re.search(r"经营性贷款余额(\d+(?:\.\d+)?)万亿元，同比增长(\d+(?:\.\d+)?)%，前三季度增加(\d+(?:\.\d+)?)亿元",hh)
    nonmort=re.search(r"不含个人住房贷款的消费性贷款余额(\d+(?:\.\d+)?)万亿元，同比下降(\d+(?:\.\d+)?)%，前三季度减少(\d+(?:\.\d+)?)亿元",hh)
    if business is None or nonmort is None:
        raise ValueError("PBOC household business/nonmortgage consumption missing")
    return {
        "source_url":url,"republication_date":published.isoformat(),
        "period_end":"2026-09-30","frequency":"quarter_end_stock_plus_YTD_net_flow",
        "individual_mortgage_balance_trillion_cny":float(mort.group(1)),
        "individual_mortgage_balance_yoy_pct":-float(mort.group(2)),
        "individual_mortgage_ytd_net_change_trillion_cny":-float(mort.group(3)),
        "real_estate_developer_LOAN_balance_trillion_cny":float(dev.group(1)),
        "real_estate_developer_LOAN_balance_yoy_pct":-float(dev.group(2)),
        "household_business_loan_balance_trillion_cny":float(business.group(1)),
        "household_business_loan_yoy_pct":float(business.group(2)),
        "household_nonmortgage_consumption_balance_trillion_cny":float(nonmort.group(1)),
        "household_nonmortgage_consumption_yoy_pct":-float(nonmort.group(2)),
        "new_individual_mortgage_originations":None,
        "mortgage_prepayment_volume":None,
        "mlt_consumption_loan_ytd_flow":None,
        "statistical_entity":"bank_loan_balance_not_NBS_developer_received_funding",
        "original_PBOC_publication_timestamp":None,
        "publication_provenance":"official_shanghai_government_republication_of_PBOC_not_original_vintage",
    }


def collect(now:datetime|None=None,fetcher=read_url)->dict:
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("timezone-aware evaluation required")
    today=now.astimezone(timezone.utc).date()
    finance=parse_financial(fetcher(FINANCIAL,12),today)
    allocation=parse_credit(fetcher(CREDIT,12),today)
    if finance["period_end"]!=allocation["period_end"]:
        raise ValueError("PBOC releases have mismatched reporting periods")
    return {
        "schema":SCHEMA,"as_of_date_utc":today.isoformat(),"status":"complete",
        "period_end":finance["period_end"],
        "financial_statistics":finance, "loan_allocation":allocation,
        "housing_turning_point_confirmed":False,
        "housing_turning_point_reason":"Individual mortgage stock is declining and no monthly new-origination/prepayment decomposition exists.",
        "china_recovery_breadth_score":None,"private_credit_impulse":None,
        "source_quality":"government_republication_not_original_first_publication_vintage",
        "risk_alert_authorized":False,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    args=p.parse_args()
    out=collect()
    write_if_changed(args.root/"data/pboc_credit_context.json",out)
    print(json.dumps({
        "status":out["status"],"period_end":out["period_end"],
        "mortgage_balance_yoy":out["loan_allocation"]["individual_mortgage_balance_yoy_pct"],
        "government_share_tsf_pct":out["financial_statistics"]["gov_bond_fraction_of_tsf_pct"],
        "household_mlt_ytd_100m":out["financial_statistics"]["household_medium_long_ytd_flow_100m_cny"],
        "user_alert_authorized":False},sort_keys=True))


if __name__=="__main__":
    main()

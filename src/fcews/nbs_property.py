"""Original NBS China property data: ALL 70 cities and developer volume/funding.

Data are price indices (last month = 100), not percent returns or a
nationwide mean. Developer-received mortgage funds are NOT household mortgage
balances, and cumulative YoY rates cannot be mixed with monthly price levels.
Fail closed on incomplete tables, stale dates or unexpected official HTML.
"""
from __future__ import annotations

import argparse
import calendar
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from .cli import ROOT, write_if_changed
from .collect import read_url
from .nbs import OfficialLinks, VisibleText

INDEX = "https://www.stats.gov.cn/sj/zxfb/"
# Official URLs are discovery fallbacks, NOT synthetic data. Always fetch and
# read the original document and reject any stale fallback after 80 days.
SEEDS = {
    "price": (
        "https://www.stats.gov.cn/sj/zxfb/202610/t20261019_1965609.html",
        "https://www.stats.gov.cn/sj/zxfb/202609/t20260915_1965304.html",
    ),
    "market": (
        "https://www.stats.gov.cn/sj/zxfb/202610/t20261019_1965615.html",
        "https://www.stats.gov.cn/sj/zxfb/202609/t20260915_1965310.html",
    ),
}
PRICE_TITLE = re.compile(r"(20\d{2})年(\d{1,2})月份?70个大中城市商品住宅销售价格变动情况")
MARKET_TITLE = re.compile(r"(20\d{2})年1[—–-](\d{1,2})月份?全国房地产市场基本情况")
PUBLISHED = re.compile(r"(20\d{2})[/-](\d{1,2})[/-](\d{1,2})\s+\d{1,2}:\d{2}")
CITIES = tuple("""北京 天津 石家庄 太原 呼和浩特 沈阳 大连 长春 哈尔滨 上海 南京 杭州 宁波 合肥 福州 厦门 南昌 济南 青岛 郑州 武汉 长沙 广州 深圳 南宁 海口 重庆 成都 贵阳 昆明 西安 兰州 西宁 银川 乌鲁木齐 唐山 秦皇岛 包头 丹东 锦州 吉林 牡丹江 无锡 徐州 扬州 温州 金华 蚌埠 安庆 泉州 九江 赣州 烟台 济宁 洛阳 平顶山 宜昌 襄阳 岳阳 常德 韶关 湛江 惠州 桂林 北海 三亚 泸州 南充 遵义 大理""".split())
assert len(CITIES) == 70 and len(set(CITIES)) == 70
CITY_RE = re.compile("(" + "|".join(sorted(map(re.escape, CITIES), key=len, reverse=True)) + r")((?:\d{2,3}\.\d){3})")
TRIPLET = re.compile(r"(\d{2,3}\.\d)(\d{2,3}\.\d)(\d{2,3}\.\d)")
SCHEMA = "fcews.nbs_property.v1"


def official_page(url: str) -> bool:
    try:
        p = urlsplit(url)
        return (p.scheme == "https" and p.hostname in {"www.stats.gov.cn", "stats.gov.cn"}
                and p.username is None and p.password is None and p.port in {None,443}
                and bool(re.fullmatch(r"/sj/(?:zxfb|zxfbhjd)/20\d{4}/t20\d{6}_\d+\.html", p.path)))
    except (ValueError, TypeError):
        return False


def compact_html(raw: str) -> str:
    parser = VisibleText()
    parser.feed(raw)
    # NBS puts spaces between Chinese characters of certain city names.
    return re.sub(r"\s+", "", "".join(parser.parts).replace("\u3000", ""))


def checked_date(raw: str, now: date) -> date:
    parser = VisibleText()
    parser.feed(raw)
    m = PUBLISHED.search(" ".join(parser.parts))
    if not m:
        raise ValueError("official NBS publication datetime missing")
    published = date(*map(int,m.groups()))
    if published > now:
        raise ValueError("future NBS release")
    return published


def discover(index_html: str, kind: str, today: date) -> list[str]:
    if kind not in ("price", "market"):
        raise ValueError("unknown NBS property report type")
    parser = OfficialLinks()
    parser.feed(index_html)
    rx = PRICE_TITLE if kind == "price" else MARKET_TITLE
    results = []
    for href, label in parser.links:
        label = re.sub(r"\s+", "", label)
        m = rx.fullmatch(label)
        if not m:
            continue
        year, month = map(int, m.groups())
        if not (1 <= month <= 12 and date(year,month,1) <= today):
            continue
        url = urljoin(INDEX, href)
        if official_page(url):
            results.append(((year,month),url))
    results.sort(reverse=True)
    return [url for _,url in results[:2]]


def parse_prices(raw: str, url: str, today: date) -> dict:
    if not official_page(url):
        raise ValueError("not an official 70-city article")
    published = checked_date(raw, today)
    text = compact_html(raw)
    m = PRICE_TITLE.search(text)
    if not m:
        raise ValueError("NBS 70-city release title missing")
    year, month = map(int,m.groups())
    period = date(year,month,calendar.monthrange(year,month)[1])
    if period > published or (today-period).days > 80:
        raise ValueError("70-city report unavailable or stale")
    markers = (
        re.search(r"表1[:：]?(?:20\d{2}年)?\d{1,2}月70个大中城市新建商品住宅销售价格指数",text),
        re.search(r"表2[:：]?(?:20\d{2}年)?\d{1,2}月70个大中城市二手住宅销售价格指数",text),
        re.search(r"表3[:：]?",text),
    )
    if any(x is None for x in markers) or not markers[0].start() < markers[1].start() < markers[2].start():
        raise ValueError("70-city table boundaries missing")
    tables = {}
    for kind, section in (("new", text[markers[0].end():markers[1].start()]),
                          ("used",text[markers[1].end():markers[2].start()])):
        cities = {}
        for match in CITY_RE.finditer(section):
            city = match.group(1)
            # Underlying table uses one decimal per monthly/yearly index.
            values = TRIPLET.fullmatch(match.group(2))
            if not values or city in cities:
                raise ValueError("duplicate city or malformed NBS index")
            mom,yoy,avg = map(float,values.groups())
            if not all(65 <= x <= 145 for x in (mom,yoy,avg)):
                raise ValueError("impossible 70-city price index")
            cities[city] = {"mom_index":mom, "yoy_index":yoy, "ytd_avg_index":avg}
        if set(cities) != set(CITIES):
            raise ValueError("70-city table incomplete/unknown city: " + kind +
                             f" (valid {len(cities)}/70)")
        tables[kind] = {
            "city_count": len(cities),
            "mom_rising": sum(v["mom_index"] > 100 for v in cities.values()),
            "mom_flat": sum(v["mom_index"] == 100 for v in cities.values()),
            "mom_falling":sum(v["mom_index"] < 100 for v in cities.values()),
            "yoy_rising":sum(v["yoy_index"] > 100 for v in cities.values()),
            "cities":dict(sorted(cities.items())),
        }
        if sum(tables[kind][k] for k in ("mom_rising","mom_flat","mom_falling")) != 70:
            raise ValueError("city count reconciliation failed")
    return {"source_url":url, "published_date":published.isoformat(),
            "period_end":period.isoformat(), "month":f"{year:04d}-{month:02d}",
            "new":tables["new"], "used":tables["used"],
            "unit":"index_previous_month_equals_100", "origin":"NBS", "status":"complete"}


def signed_change(raw: str) -> float:
    m = re.fullmatch(r"(增长|下降)(\d+(?:\.\d+)?)%",raw)
    if not m:
        raise ValueError("ambiguous rate expression")
    return round(float(m.group(2)) * (1 if m.group(1)=="增长" else -1),4)


def required_rate(text: str, pattern: str) -> float:
    matches = re.findall(pattern,text)
    if len(matches)!=1:
        raise ValueError(f"NBS expected one unique occurrence of {pattern!r}, found {len(matches)}")
    return signed_change(matches[0])


def parse_market(raw: str,url: str,today: date) -> dict:
    if not official_page(url):
        raise ValueError("nonofficial NBS property market URL")
    published=checked_date(raw,today)
    text=compact_html(raw)
    m=MARKET_TITLE.search(text)
    if not m:
        raise ValueError("NBS national property title missing")
    year,month=map(int,m.groups())
    period=date(year,month,calendar.monthrange(year,month)[1])
    if period>published or (today-period).days>80:
        raise ValueError("property release future/stale")
    # Narrative sections constrain lookalike values from the detailed tables.
    a=text.find("一、房地产开发投资完成情况")
    b=text.find("二、商品房销售和待售情况")
    c=text.find("三、房地产开发企业到位资金情况")
    d=text.find("表1")
    if min(a,b,c,d)<0 or not a<b<c<d:
        raise ValueError("NBS property report section boundaries changed")
    sales=text[b:c]
    funding=text[c:d]
    residential_area=required_rate(sales,r"其中住宅销售面积(增长\d+(?:\.\d+)?%|下降\d+(?:\.\d+)?%)")
    residential_value=required_rate(sales,r"其中住宅销售额(增长\d+(?:\.\d+)?%|下降\d+(?:\.\d+)?%)")
    price_inventory=required_rate(sales,r"新建商品房待售面积\d+万平方米，同比(增长\d+(?:\.\d+)?%|下降\d+(?:\.\d+)?%)")
    money={}
    for key,word in (("developer_domestic_loans","国内贷款"),
                     ("developer_self_financing","自筹资金"),
                     ("developer_deposits_advance","定金及预收款"),
                     ("developer_received_mortgages","个人按揭贷款")):
        match=re.search(re.escape(word)+r"(\d+)亿元，(增长\d+(?:\.\d+)?%|下降\d+(?:\.\d+)?%)",funding)
        if not match:
            raise ValueError("missing developer cash-flow category "+word)
        money[key]={"amount_100m_cny":int(match.group(1)),
                    "cumulative_yoy_pct":signed_change(match.group(2)),
                    "statistical_entity":"developer_received_funds_not_household_credit"}
    return {
        "source_url":url,"published_date":published.isoformat(),
        "period_end":period.isoformat(),"period_type":"year_to_date_cumulative",
        "residential_sales_area_yoy_pct":residential_area,
        "residential_sales_value_yoy_pct":residential_value,
        "new_homes_unsold_area_yoy_pct":price_inventory,
        "developer_funding":money,
        "credit_warning":"Developer mortgage receipts are NOT PBOC household mortgage balances; prepayment and operating-loan flows unobserved.",
        "origin":"NBS","status":"complete",
    }


def fetch_pair(kind: str,index_html: str,now:date,fetcher) -> list[dict]:
    urls=discover(index_html,kind,now)
    for fallback in SEEDS[kind]:
        if fallback not in urls:
            urls.append(fallback)
    outputs={}
    errors={}
    for url in urls[:4]:
        if not official_page(url):
            continue
        try:
            raw=fetcher(url,12)
            record=parse_prices(raw,url,now) if kind=="price" else parse_market(raw,url,now)
            # Do not silently overwrite conflicting versions of same period.
            period=record["period_end"]
            if period in outputs and record!=outputs[period]:
                raise ValueError("same-period conflicting NBS releases require review")
            outputs[period]=record
        except (OSError,ValueError,TypeError) as exc:
            errors[url]=type(exc).__name__+": "+str(exc)[:180]
    results=sorted(outputs.values(),key=lambda r:r["period_end"],reverse=True)
    if not results:
        raise ValueError("no official verified NBS "+kind+" source: "+json.dumps(errors))
    if len(results)<2:
        raise ValueError("two verified monthly NBS "+kind+" releases required for trend comparison: "+json.dumps(errors))
    # A site index that contains a future release must not be drowned by stale seeds.
    if (now-date.fromisoformat(results[0]["period_end"])).days>80:
        raise ValueError("newest property report stale")
    return results[:2]


def collect(now:datetime|None=None,fetcher=read_url)->dict:
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("timezone-aware evaluation required")
    today=now.astimezone(timezone.utc).date()
    index=fetcher(INDEX,12)
    prices=fetch_pair("price",index,today,fetcher)
    market=fetch_pair("market",index,today,fetcher)
    same_period=prices[0]["period_end"]==market[0]["period_end"]
    # Used-home price diffusion is the more relevant national breadth signal.
    # Cumulative sales area YoY may change even when monthly sales fall.
    signals={
        "used_price_rising_city_count_change":prices[0]["used"]["mom_rising"]-prices[1]["used"]["mom_rising"],
        "new_price_rising_city_count_change":prices[0]["new"]["mom_rising"]-prices[1]["new"]["mom_rising"],
        "residential_sales_cumulative_yoy_pp_change":round(market[0]["residential_sales_area_yoy_pct"]-market[1]["residential_sales_area_yoy_pct"],4),
        "developer_mortgage_receipts_yoy_pp_change":round(market[0]["developer_funding"]["developer_received_mortgages"]["cumulative_yoy_pct"]-market[1]["developer_funding"]["developer_received_mortgages"]["cumulative_yoy_pct"],4),
        "unsold_area_yoy_pp_change":round(market[0]["new_homes_unsold_area_yoy_pct"]-market[1]["new_homes_unsold_area_yoy_pct"],4),
    }
    return {
        "schema":SCHEMA,"as_of_date_utc":today.isoformat(),
        "status":"complete" if same_period else "incomparable_periods",
        "latest_prices":prices[0],"previous_prices":prices[1],
        "latest_market":market[0],"previous_market":market[1],
        "directional_signals":signals,
        "housing_turning_point_confirmed":False,
        "housing_turning_point_reason":"PBOC household mortgage new lending/balance cross-check absent; developer-received mortgage funds do not substitute.",
        "china_recovery_breadth_score":None,
        "risk_alert_role":"context_only_no_independent_systemic_family",
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    options=p.parse_args()
    output=collect()
    write_if_changed(options.root/"data/nbs_property_context.json",output)
    print(json.dumps({"status":output["status"],
                      "period":output["latest_prices"]["period_end"],
                      "new_rising":output["latest_prices"]["new"]["mom_rising"],
                      "used_rising":output["latest_prices"]["used"]["mom_rising"],
                      "developer_mortgage_not_household":True,
                      "turning_point_confirmed":False},sort_keys=True))
    if output["status"]!="complete":
        raise SystemExit(2)


if __name__=="__main__":
    main()

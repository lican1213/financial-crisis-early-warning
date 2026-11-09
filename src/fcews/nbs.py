"""Auto-read the current official NBS China manufacturing PMI release.

Unlike a user-entered URL/number pair, this adapter retrieves the original
stats.gov.cn article and extracts the observations in the manufacturing section.
Publication date and survey month are distinct. No private-sector credit or
nationwide property turning point is inferred from PMI.
"""
from __future__ import annotations

import argparse
import calendar
import json
import re
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from .cli import ROOT, write_if_changed
from .collect import read_url

INDEX = "https://www.stats.gov.cn/sj/zxfbhjd/"
TITLE = re.compile(r"(20\d{2})年(\d{1,2})月(?:份)?中国采购经理指数运行情况")
PUBLISHED = re.compile(r"(20\d{2})[/-](\d{1,2})[/-](\d{1,2})\s+\d{1,2}:\d{2}")
SCHEMA = "fcews.nbs_official_pmi.v1"


class OfficialLinks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.current = None
        self.parts = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a" and self.current is None:
            self.current = dict(attrs).get("href")
            self.parts = []

    def handle_data(self, data):
        if self.current is not None:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.current is not None:
            self.links.append((self.current, "".join(self.parts).strip()))
            self.current = None
            self.parts = []


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.ignored = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.ignored += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.ignored > 0:
            self.ignored -= 1

    def handle_data(self, data):
        if not self.ignored:
            self.parts.append(data)


def valid_article(url: str) -> bool:
    try:
        p = urlsplit(url)
        return (p.scheme == "https" and p.hostname in ("www.stats.gov.cn", "stats.gov.cn")
                and p.username is None and p.password is None and p.port in (None, 443)
                and p.path.startswith("/sj/zxfbhjd/")
                and bool(re.search(r"/t\d{8}_\d+\.html$", p.path)))
    except (TypeError, ValueError):
        return False


def discover_pmi(index_html: str, today: date) -> tuple[str, int, int]:
    parser = OfficialLinks()
    parser.feed(index_html)
    possible = []
    for href, label in parser.links:
        label = re.sub(r"\s+", "", label)
        m = TITLE.fullmatch(label)
        if not m:
            continue
        year, month = int(m.group(1)), int(m.group(2))
        if not (1 <= month <= 12) or (year, month) > (today.year, today.month):
            continue
        url = urljoin(INDEX, href)
        if not valid_article(url):
            continue
        possible.append((year, month, url))
    if not possible:
        raise ValueError("NBS official index lists no valid current manufacturing PMI release")
    year, month, url = max(possible)
    if (today - date(year, month, 1)).days > 80:
        raise ValueError("NBS PMI index only exposes an obsolete release")
    return url, year, month


def parse_pmi(article_html: str, url: str, year: int, month: int, today: date) -> dict:
    if not valid_article(url):
        raise ValueError("nonofficial PMI article URL")
    parser = VisibleText()
    parser.feed(article_html)
    raw = "".join(parser.parts)
    raw = raw.replace("\u3000", "").replace("\xa0", "")
    published_match = PUBLISHED.search(raw)
    if published_match is None:
        raise ValueError("NBS official publication timestamp not found")
    pub = date(*map(int, published_match.groups()))
    period_end = date(year, month, calendar.monthrange(year, month)[1])
    if not period_end <= pub <= today:
        raise ValueError("release was unavailable as of run date")
    compact = re.sub(r"\s+", "", raw)
    if not TITLE.search(compact):
        raise ValueError("article does not match official PMI title")
    # Restrict extraction to the manufacturing section. The nonmanufacturing
    # section contains another 'new orders' value that MUST NOT be mixed in.
    start = compact.find("一、中国制造业采购经理指数运行情况")
    end = compact.find("二、中国非制造业采购经理指数运行情况")
    if start < 0 or end <= start:
        raise ValueError("NBS manufacturing section boundaries changed")
    block = compact[start:end]
    patterns = {
        "NBS_PMI_MANUFACTURING": r"制造业采购经理指数[（(]PMI[）)]为([0-9]+(?:\.[0-9]+)?)%",
        "NBS_PMI_NEW_ORDERS": r"新订单指数为([0-9]+(?:\.[0-9]+)?)%",
        "NBS_PMI_SMALL": r"中、小型企业PMI分别为[0-9]+(?:\.[0-9]+)?%和([0-9]+(?:\.[0-9]+)?)%",
    }
    observations = {}
    for code, pattern in patterns.items():
        matches = re.findall(pattern, block)
        if len(matches) != 1:
            raise ValueError("missing/ambiguous NBS figure in manufacturing section: " + code)
        value = float(matches[0])
        if not 0 <= value <= 100:
            raise ValueError("out-of-range PMI")
        observations[code] = {
            "value": value, "unit": "diffusion_index_percent",
            "observation_month": f"{year:04d}-{month:02d}",
            "period_end": period_end.isoformat(),
            "published_date": pub.isoformat(),
            "source_url": url, "origin": "China_National_Bureau_of_Statistics",
            "source_validation": "live_article_section_parsed_not_independent_historical_vintage",
        }
    return {
        "schema": SCHEMA, "status": "complete", "released_at_date": pub.isoformat(),
        "source_url": url, "observations": observations,
        "interpretation": "Manufacturing PMI demand context only; no housing/credit score or crisis notification",
        "alert_authorized": False, "score_authorized": False,
    }


def collect(now: datetime | None = None, fetcher=read_url) -> dict:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now requires timezone")
    today = now.astimezone(timezone.utc).date()
    index = fetcher(INDEX, 12)
    url, year, month = discover_pmi(index, today)
    article = fetcher(url, 12)
    return parse_pmi(article, url, year, month, today)


def refresh(root: Path = ROOT, now: datetime | None = None, fetcher=read_url) -> dict:
    result = collect(now, fetcher)
    write_if_changed(root / "data/nbs_pmi_context.json", result)
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=ROOT)
    args = p.parse_args()
    value = refresh(args.root)
    print(json.dumps({"status": value["status"], "source": value["source_url"],
                      "published_date": value["released_at_date"],
                      "values": {k:v["value"] for k,v in value["observations"].items()},
                      "alert_authorized": value["alert_authorized"]}, sort_keys=True))


if __name__ == "__main__":
    main()

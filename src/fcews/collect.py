"""Official-source adapters with bounded parallel fetches and explicit source failures."""
from __future__ import annotations

import csv
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from io import StringIO
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .core import Observation

FRED_CODES = (
    "STLFSI4", "NFCI", "ANFCI", "BAMLH0A0HYM2",
    "VIXCLS", "SOFR", "TGCR", "DGS10", "DGS30",
)
NYFED_CODES = ("SOFR", "TGCR", "BGCR")
NYFED_BASE = "https://markets.newyorkfed.org/api/rates/secured/"
OFR_URL = "https://www.financialresearch.gov/financial-stress-index/data/fsi.csv"
FRED_GRAPH = "https://fred.stlouisfed.org/graph/fredgraph.csv"
FRED_API = "https://api.stlouisfed.org/fred/series/observations"
BYTES_LIMIT = 1_000_000


def read_url(url: str, timeout: float = 8.0) -> str:
    request = Request(url, headers={
        "User-Agent": "FCEWS/0.3 (+https://github.com/lican1213/financial-crisis-early-warning)",
        "Accept": "application/json,text/csv;q=0.9,*/*;q=0.5",
    })
    with urlopen(request, timeout=timeout) as response:
        result = response.read(BYTES_LIMIT + 1)
        if len(result) > BYTES_LIMIT:
            raise ValueError("response exceeds size limit")
        return result.decode("utf-8-sig")


def parse_fred_csv(series: str, content: str, retrieved_utc: str) -> Observation:
    reader = csv.DictReader(StringIO(content))
    if not reader.fieldnames or series not in reader.fieldnames:
        raise ValueError("missing FRED column " + series)
    for row in reversed(list(reader)):
        value = (row.get(series) or "").strip()
        if value in ("", ".", "NaN"):
            continue
        day = row.get("DATE") or row.get("observation_date")
        if not day:
            raise ValueError("FRED csv missing date")
        return Observation(series, day, float(value),
                           "https://fred.stlouisfed.org/series/" + series, retrieved_utc)
    raise ValueError("no numeric FRED observation " + series)


def parse_fred_json(series: str, content: str, retrieved_utc: str) -> Observation:
    document = json.loads(content)
    if "observations" not in document:
        raise ValueError("missing FRED API observations")
    for row in document["observations"]:
        if row.get("value") not in (None, "", "."):
            return Observation(series, row["date"], float(row["value"]),
                               "https://fred.stlouisfed.org/series/" + series,
                               retrieved_utc)
    raise ValueError("no numeric FRED API observation " + series)


def parse_nyfed_json(series: str, content: str, retrieved_utc: str) -> Observation:
    document = json.loads(content)
    rates = document.get("refRates")
    if not isinstance(rates, list) or not rates:
        raise ValueError("NY Fed API missing refRates")
    for row in rates:
        if row.get("effectiveDate") and row.get("percentRate") not in (None, ""):
            return Observation(
                series, row["effectiveDate"], float(row["percentRate"]),
                "https://www.newyorkfed.org/markets/reference-rates/" + series.lower(),
                retrieved_utc,
            )
    raise ValueError("NY Fed API has no usable reference rate")


def fetch_nyfed(series: str, timeout: float = 8.0) -> Observation:
    retrieved = datetime.now(timezone.utc).isoformat()
    url = NYFED_BASE + series.lower() + "/last/1.json"
    return parse_nyfed_json(series, read_url(url, timeout), retrieved)


def parse_ofr_csv(content: str, retrieved_utc: str) -> Observation:
    reader = csv.DictReader(StringIO(content))
    if not reader.fieldnames:
        raise ValueError("empty OFR CSV")
    date_key = next((k for k in reader.fieldnames if k.strip().lower() in ("date", "observation date")), None)
    value_key = next((k for k in reader.fieldnames if k.strip().lower() in ("ofr fsi", "ofr_fsi", "financial stress index")), None)
    if not date_key or not value_key:
        raise ValueError("OFR FSI schema missing date or headline index")
    valid = []
    for row in reader:
        day, raw = row.get(date_key, ""), row.get(value_key, "")
        if day and raw not in ("", ".", None):
            valid.append((day, float(raw)))
    if not valid:
        raise ValueError("OFR FSI: no numeric rows")
    day, value = max(valid)
    return Observation("OFR_FSI", day, value, OFR_URL, retrieved_utc)


def fetch_ofr(timeout: float = 8.0) -> Observation:
    return parse_ofr_csv(read_url(OFR_URL, timeout), datetime.now(timezone.utc).isoformat())


def fetch_fred(series: str, timeout: float = 8.0) -> Observation:
    retrieved = datetime.now(timezone.utc).isoformat()
    key = os.getenv("FRED_API_KEY", "").strip()
    if key:
        url = FRED_API + "?" + urlencode({
            "series_id": series, "api_key": key, "file_type": "json",
            "sort_order": "desc", "limit": 10,
        })
        return parse_fred_json(series, read_url(url, timeout), retrieved)
    url = FRED_GRAPH + "?" + urlencode({"id": series, "cosd": "2026-01-01"})
    return parse_fred_csv(series, read_url(url, timeout), retrieved)


def collect_all(timeout: float = 8.0) -> tuple[dict[str, Observation], dict[str, str]]:
    """Collect in parallel; NYFed observations replace FRED duplicates when available."""
    results: dict[str, Observation] = {}
    errors: dict[str, str] = {}
    # Dedicated NY Fed API can operate while FRED is unreachable.
    jobs = [("FRED:" + code, fetch_fred, code) for code in FRED_CODES]
    jobs += [("NYFED:" + code, fetch_nyfed, code) for code in NYFED_CODES]
    jobs.append(("OFR:OFR_FSI", lambda code, timeout: fetch_ofr(timeout), "OFR_FSI"))
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(fn, code, timeout): name for name, fn, code in jobs}
        collected: dict[str, Observation] = {}
        for future in as_completed(futures):
            name = futures[future]
            try:
                collected[name] = future.result()
            except (OSError, UnicodeError, ValueError, KeyError, TypeError) as error:
                # Never include API-key-bearing URLs or response bodies in errors.
                errors[name] = type(error).__name__ + ": " + str(error)[:120]
    for code in FRED_CODES:
        item = collected.get("FRED:" + code)
        if item:
            results[code] = item
    if collected.get("OFR:OFR_FSI"):
        results["OFR_FSI"] = collected["OFR:OFR_FSI"]
    for code in NYFED_CODES:
        item = collected.get("NYFED:" + code)
        if item and (code not in results or item.date >= results[code].date):
            results[code] = item
    return results, errors


def collect_fred(codes=FRED_CODES, timeout=8):
    """Compatibility wrapper for focused collector tests."""
    rows, errors = {}, {}
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(fetch_fred, code, timeout): code for code in codes}
        for future in as_completed(futures):
            code = futures[future]
            try:
                rows[code] = future.result()
            except (OSError, UnicodeError, ValueError, TypeError) as error:
                errors[code] = type(error).__name__ + ": " + str(error)[:120]
    return rows, errors

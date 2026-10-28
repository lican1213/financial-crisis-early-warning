"""Read dated FRED CSV observations; API key not required."""
from __future__ import annotations

import csv
from datetime import datetime, timezone
from io import StringIO
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .core import Observation

FRED_CODES = (
    "STLFSI4", "NFCI", "ANFCI", "BAMLH0A0HYM2",
    "VIXCLS", "SOFR", "TGCR", "DGS10", "DGS30",
)


def parse_fred_csv(series: str, content: str, retrieved_utc: str) -> Observation:
    reader = csv.DictReader(StringIO(content))
    if not reader.fieldnames or series not in reader.fieldnames:
        raise ValueError("missing series column: " + series)
    for row in reversed(list(reader)):
        raw = (row.get(series) or "").strip()
        if raw in ("", ".", "NaN"):
            continue
        day = row.get("DATE") or row.get("observation_date")
        if not day:
            raise ValueError("missing observation date column")
        return Observation(
            series, day, float(raw),
            "https://fred.stlouisfed.org/series/" + series,
            retrieved_utc,
        )
    raise ValueError("no numeric observations for " + series)


def collect_fred(codes=FRED_CODES, timeout=15):
    retrieved_utc = datetime.now(timezone.utc).isoformat()
    rows, errors = {}, {}
    for code in codes:
        url = "https://fred.stlouisfed.org/graph/fredgraph.csv?" + urlencode({"id": code})
        try:
            request = Request(url, headers={"User-Agent": "FCEWS/0.2 macro monitoring"})
            with urlopen(request, timeout=timeout) as response:
                content = response.read(4_000_000).decode("utf-8-sig")
            rows[code] = parse_fred_csv(code, content, retrieved_utc)
        except (OSError, UnicodeError, ValueError) as error:
            errors[code] = str(error)[:180]
    return rows, errors

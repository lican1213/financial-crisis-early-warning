"""Primary-document verification for human-reviewed contagion events.

Only source integrity and timestamp provenance are machine-verified here.
A causal contagion claim still requires an accountable human reviewer.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from urllib.parse import urlsplit
from urllib.request import build_opener, HTTPRedirectHandler, Request

TRUSTED_DOMAINS = frozenset({
    "fdic.gov", "federalreserve.gov", "newyorkfed.org", "treasury.gov",
    "financialresearch.gov", "sec.gov", "cftc.gov", "ecb.europa.eu",
    "bankofengland.co.uk", "bis.org", "imf.org", "fsb.org",
    "federalreservebank.org", "federalreservebanks.org",
    "eia.gov", "energy.gov", "esma.europa.eu", "eba.europa.eu",
})
CATEGORIES = {"bank", "fund", "sovereign", "repo", "payment", "energy", "private_credit"}
MAX_DOCUMENT_BYTES = 2_000_000


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("source redirect requires an explicitly reviewed final URL")


def trusted_url(url: str) -> bool:
    try:
        p = urlsplit(url)
        host = (p.hostname or "").lower().rstrip(".")
        return (
            p.scheme == "https" and bool(host) and p.port in (None, 443)
            and p.username is None and p.password is None and
            not p.fragment and
            any(host == d or host.endswith("." + d) for d in TRUSTED_DOMAINS)
        )
    except (ValueError, TypeError):
        return False


def retrieve_document(url: str, timeout: int = 8) -> bytes:
    if not trusted_url(url):
        raise ValueError("untrusted primary-source domain")
    request = Request(url, headers={"User-Agent": "FCEWS/0.4 source-integrity review"})
    with build_opener(NoRedirect()).open(request, timeout=timeout) as response:
        data = response.read(MAX_DOCUMENT_BYTES + 1)
    if len(data) > MAX_DOCUMENT_BYTES:
        raise ValueError("document exceeds evidence size limit")
    if not data:
        raise ValueError("empty source document")
    return data


def aware_utc(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("timestamp lacks timezone")
    return result.astimezone(timezone.utc)


def inspect_event(event: dict, now: datetime, reader=retrieve_document) -> dict:
    """Return a verified candidate or raise a source-specific failure."""
    if event.get("review_status") != "approved" or event.get("verified") is not True:
        raise ValueError("not human-approved")
    identifier = str(event.get("id", ""))
    if not re.fullmatch(r"[A-Za-z0-9._-]{4,100}", identifier):
        raise ValueError("invalid event identifier")
    if event.get("category") not in CATEGORIES:
        raise ValueError("invalid event category")
    if len(str(event.get("cross_market_mechanism", "")).strip()) < 30:
        raise ValueError("insufficiently documented contagion mechanism")
    if len(str(event.get("verified_by", "")).strip()) < 3:
        raise ValueError("missing named reviewer")
    when = aware_utc(str(event["published_at_utc"]))
    reviewed = aware_utc(str(event["verified_at_utc"]))
    now = now.astimezone(timezone.utc)
    if when > reviewed or reviewed > now:
        raise ValueError("event publication/review is in the future or out of order")
    url = str(event.get("primary_source_url", ""))
    if not trusted_url(url):
        raise ValueError("not an approved primary-source domain")
    expected = str(event.get("source_sha256", "")).lower()
    if not re.fullmatch("[0-9a-f]{64}", expected):
        raise ValueError("malformed source checksum")
    actual = hashlib.sha256(reader(url)).hexdigest()
    if actual != expected:
        raise ValueError("primary document SHA256 changed")
    return dict(event, evidence_checked_at_utc=now.isoformat(), source_sha256=actual)


def verify_events(events: list[dict], now: datetime, reader=retrieve_document):
    verified, failures = [], {}
    for event in events:
        identifier = str(event.get("id", "unknown"))
        if event.get("review_status") not in ("approved",):
            # Pending or rejected events are not source errors.
            continue
        try:
            verified.append(inspect_event(event, now, reader))
        except (ValueError, KeyError, TypeError, OSError) as error:
            failures[identifier] = type(error).__name__ + ": " + str(error)[:150]
    return verified, failures

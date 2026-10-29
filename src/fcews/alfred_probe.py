"""Diagnostic only: small requests to official ALFRED historical graph CSV.

Probe both the documented-no-key *graph* endpoint and tiny individual
requested vintages. Never treat a 404, captcha, HTML or today's fallback
column as a valid point-in-time observation.
"""
import csv
import io
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE="https://alfred.stlouisfed.org/graph/alfredgraph.csv"


def probe(fetch=None):
    reqs=[
        ("PAYEMS_reference", "PAYEMS","2026-09-04",False),
        ("PAYEMS_filtered", "PAYEMS","2026-09-04",True),
        ("VIX_2008", "VIXCLS","2008-09-12",False),
        ("VIX_2020", "VIXCLS","2020-03-13",False),
        ("HY_2008", "BAMLH0A0HYM2","2008-09-12",False),
        ("NFCI_2011", "NFCI","2011-09-09",False),
    ]
    if fetch is None:
        def fetch(url):
            headers={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/123 Safari/537.36",
                     "Accept":"text/csv,*/*;q=0.1"}
            with urlopen(Request(url,headers=headers),timeout=12) as resp:
                return resp.read(4096).decode("utf-8-sig",errors="replace")
    result={}
    for label,code,vintage,filtered in reqs:
        params={"id":code,"vintage_date":vintage}
        if filtered:
            params.update({"cosd":"2025-01-01","coed":"2026-10-28"})
        url=BASE+"?"+urlencode(params)
        try:
            raw=fetch(url)
            row=next(csv.reader(io.StringIO(raw)),[])
            expected=code+"_"+vintage.replace("-","")
            result[label]={"response":"csv" if row and row[-1]==expected else "invalid_header",
                           "header":row[:4],"expected":expected}
        except (HTTPError,URLError,ValueError,TimeoutError,OSError) as err:
            result[label]={"response":type(err).__name__,
                           "status_code":getattr(err,"code",None)}
    return result


if __name__=="__main__":
    print(json.dumps(probe(),sort_keys=True))

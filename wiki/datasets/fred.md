---
title: IF-001 through IF-005 — FRED Adapter Manifest
kind: dataset
status: active
updated: 2026-10-28
summary: Series identifiers, units, lag and known failures for the implemented FRED CSV collector.
---

# Official FRED adapter contract

**Implementation:** [`src/fcews/collect.py`](../../src/fcews/collect.py), [`src/fcews/core.py`](../../src/fcews/core.py).

**Transport:** `https://fred.stlouisfed.org/graph/fredgraph.csv?id={ID}`; read-only public CSV. The FRED connector redistributes several agencies' series; **original publisher** should remain a metadata field. **Credentials:** no key in current CSV implementation. **Retries:** not implemented. **Timeout:** 15 seconds per series; running all serially may exceed the GitHub 12-minute job only if external network becomes pathologically slow. **Schema:** CSV DATE, series-code column; `.` missing; take latest numeric observation; parse timestamp on ingestion.

| IF | Series | Publisher | Unit / cadence | Decision role | Critical known issue |
| --- | --- | --- | --- | --- | --- |
| IF-001 | [STLFSI4](https://fred.stlouisfed.org/series/STLFSI4) | St. Louis Fed | Index; weekly | System pressure | Revised / delayed |
| IF-001 | [NFCI](https://fred.stlouisfed.org/series/NFCI) | Chicago Fed | Index; weekly | Same system family | Not independent of ANFCI |
| IF-001 | [ANFCI](https://fred.stlouisfed.org/series/ANFCI) | Chicago Fed | Index; weekly | Same system family | Revised / delayed |
| IF-002 | [BAMLH0A0HYM2](https://fred.stlouisfed.org/series/BAMLH0A0HYM2) | ICE BofA via FRED | **Percent**; daily | Credit | 6.0 = 600bp |
| IF-003 | [VIXCLS](https://fred.stlouisfed.org/series/VIXCLS) | Cboe via FRED | Index; daily | Volatility | Close not live futures term structure |
| IF-004 | [SOFR](https://fred.stlouisfed.org/series/SOFR) | NY Fed via FRED | **Percent**; daily | Funding paired TGCR | Dates must match |
| IF-004 | [TGCR](https://fred.stlouisfed.org/series/TGCR) | NY Fed via FRED | **Percent**; daily | Funding paired SOFR | Repo basket coverage incomplete |
| IF-005 | [DGS10](https://fred.stlouisfed.org/series/DGS10) | Federal Reserve | Percent; daily | Context | Not a direct crisis threshold |
| IF-005 | [DGS30](https://fred.stlouisfed.org/series/DGS30) | Federal Reserve | Percent; daily | Context | Not a direct crisis threshold |

**Current freshness logic:** weekly source readings accepted up to 15 calendar days old; other inputs up to seven days. This is a technical heuristic, not validated against specific release calendars. The collector may record FRED's most recent revised series rather than its initial version.

**Data QA:** reject non-numeric, out-of-range future date, stale observations and SOFR/TGCR mismatch. Test [core unit tests](../../tests/test_core.py). Missing data should be visible in diagnostics and excluded from independent-family count; if service fails, do not silently claim no financial risk.

**Current deployment verification:** unverified; check [Issue #1](https://github.com/lican1213/financial-crisis-early-warning/issues/1). The FRED service's historical licensing/access terms and rate limits have not yet been independently recorded.

Related: [registry](registry.md), [PIT concept](../concepts/point-in-time.md).

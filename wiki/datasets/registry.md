---
title: Financial Data Interface Registry
kind: dataset
status: active
updated: 2026-10-28
summary: Single catalog of implemented, experimental and missing official-source data interfaces.
---

# Interface registry

Interfaces are technical contracts with separate observation, publication and ingestion timestamps.

**Authoritative source directory:** [Federal Reserve Economic Data (FRED)](https://fred.stlouisfed.org/), with original publisher and observation-level provenance recorded in the [FRED adapter manifest](fred.md). **Implemented** means code exists, not that the live scheduled job has been independently verified.

| ID | Source / family | Status 2026-10-28 | Owner / implementation |
| --- | --- | --- | --- |
| IF-001 | FRED: STLFSI4/NFCI/ANFCI | Code implemented; live unverified | [FRED manifest](fred.md) |
| IF-002 | FRED: BAMLH0A0HYM2 | Code implemented; live unverified | [FRED manifest](fred.md) |
| IF-003 | FRED: VIXCLS | Code implemented; live unverified | [FRED manifest](fred.md) |
| IF-004 | FRED + NY Fed SOFR/TGCR/BGCR | **Live 2026-10-29** | [FRED manifest](fred.md) |
| IF-005 | FRED: DGS10/DGS30 | Context-only implementation | [FRED manifest](fred.md) |
| IF-006 | OFR FSI | **Live 2026-10-29** | [Official feeds](official-pending.md) |
| IF-007 | MOVE / VIX futures term structure | Planned | [Official feeds](official-pending.md) |
| IF-008 | Repo SRF, dealer Treasury liquidity | Planned | [Official feeds](official-pending.md) |
| IF-009 | Bank/non-bank/sovereign/energy contagion events | Manual `events.json` candidate only | [Event schema](events.md) |
| IF-010 | Private credit and real estate redemption telemetry | Planned | [Official feeds](official-pending.md) |

Source code: [collector](../../src/fcews/collect.py), [decision engine](../../src/fcews/core.py). Working state: [handoff](../operations/HANDOFF.md).

### Standard dataset fields (target schema)
`id`, `publisher`, `official_url`, `transport`, `series_id`, `unit`, `frequency`, `observation_date`, `first_available_at_utc`, `retrieved_at_utc`, `vintage_id`, `revised`, `latency`, `licence`, `family`, `alert_role`, `fallback_policy`, `last_verified_run`, `quality_test`, `failure_mode`.

A value without verified first-availability metadata may be used for a *current context check* but not a scientifically valid historical lead-time result.

### Interface change protocol
Open Issue → verify official endpoint/schema/units → fake fixture test → current-source check → PIT publication alignment → update manifest + Issue + changelog → rerun regression tests. Data outage remains visible in diagnostics; don't replace it with a fabricated value.

## Official source verification (2026-10-29)
- [OFR FSI official CSV](https://www.financialresearch.gov/financial-stress-index/data/fsi.csv) succeeded in [GitHub Actions 40788157364](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40788157364), observation date 2026-10-26. It counts in the **same systemic family** as NFCI/STLFSI, not an additional independent signal.
- [NY Fed market API](https://markets.newyorkfed.org/static/docs/markets-api.html): SOFR, TGCR and BGCR returned current official reference-rate observations and overcame one redundant FRED TGCR HTTP error.
- [FRED official](https://fred.stlouisfed.org/) CSV fallback succeeded for eight of nine requested series. FRED_API_KEY enables the official JSON observations endpoint if configured; no credentials are stored in GitHub.
- Results are in [live health](../../data/health.json) and [source observations](../../data/observations.json). First-seen timestamps are not actual publisher release timestamps; for historical research use PIT archives and release calendars.

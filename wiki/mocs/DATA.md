---
title: MOC — Data Lineage and Interfaces
kind: moc
status: active
updated: 2026-11-09
summary: Navigation map from risk claims to source, units, publication lag and adapter.
---

# MOC — data lineage

- [Interface master registry](../datasets/registry.md): all feeds, status and version.
- [FRED adapter contract](../datasets/fred.md): series IDs, percent-vs-bp, revisions.
- [Planned OFR/MOVE/repo/energy interfaces](../datasets/official-pending.md): sources not yet operational.
- [Event-evidence schema](../datasets/events.md): bank/fund/sovereign/energy cases.
- [Source-dated leading research and anti-lookahead evidence ledger](../datasets/leading-research.md): staffing, rates, China price/volume/mortgage and credit, no spoofed releases.
- [Point-in-time interpretation](../concepts/point-in-time.md): observation date ≠ availability date.
- [Source-provenance method](../sources/llm-wiki-methods.md): compile once with citations, revise transparently.

Never fill missing observations with reassuring zeroes or use the latest revised historical value as the original publication.

Related: [MOC risk](RISK.md), [MOC engineering](ENGINEERING.md).

## Current official feeds and historical evidence (2026-10-29)
- [OFR repo](../../data/stfm_context.json), [ECB CISS](../../data/ecb_ciss_context.json), [FDIC failure review](../../data/fdic_review.json), and [Cboe implied-vol plus VX contracts](../../data/volatility_context.json).
- [Actual revised-history analysis](../../reports/expost_latest.json) versus [ALFRED as-of 404 diagnostics](../../reports/alfred_smoke.json). Do not confuse ex-post with PIT.
- [Monitoring cadence](../../docs/operations/CADENCE.md), [model-failure counterexamples](../operations/INCIDENTS.md) and [data interface registry](../datasets/registry.md).

## 2026-11-06 data health qualification

[Live observation audit](../../src/fcews/quality.py) measures weekday lag against daily and weekly source-specific grace windows; it does not assert the official release date or use market stress thresholds. [Collection reconciliation](../../src/fcews/cli.py) distinguishes a redundant FRED SOFR/TGCR failure recovered from NY Fed from a truly missing rate, keeping both error lists. The four required live independent families must all be present for `healthy`; three means at most `partial`, even if the cached data preserve earlier risk context. [Operational specification](../../docs/operations/CADENCE.md).


### Source coverage expansion — NBS housing + issuer staffing (2026-11-09)
See [leading-research interface](../datasets/leading-research.md), [70-city full-table parser](../../src/fcews/nbs_property.py), [issuer IR adapter](../../src/fcews/staffing_ir.py) and [red-team regression](../../tests/test_nbs_property.py). Grain is city×month×price-type, YTD sales/unsold/developer funding by month-end report, or issuer×quarter×measure, **not** an interchangeable single weekly datapoint. Missing PBOC original mortgage credit and genuine corporate hiring volume still prevent calibrated national-turning-point or global Staffing Pulse claims.

### PBOC personal mortgage vs medium-long flow and TSF (2026-11-09)
[Official-government PBOC report parser](../../src/fcews/pboc_credit.py) now distinguishes *original agency*, *government redistribution*, *publication*, *reporting period*, *loan stock*, *YTD flow*, *government share in total TSF* and *not yet validated PIT original vintage*. [Full contract](../datasets/leading-research.md) and [falsification tests](../../tests/test_pboc_credit.py). No substitution of NBS developer receipts for PBOC personal mortgage balances.

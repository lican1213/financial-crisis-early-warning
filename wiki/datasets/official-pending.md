---
title: IF-006 through IF-010 — Pending Official Data Feeds
kind: dataset
status: planned
updated: 2026-10-28
summary: Audited wishlist for key financial stress feeds that must not be represented as operational.
---

# Planned interface contracts

| IF | Prospective primary source | Desired fields | Current status / failure mode |
| --- | --- | --- | --- |
| IF-006 OFR FSI | [US OFR](https://www.financialresearch.gov/financial-stress-index/) | official level, history, publisher release timestamp, revisions, component family | no adapter or verified terms; overlapping system risk family |
| IF-007 MOVE | [ICE Data Indices](https://www.ice.com/market-data/indices) | as-of level, distribution or authorized alternative, units, usage rights | data license/source availability unresolved |
| IF-007 VIX futures | [Cboe VIX](https://www.cboe.com/tradable_products/vix/) | dated futures maturities, F1/F2 and front-end inversion, official publication | not connected; never infer term structure from spot VIX |
| IF-008 NY Fed repo | [NY Fed Markets](https://www.newyorkfed.org/markets/) | SRF operations, repo benchmarks, trade date, publication | partial SOFR/TGCR only |
| IF-008 Treasury | [US Treasury](https://home.treasury.gov/) | maturity yield/auction tails; for depth use verified market feeds | daily DGS10/DGS30 are not Treasury order-book depth |
| IF-009 banking | [FDIC](https://www.fdic.gov/), [Fed](https://www.federalreserve.gov/), [ECB](https://www.ecb.europa.eu/) | primary resolution/liquidity action, date, counterparties, contagion proof | manual event record only |
| IF-010 private credit | fund / regulator disclosure, [SEC](https://www.sec.gov/) | redemption gating, asset-level write-down, leverage, bank exposures | unnormalized, prospective only |
| IF-010 energy | government/energy operators, [EIA](https://www.eia.gov/) | verified outage location, throughput loss and duration | rumors are not verified outages |

**Implementation checklist:** verify real endpoint and permissions; store source document or URL + hash, first-public timestamp and time zone, observation period, unit, effective rule, revision policy, outage path. Add fixtures for numerical error and false alarm. A market-data website being listed here does not imply a free API.

Current work: [Issue #2](https://github.com/lican1213/financial-crisis-early-warning/issues/2). Cross-market event standard: [events contract](events.md).

## 2026-10-29 status change
OFR FSI and NY Fed secured-rate API have moved into **operational** adapters, demonstrated by [real run 40788157364](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40788157364). The earlier table above is retained as a historical pre-implementation inventory, not an accurate live status list. Consult [current registry](registry.md). MOVE pricing and licensing, VIX full futures curve, Treasury order-book liquidity and bank/fund private-credit event feeds remain unresolved under [Issue #2](https://github.com/lican1213/financial-crisis-early-warning/issues/2).

## Source limitations updated 2026-10-29
[ICE MOVE publisher](https://www.ice.com/market-data/indices): licensed, no authorized feed; Cboe VX and Treasury realized-rate volatility cannot substitute for it. [Cboe real futures](../../data/volatility_context.json), [ECB CISS](../../data/ecb_ciss_context.json), [FDIC failures](../../data/fdic_review.json) and [OFR repo](../../data/stfm_context.json) have genuine official API observations.
[Public ALFRED as-of smoke](../../reports/alfred_smoke.json) failed HTTP 404 across all four series. The authenticated FRED API vintage exporter needs an authorized API key and source timing audit. Historical full-run automatic retries are disabled until the endpoint works. Private credit fund redemption, UST market depth, intraday MOVE and complete systemic institutional stress feeds remain out of automatic coverage.

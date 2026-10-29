---
title: MOC — Data Lineage and Interfaces
kind: moc
status: active
updated: 2026-10-28
summary: Navigation map from risk claims to source, units, publication lag and adapter.
---

# MOC — data lineage

- [Interface master registry](../datasets/registry.md): all feeds, status and version.
- [FRED adapter contract](../datasets/fred.md): series IDs, percent-vs-bp, revisions.
- [Planned OFR/MOVE/repo/energy interfaces](../datasets/official-pending.md): sources not yet operational.
- [Event-evidence schema](../datasets/events.md): bank/fund/sovereign/energy cases.
- [Point-in-time interpretation](../concepts/point-in-time.md): observation date ≠ availability date.
- [Source-provenance method](../sources/llm-wiki-methods.md): compile once with citations, revise transparently.

Never fill missing observations with reassuring zeroes or use the latest revised historical value as the original publication.

Related: [MOC risk](RISK.md), [MOC engineering](ENGINEERING.md).

## Current official feeds and historical evidence (2026-10-29)
- [OFR repo](../../data/stfm_context.json), [ECB CISS](../../data/ecb_ciss_context.json), [FDIC failure review](../../data/fdic_review.json), and [Cboe implied-vol plus VX contracts](../../data/volatility_context.json).
- [Actual revised-history analysis](../../reports/expost_latest.json) versus [ALFRED as-of 404 diagnostics](../../reports/alfred_smoke.json). Do not confuse ex-post with PIT.
- [Monitoring cadence](../../docs/operations/CADENCE.md), [model-failure counterexamples](../operations/INCIDENTS.md) and [data interface registry](../datasets/registry.md).

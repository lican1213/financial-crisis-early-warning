---
title: FCEWS Wiki Master Index
kind: index
status: active
updated: 2026-11-09
summary: Entry point for the financial crisis early-warning knowledge base and operational memory.
---

# FCEWS Second Brain — master index

**Start here every session.** Operational reality is determined by code, tests, Actions and Issues, not by a persuasive model summary.

## Reading order / session resume
1. [Handoff and current version](operations/HANDOFF.md)
2. [Open work and GitHub Issues](tasks.md)
3. [Failure register and incidents](operations/INCIDENTS.md)
4. [Activity timeline](log.md)
5. [Agent schema](schema.md) and [system synthesis](overview.md)

## Maps of Content
- [MOC: Financial risk and alert decisions](mocs/RISK.md)
- [MOC: Data lineage and connectors](mocs/DATA.md)
- [MOC: Engineering and validation](mocs/ENGINEERING.md)
- [MOC: Delivery, operations and continuity](mocs/DELIVERY.md)

## Concept pages
- [Independent indicator families](concepts/stress-families.md)
- [Four-condition alert contract](concepts/alert-contract.md)
- [Point-in-time measurement](concepts/point-in-time.md)

## Interface and source registers
- [Data interface registry](datasets/registry.md)
- [FRED source adapter](datasets/fred.md)
- [Pending official data interfaces](datasets/official-pending.md)
- [Event evidence contract](datasets/events.md)
- [LLM-Wiki methodology source](sources/llm-wiki-methods.md)
- [Open-source implementation references](sources/reference-projects.md)

## Operational memory and decisions
- [Decision ADR-0001: GitHub/wiki truth boundaries](decisions/ADR-0001.md)
- [Decision ADR-0002: Alert gate and incident discipline](decisions/ADR-0002.md)
- [Decision ADR-0003: Retire weekly pushes; integrate source-gated research](decisions/ADR-0003.md)
- [Maintenance routine](operations/MAINTENANCE.md)
- [Event and failure register](operations/INCIDENTS.md)
- [Current handoff](operations/HANDOFF.md)
- [Tasks / roadmap](tasks.md)
- [Append-only log](log.md)
- [Knowledge conventions](schema.md)
- [Living system thesis](overview.md)

## Directory navigation (topic-level indexes)
- [MOC directory](mocs/_index.md)
- [Concept directory](concepts/_index.md)
- [Source interface directory](datasets/_index.md)
- [External source directory](sources/_index.md)
- [Architecture decision directory](decisions/_index.md)
- [Operations directory](operations/_index.md)

## Release snapshot
- **Code**: `pyproject.toml` v0.4.0; official OFR, FRED and NY Fed four-family monitoring with candidate GitHub outbox; the 2026-11-06 branch adds source-health and cadence audits (verify remote CI/merge in the latest handoff).
- **Wiki**: MOC structure, failure register and append-only history; **not** an improvement in forecast calibration.
- **Current blockers**: GitHub best-effort hourly scheduling with verified long gaps, original-release PIT coverage and threshold calibration, licensed ICE MOVE/Treasury market depth, authenticated end-user delivery receipt.
- **Canonical task tracker**: [repository Issues](https://github.com/lican1213/financial-crisis-early-warning/issues).
- **Raw runtime snapshots**: [data directory](../data/), not an encyclopedic wiki.

## Monitoring cycle and maintenance table
- [Authoritative hourly / daily / weekly / monthly cadence](../docs/operations/CADENCE.md) — live workflows, silent alerts, release reconciliation and model audit.

## Source model
Read provenance before answering: publication date vs observation date vs first available timestamp vs retrieval time. Never retroactively treat a revised series as what traders knew on that date.

## Latest 2026-10-29 MOC cross-links
- [Refreshed hourly/daily/weekly/monthly cycle](../docs/operations/CADENCE.md).
- [OFR repo](../data/stfm_context.json), [ECB CISS](../data/ecb_ciss_context.json), [FDIC official review](../data/fdic_review.json), [Cboe VIX/VX futures](../data/volatility_context.json).
- [Revised-history actual data](../reports/expost_latest.json), [ALFRED as-of 404 manifest](../reports/alfred_smoke.json), [red-team failures](operations/INCIDENTS.md).
- [Handoff and true test acceptance](operations/HANDOFF.md); [live GitHub Issues](tasks.md).

## Latest 2026-11-06 reliability cross-links
- [Operational schedule/freshness specification](../docs/operations/CADENCE.md), [FAIL-033–037](operations/INCIDENTS.md) and [verified project comparables](sources/reference-projects.md).
- [Engineering tests](../tests/test_integration.py), [run-gap tests](../tests/test_schedule_health.py), [weekdays-age tests](../tests/test_quality.py), and [latest deployment handoff](operations/HANDOFF.md).

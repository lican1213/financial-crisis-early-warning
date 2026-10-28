---
title: FCEWS Wiki Master Index
kind: index
status: active
updated: 2026-10-28
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
- **Code**: v0.2, FRED-backed rules engine with tests; initial rollout recorded 2026-10-28.
- **Wiki**: v0.3 knowledge schema and MOCs; not equivalent to model forecasting upgrade.
- **Current blockers**: unverified Actions execution, uncali­brated PIT thresholds, external OFR/MOVE interfaces, ChatGPT delivery.
- **Canonical task tracker**: [repository Issues](https://github.com/lican1213/financial-crisis-early-warning/issues).
- **Raw runtime snapshots**: [data directory](../data/), not an encyclopedic wiki.

## Source model
Read provenance before answering: publication date vs observation date vs first available timestamp vs retrieval time. Never retroactively treat a revised series as what traders knew on that date.

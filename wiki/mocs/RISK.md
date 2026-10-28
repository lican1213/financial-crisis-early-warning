---
title: MOC — Financial Risk and Alert Decisions
kind: moc
status: active
updated: 2026-10-28
summary: Routes risk interpretation questions without restating data or code.
---

# MOC — systemic risk

- **What triggers a notification?** [Four-condition contract](../concepts/alert-contract.md), [current implementation](../../src/fcews/core.py).
- **Why independent evidence?** [Risk families and proxies](../concepts/stress-families.md), [dataset registry](../datasets/registry.md).
- **What could fool a historical backtest?** [Point-in-time discipline](../concepts/point-in-time.md), [validation protocol](../../docs/moc/BACKTEST.md).
- **How are bank/fund incidents grounded?** [Event source contract](../datasets/events.md), [unresolved incidents](../operations/INCIDENTS.md).
- **What is still unverified?** [System overview](../overview.md), [handoff](../operations/HANDOFF.md).

Decision sequence: observe → confirm source/first availability → classify family/event contagion → compare state and weekly baseline → fire once or remain silent. Risk labels are ordinal and cannot be interpreted as fitted probabilities.

Related: [MOC data](DATA.md), [MOC delivery](DELIVERY.md).

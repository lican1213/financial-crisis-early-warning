---
title: MOC — Engineering and Validation
kind: moc
status: active
updated: 2026-10-28
summary: Guides development, tests, failures and evidence-backed completion.
---

# MOC — engineering

- [Agent working contract](../../AGENTS.md), [wiki schema](../schema.md).
- [Project tasks](../tasks.md): GitHub Issues canonical status and acceptance.
- [Handoff state](../operations/HANDOFF.md): verified code and blockers.
- [Failure and adversarial cases](../operations/INCIDENTS.md).
- [Maintenance and quality checklist](../operations/MAINTENANCE.md).
- [ADR-0001](../decisions/ADR-0001.md): avoid competing status databases.
- [ADR-0002](../decisions/ADR-0002.md): alert operational boundaries.
- [Historical test protocol](../../docs/moc/BACKTEST.md); [tests](../../tests/test_core.py).
- [External implementation lessons](../sources/reference-projects.md).

Any threshold, family or event-verification change needs at least one test intended to **disprove** the new rule. Record negative outcomes rather than overengineering hypothetical exceptions.

Related: [MOC data](DATA.md), [MOC delivery](DELIVERY.md).

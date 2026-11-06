---
title: MOC — Engineering and Validation
kind: moc
status: active
updated: 2026-11-06
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

## 2026-11-06 reliability patch

The active code gates are [source/fallback health](../../src/fcews/cli.py), [source age](../../src/fcews/quality.py), and [GitHub scheduled-run audit](../../src/fcews/schedule_health.py). Regression evidence: [integration](../../tests/test_integration.py), [quality](../../tests/test_quality.py), [schedule health](../../tests/test_schedule_health.py), and [baseline](../../tests/test_weekly_context.py). The schedule audit checks **actual successful cron runs**, not only configured YAML. Review [FAIL-033–037](../operations/INCIDENTS.md) for falsification and unresolved platform constraints. No financial risk threshold or independent-family membership was changed.

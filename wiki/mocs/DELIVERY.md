---
title: MOC — Delivery and Continuity
kind: moc
status: active
updated: 2026-10-28
summary: Routes runbooks, daily checks, notification semantics and next-agent context.
---

# MOC — operations

- [Handoff](../operations/HANDOFF.md): source of truth for what actually ran.
- [Maintenance](../operations/MAINTENANCE.md): session, daily, weekly, incident checks.
- [Incidents/failures](../operations/INCIDENTS.md): open risks and remediation proof.
- [Taskboard](../tasks.md): Issues for execution and closures.
- [Change log](../log.md): project changes, not one log entry per hourly poll.
- [Alert gate](../concepts/alert-contract.md): GitHub candidate ≠ external user notification.
- [Interface catalog](../datasets/registry.md): coverage and known absences.

When a session resumes, confirm default branch HEAD, open Issues, CI state, last successful data timestamp and whether notifications were actually delivered; never infer from README claims.

Related: [MOC engineering](ENGINEERING.md).

## Cadence, 2026-10-29
[Hourly/daily/weekly/monthly schedule](../../docs/operations/CADENCE.md) records exact UTC and Beijing times, Action owner, persistent run evidence, weekly risk-grade reconciliation, and monthly out-of-sample audit. GitHub candidate issues are separate from end-user ChatGPT notifications. [Recent source run](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40788157364).

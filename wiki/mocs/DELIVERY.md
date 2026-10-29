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

## Verified delivery and cadence (2026-10-29)
- [GitHub integration canary #11](https://github.com/lican1213/financial-crisis-early-warning/issues/11) created/read/closed as a non-crisis test.
- Existing ChatGPT hourly/weekly task prompts read GitHub source snapshots; no GitHub webhook can directly deliver ChatGPT responses in this deployment.
- [Hour/day/week/month cycle](../../docs/operations/CADENCE.md) and [operational handoff](../operations/HANDOFF.md). All unverified data-health or regulator-review failures remain separate from crisis notifications.

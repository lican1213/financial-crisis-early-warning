---
title: FCEWS Task Dashboard
kind: taskboard
status: active
updated: 2026-10-28
summary: Navigational work queue; live GitHub Issues are authoritative for status and acceptance.
---

# Work queue — authoritative task state in GitHub Issues

This page is a **dated view** (2026-10-28), not a second source of status. Open each Issue to see current assignment, blocking dependencies, discussion and proof of completion.

| Priority | Task | Completion proof |
| --- | --- | --- |
| P0 | [#4 Verify hourly Action end-to-end](https://github.com/lican1213/financial-crisis-early-warning/issues/4) | Successful Actions run, evidence commit, intentional silent run |
| P0 | [#5 Point-in-time historical backtest](https://github.com/lican1213/financial-crisis-early-warning/issues/5) | Timestamped vintage data, untouched chronological holdout, missed/false alerts |
| P1 | [#6 Official OFR/MOVE/repo/Treasury sources](https://github.com/lican1213/financial-crisis-early-warning/issues/6) | Sources, adapter tests, normalized units, lags |
| P1 | [#7 Event verification / contagion registry](https://github.com/lican1213/financial-crisis-early-warning/issues/7) | Primary evidence readback and adversarial rumor test |
| P1 | [#8 Weekly baseline and delivery integration](https://github.com/lican1213/financial-crisis-early-warning/issues/8) | Reconciled baseline and deduplicated actual delivery |
| P1 | [#9 Second brain MOC and lint](https://github.com/lican1213/financial-crisis-early-warning/issues/9) | Committed wiki, test results, link audit and Agent startup |

Also inspect [all Issues](https://github.com/lican1213/financial-crisis-early-warning/issues), including earlier issues #1–#3, rather than assuming the above is exhaustive.

## Execution loop
Pick an Issue → test/verify preconditions → implement → adversarial tests → run CI/wiki lint → update source manifests and related MOCs → append [log](log.md) → update [handoff](operations/HANDOFF.md) → close Issue **only on evidence**.

## Dependency order
P0 operational truth (#4) before claiming hourly protection; PIT backtesting (#5) before raising confidence in thresholds; source adapters (#6) and event provenance (#7) before extending coverage; notification integration (#8) after gate stability. Documentation and lint (#9) run alongside all changes.

For project rationale read [engineering MOC](mocs/ENGINEERING.md).

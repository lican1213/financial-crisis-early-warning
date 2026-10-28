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
| P0 | [#1 Verify hourly Action end-to-end](https://github.com/lican1213/financial-crisis-early-warning/issues/1) | Successful Actions run, evidence commit, intentional silent run |
| P0 | [#3 Point-in-time historical backtest](https://github.com/lican1213/financial-crisis-early-warning/issues/3) | Timestamped vintage data, untouched chronological holdout, missed/false alerts |
| P1 | [#2 Official OFR/MOVE/repo/Treasury sources](https://github.com/lican1213/financial-crisis-early-warning/issues/2) | Sources, adapter tests, normalized units, lags |
| P1 | [#7 Event verification / contagion registry](https://github.com/lican1213/financial-crisis-early-warning/issues/7) | Primary evidence readback and adversarial rumor test |
| P1 | [#8 Weekly baseline and delivery integration](https://github.com/lican1213/financial-crisis-early-warning/issues/8) | Reconciled baseline and deduplicated actual delivery |
| P1 | [#9 Second brain MOC and lint](https://github.com/lican1213/financial-crisis-early-warning/issues/9) | Committed wiki, test results, link audit and Agent startup |

**Deduplicated 2026-10-28:** #1 supersedes #4; #3 supersedes #5; #2 supersedes #6. Original acceptance criteria were merged into the earlier Issues; duplicates were closed with history preserved. [All Issues](https://github.com/lican1213/financial-crisis-early-warning/issues).

## Execution loop
Pick an Issue → test/verify preconditions → implement → adversarial tests → run CI/wiki lint → update source manifests and related MOCs → append [log](log.md) → update [handoff](operations/HANDOFF.md) → close Issue **only on evidence**.

## Dependency order
P0 operational truth (#1) before claiming hourly protection; PIT backtesting (#3) before raising confidence in thresholds; source adapters (#2) and event provenance (#7) before extending coverage; notification integration (#8) after gate stability. Documentation and lint (#9) run alongside all changes.

For project rationale read [engineering MOC](mocs/ENGINEERING.md).

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
| Done | [#9 Second brain MOC and lint](https://github.com/lican1213/financial-crisis-early-warning/issues/9) | Committed wiki, test results, link audit and Agent startup |

**Deduplicated 2026-10-28:** #1 supersedes #4; #3 supersedes #5; #2 supersedes #6. Original acceptance criteria were merged into the earlier Issues; duplicates were closed with history preserved. [All Issues](https://github.com/lican1213/financial-crisis-early-warning/issues).

## Execution loop
Pick an Issue → test/verify preconditions → implement → adversarial tests → run CI/wiki lint → update source manifests and related MOCs → append [log](log.md) → update [handoff](operations/HANDOFF.md) → close Issue **only on evidence**.

## Dependency order
P0 operational truth (#1) before claiming hourly protection; PIT backtesting (#3) before raising confidence in thresholds; source adapters (#2) and event provenance (#7) before extending coverage; notification integration (#8) after gate stability. Documentation and lint (#9) run alongside all changes.

For project rationale read [engineering MOC](mocs/ENGINEERING.md).

## Completed MOC structure follow-up
- [#10 Topic-level directory indexes and negative lint tests](https://github.com/lican1213/financial-crisis-early-warning/issues/10): 6 topic _index.md files, two adversarial fixtures, [passing CI #40719684672](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40719684672). Issue status is authoritative and must be checked from GitHub.

## Progress checkpoint — 2026-10-29
- [#1](https://github.com/lican1213/financial-crisis-early-warning/issues/1): live 11-source successful Actions [#40788157364](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40788157364). Another verification of unchanged-data quiet behavior and first new scheduled run is required before closing.
- [#2](https://github.com/lican1213/financial-crisis-early-warning/issues/2): OFR FSI and NY Fed repo-reference rate adapters working; MOVE, VIX future curve, Treasury depth, and institution-level nonbank sources outstanding.
- [#3](https://github.com/lican1213/financial-crisis-early-warning/issues/3): strict first-public-timestamp replay engine and anti-future-revision tests; full original-vintage event data and calibrated walk-forward accuracy pending.
- [#7](https://github.com/lican1213/financial-crisis-early-warning/issues/7): source hash, reviewer identity and explicit approval are now required for a reviewed candidate, but code cannot authenticate a claimed document without fetching it.
- [#8](https://github.com/lican1213/financial-crisis-early-warning/issues/8): GitHub candidate issues are retriable and deduped; no authenticated ChatGPT push bridge. [Monitoring cycle table](../docs/operations/CADENCE.md).

## 2026-10-29 objective acceptance update
- [#1 Hourly monitor](https://github.com/lican1213/financial-crisis-early-warning/issues/1): push-trigger real source runs and non-crisis GitHub canary verified, but a new-version hourly schedule-triggered execution remains unverified.
- [#2 Additional sources](https://github.com/lican1213/financial-crisis-early-warning/issues/2): ECB CISS, OFR STFM, FDIC, Cboe index and monthly VX official feeds verified. ICE MOVE licensing and Treasury live depth remain unfulfilled.
- [#3 Historical validation](https://github.com/lican1213/financial-crisis-early-warning/issues/3): genuine revised-FRED diagnostic plus pre-2007 BAA10Y historical proxy, 2011 and 2023 misses; ALFRED initial batch 404 then partial 11/20 public as-of cells; only 20% three-family coverage, full historical holdout still blocked.
- [#7 Primary event review](https://github.com/lican1213/financial-crisis-early-warning/issues/7): source SHA, official-host restriction, timestamps and reviewer plus FDIC review-only queue built; a real reviewed contagion case remains untested.
- [#8 Delivery](https://github.com/lican1213/financial-crisis-early-warning/issues/8): GitHub Issue create/readback/close canary [#11](https://github.com/lican1213/financial-crisis-early-warning/issues/11) verified, existing ChatGPT automations pull GitHub. Signed push webhook and common calibrated severity scale remain absent.
[117 passing tests](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40801824139); [updated cycle table](../docs/operations/CADENCE.md). Retain all unresolved acceptance criteria.

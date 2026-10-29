---
title: FCEWS Agent Handoff — Current Verified State
kind: operations
status: active
updated: 2026-10-28
summary: Short restart checkpoint with precise version, outstanding validation, risks and next tasks.
---

# Agent handoff — read before coding

**Project:** [lican1213/financial-crisis-early-warning](https://github.com/lican1213/financial-crisis-early-warning)
**Owner:** linked GitHub account
**Visibility as observed:** PUBLIC (2026-10-28); no personal financial data or secrets.
**Repository version:** FCEWS model v0.2.0; second-brain wiki schema v0.3.1 (topic index hardening).
**Last verified code+wiki commit:** [9fb89fc](https://github.com/lican1213/financial-crisis-early-warning/commit/9fb89fcfc9e3211d35dc6bd1a84366b711da0dd9) (documentation-only follow-up commits need their own CI readback).
**Code commit:** [b217c71](https://github.com/lican1213/financial-crisis-early-warning/commit/b217c71f17b4b29e84464e7ec7ff44abc06c9ff1).
**Verification:** latest [GitHub Actions #40719684672](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40719684672) succeeded: **28/28 tests; wiki lint PASS for 29 pages**. Earlier failed [#40719452896](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40719452896) preserved in FAIL-014. Scheduled hourly monitor with real FRED ingestion remains **unverified**; PIT backtest and ChatGPT push integration remain open.

## Known working implementation
FRED public CSV request and parser; pure decision gate; four indicator families; draft candidate alert GitHub issue; GitHub workflow YAML; state persistence. Some tests exist and assertions are not equivalent to live source validation.

## Canonical tasks
Issues #1, #2 and #3 are canonical; overlapping #4–#6 were closed as duplicates with merged acceptance criteria. Consult the live GitHub tracker before creating another task.

## Priority next session
1. Read [taskboard](../tasks.md) and [FAIL register](INCIDENTS.md); inspect real GitHub Actions status; reproduce scheduled/manual runs [#1](https://github.com/lican1213/financial-crisis-early-warning/issues/1).
2. Remove or mitigate statistical/operational defects exposed by a source-provenance adversarial audit [#3](https://github.com/lican1213/financial-crisis-early-warning/issues/3).
3. Add official OFR / market depth / repo / volatility feeds with interface-by-interface QA [#2](https://github.com/lican1213/financial-crisis-early-warning/issues/2).
4. Introduce canonical event provenance and safe notification linkage [#7](https://github.com/lican1213/financial-crisis-early-warning/issues/7), [#8](https://github.com/lican1213/financial-crisis-early-warning/issues/8).
5. Keep wiki lint enabled and MOC updated [#9](https://github.com/lican1213/financial-crisis-early-warning/issues/9).

## State discipline
No duplicate full reports on calm runs. Freshness is not first availability. A green technical score is not proof of global financial stability. Current repo public status requires user-controlled GitHub Settings change if private desired.

**Handoff checklist:** update commit SHA, latest successful test and Actions URLs, current open P0 Issues, interface IDs newly verified, known false positives, exact next action; append [project log](../log.md). If uncertain, say 'not verified'.

## Directory-index maintenance addition
A MOC completeness audit after CI #40718526292 identified missing topic-level _index.md pages. Added them and strengthened lint / fixtures; verify the new GitHub CI run before closing the documentation task. Source of truth for current task status: [Issues](https://github.com/lican1213/financial-crisis-early-warning/issues).

## Verification checkpoint for directory-index hardening
Commit [0867151e](https://github.com/lican1213/financial-crisis-early-warning/commit/0867151e95f440cbe6b0a94f00bdcabbe4c5d008) added six indexes and two new falsification tests. Its [CI #40719452896](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40719452896) failed in a fixture because a folder was created twice (27 pass, 1 error); fix recorded in FAIL-014. The next run must pass unit tests and wiki lint before Issue #10 can close.

## Latest CI readback
The directory index + fixture repair is verified: [run 40719684672](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40719684672) reports 28 passed tests and a 29-page wiki lint PASS. Documentation maintenance [#10](https://github.com/lican1213/financial-crisis-early-warning/issues/10) may close with this acceptance evidence. This is **not** evidence that the hourly market monitor has run.

## 2026-10-29 verified operational checkpoint — v0.3
- [Real GitHub workflow 40788157364](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40788157364) SUCCESS: 11 dated official observations across four stress families; FRED TGCR transient HTTP error recovered from NYFed reference API. No user financial-crisis notification.
- [Latest real check 40788555440](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40788555440) SUCCESS; operation is no longer simulated. Existing periodic scheduling is managed by GitHub Actions and the separate original ChatGPT automation.
- The source collector uses FRED public CSV with optional FRED_API_KEY JSON access, OFR FSI CSV, NY Fed SOFR/TGCR/BGCR. Health distinguishes fresh live sources from cached observations and documents failure separately from calm market readings.
- PIT replay with published-at timestamps, recoverable issue outbox and health-incident dedup implemented. No complete crisis-vintage backtest or ChatGPT push integration, licensed MOVE or market-depth feed yet. [Cadence](../../docs/operations/CADENCE.md).
- **Current tests:** 53-test adversarial suite; [CI 40788555417](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40788555417) found a remaining int/float difference in the stable evidence SHA despite normalized cached data. Corrected stable snapshot serialization; verify new CI before claiming PASS.
- Canonical open work: [#1](https://github.com/lican1213/financial-crisis-early-warning/issues/1) live scheduled verification and deliberate unchanged poll, [#2](https://github.com/lican1213/financial-crisis-early-warning/issues/2) licensed additional sources, [#3](https://github.com/lican1213/financial-crisis-early-warning/issues/3) historical PIT test, [#7](https://github.com/lican1213/financial-crisis-early-warning/issues/7) event auth, [#8](https://github.com/lican1213/financial-crisis-early-warning/issues/8) real user notification delivery.

## Verified 2026-10-29 restart checkpoint — v0.4
[117 passing code/adversarial tests and 29-page MOC lint](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40801824139). Real [ECB/OFR/FDIC context check](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40801545198) and [Cboe volatility check](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40801824156). Cboe official 2026-10-28 front VX 18.5982, second 18.7752, F2-F1 +0.177 (no futures backwardation); genuine MOVE data licensed/unavailable. [Test GitHub Issue #11](https://github.com/lican1213/financial-crisis-early-warning/issues/11) created/readback/closed; this is not an actual financial alert delivery.
Original Sunday 2026-10-25 six-module watch grade orange 66/100 is stored in [weekly baseline](../../data/weekly_baseline.json); four-family green technical readings are not a comparable automatic downgrade.
[Revised FRED historical report](../../reports/expost_latest.json): 2011/2023 missed; high-yield OAS public truncated history; pre-2007 BAA10Y credit proxy only as an ex-post sensitivity. [ALFRED public-vintage attempt](../../reports/alfred_smoke.json): initial batch requests returned HTTP 404; later per-date probing accepted 11/20 as-of series-date cells, with just 20% of checkpoints showing three-family source coverage. Automatic expensive full as-of runs suspended; manual retry with valid authorized endpoint only.
Next gates: [#1 current schedule-run](https://github.com/lican1213/financial-crisis-early-warning/issues/1), [#2 licensed market depth/MOVE](https://github.com/lican1213/financial-crisis-early-warning/issues/2), [#3 authentic historical PIT](https://github.com/lican1213/financial-crisis-early-warning/issues/3), [#7 reviewed event](https://github.com/lican1213/financial-crisis-early-warning/issues/7), [#8 delivery and scale comparability](https://github.com/lican1213/financial-crisis-early-warning/issues/8). [Cadence](../../docs/operations/CADENCE.md).

Latest evidence: [partial ALFRED public as-of smoke](https://github.com/lican1213/financial-crisis-early-warning/blob/main/reports/alfred_smoke.json) accepted VIXCLS 4/5, NFCI 4/5, STLFSI4 2/5, HY OAS 1/5 across five dates; 20% three-family coverage. This is **not** a complete historical PIT backtest.

## 2026-10-29 — live v0.5 feed and historical coverage handoff
- [GitHub read-only ChatGPT feed](../../data/chatgpt_feed.json) generated and verified with candidate_count=0, health=partial, technical severity=green while weekly six-factor watch=orange; they are *not* calibrated on one scale. User's existing hourly condition-watch automation enabled; its prompt explicitly prioritizes feed and source evidence and requires four strict systemic triggers, otherwise true silence. No webhook or end-user receipt.
- Official [Cboe daily context](../../data/volatility_context.json) includes as-of 2026-10-28 VIX9D/VIX/VIX3M/VIX6M, real VX monthly F1=18.5982, F2=18.7752 (contango), and UST realized yield vol. ICE MOVE licensed quote not available.
- Real [public ALFRED smoke report](../../reports/alfred_smoke.json): VIXCLS and NFCI 4/5, STLFSI4 2/5, HY OAS 1/5 selected as-of snapshots; old summary claiming 0 snapshots is superseded. Historical full-weekly job [Actions 40802656579](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40802656579) started; inspect latest status and do not call it successful before completion.
- [Coverage audit](../../src/fcews/coverage.py) and negative fixtures distinguish false negatives with three independent vintage families, partial two-family events and non-assessable events. No calibrated prediction probabilities or historical trading claims.
- [Cycle table](../../docs/operations/CADENCE.md) updated. Highest remaining: original ICE MOVE subscription and Treasury order-depth rights, complete audited PIT history, authenticated push event/receipt rather than hourly poll.

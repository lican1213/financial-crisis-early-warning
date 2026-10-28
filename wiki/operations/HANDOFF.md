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

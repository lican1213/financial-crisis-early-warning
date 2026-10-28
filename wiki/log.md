---
title: FCEWS Project Operation Log
kind: log
status: active
updated: 2026-10-28
summary: Append-only developer and agent actions; runtime checkpoints are stored separately.
---

# Project log (append only)

## 2026-10-28 — initialize repository
Repository `lican1213/financial-crisis-early-warning` created under linked GitHub account. Public visibility observed. Code initial bootstrap committed.

## 2026-10-28 — v0.2 source-dated monitoring prototype
Deployed Python FRED collector, pure alert decision gate, persistent state, candidate GitHub Issue workflow and regression tests. The source-dated collector was **not** validated against actual GitHub Actions production execution or point-in-time data vintage. Reference: [legacy changelog](../docs/moc/CHANGELOG.md).

## 2026-10-28 — MOC second-brain implementation
Reviewed [nvk/llm-wiki AGENTS.md](sources/llm-wiki-methods.md) and [cobusgreyling/llm-wiki](sources/llm-wiki-methods.md). Added topic MOCs, provenance and dataset records, operational handoff, task routing and executable wiki lint checks. Created GitHub Issues #4–#9 for unclosed work. Added ADRs and a failure register. **Commit and CI verification must be recorded in handoff after merge**.

## Rule
Append new dated operations. Never silently rewrite older observations to make results appear successful. Every significant change names tests, actual commit or run URL, and the still-open work. Unchanged hourly polling belongs in Actions logs; only changed material snapshots belong in version control.

## 2026-10-28 — initial MOC CI falsification and repair
GitHub [Actions run 40718335555](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40718335555) executed 26/26 unit/adversarial tests successfully, but the structural lint failed: `wiki/datasets/registry.md` lacked an explicit external source reference. Recorded the failure rather than ignoring it; added the FRED official source registry link, updated incident and handoff. Lint retest on the next commit is the completion gate.

## 2026-10-28 — passing CI, canonical task consolidation
[CI run 40718526292](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40718526292) completed successfully: 26/26 unit/adversarial tests and wiki lint passed. Audited existing issues: #1–#3 predated later #4–#6. Merged added acceptance requirements into #1–#3 and closed #4–#6 as duplicates, preserving history. Updated handoff and taskboard. Real hourly live run is still not verified.

## 2026-10-28 — strengthen MOC folder navigation
Validated corrected [MOC CI #40718526292](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40718526292) passed 26 tests and structural lint. Adversarial review identified missing topic _index.md files and a missing linter invariant. Added six topic indexes and new missing-index / unreachable-index tests; a new CI run is required before treating this patch as verified.

## 2026-10-28 — adversarial test fixture regression and correction
The new [run #40719452896](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40719452896) failed at the unit-test step: 27 tests passed, one errored because `test_missing_source_frontmatter_is_detected` called `mkdir` on a directory already created by the topic-index fixture. Production model logic was not implicated. Corrected the fixture with `exist_ok=True`; awaiting a successful CI readback before declaring completion.

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

## 2026-10-28 — topic-index and adversarial CI verification
[GitHub Actions 40719684672](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40719684672) completed SUCCESS after fixture repair [commit 9fb89fc](https://github.com/lican1213/financial-crisis-early-warning/commit/9fb89fcfc9e3211d35dc6bd1a84366b711da0dd9): 28 tests passed; structural lint passed on 29 knowledge pages. P2 documentation follow-up [#10](https://github.com/lican1213/financial-crisis-early-warning/issues/10) has completion evidence. Still open: live hourly monitor #1, PIT calibration #3, sources #2, event vetting #7, delivery #8.

## 2026-10-29 — live market-source upgrade, fault injection, and cadence publication
- Original [scheduled run 40769178684](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40769178684) returned success despite 9/9 FRED timeouts. Captured as monitoring false-success incident.
- Official [OFR Financial Stress Index](https://www.financialresearch.gov/financial-stress-index/data/fsi.csv) and [NY Fed Markets API](https://markets.newyorkfed.org/static/docs/markets-api.html) integrated alongside parallel FRED; [run 40788157364](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40788157364) confirmed 11 observations, four independent families, source health partial because one redundant FRED TGCR call failed.
- Added candidate GitHub issue outbox with idempotent readback and recovery from lost acknowledgment; explicit DATA-HEALTH issue for insufficient newly retrieved coverage; point-in-time release-timestamp replay (not a calibrated historical result).
- Added tests for complete source outage with fresh cache, exact-repeat fetch and vintage log, independently updated family recovery and post-issue-response loss. [CI 40788377354](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40788377354) found int-to-float persistence drift; [CI 40788555417](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40788555417) further found snapshot evidence-hash int/float mismatch. Both negative findings retained; final check pending.
- Created [hourly-to-monthly cadence](../docs/operations/CADENCE.md) and updated source interface audit. Do not equate technical green with human weekly high-risk observation status.

## 2026-10-29 — v0.4 additional source integrations and actual red-team outcomes
- Official [OFR repo API](https://www.financialresearch.gov/short-term-funding-monitor/api-specs/api-data-single/), [ECB CISS](https://data.ecb.europa.eu/data/datasets/CISS), and [FDIC failures](https://api.fdic.gov/banks/docs/) ingested; [source run](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40801545198) SUCCESS. ECB CISS dated Oct27 0.0186001, OFR repo dated Oct27 4.08 percent, no recent large FDIC review candidates.
- [Cboe VIX9D/VIX/VIX3M/VIX6M and CFE VX futures](../data/volatility_context.json) official source and real CSV headers validated; front 18.5982, second 18.7752 on Oct28, +0.177 contango. [Run](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40801824156) SUCCESS. ICE MOVE remains restricted.
- [Non-crisis GitHub Issue #11](https://github.com/lican1213/financial-crisis-early-warning/issues/11) create/readback/close succeeded. Existing ChatGPT hourly/weekly prompts now pull and reconcile GitHub source evidence.
- Real [revised-FRED 2007–2026 historical analysis](../reports/expost_latest.json): 5,173 weekdays, 16 candidate alarms, 14 outside four chosen event windows, 2011/2023 misses. Separate pre-2007 BAA10Y 95th percentile 3.39% remains only ex-post sensitivity, not live HY OAS.
- [Experimental ALFRED as-of public endpoint](../reports/alfred_smoke.json): initial multi-series vintage request 4/4 HTTP 404; later individual as-of date probes accepted 11/20 cells with 20% three-family coverage, so reliable historical performance remains unverified. Automatic full scheduled retries disabled; failed attempt preserved.
- Adversarial regressions found FDIC syntax error, Cboe test URL-query parsing, escaped CSV fixtures, real CFE Price field versus Settlement Price, and cancelled job from shared concurrency group. Issues corrected; [117-test CI + wiki lint PASS](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40801824139).
- Updated [monitoring cycle](../docs/operations/CADENCE.md) and canonical [open Issues](tasks.md).

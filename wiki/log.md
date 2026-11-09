---
title: FCEWS Project Operation Log
kind: log
status: active
updated: 2026-11-09
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

## 2026-10-29 — original-as-of source partially recovered, ChatGPT polling delivery and source audit
Public ALFRED's multi-era request returned HTTP404. Retesting date-scoped queries [smoke run 40802069743](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40802069743) recovered 4 of 5 VIX and NFCI, 2 STLFSI4 and 1 HY OAS **historical as-of snapshots**. Initiated full weekly 2007–2026 as-of [Action 40802656579](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40802656579), outcome pending at log time. Added historical event source-family coverage audit to distinguish unassessable windows from actual model misses. [Cboe genuine monthly VX data](../data/volatility_context.json) now includes F1/F2 +0.177 contango; ICE MOVE still requires authorized feed. Verified hourly [ChatGPT polling feed](../data/chatgpt_feed.json) with zero candidates and explicit no-notify contract; existing ChatGPT automation prompt updated in place, not new task. [Monitoring cadence](../docs/operations/CADENCE.md) updated.

## 2026-10-29 — authorized ALFRED PIT entry point and 135-test CI
Committed [authorized original-vintage runner](../src/fcews/pit_authorized.py), [GitHub Actions workflow](../.github/workflows/alfred-authorized.yml), and adversarial empty/missing-key tests. [CI #40803626615](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40803626615) passed 135/135 unit/falsification tests and 29-page MOC lint. The user must add `FRED_API_KEY` via Actions secrets and manually invoke the workflow; neither public historic sample nor the installed code proves complete 2008/2011/2020/2023 accuracy yet. Existing ChatGPT hourly condition-watch prompt was updated to prioritize the [stable feed](../data/chatgpt_feed.json), but live end-user notification receipt remains outside GitHub's control.

## 2026-11-06 — baseline CI, fallback data health and schedule-gap red team

- Read the current main branch, latest weekly baseline, 135-test suite, Actions logs and real scheduled-run history before editing. Reproduced one failing test: old hardcoded 66/100 after the 2026-11-01 six-module orange 68/100 human baseline. The test now reads the configured band and checks no unsupported downgrade.
- Built adversarial fixtures for NY Fed official TGCR fallback (versus VIX outage and a forged/invalid URL), four independent live families, daily and weekly source-age grace, missing/failed hourly runs, and trusted national regulator hosts. The FCEWS market-risk decision rule and user four notification gates were left unchanged.
- Followed [Healthchecks heartbeat grace](sources/reference-projects.md), [Great Expectations freshness](sources/reference-projects.md), and [OpenBB data-provider](sources/reference-projects.md) patterns at the engineering-concept level without importing any of their packages. Actual GitHub check.yml cron gaps reached 9.64 hours; the new daily audit warns on a >90-minute successful-schedule gap, while the unresolved GitHub scheduling reliability remains Issue #1.
- Local acceptance: full `unittest` regression and 29-page wiki lint; remote commit, Actions run, issue update and final status are to be recorded as separate evidence after GitHub execution. A data-health fault never constitutes a market crisis. Missing FRED_API_KEY original PIT coverage, proprietary MOVE/Treasury depth and webhook receipt remain explicitly open.

## 2026-11-06 — remote PR fault injection exposed branch data pollution

While staging [PR #13](https://github.com/lican1213/financial-crisis-early-warning/pull/13), the existing `check.yml` `push` trigger ran source collection on the feature branch and committed three live runtime files there. This is an observed defect, not a hypothetical precaution. Patched the workflow to permit the production polling job only on `main` and added a branch-safety regression; cleanup commit restores the three runtime files to their main-branch contents so the PR stays code + documentation only. Record actual follow-up Actions outcome in handoff after verification.

## 2026-11-06 — merged CI and live source readback

[PR #13](https://github.com/lican1213/financial-crisis-early-warning/pull/13) merged as [a7ea416](https://github.com/lican1213/financial-crisis-early-warning/commit/a7ea4167749e903e370b5a5996e820b3b54a4a47). [PR validation 42183639758](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/42183639758), [main test 42183769730](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/42183769730) and [main official-source check 42183769689](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/42183769689) all completed SUCCESS. GitHub main health source record had four live families, recovered official FRED TGCR through NY Fed, zero unresolved source errors; ChatGPT feed remained zero candidates, explicit no notification. A push-triggered passing run is not proof of an hourly schedule SLA. [Handoff](operations/HANDOFF.md) records the remaining work and exact links.


## 2026-11-09 — paused weekly report -> structured leading research migration
Opened [Issue #14](https://github.com/lican1213/financial-crisis-early-warning/issues/14) and branch `feature/monitor-research-gates-20261109`. Implemented [official US labor/curve/IG context and primary release ledger](../src/fcews/research.py), [red-team regressions](../tests/test_research.py), [separate daily research workflow](../.github/workflows/research.yml), and removed outdated Sunday alert scheduling text. Added a second best-effort GitHub cron check slot and pull/rebase before data writes. Preserved four-family alert policy, latest 2026-11-08 historical six-module orange/70 baseline, and `model_comparability=not_calibrated`. Note: GitHub CI, live collector run, and external independent heartbeat require **separate actual evidence readback**; do not mark DONE from these commits alone.


## 2026-11-09 — PR #15 merged and actual research run
[PR #15](https://github.com/lican1213/financial-crisis-early-warning/pull/15) merged at [86726df](https://github.com/lican1213/financial-crisis-early-warning/commit/86726df8914f656af22f2b7e695e0cb66e40c01c). Remote PR [CI 42547283371](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/42547283371) confirmed **172/172 tests and 31 wiki pages PASS**. Main [risk-gate run 42547475263](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/42547475263) succeeded with four live families and zero unresolved errors/candidates. Main [research run 42547475174](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/42547475174) succeeded: six source-dated official US series and no missing US indicators; CN/firm ledger remains empty and scoring null. Follow-up targeted bridge integration adds release-status and freshness-only feed metadata; record its independent test outcome separately.


## 2026-11-09 — bridge PR #16 merged, production polling and MOC gate readback
[PR #16](https://github.com/lican1213/financial-crisis-early-warning/pull/16) merged as [48ecc04](https://github.com/lican1213/financial-crisis-early-warning/commit/48ecc042e775828d36200f263f93324a9d882b3f). [PR CI](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/42547919361) and [main CI](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/42547974958) PASS, 175 tests and 31 wiki-page lint. [Main live FCEWS](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/42547974914) SUCCESS. Actual [GitHub JSON feed](../data/chatgpt_feed.json) includes fresh source dates and null China/firm scores but forbids research-derived alerts; `candidate_count=0`. User-facing weekly report remains paused. [Issue #14](https://github.com/lican1213/financial-crisis-early-warning/issues/14) updated with completion/remaining gates, not falsely closed.


## 2026-11-09 — official China PMI article source adapter and adversarial correction
Added [NBS article discovery/section parser](../src/fcews/nbs.py) and [negative fixtures](../tests/test_nbs.py), separate research workflow step and read-only [bridge](../src/fcews/bridge.py) provenance fields. An initial GitHub test rejected an article whose title month did not match the index entry (FAIL-044); repaired the **real** title matching bug rather than weakening the test. Production Actions and source readback must be recorded after merge before calling the China PMI adapter live.


## 2026-11-09 — live Chinese NBS demand evidence and post-collection handoff race
[PR #17](https://github.com/lican1213/financial-crisis-early-warning/pull/17) merged as [709c589](https://github.com/lican1213/financial-crisis-early-warning/commit/709c5895d6798c983ed2cacf55c675db7e850091). [CI](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/42548769651) passed 186 tests, 31 wiki pages; main [research run](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/42548838233) SUCCESS. Original [NBS output](../data/nbs_pmi_context.json) validated October manufacturing PMI 49.3, new orders 49.4 and small enterprise PMI 47.5, dates October 31. A subsequent feed readback revealed stale source-summary metadata, not a failed original NBS source fetch; recorded [FAIL-045](operations/INCIDENTS.md) and repaired data-persist-before-bridge ordering on the independent follow-up branch. Test, CI and live integration verification still required.


## 2026-11-09 — final FAIL-045 live source-to-feed proof
[PR #18](https://github.com/lican1213/financial-crisis-early-warning/pull/18) merged as [058badc](https://github.com/lican1213/financial-crisis-early-warning/commit/058badc7218ed608bc1b8123a152a98a8f23fc58). [Main CI](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/42549320850) SUCCESS, **186 passing tests and 31-page wiki lint**. [Main official research workflow](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/42549320848) SUCCESS including post-commit read-only bridge regeneration, which corrected the previously observed stale PMI summary. Actual [feed](../data/chatgpt_feed.json) read back 2026-10-31 NBS release and source-dated manufacturing indicators; both uncalibrated China/recruiting scores null, candidate_count zero, notification false. Remaining scheduler SLA, additional China/IR releases, point-in-time history and scoring calibration have NOT passed acceptance and remain open.


## 2026-11-09 — full official housing + five-issuer demand adapters (PR staging)
Extended [research pipeline](../.github/workflows/research.yml) with [70-city full price/developer data adapter](../src/fcews/nbs_property.py) and [five primary IR recruiting adapters](../src/fcews/staffing_ir.py), complete with [property counterexamples](../tests/test_nbs_property.py), [staffing counterexamples](../tests/test_staffing_ir.py), read-only feed and missingness isolation. Retain original NBS source dates, split monthly price breadth from cumulative year-over-year demand, and never treat developer mortgage receipts as PBOC household mortgages. **Remote CI and main live source readback have separate gates; this staging entry does not claim success until proven.**


## 2026-11-09 — production failure-led 70-city and issuer-IR source repairs
Initial [main research Action 42605458287](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/42605458287) failed operationally while saving valid US, NBS PMI and three company releases. Live failures: official NBS 70-city HTML over generic 1MB cap; Manpower investor site HTTP403; Michael Page original LSE release failed metric extraction. Focused repair branch `fix/live-70city-issuer-v2-20261109` added bounded dedicated NBS HTML reader, a corporate Manpower original alternate and a page-gross-fee regex plus tests. CI/live acceptance follow separately; no fabricated missing data and no market-crisis alert.

## 2026-11-09 — fifth recruitment issuer source: official PDF
Verified [Michael Page investor original PDF](https://investors.michaelpage.com/~/media/Files/P/page-v2/ir/result-reports/2026/q3-2026-trading-statement.pdf) dated 13-Oct-2026 with Q3 constant-currency gross profit +1.5%, permanent +1.1%, temporary +2.6%. Replaced empty LSE JS shell with a pinned exact original IR PDF and original-content SHA, bounded 2MB response, pypdf text extraction and red-team tests. A test exposed duplicate same-value gross profit headline extraction; changed parser to collapse concordant repeated values, not conflicting values. Production gate and MOC acceptance are separate and pending.

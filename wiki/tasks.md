---
title: FCEWS Task Dashboard
kind: taskboard
status: active
updated: 2026-11-09
summary: Navigational work queue; live GitHub Issues are authoritative for status and acceptance.
---

# Work queue — authoritative task state in GitHub Issues

This page is a **dated view** (2026-10-28), not a second source of status. Open each Issue to see current assignment, blocking dependencies, discussion and proof of completion.

| Priority | Task | Completion proof |
| --- | --- | --- |
| P0 | [#14 Source-gated leading research and cron mitigation](https://github.com/lican1213/financial-crisis-early-warning/issues/14) | PR CI + live Actions readback, source-document gates; external heartbeat remains open |
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

## 2026-10-29 verified source and connection advances
- [#2](https://github.com/lican1213/financial-crisis-early-warning/issues/2): official Cboe VIX9D/VIX/VIX3M/VIX6M, monthly VX futures, UST realized yield volatility, ECB CISS, OFR repo, FDIC review operational. Latest [data](../data/volatility_context.json): true CFE monthly front/second; genuine ICE MOVE quote and Treasury market depth are still licensed/unavailable.
- [#3](https://github.com/lican1213/financial-crisis-early-warning/issues/3): public ALFRED vintage smoke [partial success](../reports/alfred_smoke.json) and [coverage classification](../src/fcews/coverage.py) added; full weekly 2007–2026 PIT collection [Action 40802656579](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40802656579) started; no success claim until its result and actual source coverage are checked. The ex-post model still misses 2011/2023 and does not establish predictive accuracy.
- [#8](https://github.com/lican1213/financial-crisis-early-warning/issues/8): published [read-only ChatGPT feed](../data/chatgpt_feed.json), existing hourly user task prompt updated and enabled. GitHub Issue canary verified. GitHub webhook-to-ChatGPT event and end-user receipt not supported by current integration, so the bridge is authenticated hourly polling rather than zero-latency push. Four original alert conditions unchanged.
- [Cadence](../docs/operations/CADENCE.md) updated including monthly ALFRED, weekday Cboe and hourly ChatGPT polling.

## Authorized historical PIT run gate — 2026-10-29
- [#3 historical predictive validation](https://github.com/lican1213/financial-crisis-early-warning/issues/3): [authorized ALFRED workflow](../.github/workflows/alfred-authorized.yml) is deployed, [135-test CI PASS](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40803626615). Real original-vintage export remains unexecuted until `FRED_API_KEY` is configured in GitHub Actions Secrets and owner invokes the workflow. Confirm source release-day, family coverage and holdout results; don't close on code alone.
- [#8 ChatGPT polling bridge](https://github.com/lican1213/financial-crisis-early-warning/issues/8): [live feed](../data/chatgpt_feed.json) and original hourly task read instructions verified; no signed push webhook or exact-once end-user acknowledgement. User four-gate true silence preserved.

## 2026-11-06 reliability work — local tests passed; GitHub acceptance tracked in handoff

- [#1 Cron execution](https://github.com/lican1213/financial-crisis-early-warning/issues/1): actual hourly scheduled runs had gaps up to 9.64 hours over the November 1–6 audit window. Added daily 24-hour schedule-run audit with 90-minute grace and separate operational warnings; **does not repair GitHub's best-effort scheduler**. Do not close #1 until a real independent heartbeat or external scheduler meets the agreed cadence.
- [#1 Production-branch isolation](https://github.com/lican1213/financial-crisis-early-warning/issues/1): PR #13 itself demonstrated old `check.yml` could push live `data/` into feature branches. Restrict the production check job to `main`, restore branch-only data and add [workflow test](../tests/test_workflows.py). Actual remote branch diff/CI readback required.
- [#2 Data feeds](https://github.com/lican1213/financial-crisis-early-warning/issues/2): fallback SOFR/TGCR errors separated into recovered/unresolved, four-family live-health requirement and weekday source-age diagnostics. Licensed ICE MOVE, Treasury depth and full private-credit sources remain open.
- [#7 Verified events](https://github.com/lican1213/financial-crisis-early-warning/issues/7): accept known official regulator hosts in Brazil, Paraguay and Serbia (and other named authorities) under the existing document-hash/reviewer gate; forged domains and malformed URLs tested. **No newly authenticated real cross-market event has been promoted**.
- [#8 Weekly baseline](https://github.com/lican1213/financial-crisis-early-warning/issues/8): baseline test no longer hardcodes historic 66/100 once the 2026-11-01 six-module baseline became orange 68/100. Technical green remains incomparable and no ChatGPT notification receipt is claimed.


## 2026-11-09 production verification
- [Issue #14](https://github.com/lican1213/financial-crisis-early-warning/issues/14): base PR #15 merged; official US research 6/6 live source-dated records, regression 172 tests and MOC 31 pages passed. Research bridge follow-up and full China/company original-document ingestion need separate gates; do not claim complete automated China scores.
- [Issue #1](https://github.com/lican1213/financial-crisis-early-warning/issues/1): GitHub twice-hourly schedule mitigation deployed, but independent heartbeat/service-level guarantee not completed. Remains open.


## 2026-11-09 follow-up acceptance gate
- [PR #16 read-only bridge](https://github.com/lican1213/financial-crisis-early-warning/pull/16): merged; actual feed readback fresh, six US research series and no market alert. [CI 175 tests + 31 wiki](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/42547919361) passed.
- **Still P1 #14:** source-specific NBS/PBOC (housing/credit) and recruiter company original-document numeric readback, publication-vintage verification and objective scoring gate. **Still P0 #1:** truly independent scheduler/heartbeat. No claims of full coverage until each acceptance is real.


## 2026-11-09 NBS first live source candidate
[Issue #14](https://github.com/lican1213/financial-crisis-early-warning/issues/14): NBS manufacturing PMI/new orders/small-firm adapter under gate; must be verified by main Actions after merge. Other China/firm original releases and the actual national recovery breadth scoring method remain open.


## 2026-11-09 NBS source adapter production evidence
- [PR #17 / commit 709c589](https://github.com/lican1213/financial-crisis-early-warning/pull/17) shipped: genuine NBS manufacturing PMI, new-order and small-firm PMI [source-dated official snapshot](../data/nbs_pmi_context.json) via [successful main research Action 42548838233](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/42548838233); 186 tests and MOC PASS. Source feed refresh ordering requires the follow-up FAIL-045 fix before its acceptance gate.


## 2026-11-09 final production source delivery checkpoint
- FAIL-045 source-to-feed race addressed: [PR #18](https://github.com/lican1213/financial-crisis-early-warning/pull/18), [main research run 42549320848](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/42549320848), [main CI 42549320850](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/42549320850): 186 unit+adversarial tests and 31-page wiki PASS. Read-only feed now has official NBS source dates, US research dates, no new crisis alerts and no made-up global staffing/China breadth scores.
- Do not mark whole Issue #14 complete: staffed-company filings, full property/credit evidence and formal recovery breadth scores remain missing. Do not close #1 without independent cadence owner or #3 without original-vintage data and holdout.


## 2026-11-09 property/IR expansion acceptance
- [#14](https://github.com/lican1213/financial-crisis-early-warning/issues/14): 70-city table coverage, NBS developer sales/funding and five issuer IR original-source automation staged. CI fixture pass is **not** source-live acceptance. Missing PBOC personal mortgage lending, China lending/private-credit impulse, complete staffing actual hiring/contract volume and index scoring remain as explicit acceptance gaps. Keep issue OPEN until verified.

- [#14](https://github.com/lican1213/financial-crisis-early-warning/issues/14) live acceptance: PR #19 code merged but [research Action 42605458287](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/42605458287) failed 70-city page over 1MB generic cap; 3/5 recruiter originals verified, 2 unavailable. Transport repair branch `fix/live-70city-issuer-v2-20261109` staged; do not mark full source coverage complete until original government and primary issuer readback passes.

## 2026-11-09 recruiting-source closeout candidate
- [#14](https://github.com/lican1213/financial-crisis-early-warning/issues/14): four firm official sources + full NBS 70-city price/sales/developer funds already in production. Michael Page fifth source now an original corporate PDF [issuer Q3 2026 PDF](https://investors.michaelpage.com/~/media/Files/P/page-v2/ir/result-reports/2026/q3-2026-trading-statement.pdf); CI and live main readback required before 5/5 is accepted. Pending: PBOC mortgage direct source, complete empirical hiring volumes, quantitative breadth calibration, PIT original vintage, independent scheduling.

---
title: Adversarial Incident and Failure Register
kind: operations
status: active
updated: 2026-11-06
summary: Failed assumptions, reproducible counterexamples, live deployment gaps and accountable issue links.
---

# Failure / adversarial test register

A defect is only fixed after a reproducible test and a verified commit; a remaining data limitation stays open. Legacy brief list: [docs/moc/FAILURES](../../docs/moc/FAILURES.md).

| ID | Finding | Resolution / tracking |
| --- | --- | --- |
| FAIL-001 | Six hourly polls of identical source data counted as three recovery days | Mitigated in v0.2 by distinct observation dates; still needs actual release stamps [#5](https://github.com/lican1213/financial-crisis-early-warning/issues/3) |
| FAIL-002 | First-run dual-family stress was silently discarded | Fixed at unit-test level in v0.2; live run still needs [#4](https://github.com/lican1213/financial-crisis-early-warning/issues/1) |
| FAIL-003 | STLFSI/NFCI/ANFCI could falsely count as independent | Same-family aggregation in v0.2; review OFR overlap [#6](https://github.com/lican1213/financial-crisis-early-warning/issues/2) |
| FAIL-004 | No source-dated weekly baseline | Defaults to unknown; reconcile real weekly report [#8](https://github.com/lican1213/financial-crisis-early-warning/issues/8) |
| FAIL-005 | Relying on today's revised macro data falsifies backtested lead time | Open; ALFRED/PIT and release calendars [#5](https://github.com/lican1213/financial-crisis-early-warning/issues/3) |
| FAIL-006 | Verified boolean + URL can be manually forged | Open; signed/source-readback verification [#7](https://github.com/lican1213/financial-crisis-early-warning/issues/7) |
| FAIL-007 | One spread misrepresents all repo funding health | Open; SRF/repo depth [#6](https://github.com/lican1213/financial-crisis-early-warning/issues/2) |
| FAIL-008 | GitHub candidate Issue confused with sent ChatGPT notification | Open; delivery contract [#8](https://github.com/lican1213/financial-crisis-early-warning/issues/8) |
| FAIL-009 | GitHub Actions may not yet have run successfully | Open; live execution validation [#4](https://github.com/lican1213/financial-crisis-early-warning/issues/1) |
| FAIL-010 | Repository public though initial recommendation was private | User account setting; no secrets committed. See [handoff](HANDOFF.md) |
| FAIL-011 | Heuristic thresholds not calibrated to historical distributions | Open [#5](https://github.com/lican1213/financial-crisis-early-warning/issues/3) |
| FAIL-012 | Multiple task logs cause agent drift across sessions | ADR and single canonical Issues; maintain wiki lint [#9](https://github.com/lican1213/financial-crisis-early-warning/issues/9) |
| FAIL-013 | MOC registry lacked explicit official provenance | Detected by [CI 40718335555](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40718335555): 26 unit tests pass, one wiki lint fails. Added FRED source to registry and confirmed [CI 40718526292](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40718526292) passed 26 tests and lint [#9](https://github.com/lican1213/financial-crisis-early-warning/issues/9) |

| FAIL-014 | Earlier Issues #1–#3 duplicated by #4–#6 | Merged added acceptance criteria into earlier Issues, closed later ones as duplicate; taskboard now canonical. |

For each future failure record observed UTC time, actual vs expected behavior, minimal reproducer, test name, impacted files, source evidence, issue, fix commit and re-test outcome. Never silently erase a failed experiment.

Next: [handoff](HANDOFF.md), [taskboard](../tasks.md).

## FAIL-014 — 2026-10-28 topic-index fixture directory collision
Observed [CI #40719452896](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40719452896): after adding a `sources/_index.md` fixture, the test attempted a second `mkdir` of `sources/` without `exist_ok=True`, raising `FileExistsError`. Reproduces consistently in the Python 3.12 GitHub runner. Corrective change: idempotent fixture directory creation; new CI readback required. Keeps original failing run for audit.

**FAIL-014 resolution (2026-10-28):** [commit 9fb89fc](https://github.com/lican1213/financial-crisis-early-warning/commit/9fb89fcfc9e3211d35dc6bd1a84366b711da0dd9) corrected duplicate fixture directory creation. Subsequent [GitHub Actions 40719684672](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40719684672): 28/28 tests and 29-page structural lint PASS. The initial failure remains in the log as audit evidence.

## 2026-10-29 source / model adversarial findings
- **FAIL-015 — nine-source blind success.** [Old schedule run 40769178684](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40769178684) was green despite all FRED requests timing out. New version requires three newly collected indicator families; missing coverage creates a deduplicated data-health incident and fails the job. **Market risk alert stays silent** unless one of four user-defined conditions is established.
- **FAIL-016 — issue created but receipt lost.** Persistent outbox and GitHub issue-body fingerprint permit replay after lost HTTP response, with confirmed readback before state acknowledgment. Network-fault fixture passed under [integration tests](../../tests/test_integration.py).
- **FAIL-017 — hourly commit churn.** Previously equal source observations with later retrieved_utc were rewritten. New cache preserves original retrieval time for unchanged values and records a local first-seen vintage event only for changed values or genuine same-date revisions; exact-repeat tests included.
- **FAIL-018 — unilateral recovery.** Three distinct daily VIX dates once counted as three confirmed recovery periods even if all credit/system measures were unchanged. New recovery count advances only after two independent families' observation dates advance; simulated tests included.
- **FAIL-019 — live outage hidden by cached readings.** Stale-but-not-expired cache can assist current risk state but must not satisfy data-feed health. The live gate is computed from newly returned source observations, independent of cached context. Failed-only-with-fresh-cache test included.
- **FAIL-020 — numeric serialization drift.** [CI run 40788377354](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40788377354) detected 3 versus 3.0 in cache JSON, and [CI 40788555417](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40788555417) detected the same mismatch in the evidence signature. Normalized both to float and rerun full tests (see latest Actions).
- **FAIL-021 — PIT coverage limitation.** Engine tests exclude future revisions and unreleased data but comprehensive original historical ALFRED vintages and benchmark results have not been built. [Issue #3](https://github.com/lican1213/financial-crisis-early-warning/issues/3) remains open.

## V0.4 additional adversarial failures, 2026-10-29
- FAIL-022: Public FRED ICE high-yield OAS historical values available only roughly since 2023-10 after the 2026 licensing restriction. Pre-2023 real-time backtesting cannot assume HY observations were available. [Ex-post diagnosis](../../reports/expost_latest.json).
- FAIL-023: Pre-2007 trained BAA10Y investment-grade proxy 95th percentile 3.39 percent gave ex-post signals in 2008 and 2020 selected windows, **missed 2011 and 2023**, with 14 unmatched alarms across 5,173 weekdays. Never label proxy HY OAS or claim validated PIT.
- FAIL-024: Initial ALFRED vintage batched URL failed 4/4 with HTTP 404; subsequent corrected individual as-of requests accepted 11/20 cells. Coverage remains inadequate: only 20% of five source decision dates contain at least three families. Automated full-monthly pull disabled; authenticated endpoint required.
- FAIL-025: Actual Cboe CFE settlement CSV Price field differed from synthetic expected Settlement Price. Parser and regression updated; no ICE MOVE substitution. [Actual data](../../data/volatility_context.json).
- FAIL-026: FDIC Python dict syntax, synthetic FRED test id query suffix, escaped CSV newline fixtures, missing file staging and wrongly shared GitHub Actions concurrency group initially caused test/job failures. Corrected with failure traces preserved; [117-pass CI](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40801824139).
- FAIL-027: A push-triggered live run does not prove the current hourly cron schedule; [#1](https://github.com/lican1213/financial-crisis-early-warning/issues/1) remains open.
- FAIL-028: Genuine ICE MOVE and order-book depth licensing not available. Cboe equity-vol index term, VX futures and Treasury realized yield-vol are different instruments.

## 2026-10-29 historical availability + delivery closure gaps
- **FAIL-029 — inaccurate 'all ALFRED unavailable' summary:** initial batched public historical as-of query returned 404, but splitting noncontiguous historical dates into single-vintage queries yielded [actual verified 5-date smoke](../../reports/alfred_smoke.json): four VIX and four NFCI, two STLFSI4 and one HY OAS. The initial all-404 report is not a global ALFRED availability conclusion; record the partial original-as-of evidence and missing pre-2023 credit separately.
- **FAIL-030 — historical miss vs missing family:** the revised-data simulation cannot label an original PIT crisis missed when contemporaneously available independent source families are absent. Added [event assessability audit](../../src/fcews/coverage.py) and 6 negative tests. Raw missed-events remain visible; audited results split fully observed, partially observed and unevaluable events.
- **FAIL-031 — ChatGPT transport is not webhook:** [read-only feed](../../data/chatgpt_feed.json) consumed by an hourly condition-watch has no guaranteed immediate push or GitHub-to-ChatGPT user receipt. Unchanged signal means *true silence*. The external GitHub issue canary verifies GitHub operation only; never call this exactly-once end-user notification.
- **FAIL-032 — licensed data boundary:** Cboe equity implied-vol term, actual CFE VX futures and UST realized yield-vol are different instruments from the proprietary ICE MOVE; none may be relabelled MOVE to falsely complete the source checklist.

## 2026-11-06 — operational falsification and regression repairs

- **FAIL-033 — the weekly-grade fixture froze a historical score.** [GitHub daily audit 41985002934](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/41985002934) failed because `tests/test_weekly_context.py` required 66/100 after a real 2026-11-01 weekly orange 68/100 baseline was committed. Fix: assert the score lies inside the baseline's stated `orange` grade band; retain checks against an automatic technical-green downgrade. Unit tests reproduce the changed baseline and pass locally; GitHub commit/CI readback belongs in [handoff](HANDOFF.md).
- **FAIL-034 — redundant provider outage mislabeled as incomplete data.** The historical FRED TGCR HTTP failure was recorded as a generic source error although NY Fed successfully supplied the same rate. [Integration negative tests](../../tests/test_integration.py) now require an official-host match to mark a provider error as `recovered`, while VIX 503, hostile lookalike URLs and malformed URLs remain unresolved. The full error trail remains available. A live run with only system/credit/volatility and no funding is `partial`, not fully `healthy`.
- **FAIL-035 — configured hourly GitHub cron is not actual hourly coverage.** Direct GitHub Actions readback on 2026-11-06 found only three successful scheduled checks in the most recent 24 hours (maximum gap 468.8 minutes); over the wider November 1–6 window the longest observed gap was 9.64 hours. [Schedule-health tests](../../tests/test_schedule_health.py) separate cron successes from pushes and failures. [Daily audit](../../.github/workflows/daily-audit.yml) now warns if any gap exceeds 90 minutes. **Not resolved:** GitHub Actions `schedule` is best-effort and the daily audit itself can run late. [Issue #1](https://github.com/lican1213/financial-crisis-early-warning/issues/1) stays open until a genuinely independent cadence owner exists.
- **FAIL-036 — dated but late data could still look healthy.** The old live-family gate checked stale-vs-model maximum age, but not reasonable publisher cadence. Added [quality diagnostics](../../src/fcews/quality.py) with >3 weekday daily / >8 weekday weekly overdue bounds and weekend/future-date negative tests. These operational grace windows are **not official release calendars**, and must not turn into financial crisis triggers.
- **FAIL-037 — authority host coverage and spoofing.** Previously several national central bank hostnames could not be attached to human-reviewed official event records. Added explicit regulator roots and [host-spoof tests](../../tests/test_events.py); reviewer identity, SHA and contagion evidence are still mandatory. New domain allowance alone is not an authenticated event, and #7 remains open for real source readback.
- **FAIL-038 — production push trigger wrote runtime files on feature branches.** The initial GitHub-hosted repair branch invoked `check.yml` automatically and acquired `data/health.json`, `data/latest_check.json` and `data/chatgpt_feed.json` bot commits unrelated to source changes. The workflow formerly accepted `push` on any branch and committed `data/` unconditionally. Restrict both push dispatch and the `monitor` job to `refs/heads/main`; [workflow regression](../../tests/test_workflows.py) ensures that branch protection cannot silently disappear. Restore the three data files to the main branch's tracked versions in PR #13; source collection on `main` remains unchanged.

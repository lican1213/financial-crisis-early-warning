---
title: Adversarial Incident and Failure Register
kind: operations
status: active
updated: 2026-10-28
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

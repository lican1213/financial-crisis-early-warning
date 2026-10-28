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
| FAIL-001 | Six hourly polls of identical source data counted as three recovery days | Mitigated in v0.2 by distinct observation dates; still needs actual release stamps [#5](https://github.com/lican1213/financial-crisis-early-warning/issues/5) |
| FAIL-002 | First-run dual-family stress was silently discarded | Fixed at unit-test level in v0.2; live run still needs [#4](https://github.com/lican1213/financial-crisis-early-warning/issues/4) |
| FAIL-003 | STLFSI/NFCI/ANFCI could falsely count as independent | Same-family aggregation in v0.2; review OFR overlap [#6](https://github.com/lican1213/financial-crisis-early-warning/issues/6) |
| FAIL-004 | No source-dated weekly baseline | Defaults to unknown; reconcile real weekly report [#8](https://github.com/lican1213/financial-crisis-early-warning/issues/8) |
| FAIL-005 | Relying on today's revised macro data falsifies backtested lead time | Open; ALFRED/PIT and release calendars [#5](https://github.com/lican1213/financial-crisis-early-warning/issues/5) |
| FAIL-006 | Verified boolean + URL can be manually forged | Open; signed/source-readback verification [#7](https://github.com/lican1213/financial-crisis-early-warning/issues/7) |
| FAIL-007 | One spread misrepresents all repo funding health | Open; SRF/repo depth [#6](https://github.com/lican1213/financial-crisis-early-warning/issues/6) |
| FAIL-008 | GitHub candidate Issue confused with sent ChatGPT notification | Open; delivery contract [#8](https://github.com/lican1213/financial-crisis-early-warning/issues/8) |
| FAIL-009 | GitHub Actions may not yet have run successfully | Open; live execution validation [#4](https://github.com/lican1213/financial-crisis-early-warning/issues/4) |
| FAIL-010 | Repository public though initial recommendation was private | User account setting; no secrets committed. See [handoff](HANDOFF.md) |
| FAIL-011 | Heuristic thresholds not calibrated to historical distributions | Open [#5](https://github.com/lican1213/financial-crisis-early-warning/issues/5) |
| FAIL-012 | Multiple task logs cause agent drift across sessions | ADR and single canonical Issues; maintain wiki lint [#9](https://github.com/lican1213/financial-crisis-early-warning/issues/9) |

For each future failure record observed UTC time, actual vs expected behavior, minimal reproducer, test name, impacted files, source evidence, issue, fix commit and re-test outcome. Never silently erase a failed experiment.

Next: [handoff](HANDOFF.md), [taskboard](../tasks.md).

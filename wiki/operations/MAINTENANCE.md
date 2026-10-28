---
title: FCEWS Wiki and Monitor Maintenance
kind: operations
status: active
updated: 2026-10-28
summary: Repeatable cadence and acceptance gates for model data, code, MOC pages and notification flow.
---

# Maintenance SOP

## At every development session
Read [handoff](HANDOFF.md), [issues](../tasks.md), [failure register](INCIDENTS.md). Verify HEAD/recent commits; run `PYTHONPATH=src python -m unittest discover -s tests -v` and `python scripts/wiki_lint.py`; choose one Issue; make change with counterexample and fresh source provenance; update relevant MOCs and source manifests; append [log](../log.md), update handoff, post commit/test proof to Issue.

## Every hourly scheduled execution (GitHub Actions, once enabled)
Collect real source observations; distinguish poll time from economic time; check API failures; compute stable evidence hash; write state change only when necessary; open new candidate issue only if a qualified gate fires. Keep mundane unchanged runs in GitHub Action run logs; avoid meaningless one-commit-per-hour noise.

## Every weekly review
Reconcile published weekly risk grade and its source/time to `data/weekly_baseline.json`; inspect missing data and alerts; review recent false positives, caught issues and source revision drift; update task priorities; record verified actions in log. Never programmatically assign `green` solely because data is missing.

## Monthly adversarial audit
Audit all critical interface URLs/licenses/release lags; manual spot-check primary events; run orphan and broken-link lint; review stale MOCs (no live status copied without source), task dependencies, revision impact and false alert rate. Retrospective benchmark only against true point-in-time data.

## Incident response
1. Log failure ID, first observed time, blast radius and source evidence in [INCIDENTS](INCIDENTS.md).
2. Stop unauthorized user-facing alerts if evidence has not been verified; preserve raw diagnostics.
3. Reproduce with an adversarial regression fixture, fix and run all tests.
4. Mark issue closed only after production behavior has been checked; reflect outcome in source/ADR/log/handoff.
5. Distinguish routine API lag from systemic financial event; log each in its own correct category.

## Log rotation
Once operation log grows large (e.g. >30 entries), move oldest **unaltered** entries to dated archive Markdown, add archive to master index and maintain cross-links. Do not compress away failures or overwrite historical incidents to claim progress.

Related: [AGENTS.md](../../AGENTS.md), [system overview](../overview.md), [MOC delivery](../mocs/DELIVERY.md).

---
title: Source — External Financial Monitoring Projects
kind: source
status: under-review
updated: 2026-11-06
summary: Pointers for implementation research without copying undocumented performance claims.
---

# External implementation references

Code patterns are **inputs for inspection**, not independent validation of the user's financial-risk model.

- [macro-liquidity-pipeline](https://github.com/lauren-shih/macro-liquidity-pipeline) — study data provenance and release alignment; project applicability requires a concrete code review.
- [credit-spread-analyzer](https://github.com/AndrewFSee/credit-spread-analyzer) — possible credit signal measurement and walk-forward tests, not proof of a trading edge.
- [CBSRM / CISS-Sahm systemic risk](https://github.com/Allisterh/cbsrm-CISS-Sahm-rule-systemic-risk) — stress aggregation and explainability concepts; verify licensing and dependencies before reuse.
- [nvk/llm-wiki](https://github.com/nvk/llm-wiki) — agent navigation, MOC, schema and operational memory.

## 2026-11-06 implementation patterns actually applied

- [healthchecks/healthchecks](https://github.com/healthchecks/healthchecks) — time-based job monitoring separates the expected check-in period from a configurable grace period. Applied **period+grace** concept to the FCEWS GitHub schedule audit: hourly success with 90-minute maximum gap. This is retrospective daily auditing, not a Healthchecks service deployment or a guarantee against GitHub cron drops.
- [Great Expectations data-freshness guidance](https://docs.greatexpectations.io/docs/reference/learn/data_quality_use_cases/freshness/) — validate the age of observed data as a data-quality dimension. Applied to `quality.py` as business-day-based source diagnostics, separated from risk thresholds and documented as less accurate than an actual release calendar.
- [OpenBB provider architecture](https://docs.openbb.co/odp/python/faqs/data_providers) — distinguish data identities and providers. The FCEWS collector already had official FRED / NY Fed SOFR and TGCR fallbacks; the new health classification reports a recovered provider failure without hiding the underlying error. No OpenBB dependency was imported.

These are **referenced engineering patterns**, not copied code or an endorsement of FCEWS's financial forecast. Corresponding failure tests and the actual GitHub schedule readback are in [incidents](../operations/INCIDENTS.md) and [cadence](../../docs/operations/CADENCE.md).

**Status:** architectural inspiration only. No copied source code, no imported return statistics, no claim these references outperform FCEWS. A future documented review should specify commit/version, license, applicable method, limitations and test fixture.

Tracking: [taskboard](../tasks.md), [point-in-time testing](../concepts/point-in-time.md).

## 2026-11-16 — concrete follow-up patterns
- [Healthchecks job monitoring](https://github.com/healthchecks/healthchecks) uses check-in pings and explicit period/grace independent of payload changes. Applied as a small separately published [poll receipt implementation](../../src/fcews/heartbeat.py), not a new server. A successful manual/push run cannot move the scheduled-success clock. An actual external dead-man check remains the next step if an owner-provisioned endpoint is available; GitHub-only heartbeats cannot detect failure of GitHub itself without an outside reader.
- [Prometheus Alertmanager routing](https://github.com/prometheus/alertmanager/blob/main/docs/configuration.md) and [HA notification log](https://github.com/prometheus/alertmanager/blob/main/docs/high_availability.md) distinguish alert identity and material changes from repetition. Applied to the [direct-channel episode state](../../src/fcews/core.py): missing/asynchronous measurements cannot reset an active stress episode, a genuinely new confirmed direct channel generates a new candidate, aligned newer normal evidence rearms. Unlike Alertmanager periodic repeats, FCEWS remains strictly silent absent new material evidence.
- [GitHub scheduling troubleshooting](https://docs.github.com/en/actions/how-tos/troubleshoot-workflows) describes delayed/dropped scheduled events. Do not count push/manual execution as proof of cron or promise exactly-once ChatGPT delivery. No external dependencies or numeric risk threshold changes.

## 2026-11-16 — second adversarial repair: alert identity and time alignment
- [Prometheus alerting state](https://github.com/prometheus/prometheus/blob/main/rules/alerting.go), [Alertmanager notification log](https://github.com/prometheus/alertmanager/blob/main/docs/high_availability.md): individual firing/resolved instances, not cumulative group membership. Our per-channel dated resolution and re-entry adds no periodic repeats; a missing reading is not a resolution.
- [pandas ordered joins](https://github.com/pandas-dev/pandas/blob/main/doc/source/user_guide/merging.rst): match explicit dated keys; use exact observation-date joins, not interpolation or nearest-date substitution. Retain a bounded recent source window in the stdlib implementation. A newer observed normal reading invalidates older stress. The replay engine separately selects only versions released by the decision instant.
- [GitHub Actions concurrency controls](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency), [run-attempt identity](https://docs.github.com/en/actions/reference/workflows-and-actions/variables), [rerun semantics](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/re-run-workflows-and-jobs): queue up to 100 pending runs, keep one writer, check out the current main state, separate natural first attempt from retries. The cap and provider scheduling remain best-effort, not a guaranteed heartbeat.

## 2026-11-16 — cross-stage durable candidate handoff
- [Microsoft architecture-center transactional outbox](https://learn.microsoft.com/en-us/azure/architecture/databases/guide/transactional-out-box-cosmos) and [idempotent consumer](https://github.com/MicrosoftDocs/architecture-center/blob/main/docs/patterns/idempotent-consumer.md): persist intent before external side effects; use stable IDs through replay and acknowledgement. FCEWS uses existing Git state/outbox/feed written together before Issue delivery, not an external broker or database transaction guarantee. A failure of the optional Issue API must not prevent publication of the durable pending candidate. Original creation age is not refreshed by retries.
- [Alertmanager notification log](https://github.com/prometheus/alertmanager/blob/main/docs/high_availability.md): compare changes in firing/resolved identities rather than treat all repeated observations as new alarms. Preserve exact-date groups; use newly confirmed channel identity across all currently valid dates, not the latest display group. No periodic user repeats.

## 2026-11-17 — reuse before adding
- [Ponytail](https://github.com/DietrichGebert/ponytail): apply the minimal complete change, reuse existing code and avoid unnecessary dependencies; preserve nontrivial risk validation. Adopted in [development protocol](../../docs/operations/DEVELOPMENT.md), not installed as another runtime component.
- [QuantConnect LEAN time frontier](https://github.com/QuantConnect/Lean), [time-slice specification](https://www.quantconnect.com/docs/v2/writing-algorithms/key-concepts/time-modeling/timeslices): release availability determines what is observable at each decision. Reuse [existing replay](../../src/fcews/backtest.py) for benchmark/coverage rather than importing a trading engine. [ALFRED official API](https://fred.stlouisfed.org/docs/api/fred/series_observations.html) distinguishes vintage revisions; raw licensed data stay outside Git. No new dependency.


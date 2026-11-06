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

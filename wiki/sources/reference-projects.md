---
title: Source — External Financial Monitoring Projects
kind: source
status: under-review
updated: 2026-10-28
summary: Pointers for implementation research without copying undocumented performance claims.
---

# External implementation references

Code patterns are **inputs for inspection**, not independent validation of the user's financial-risk model.

- [macro-liquidity-pipeline](https://github.com/lauren-shih/macro-liquidity-pipeline) — study data provenance and release alignment; project applicability requires a concrete code review.
- [credit-spread-analyzer](https://github.com/AndrewFSee/credit-spread-analyzer) — possible credit signal measurement and walk-forward tests, not proof of a trading edge.
- [CBSRM / CISS-Sahm systemic risk](https://github.com/Allisterh/cbsrm-CISS-Sahm-rule-systemic-risk) — stress aggregation and explainability concepts; verify licensing and dependencies before reuse.
- [nvk/llm-wiki](https://github.com/nvk/llm-wiki) — agent navigation, MOC, schema and operational memory.

**Status:** architectural inspiration only. No copied source code, no imported return statistics, no claim these references outperform FCEWS. A future documented review should specify commit/version, license, applicable method, limitations and test fixture.

Tracking: [taskboard](../tasks.md), [point-in-time testing](../concepts/point-in-time.md).

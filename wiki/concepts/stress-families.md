---
title: Independent Stress Indicator Families
kind: concept
status: active
updated: 2026-11-16
summary: Stops correlated indexes and multiple credit spreads from falsely triggering an independent-family alarm.
---

# Independent stress families

Alert condition 2 is **two or more independent evidence families simultaneously in pressure regimes**, not two tickers or two news articles. Count each family once. The legacy technical grade tracks the following overlapping diagnostic groups, not four independent votes:

| Family | Current inputs | Major limitation |
| --- | --- | --- |
| System-wide conditions | OFR FSI, STLFSI4, NFCI, ANFCI | Composite inputs overlap with direct credit, volatility and funding measures |
| Credit funding | BAMLH0A0HYM2 | Index percent, high-yield weakness can be sector-specific |
| Market volatility | VIXCLS | Equity implied volatility alone is not funding failure |
| Overnight financing | SOFR–TGCR | Small scalar spread can miss collateral haircuts and non-bank run pressure |

DGS10 / DGS30 are currently context only; elevated yields without functioning-market breakdown are not an automatic crisis flag. The automatic two-family candidate gate requires at least two distinct direct channels on the same observation date; composites are corroboration only. See [OFR methodology](https://www.financialresearch.gov/financial-stress-index/) and [core regression tests](../../tests/test_core.py). Same-date matching is deliberately conservative, not proof of statistical independence; separately verified overlapping windows and contagion events remain eligible for user-level review. The former raw technical grade remains for continuity and is not alert authorization.

A proxy is not an identity: normal SOFR/TGCR spread **does not prove** banks or private funds are healthy. Use event evidence for emerging contagion and supplement funding gauges (SRF, repo fails, volatility, dealer balance sheet).

The cutoffs currently encoded are provisional heuristics. Historical calibration is [Issue #3](https://github.com/lican1213/financial-crisis-early-warning/issues/3), not a completed validation. See [data registry](../datasets/registry.md) and [point-in-time availability](point-in-time.md).

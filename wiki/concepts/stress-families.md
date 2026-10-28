---
title: Independent Stress Indicator Families
kind: concept
status: active
updated: 2026-10-28
summary: Stops correlated indexes and multiple credit spreads from falsely triggering an independent-family alarm.
---

# Independent stress families

Alert condition 2 is **two or more independent evidence families simultaneously in pressure regimes**, not two tickers or two news articles. Count each family once. Current `src/fcews/core.py` families:

| Family | Current inputs | Major limitation |
| --- | --- | --- |
| System-wide conditions | STLFSI4, NFCI, ANFCI | Correlated, weekly and revised; not three independent alarms |
| Credit funding | BAMLH0A0HYM2 | Index percent, high-yield weakness can be sector-specific |
| Market volatility | VIXCLS | Equity implied volatility alone is not funding failure |
| Overnight financing | SOFR–TGCR | Small scalar spread can miss collateral haircuts and non-bank run pressure |

DGS10 / DGS30 are currently context only; elevated yields without functioning-market breakdown are not an automatic crisis flag. OFR FSI will require a decision about overlap with STLFSI4/NFCI rather than auto-counting as a new independent family.

A proxy is not an identity: normal SOFR/TGCR spread **does not prove** banks or private funds are healthy. Use event evidence for emerging contagion and supplement funding gauges (SRF, repo fails, volatility, dealer balance sheet).

The cutoffs currently encoded are provisional heuristics. Historical calibration is [Issue #3](https://github.com/lican1213/financial-crisis-early-warning/issues/3), not a completed validation. See [data registry](../datasets/registry.md) and [point-in-time availability](point-in-time.md).

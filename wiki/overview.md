---
title: FCEWS Living System Overview
kind: overview
status: active
updated: 2026-10-28
summary: A concise synthesized account of the actual warning system, boundaries and open causal questions.
---

# System overview (living synthesis)

The user needs a financial-crisis monitor that is **quiet by default**: notify only when a weekly grade truly changes, two independent indicator families are simultaneously stressed, a confirmed event can transmit across markets, or previous stress recedes convincingly. Frequent market moves by themselves are not equivalent to a financial crisis.

Current v0.2 is a rule-based prototype, not a calibrated predictive model. The [four gate contract](concepts/alert-contract.md) is coded in `src/fcews/core.py` with daily and weekly FRED observations. The project does not yet ingest OFR FSI/MOVE, bank or private credit event records automatically, verify first-publication timestamps for historical simulation, or deliver alerts via ChatGPT.

The most important research risk is mistaking **measurement convenience** for systemic stress: three correlated Fed indexes can masquerade as three independent alarms, SOFR/TGCR spreads can miss collateral-level stress, and retrospectively revised series can make crisis prediction appear easier than it was. See [independent families](concepts/stress-families.md), [point-in-time discipline](concepts/point-in-time.md), and the [failure register](operations/INCIDENTS.md).

Engineering objective: a reproducible warning gate with explicit data availability and candidate-event provenance; then calibrated risk detection on out-of-sample historical windows; only then live notification and potential portfolio use. Silence means no *new sufficient trigger*, **not** proof that all markets are healthy.

Next action: verify real GitHub Actions executions and stamp interface-first available times. See [GitHub task board](tasks.md).

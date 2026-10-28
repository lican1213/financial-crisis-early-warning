# FCEWS — Financial Crisis Early Warning System

Evidence-first, source-dated financial-crisis monitor. **No material change means no alert.** The goal is reliable crisis escalation, not reporting every market move.

## Current deployment: model v0.2 / second brain v0.3
- Python FRED collector: STLFSI4, NFCI, ANFCI, HY OAS, VIX, SOFR/TGCR, DGS10, DGS30.
- Four candidate alert gates: above a sourced weekly baseline; two independent stress families; verified potentially contagious event; sustained recovery on distinct observation dates.
- GitHub Actions workflow templates for hourly checks and candidate issue reporting. **Live execution has not yet been verified.** GitHub candidate Issues are **not** automatic ChatGPT notifications.
- OFR FSI, MOVE, Treasury market depth, VIX futures curve and complete private-credit/bank feeds **are not connected**.
- Thresholds are provisional; this is not an out-of-sample calibrated crisis prediction model.
- Repository was observed **public** on 2026-10-28: no keys, personal portfolio allocations or secrets.

## Agent-first second brain
Read [wiki/_index.md](wiki/_index.md) → [current handoff](wiki/operations/HANDOFF.md) → [Issue taskboard](wiki/tasks.md) → relevant [MOC maps](wiki/mocs/ENGINEERING.md). The [AGENTS.md](AGENTS.md) contract tells any ChatGPT/Codex/Claude/OpenCode agent how to maintain source provenance, API manifests, historical decisions, failure cases and tests. GitHub Issues are canonical for task status; no fake completed milestones.

## Run locally

    PYTHONPATH=src python -m unittest discover -s tests -v
    python scripts/wiki_lint.py
    PYTHONPATH=src python -m fcews.cli

The engine stores observations with dates but not verified first-release timestamps yet. HY OAS is expressed in percent (6.0 = 600bp); SOFR/TGCR difference is percent points (0.15 = 15bp). Correlated conditions indexes count as one family. Unknown data must not imply green.

For historic protocol see [point-in-time discipline](wiki/concepts/point-in-time.md) and [backtest](docs/moc/BACKTEST.md). For risks and gaps see [incident register](wiki/operations/INCIDENTS.md).

# FCEWS — Financial Crisis Early Warning System

Evidence-first, source-dated financial-crisis monitor. **No material change means no alert.**

## v0.2.0
- Public FRED source readings: STLFSI4, NFCI, ANFCI, HY OAS, VIX, SOFR/TGCR, DGS10 and DGS30.
- Gates: sourced weekly escalation, two independent stress families, newly verified contagion event, and recovery on three distinct observation dates.
- Hourly checking and GitHub candidate issues are planned in the Actions workflow. ChatGPT push is a separate unintegrated channel.
- OFR FSI, MOVE, Treasury real-time depth and full VIX curve are not yet integrated.
- **Repository currently public:** do not store secrets, portfolio holdings or personal information.

## Commands

    PYTHONPATH=src python -m unittest discover -s tests -v
    PYTHONPATH=src python -m fcews.cli

## Method
HY OAS is expressed in **percent** (6.0 = 600bp). SOFR/TGCR difference is also in percentage points (0.15 = 15bp). Related financial stress indexes count as **one family**. No crisis probabilities are claimed. Weekly baseline defaults to unknown until sourced.

Read docs/moc/INDEX.md and docs/moc/FAILURES.md before changes. Learn from macro-liquidity-pipeline (PIT), credit-spread-analyzer (out-of-sample testing) and CBSRM (audit trail). Project does not copy third-party code.

# FCEWS — Financial Crisis Early Warning System

**Quiet by default. No material change → no investor-facing crisis notification.**

## Verified operation — v0.3 (2026-10-29)

- [Live official-source run 40788157364](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40788157364) succeeded, retrieving 11 dated observations spanning four independent stress families: OFR FSI, STLFSI4/NFCI/ANFCI, HY OAS, VIX, SOFR/TGCR/BGCR and Treasury 10Y/30Y. One FRED TGCR error was recovered by the NY Fed primary API.
- The [source-health record](data/health.json), [observations](data/observations.json), and [first-seen/revision log](data/vintage_log.jsonl) provide inspectable evidence. The hourly workflow reports degraded source coverage as an operational failure, NOT as a financial-crisis event.
- GitHub candidate issues use a durable outbox, issue-fingerprint deduplication, and readback receipts; an Issue is NOT an integrated ChatGPT notification.
- The PIT replay engine can evaluate source-released-at snapshots, but no full historical original-vintage holdout has been obtained. Heuristic risk thresholds are not calibrated crisis probabilities.
- MOVE, live Treasury order depth, complete VIX term structure, bank/private credit contagion automation and real end-user notification delivery remain unresolved.

## Run and audit

    PYTHONPATH=src python -m unittest discover -s tests -v
    python scripts/wiki_lint.py
    PYTHONPATH=src python -m fcews.cli --require-healthy
    PYTHONPATH=src python -m fcews.backtest --features PIT.csv --decisions TIMES.csv --events LABELS.csv

The FRED public CSV adapter needs no key; the official JSON API is used when FRED_API_KEY is configured. [OFR original CSV](https://www.financialresearch.gov/financial-stress-index/data/fsi.csv) and [NY Fed rate APIs](https://markets.newyorkfed.org/static/docs/markets-api.html) are integrated.

## Persistent agent second brain and cycle table

- [MOC master index](wiki/_index.md), [agent contract](AGENTS.md), [data registry](wiki/datasets/registry.md), [live agent handoff](wiki/operations/HANDOFF.md), [adversarial failure register](wiki/operations/INCIDENTS.md), and [Issue tracker](https://github.com/lican1213/financial-crisis-early-warning/issues).
- [Hourly / daily / weekly / monthly cadence table](docs/operations/CADENCE.md) defines GitHub workflows and independent ChatGPT briefing responsibilities.
- [Historical validation protocol](docs/moc/BACKTEST.md).

The repository remains public; store no secrets or private account and portfolio details. Technical four-family grades are NOT automatically identical to the user's broader weekly high-risk watch grade until a signed/source-dated weekly baseline exists.

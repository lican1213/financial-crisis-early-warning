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

## V0.4 source audit — 2026-10-29
[117 passing tests and 29-page MOC audit](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40801824139). Official source context now includes [OFR repo](data/stfm_context.json), [ECB CISS](data/ecb_ciss_context.json), [FDIC review queue](data/fdic_review.json) and [Cboe implied-vol tenors + actual monthly VX futures](data/volatility_context.json). All remain context unless independently calibrated. The licensed ICE MOVE index is not impersonated.
[Non-crisis GitHub canary Issue #11](https://github.com/lican1213/financial-crisis-early-warning/issues/11) was created/read back/closed. ChatGPT's existing hourly and Sunday tasks were updated to pull source evidence; no GitHub-to-ChatGPT webhook is claimed.
[Real ex-post historical diagnostic](reports/expost_latest.json) still misses selected 2011 and 2023 stress events, including the separate pre-2007 BAA10Y credit sensitivity. [Public ALFRED vintage test](reports/alfred_smoke.json) initially returned HTTP 404, but a later per-date probe accepted 11 of 20 ALFRED as-of cells (with 2008 and many HY vintages missing); consequently the system is not a validated point-in-time crisis forecaster. [Current cadence](docs/operations/CADENCE.md); [agent handoff](wiki/operations/HANDOFF.md).

Latest evidence: [partial ALFRED public as-of smoke](https://github.com/lican1213/financial-crisis-early-warning/blob/main/reports/alfred_smoke.json) accepted VIXCLS 4/5, NFCI 4/5, STLFSI4 2/5, HY OAS 1/5 across five dates; 20% three-family coverage. This is **not** a complete historical PIT backtest.

## 2026-10-29 — Historical as-of source and ChatGPT v1 polling feed (latest)
- [Confirmed live Cboe data](data/volatility_context.json): VIX9D/VIX/VIX3M/VIX6M and genuine *monthly* CFE VX F1/F2 futures, 2026-10-28 contango +0.177; 2/5/10/30Y UST 20-day realized yield volatility. ICE MOVE remains a separate proprietary/licensed series, not a substitute. 
- [Verified public ALFRED as-of smoke](reports/alfred_smoke.json): original as-of snapshots succeeded for VIX and NFCI on four of five selected historical dates, STLFSI4 on two, HY OAS on one; 2008 and older credit-vintage access remain incomplete. [Full 2007–2026 weekly as-of Action](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40802656579) must finish before any longitudinal historical accuracy claim.
- [Historical coverage audit](src/fcews/coverage.py) separates events unassessable from missing source families from true model missed alerts; [adversarial coverage tests](tests/test_coverage.py). Parameters remain frozen, no ex-post tuning. 
- [Real GitHub-to-ChatGPT read-only feed](data/chatgpt_feed.json): schema fcews.chatgpt.readonly.v1, verified candidate Issue receipt and source-health summary, defaults to should_send_user_notification=false. Existing ChatGPT hourly condition-watch automation has been updated to read the feed and independently apply four user triggers. This is **hourly polling**, not a webhook or an end-user delivery acknowledgement.
- [Updated operational cycle table](docs/operations/CADENCE.md). Historical vintage supply and direct ICE MOVE quote licensing remain open acceptance gates.

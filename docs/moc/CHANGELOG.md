# Changelog
## 2026-10-28 — v0.2.0
- First GitHub deployment of source-dated FRED monitor, risk gate and workflow.
- Fixed duplicate hourly recovery: needs three distinct observation dates.
- Fixed first-run silent blind spot for two-family stress.
- Weekly baseline deliberately unknown until sourced.
- Added audit regression suite and source/change records.
- No calibrated crisis forecasting or ChatGPT push asserted.

## 2026-10-29 — v0.3 verified official source and notification engineering
Added bounded concurrent FRED reader, official OFR FSI CSV, NY Fed secured-rate API, live-source health monitoring, durable idempotent GitHub candidate outbox, first-seen revisions and strict timestamp historical replay. Real [run 40788157364](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40788157364) confirmed 11 official dated observations across four independent source families; no qualifying crisis alert. Adversarial tests cover missing feeds with cache, duplicate delivery after lost response, false recovery by one updating family, and integer/float unchanged-poll churn. Full historical accuracy, proprietary MOVE and end-user ChatGPT push remain open.

## 2026-10-29 — v0.4, official regional stress and observed financial market integration
Added [OFR short-term repo](../../data/stfm_context.json), [ECB CISS](../../data/ecb_ciss_context.json), [FDIC review-only failure queue](../../data/fdic_review.json), [Cboe index and monthly CFE VX futures](../../data/volatility_context.json). Strict regulator HTTPS source hash/readback and reviewer gate; non-crisis GitHub candidate-delivery canary. Added fixed pre-2007 BAA10Y historical sensitivity and strict ALFRED as-of smoke, which failed with 404. Retained selected 2011/2023 misses; no made-up MOVE or point-in-time predictive claims. [117 tests plus wiki lint PASS](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40801824139). Updated [maintenance schedule](../operations/CADENCE.md).

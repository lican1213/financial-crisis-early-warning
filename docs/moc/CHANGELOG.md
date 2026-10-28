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

# FCEWS — Monitoring and audit cadence

Updated 2026-10-29. Unless otherwise specified, times are **Beijing (UTC+8)**. GitHub Actions cron is best-effort; execution records and official observation dates, not scheduled time, determine actual data freshness.

| Frequency | Beijing time | Executor / code | Output / acceptance test |
| --- | --- | --- | --- |
| Hourly | Minute **13** | [GitHub official-source check](../../.github/workflows/check.yml) | Official OFR/FRED/NY Fed four-family decision, source-health and deduped GitHub candidate Issue; regenerated [read-only ChatGPT feed](../../data/chatgpt_feed.json). No new qualifying stress = no user notification |
| Hourly | Independent existing ChatGPT `金融风险预警` condition-watch schedule | ChatGPT automation | Reads the GitHub feed and independently verifies primary regulatory evidence. Sends a user-visible warning **only** for the user’s four trigger conditions; no material change = truly silent. **Not a GitHub push webhook.** |
| Daily | **08:25** | [Test and MOC audit](../../.github/workflows/daily-audit.yml) | Code/adversarial regressions, MOC broken-link and provenance audit |
| Daily | **08:32** | [Funding and institutional context](../../.github/workflows/context.yml) | Official OFR repo/STFM, ECB CISS and FDIC review-only registry; avoid auto-promoting context to independent trigger |
| Weekdays | **08:45** | [Cboe volatility / Treasury context](../../.github/workflows/volatility.yml) | Official VIX9D/VIX/VIX3M/VIX6M, CFE real monthly VX front/second, 20-day Treasury yield realized vol. ICE MOVE remains an unlicensed **separate** series, not an alias |
| Sunday | **10:00** | Existing ChatGPT `金融危机周报` | Six-module macro watch grade, original sources, 3/6/12-month scenarios; sync verified weekly report metadata to [weekly baseline](../../data/weekly_baseline.json). No false conversion of six-module orange to four-family green |
| Monday | **09:00** | Manual/Agent maintenance per [AGENTS](../../AGENTS.md) | Inspect last source success, incident/failure issue queue, test receipts, MOC handoff and missed-event evidence. **This row is not an automated task.** |
| Monthly | Day **2, 10:10** | [ALFRED historical vintage check](../../.github/workflows/alfred-public.yml) | Public ALFRED as-of snapshots, exact requested vintage header, strict no-future data; coverage and missing epochs separate from model false-negative. A full run is **under validation**; failures must not be labelled zero alerts or forecasting success |
| Manual, when authorized | Explicit dispatch | [ALFRED key-based exporter](../../src/fcews/pit_export.py) | Requires authorized `FRED_API_KEY` in environment/Actions Secret; never commit credentials. Date-level vintages cannot certify original intraday publisher timestamp |
| Monthly/quarterly analysis | After historical data passes completeness | [PIT benchmarking](../../src/fcews/benchmarks.py) and [coverage audit](../../src/fcews/coverage.py) | Freeze thresholds pre-holdout; report event evaluability, lead time, misses, false alarms per 100 checks and adverse quiet-market controls. Without adequate historical coverage, keep issue open |
| Event driven | On official validated bank/fund/sovereign/repo/payment crisis | [Event validator](../../src/fcews/events.py) / GitHub outbox | Human-reviewed official document checksum and cross-market contagion mechanism; new candidate not automatically a ChatGPT user warning |

## Delivery boundary
The [ChatGPT feed](../../data/chatgpt_feed.json) is **poll-only**, not a push event or confirmed end-user receipt. [GitHub Issue canary #11](https://github.com/lican1213/financial-crisis-early-warning/issues/11) verifies GitHub create/read/close only; ChatGPT cannot emit an exact-once acknowledgement to the repository. The hourly ChatGPT task remains enabled. We deliberately keep user-visible responses silent without one of the four qualifying systemic changes.

## Data quality gates
A GitHub Action run marked success is not sufficient evidence of market source coverage; inspect `data/health.json`. **degraded** means fewer than three fresh live independent risk families, an operational incident, not calm markets. Context-only Cboe/MOVE substitutes do not independently increase family counts until calibration. No private holdings, credentials or user-specific assets are committed to the currently public GitHub repository.

## Historical limitations
The [ex-post diagnostic](../../reports/expost_latest.json) reports revised-value performance with look-ahead risk, not real-time historical predictive accuracy. [ALFRED smoke](../../reports/alfred_smoke.json) has authenticated some historical as-of snapshots but earlier credit and 2008 dates are missing in the public access path; classify historical **unassessability** separately from true model misses. Full 2007–2026 weekly as-of collection is being tested [here](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40802656579); its completion must be verified before publishing forecasting accuracy. ICE MOVE direct quote and Treasury order-book depth require appropriately licensed access.

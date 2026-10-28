# FCEWS monitoring and maintenance cadence (UTC / Beijing time)

**Updated 2026-10-29.** GitHub Actions schedules are best-effort and may run late. The actual workflow execution is the timestamp of record. A successful job does not mean the underlying data sources worked; inspect `data/health.json` and source observation dates.

| Cadence | UTC trigger / Beijing time (UTC+8) | Activity | Evidence and gate |
| --- | --- | --- | --- |
| **Hourly** | Minute **13 UTC** / minute **13 Beijing** | Pull FRED/OFR/NY Fed, evaluate four alert conditions, persist changed observations, deliver candidate GitHub issue once | `.github/workflows/check.yml`; confirmed source families; health issue if incomplete; no material event = silent |
| **Daily** | 00:25 UTC / **08:25 Beijing** | Run 28+ unit/adversarial tests, MOC lint and source health check | `.github/workflows/daily-audit.yml`; failed step visible in GitHub Actions |
| **Weekly: Sunday** | 02:00 UTC / **10:00 Beijing** | Existing independent ChatGPT financial-crisis weekly briefing; align source-dated weekly FCEWS baseline only after review | ChatGPT weekly brief; `data/weekly_baseline.json`; source and publication date required |
| **Weekly: Monday** | 01:00 UTC / **09:00 Beijing** | Manual/agent audit of false alarms, source gaps, open Issues and MOC manifests | `wiki/tasks.md`, `wiki/log.md`; no duplicated Issues |
| **Monthly** | First week, logged actual execution | PIT historical validation, threshold stability, contagion-model counterexamples, false-positive review | `docs/moc/BACKTEST.md`; only holdout evidence permits threshold promotion |
| **Incident-driven** | Whenever original verified evidence emerges | Review bank, fund, sovereign, repo, energy or payments contagion, then check alert threshold | Reviewed `data/events.json`; GitHub candidate issue is not a ChatGPT push |

**Operational statuses:** healthy = at least three fresh independent stress families and no source errors; partial = at least three families with one or more source failures; degraded = fewer than three fresh families. A degraded run must fail visibly and open one deduplicated DATA-HEALTH issue; it never asserts that the financial system is calm.

**Notification distinction:** The user's existing ChatGPT hourly alert and weekly briefing remain separate from GitHub candidate issues. This cadence documents them; it does not claim or make a delivery integration that has not been tested.

**Known blockers:** FRED requires an API key for the official JSON endpoint; without one the public CSV is a fallback. MOVE, Treasury market depth, and institutional balance-sheet/redeemability data remain outside the fully automated source coverage. The PIT backtest engine accepts original-release timestamps but currently lacks a validated comprehensive historical vintage dataset.

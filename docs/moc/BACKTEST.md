# Point-in-time validation
Historical cases: 2007–09, 2011–12, 2020, 2023. Controls: high VIX without contagion, regional crash, rate selloff with functioning repo.
Use the actual public release time and ALFRED vintages, never observation date or a revised modern history as a substitute.
Metrics: earliest lead-time, missed major systemic events, false alerts per 100 trading days, repeated alerts, silent-run ratio. Don't publish Brier scores until a genuine probabilistic model exists.
Choose thresholds on training periods, evaluate on untouched chronological holdouts, compare with no-alert and VIX-only baselines. Document failures.

## Source-publication-time replay (v0.3)
Run from repo root with three independent supplied CSVs:

    PYTHONPATH=src python -m fcews.backtest --features features.csv --decisions checkpoints.csv --events crises.csv

Features require series, observation_date, first_available_at_utc (offset-aware ISO timestamp), value, source_url; checkpoints require decision_at_utc; events require event_id, crisis_start_utc. The replay excludes unpublished observations and future revisions at each decision time. It counts event misses, early-lead days and false candidate alarms per 100 checkpoints; it does **not** fit crisis probability. Valid historical accuracy requires reconstructing original available-at times (ALFRED/archived publisher release) plus frozen train and chronological holdout. Modern revised CSV alone is inadmissible. An actual comprehensive historical archive and calibrated threshold evaluation remain [Issue #3](https://github.com/lican1213/financial-crisis-early-warning/issues/3).

## 2026-10-29 genuine retrospective failures
[2007–2026 revised-data report](../../reports/expost_latest.json), 5,173 weekday checkpoints, four selected crisis event windows: rule gate 16 candidate alarms, 14 outside the four windows, missed the 2011 and 2023 selected events; VIX-only 53 alarms and 52 unmatched. High-yield ICE OAS public history only from approx 2023-10. A separate fixed cutoff sensitivity using pre-2007 BAA10Y investment-grade credit spread (train N=1,748, q95=3.39 percent) gave selected 2008 lead +2.62 days and 2020 +4 days but still missed 2011/2023 with 14 unmatched. These values are **NOT** source-time-consistent predictions; the limited label set does not prove every unmatched alert false.
[Experimental ALFRED as-of manifest](../../reports/alfred_smoke.json): initial batched requests 4/4 HTTP 404; later individual as-of checks accepted 11/20 source-date cells but lacked enough coverage to validate four event windows. Authenticated API vintage exporter and chronology tests exist, but real original-publisher timestamps and out-of-sample PIT cannot be claimed. An expensive automatic historical full-run has been suspended until source verification. [Open historical task #3](https://github.com/lican1213/financial-crisis-early-warning/issues/3).

Latest evidence: [partial ALFRED public as-of smoke](https://github.com/lican1213/financial-crisis-early-warning/blob/main/reports/alfred_smoke.json) accepted VIXCLS 4/5, NFCI 4/5, STLFSI4 2/5, HY OAS 1/5 across five dates; 20% three-family coverage. This is **not** a complete historical PIT backtest.

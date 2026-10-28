# Point-in-time validation
Historical cases: 2007–09, 2011–12, 2020, 2023. Controls: high VIX without contagion, regional crash, rate selloff with functioning repo.
Use the actual public release time and ALFRED vintages, never observation date or a revised modern history as a substitute.
Metrics: earliest lead-time, missed major systemic events, false alerts per 100 trading days, repeated alerts, silent-run ratio. Don't publish Brier scores until a genuine probabilistic model exists.
Choose thresholds on training periods, evaluate on untouched chronological holdouts, compare with no-alert and VIX-only baselines. Document failures.

## Source-publication-time replay (v0.3)
Run from repo root with three independent supplied CSVs:

    PYTHONPATH=src python -m fcews.backtest --features features.csv --decisions checkpoints.csv --events crises.csv

Features require series, observation_date, first_available_at_utc (offset-aware ISO timestamp), value, source_url; checkpoints require decision_at_utc; events require event_id, crisis_start_utc. The replay excludes unpublished observations and future revisions at each decision time. It counts event misses, early-lead days and false candidate alarms per 100 checkpoints; it does **not** fit crisis probability. Valid historical accuracy requires reconstructing original available-at times (ALFRED/archived publisher release) plus frozen train and chronological holdout. Modern revised CSV alone is inadmissible. An actual comprehensive historical archive and calibrated threshold evaluation remain [Issue #3](https://github.com/lican1213/financial-crisis-early-warning/issues/3).

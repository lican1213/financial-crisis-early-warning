# FCEWS — Monitoring and audit cadence (2026-10-29)

All times below are **Beijing time (UTC+08:00)**. GitHub Actions cron runs in UTC and can be delayed. Its recorded run timestamp, not scheduled time, is controlling.

| Cadence | Beijing time | Actual execution | Acceptance rule |
|---|---|---|---|
| Hourly | Minute 13 | [.github/workflows/check.yml](../../.github/workflows/check.yml) | FRED/NY Fed/OFR, four-family silent alert gate, durable issue outbox; degraded source != market calm |
| Hourly | Existing independent ChatGPT schedule | Financial risk alert automation | Reads GitHub source state and verifies official evidence; only four user-defined conditions notify |
| Daily | 08:25 | [.github/workflows/daily-audit.yml](../../.github/workflows/daily-audit.yml) | Model tests, adversarial edge cases and MOC lint |
| Daily | 08:32 | [.github/workflows/context.yml](../../.github/workflows/context.yml) | OFR repo STFM, ECB eurozone CISS, FDIC bank-failure review queue (no automatic crisis announcement) |
| Weekdays | 08:45 | [.github/workflows/volatility.yml](../../.github/workflows/volatility.yml) | Official Cboe VIX implied-vol tenors, real CFE monthly VX front futures, Treasury realized vol; MOVE remains licensed/absent |
| Sunday | 10:00 | Original ChatGPT global financial crisis weekly brief | Six-module macro risk grade and sourced weekly-report record; not equivalent to technical 4-family grade |
| Monday | 09:00 | Human/Agent maintenance review | GitHub Issues, failed data sources, false alerts, MOC handoff, last verified commit |
| Monthly | First week, manually logged | Historical PIT validation | Original vintages, first-public timestamps and 2008/2011/2020/2023 missed-alert audit; no misleading revised-series predictive claims |
| On demand | GitHub manual dispatch | [ALFRED vintage smoke](../../.github/workflows/alfred-public.yml), [revised-data ex-post](../../.github/workflows/expost.yml) | Initial ALFRED batch returned 404; a corrected single-vintage method retrieved 11/20 smoke cells, but source coverage is incomplete; full automatic retries suspended until verified stability |
| Incident-driven | When original evidence is reviewed | [Official event gate](../../src/fcews/events.py), [FDIC review](../../src/fcews/fdic.py) | Actual regulator document SHA-256, reviewer, time, plausible contagion; candidate Issue only |

**Verification:** [117 passing tests and MOC structural audit](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40801824139). [Official volatility source run](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40801824156), [ECB/OFR/FDIC source run](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/40801545198), [non-crisis Issue canary](https://github.com/lican1213/financial-crisis-early-warning/issues/11). [Ex-post historical limits](../../reports/expost_latest.json), [zero ALFRED vintages/404](../../reports/alfred_smoke.json).

**Boundaries:** GitHub candidate Issues are not ChatGPT webhook notifications. Genuine licensed ICE MOVE and market-depth feeds are unavailable. Missed historical events remain visible. Identical data must not generate repeated hourly notifications.

Latest evidence: [partial ALFRED public as-of smoke](https://github.com/lican1213/financial-crisis-early-warning/blob/main/reports/alfred_smoke.json) accepted VIXCLS 4/5, NFCI 4/5, STLFSI4 2/5, HY OAS 1/5 across five dates; 20% three-family coverage. This is **not** a complete historical PIT backtest.

---
title: Source-dated Leading Research Registry
kind: dataset
status: active
updated: 2026-11-09
summary: US official indicator automation, China and staffing release ledger, data lineage and non-alert gates.
---

# Source-dated leading research layer

**Purpose:** retain useful weekly-report research **inside** FCEWS as structured monitoring context, without reinstating a weekly push and without confounding the independent four-family crisis severity.

## Installed code and cadence
- [Research collector and evidence gates](../../src/fcews/research.py)
- [Official research workflow](../../.github/workflows/research.yml) at Beijing 09:39 daily, best-effort.
- [Unpopulated official release ledger](../../data/research_evidence.json) contains **no invented observations**.
- [Adversarial tests](../../tests/test_research.py).
- Output on a successful main workflow: [data/research_context.json](../../data/research_context.json). Live [Actions run 42547475174](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/42547475174) independently read back six current official-source observations with no missing codes. The [monitoring run 42547475263](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/42547475263) showed healthy financial coverage with no candidate alerts. The [ChatGPT bridge](../../src/fcews/bridge.py) now forwards only snapshot dates and freshness, not risk approvals.

## Automated US official indicators

| Series | Producer / transport | Unit | Cadence | Interpretation |
| --- | --- | --- | --- | --- |
| TEMPHELPS | BLS CES via FRED | thousand persons SA | monthly | Temporary help employment is an imperfect demand proxy |
| JTSJOL | BLS JOLTS via FRED | thousand openings SA | monthly | Vacancies stock, **not** hires or new job ads |
| ICSA | US Department of Labor via FRED | persons SA | weekly | New unemployment claims, not total unemployment |
| T10Y3M | Fed / Treasury via FRED | percentage points | daily | Treasury term spread |
| T10Y2Y | Fed / Treasury via FRED | percentage points | daily | Treasury term spread |
| BAMLC0A0CM | ICE BofA via FRED | percentage points | daily | Investment-grade OAS (licensed original provider) |

Each record carries observation date, retrieval time, unit, producer and source URL. **Original release timestamp and historical vintage are not supplied by current FRED latest-value adapter**; output explicitly labels that gap. Monthly values must be observed on first day of reporting month, finite and within a 75-day grace window. A stale, malformed or mismatched source is omitted and the job fails its source-coverage gate rather than treating missing as 0/green.

## Structured release ledger: no guessed data

`data/research_evidence.json` is initially `{"releases":[]}`. Each proposed official release contains `series,authority,unit,value,period_end,published_date,source_url,definition,measure_type`. Code rejects future publication, incorrect units, spoofed hostname and duplicates. **Domain and schema validation do NOT prove that a source page actually contains the claimed figure**: independent official-document readback and a release-vintage ledger are required before promoting any user-facing numerical claim or score.

Registered corporate demand-side emitters: Randstad, ManpowerGroup, Korn Ferry, Hays, PageGroup; optional Adecco, Recruit/Indeed and Robert Half. Net profit is deliberately excluded as a recruiting demand proxy. Core release measures include organic/constant-currency/LFL revenue or gross fees, temporary/contract volume, placements and RPO orders. Cost cuts/FX/M&A must be separately annotated in a reviewed report.

Registered China groups: NBS PMI/new orders/small firms, 70-city new/used price-breadth counts, sales, residential unsold inventory, developer funds, private investment and retail; PBOC household medium-long credit, household consumption credit, **separate mortgage outstanding**, and government-bond vs company credit financing.

**Non-equivalence rule:** household medium/long loans include business and consumption; consumer medium/long loans include but are not equal to personal mortgages; developer received mortgage funds are neither household loan stock nor new household mortgage credit. Prepayments can influence mortgage balances. 2025 M1 measurement change requires comparable vintages.

## Turning point and score gates

No nationwide property turning point without at least two of three independently improving price breadth, residential sales and mortgage credit in a compatible release period, plus inventory not deteriorating. Missing stock, mismatched reporting months or stale releases => `confirmed=false`. The objective indicator is only a **diagnostic**, not evidence of causality.

China Recovery Breadth and global Staffing Pulse must remain `null` until sufficiently complete official data and explicit fixed scoring/calibration rules exist. Do **not** copy the prior human weekly 35/58 scores into current live context. The last human six-module score is historical baseline only.

No change to `src/fcews/core.py` four-family thresholds, severity model, user alerts or `data/weekly_baseline.json`. Runtime context cannot authorize a ChatGPT notification. Four-family `severity=unknown` and `model_comparability=not_calibrated` remain independent of old human orange.

## Acceptance and known blockers
- Test fake official hosts, compromised company profitability proxy, impossible release date, 71/70-city counts, NaN, duplicate revisions, one-component price bounce, deteriorating inventories, missing monthly US series.
- **Operational limitation:** a well-formed `stats.gov.cn` URL is not proof that each reported number was checked against a signed/archived release. The ledger is deliberately empty. Human review or a genuine source-specific parser/verification mechanism is still required before assigning CN or firm scores.
- **Cadence limitation:** extra GitHub cron slots are best-effort, not an independent heartbeat or guaranteed hourly SLA.
- **PIT limitation:** latest observations are not as-published original vintages; historical predictive-accuracy gate remains open.

Related: [Data MOC](../mocs/DATA.md), [Engineering MOC](../mocs/ENGINEERING.md), [ADR-0003](../decisions/ADR-0003.md), [issue #14](https://github.com/lican1213/financial-crisis-early-warning/issues/14).


## 2026-11-09 genuine NBS China PMI source extraction (live gate pending)
- [NBS official release discovery and parser](../../src/fcews/nbs.py) retrieves the [National Bureau of Statistics latest release index](https://www.stats.gov.cn/sj/zxfbhjd/) and selects the latest correctly dated `中国采购经理指数运行情况` article under an exact official hostname/path. It then extracts manufacturing PMI, manufacturing new orders, and **small-enterprise PMI** from the **manufacturing** section of the original document, not a news quote or manually typed ledger value.
- Records distinct **survey month**, **period end**, **original-page publication date** and **source URL**. A false official hostname, unpublished future release, title/month conflict, >100 PMI, missing figures or mixing nonmanufacturing orders with manufacturing are rejected with explicit errors. See [adversarial tests](../../tests/test_nbs.py).
- Daily [research workflow](../../.github/workflows/research.yml) now executes this source adapter separately from FRED and writes `data/nbs_pmi_context.json` after a live successful run. Its [ChatGPT feed handoff](../../src/fcews/bridge.py) contains source dates only and is never an autonomous financial-crisis alert.
- **Still missing:** production live-run readback, NBS 70-city full longitudinal price-breadth data, PBOC loan categories/early prepayment breakdown, staffing corporate IR source-value extraction and a calibrated macro breadth score. No original-release historical backtest is claimed.


## 2026-11-09 official NBS price census and developer financing (Issue #14)

- [NBS 70-city and national property source parser](../../src/fcews/nbs_property.py): retrieves actual NBS original releases, extracts all 70 new-home and all 70 used-home **monthly index = 100** rows, rejects duplicates, missing cities, future dates, invalid table boundaries, and mismatched reporting periods. It computes counts above/equal/below 100, year-over-year positive breadth, and source period changes. This is a census of **70 sample cities** and not a nationwide average price.
- Current official sample: [September price table](https://www.stats.gov.cn/sj/zxfb/202610/t20261019_1965609.html), [August price table](https://www.stats.gov.cn/sj/zxfb/202609/t20260915_1965304.html). Source discovery checks `/sj/zxfb/` and falls back to these **real** official original releases only while within the freshness window; no imputed rows.
- [September national property report](https://www.stats.gov.cn/sj/zxfb/202610/t20261019_1965615.html) and [August report](https://www.stats.gov.cn/sj/zxfb/202609/t20260915_1965310.html) permit an honest like-for-like comparison of YTD residential sales area/value growth, unsold area and developer receipts. These are **cumulative YTD year-over-year rates**, not monthly series. `developer_received_mortgages` is developer *cash receipts* and never PBOC household mortgage credit stock.
- Objective turning-point gate remains **false** until PBOC independently issued personal-mortgage stock/flows and inventory corroboration are available; source optimism in two categories alone is insufficient. See [counterexample tests](../../tests/test_nbs_property.py).

## 2026-11-09 issuer-level recruiting release ingestion

- [Five-issuer primary source adapters](../../src/fcews/staffing_ir.py) and [red-team tests](../../tests/test_staffing_ir.py). Original releases: [Randstad 2026Q3](https://www.randstad.com/press/2026/q3-2026-continued-top-line-momentum-drives-double-digit-profit-growth/), [ManpowerGroup Q3](https://investor.manpower.com/news-releases/news-release-details/manpowergroup-reports-3rd-quarter-2026-results), [Korn Ferry FY27 Q1](https://ir.kornferry.com/news-events/press-releases/detail/733/korn-ferry-announces-first-quarter-fiscal-2027-results-of-operations), [Hays results centre FY27 Q1](https://www.haysplc.com/investors/results-centre), [Michael Page stock exchange Q3 RNS](https://www.londonstockexchange.com/en/news/article/PAGE/third-quarter-2026-trading-update/17832048).
- Each firm reports a different economic measure: organic revenue (Randstad), organic constant currency revenue (ManpowerGroup), fee revenue constant currency (Korn Ferry), like-for-like net fees (Hays), or constant currency gross profit (Michael Page). **Never average level changes in these measures as though they are identical hiring volumes.**
- A five-firm positive-direction **breadth percentage**, if all five official texts pass, is an interpretable descriptive share and not a calibrated Staffing Pulse score. The global pulse remains **null** until original statements, contract volumes, geographic breadth and lead-time weighting have passed separate calibration.
- Finance, FX, M&A and cost cuts are diagnostic qualifications, **not hiring-demand observations**. Source errors or company-site blocking produce explicit missingness rather than a made-up value. Dynamic future issuer IR releases are not automatically assumed to exist: the currently pinned Q3 report URLs age out after 120 days and the source register must advance to confirmed new filings. SEC EDGAR/UK RNS and issuer sources are primary; news aggregators do not fill gaps.
- Data are public and source-dated, never personal portfolio data. The [read-only feed](../../src/fcews/bridge.py) forwards only reviewed source-period/direction and independent freshness; no direct user notification permission.


### Real first-run source limitations (2026-11-09)
The [initial main research execution](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/42605458287) recorded `NBS 70-city response exceeds size limit` at both primary URLs under the default 1MB FRED collector; a dedicated **bounded** NBS 12MB reader was added rather than globally weakening source limits. ManpowerGroup original IR returned 403; its alternate official corporate press page replaces the first source. Michael Page LSE gross-fee extraction required issuer-specific parser revision. CI and live source readback are mandatory to mark these repairs complete; do not fill unavailable figures with Reuters or a guessed prior report.

### Primary issuer PDF recovery — 2026-11-09
Michael Page / PageGroup previously exposed only a dynamic HTML shell at the LSE news URL, without the report's text. The canonical original [Q3 2026 issuer PDF](https://investors.michaelpage.com/~/media/Files/P/page-v2/ir/result-reports/2026/q3-2026-trading-statement.pdf) is linked directly from [Michael Page investor relations](https://investors.michaelpage.com/). Official report dated 13 October 2026 shows group constant-currency gross profit **+1.5%**, permanent **+1.1%** and temporary **+2.6%**. The [PDF parser](../../src/fcews/staffing_ir.py) reads raw PDF with pinned pypdf, rejects non-PDF, unsafe redirect, oversized PDF, absent extractable text, wrong quarter and incompatible demand basis; hashes the original bytes. Actual hiring **volume** is not inferred from fee growth. [Adversarial tests](../../tests/test_staffing_ir.py) exercise these failures. Only after official PDF live Action readback can PAGEGROUP and five-issuer breadth be marked complete. This is a *descriptive* positive-fee share, not a calibrated 0–100 staffing pulse.

## 2026-11-09 China credit: original PBOC agency statistics distributed on official government pages

[Official PBOC 2026Q3 household loan-allocation report, republished by Shanghai government's financial office 2026-10-29](https://jrj.sh.gov.cn/SCDT197/20261029/ef0635afddcd4b73a684a2c1e10ec846.html) and [PBOC Jan–Sep 2026 financial statistics, Shanghai official government republication 2026-10-15](https://jrj.sh.gov.cn/SCGK194/20261015/24a15f78c09947de9eb58a48c2fdb451.html) are **original PBOC agency report text distributed by a second official-government publisher**, not the first PBOC website/API release timestamp. This is explicitly tagged `official_government_republication_not_original_first_publication_vintage`; PIT backtesting must not treat government republishing dates as original availability.

The [source parser](../../src/fcews/pboc_credit.py) reads these two fixed, verified official-government documents rather than copying news/secondary analyses. It enforces original agency attribution, report title, publication date, same Q3 period, exact official domain/path, unit/tenor reconciliation and complete key measures: **individual mortgage balance 35.91 trillion yuan, YoY −4.1%, first-nine-month net change −1.10 trillion**; **household medium-long loan YTD flow +1062 hundred-million yuan**; household business-loan balance 25.64 trillion (+1.7% YoY); nonmortgage consumption loan balance 20.69 trillion (−2.8% YoY); corporate medium-long flow +6.53 trillion; bills +1.24 trillion; government bond net financing +10.3 trillion out of total TSF +27.46 trillion, **37.51% of flow**. All refer to public macro categories, never private user holdings.

**First principles:** a household medium-long *flow* includes business and consumption; consumption includes but is not equal to housing mortgages. Household mortgage *stock and net change* differs from developer-received mortgage *cash flow* in NBS reports. Household mortgage prepayment and new loan origination are unobservable in the present source. Therefore a positive 1062 hundred-million medium-long household flow **cannot** identify positive new home-loan demand while actual mortgage balance fell. Nor does a +27.46 trillion TSF aggregate prove private credit is strong with 37.51% of flow from government debt.

The [read-only ChatGPT interface](../../src/fcews/bridge.py) carries original quarter, provenance and distinct units only, no alert permission and no national turning-point confirmation. Descriptive credit shares are **not** the China Recovery Breadth score, and `private_credit_impulse` remains null absent appropriately period-aligned historical first-release inputs. See [credit negative tests](../../tests/test_pboc_credit.py).

### 2026-11-09 recruiter IR outage and last-verified source separation
After a successful authentic 5/5 official issuer snapshot was persisted, a subsequent [2026-11-09 research run](https://github.com/lican1213/financial-crisis-early-warning/actions/runs/42608746339) encountered a *transient ManpowerGroup official site timeout*. This caused current `data/staffing_ir_context.json` to correctly become partial 4/5, but previously published Q3 original report evidence should not disappear.

The [issuer collector](../../src/fcews/staffing_ir.py) now retries network timeouts and HTTP 429/5xx **once** (never HTTP403), records current source errors and source timestamp, and persists `data/staffing_last_verified.json` **only** after a real successful 5/5 original-issuer extraction. The archive was initialized from the actual five-source [previous GitHub source-observation commit](https://github.com/lican1213/financial-crisis-early-warning/commit/f52f13100ec1d15b124010820793b023ebe5c6d3), not invented values. Later incomplete fetches **cannot overwrite** this archive, and are explicitly operational failures, not a new labor market downturn.

The ChatGPT read-only feed labels current-poll `staffing_issuer_research` separately from historical original-source `staffing_last_verified` with `is_current_run_evidence=false`. Both have `staffing_global_score=null` and cannot authorize a financial crisis alert. The last verified report only remains relevant within the issuer's declared 120-day original release window; it never proves a successful hourly/day current fetch.

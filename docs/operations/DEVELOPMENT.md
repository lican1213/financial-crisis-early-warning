# FCEWS maintenance protocol: three stages, one evidence chain

Canonical maintenance instructions for any coding agent; read with [AGENTS](../../AGENTS.md), [cadence](CADENCE.md), and [latest handoff](../../wiki/operations/HANDOFF.md). Do not duplicate this protocol in every automation prompt. The user authorizes maintenance of the existing system, not invention of new requirements, threshold tuning, or unnecessary infrastructure.

## Fixed boundaries

- Preserve hourly ChatGPT condition-watch, both GitHub cron slots, four user notification gates, independent official-source verification, and true silence without material changes. An operational incident is not a financial event. No new weekly report, numeric score or comparison with the paused six-module orange/70 grade.
- Preserve observed values, dates, original publication availability, source identity, revisions and missingness. A latest-value diagnostic is not a calibrated probability. Do not count composite indices as independent direct channels. No synthetic values, release timestamps, API receipts or fabricated execution.
- Prefer standard, existing patterns from maintained GitHub projects and official documentation; record exactly what is reused and why. Keep code small; no dependency or service just to address a hypothetical issue. Delete superseded implementation after compatibility is checked; leave historical rationale in the MOC. Avoid redundant defensive layers.
- Stage 1 (facts): collectors, dated recent observations, quality, heartbeat. Stage 2 (decision): core confirmation, per-channel lifecycle, shared live/replay state transition. Stage 3 (handoff): durable candidate identity and evidence, pending/acknowledged Issue status, read-only feed, independent ChatGPT verification. A GitHub candidate/receipt is never a user delivery receipt.

## Mandatory loop and release gates

1. **Baseline**: read MOC, handoff, incidents and taskboard; inspect actual HEAD, latest production artifacts and open Issues. Run existing tests where available; record unavailable tools and do not equate old results with current code.
2. **Root cause and reference**: reproduce a concrete failure with a fixture; separate intended limitations, actual defects and research uncertainty. Inspect relevant upstream implementation/docs. Choose minimal change; document second-/third-order effects on consumers, data contracts, migrations, replay and notification semantics.
3. **Implementation**: create branch; add failing regression or establish actual counterexample before repair where feasible. Preserve interface compatibility, stable identities, source provenance and recovery. Keep business state and durable outbox in the same pushed change before side effects; do not claim a database transaction or exactly-once guarantee. Re-run the failing case and all affected tests.
4. **Cross-stage Gate**: run full tests plus MOC lint. Exercise source date mismatch, late third channel, later normal reading, outages, revision/no lookahead, state persistence, pending candidate, Issue failure/retry/duplicate acknowledgement, stale candidate and no notification authorization. Tests use isolated temporary roots and synthetic fixtures; no production crisis alerts or fake production data. Production and replay use shared state transition with explicit live versus historical availability. Update fixture/schema consumers rather than removing assertions to pass.
5. **Adversarial Gate**: independently inspect the full changed data path, not only the edited functions; distinguish independently executed counterexamples, static findings and unresolved risks. If a Gate fails, return to the responsible stage and repeat within the actual session. Do not expand scope merely to increase test count.
6. **Deployment Gate**: require completed CI for exact PR head, inspect logs, merge with SHA check, verify main code and fresh actual production artifacts / job logs. Compare snapshot/feed/heartbeat identity where applicable. Push/manual success is not natural cron; one natural success is not continuity. ChatGPT configuration readback is not runtime or receipt. If a Gate cannot be verified, record OPEN, never claim it passed.
7. **Handoff and freeze**: update Issue, MOC handoff, append-only log and incident record; include PR/commit/CI/run links and explicit remaining gaps. Freeze engineering when material defects are resolved and relevant gates pass; continue empirical PIT calibration separately. No artificial hardening loops or background promises.

## Maintenance priorities and later development

| Workstream | Next acceptance criterion |
| --- | --- |
| Engineering | Natural cron continuity evidenced by real first-attempt runs over the existing 24-hour audit window; independent external dead-man service only if provisioned; user delivery status remains unknown without authorized receipt. |
| Research | Original-release data coverage and PIT/historical calibration on documented crisis events, independent holdout and sensitivity analysis; report missing vintages and separate candidate counts from crisis alert precision. No automatic tuning or new scores in the live model. |
| Coverage | Licensed MOVE and credible Treasury market depth; regulator/institution events; China private credit and housing only when original data and comparable measures available. No proxy substitution as original source. |

Use [core](../../src/fcews/core.py), [CLI](../../src/fcews/cli.py), [PIT replay](../../src/fcews/backtest.py), [bridge](../../src/fcews/bridge.py), [delivery](../../src/fcews/delivery.py), and [cross-stage tests](../../tests/test_cross_stage.py) as the primary code path. Keep open [cadence #1](https://github.com/lican1213/financial-crisis-early-warning/issues/1), [PIT #3](https://github.com/lican1213/financial-crisis-early-warning/issues/3), and [delivery #8](https://github.com/lican1213/financial-crisis-early-warning/issues/8) until independent evidence warrants closure.

## Reusable agent prompt

Maintain FCEWS following this protocol. Start from current HEAD and MOC, identify actual failure and reference mature implementations, reproduce it, plan impacts on all three stages, make minimal repair; test the whole chain and independently try to disprove it. On failure loop back. Merge only with verified exact-HEAD CI; check real production outputs and runtime, and record MOC/Issue evidence. Preserve thresholds, hourly frequency, four notification gates and strict silence; no invented facts, fake runs, unnecessary modules, stale data as new, or claims stronger than evidence. If runtime/receipt/PIT is unavailable, say what is verified and what is open. Prioritize high-impact fixes over endlessly searching for hypothetical problems.

### Ponytail maintenance rule (2026-11-17)
Follow the [original Ponytail project](https://github.com/DietrichGebert/ponytail): question whether the work is necessary; reuse existing project code first, then stdlib, native platform and existing dependencies; add only the smallest complete fix. Follow all consumers and preserve evidence, data-loss protections and tests. No new framework, service, abstraction or repeated workflow to solve a problem already covered by an existing path. Keep intentional shortcuts and limits documented here or in the relevant source, not in separate scaffolding. Gate stops when the actual defect is resolved and verified; research gaps are not reasons to keep growing the production code.


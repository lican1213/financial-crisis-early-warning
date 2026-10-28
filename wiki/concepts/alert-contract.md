---
title: Four-Condition Alert Contract
kind: concept
status: active
updated: 2026-10-28
summary: Operational definition of meaningful changes and what remains silent.
---

# Four-condition alert contract

The user expects a notification **only** when at least one of these is established:

1. Risk severity materially **increases relative to the most recent sourced weekly report**, not an arbitrary zero or hardcoded green baseline.
2. **Two independent families** simultaneously cross historically validated pressure ranges.
3. A bank, fund, sovereign, repo, payment-system or energy-related event is **confirmed by reliable primary evidence** and has a plausible **cross-market contagion mechanism**.
4. Existing leading indicators **recover** convincingly enough to justify an actual risk downgrade.

Until historical validation, v0.2 thresholds are provisional candidate gates, not proven historical pressure ranges. In v0.2 recovery requires three distinct observation dates; it does **not** establish three distinct actual publication timestamps yet.

### Output contract for a confirmed warning
Explicit event, verified vs unverified evidence, risk grade and measured confidence, three indicators for the coming 72h, recommended and contraindicated immediate investor actions. Link primary source documents and their observed/published dates. No routine daily updates.

### Quiet runs
No change means **no user alert**. GitHub Action logs still capture the execution; changed data evidence snapshots go to `data/`. Missing data, source outage and unknown weekly grade must be reported in diagnostics without being mislabeled green or triggering a crisis alert.

### Important boundary
GitHub issue `FCEWS candidate alert` is a **review queue**, not a notification to the end user. The existing ChatGPT automation remains independent until a tested delivery bridge is built. Source verification is not achieved merely by setting an event `verified` boolean. See [event contract](../datasets/events.md), [ADR-0002](../decisions/ADR-0002.md), [Issue #8](https://github.com/lican1213/financial-crisis-early-warning/issues/8).

---
title: IF-009 — Verified Contagion Event Contract
kind: dataset
status: under-review
updated: 2026-10-28
summary: Human-reviewed primary source standards and replay protection for systemic incidents.
---

# Event provenance contract

Currently `data/events.json` is manually supplied and only fields `id`, `verified`, `primary_source_url`, and `cross_market_mechanism` are checked. **That is not source authentication**; setting `verified=true` alone can trigger a candidate issue.

**Future schema:**
`event_id`, `category`, `occurred_at_utc`, `published_at_utc`, `first_seen_at_utc`, `issuer`, `primary_source_url`, `source_document_sha256`, `secondary_corrob_url` (when feasible), `institutions_and_exposures`, `cross_market_mechanism`, `verified_by`, `verified_at_utc`, `duplicate_key`, `status`, `confidence`, `retraction_reason`.

Accepted events need an explicit plausible chain from idiosyncratic distress into market-wide funding, collateral, payment, sovereign or liquidation feedback. Media retelling of the same event is one event ID. Social rumors or a price move without official physical supply-loss confirmation stay in the unverified queue.

Verification workflow: record claim → fetch original regulatory/company/central bank document → check time and quantity → infer possible transmission → independent corroboration if necessary → human review → alert gate. Revisions/retractions preserve prior evidence rather than silently deleting event history.

Open action: [Issue #7](https://github.com/lican1213/financial-crisis-early-warning/issues/7). Related: [risk alerts](../concepts/alert-contract.md), [failure register](../operations/INCIDENTS.md).

## Official source verification and FDIC review intake
[Event verifier](../../src/fcews/events.py) checks the original official HTTPS document URL, redirects, downloaded bytes SHA256, publication and review time, reviewer decision, event category and specific transmission mechanism. [FDIC source queue](../../data/fdic_review.json) records regulatory bank failures for **review only**; candidate feed records do not notify the user without reviewed cross-market evidence. [Adversarial event tests](../../tests/test_events.py) include forged domains, changed bytes and future publication. Reviewer strings are accountable labels, not cryptographically authenticated identities.

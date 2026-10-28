---
title: Point-in-Time Financial Data Availability
kind: concept
status: active
updated: 2026-10-28
summary: Prevents false lead-time claims from revised series and observation-versus-publication-date confusion.
---

# Point-in-time data: what the model actually knew

A historical feature needs at least four clocks: `observation_date` (economic period), `published_at` (first release), `retrieved_at` (our snapshot fetch), and `vintage_at` (as-published revision). A one-week lag estimate is not proof of exact release timing.

**Forbidden backtest:** take the latest full FRED series and join a weekly Friday observation to the same Friday's crisis predictor when the actual release was days later. **Required:** freeze the evidence as it was publicly available at each prediction timestamp; use archived Fed/OFR releases or ALFRED vintages, and exclude any series whose release time cannot be established.

Example: an NFCI value labeled Friday may become available on a subsequent Wednesday. The exact release should be looked up; the example is conceptual, not a statement of an actual Oct 2026 release date.

The v0.2 collector records observation date and retrieval time only; it therefore cannot support audited crisis forecasting claims. For a next-generation adapter, store `available_at_utc`, `source_document_sha256`, `revision_sequence`, `unit`, `series_version` and release calendar.

Related: [FRED adapter](../datasets/fred.md), [historical backtest protocol](../../docs/moc/BACKTEST.md), [Issue #3](https://github.com/lican1213/financial-crisis-early-warning/issues/3).

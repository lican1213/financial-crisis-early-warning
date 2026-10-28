---
title: Source — LLM Wiki MOC and Knowledge Compilation
kind: source
status: active
updated: 2026-10-28
summary: Provenance and adaptations from the public agent-first LLM Wiki architecture.
---

# Source record: LLM Wiki / Maps of Content

**Source A:** [nvk/llm-wiki AGENTS.md](https://github.com/nvk/llm-wiki/blob/master/AGENTS.md). Viewed 2026-10-28 via linked GitHub. It defines a registry, topical wikis, directory indexes, durable operation log, isolated raw inputs, synthesized linked pages, inventory/task entities, agent schemas and lint habits.

**Source B:** [cobusgreyling/llm-wiki README](https://github.com/cobusgreyling/llm-wiki). Viewed 2026-10-28 via linked GitHub. It emphasizes raw/wiki/schema separation, citations, incremental ingest/query/lint, page-level links, agent onboarding, optional search/index, and mechanically checked orphan/broken pages.

**Independent index:** [awesome-llm-wiki](https://github.com/gavischneider/awesome-llm-wiki) tracks alternative designs. Not a source of verified financial indicators.

### FCEWS adaptation
One repository = one specialized topic wiki. Multiple **MOCs are navigation**, not repeated summaries. Runtime market data remains versioned separately; GitHub Issues own task status; append-only project log owns engineering memory; ADRs own durable decisions. Source pages record read provenance; concept pages synthesize conflicting claims and counterexamples; deterministic lint maintains structural health.

We intentionally do **not** install a heavy daemon, external paid index, or background LLM worker into hourly monitoring. The GitHub-native+stdlib approach reduces latency and unaudited operating costs while preserving agent portability.

Related: [agent contract](../../AGENTS.md), [schema](../schema.md), [MOC engineering](../mocs/ENGINEERING.md).

---
title: FCEWS Wiki Schema
kind: protocol
status: active
updated: 2026-10-28
summary: Bounded page types, source fidelity and maintenance rules.
---

# Knowledge compilation protocol

## Hierarchy
`raw/` holds immutable sourced inputs when archived locally. `wiki/sources/` records what was actually read and when. `wiki/concepts/` contains synthesis and falsifiable reasoning, not quotations pasted from references. `wiki/datasets/` contains technical adapters and provenance. `wiki/mocs/` only links, briefly maps boundaries and marks missing areas. `wiki/decisions/` is immutable architecture decision history. `wiki/operations/` explains the run-state and prevents agent drift.

## Frontmatter
Every `wiki/**/*.md` page must start with:
- `title`: short unique descriptive title.
- `kind`: one of index, overview, moc, concept, dataset, source, decision, taskboard, operations, log, protocol.
- `status`: active, planned, under-review, superseded or archived.
- `updated`: ISO date.
- `summary`: 1–2 sentences.

## Evidence discipline
Record: source name, URL, publisher, first availability when known, raw units, release cadence, revision policy, retrieval or access method, dependencies, known false-positive routes. A citation links to source **and** supports only a specific claim; no inferred API endpoint or license assurance. A page can flag unresolved contradictions instead of forcing consensus.

## Stable IDs
Use `ADR-XXXX` for architecture decisions; `IF-XXX` for datasets/interfaces; `FAIL-XXX` for incidents; GitHub `#N` for actionable tasks. All task statuses live in GitHub Issues. The taskboard is a navigation view, updated on each intentional audit, never a second independent database.

## Maintenance commands
`python scripts/wiki_lint.py`: broken local links, missing required metadata, duplicate titles, orphan wiki pages and missing MOC coverage. `PYTHONPATH=src python -m unittest discover -s tests -v`: model tests plus wiki tests. The linter is deterministic stdlib Python; it cannot independently prove source accuracy or credential hygiene.

## Agent workflows
1. **Ingest** official source/repo → source record → update dataset/concept → link from MOC/master index → log.
2. **Query** read master index → choose MOC → source-backed answer → promote reusable findings only.
3. **Lint** run validator; fix orphan, broken link or stale page; register unresolved substantive contradictions as issues.
4. **Promote** recurring observation or failure → concept page and/or ADR, with evidence, counterexamples and decision trail.
5. **Rotate** long logs into dated archive only when preserving full append-only chronological history and linking every archive.
6. **Handoff** update active version, exact current blockers, tests/run links and next Issue; no vague claims of completion.

Related: [maintenance](operations/MAINTENANCE.md), [MOC engineering](mocs/ENGINEERING.md), [methodological source](sources/llm-wiki-methods.md).

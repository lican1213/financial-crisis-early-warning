# FCEWS Agent Contract (Codex / Claude Code / OpenCode / ChatGPT)

Scope: maintain **this financial crisis early-warning repository**, not unrelated investment or research projects. GitHub is persistent memory. A chat answer alone is not a completed project change.

## Mandatory session startup (in order)
1. Read [wiki/_index.md](wiki/_index.md), [wiki/operations/HANDOFF.md](wiki/operations/HANDOFF.md), and [wiki/tasks.md](wiki/tasks.md).
2. Read [wiki/operations/INCIDENTS.md](wiki/operations/INCIDENTS.md), then the relevant topic MOC and its source/decision pages.
3. Inspect code and run `PYTHONPATH=src python -m unittest discover -s tests -v` and `python scripts/wiki_lint.py`.
4. Confirm current GitHub Issues and latest Actions run before stating a feature is operational.
5. Pick one concrete Issue, edit only affected files, add adversarial tests and a documented falsification attempt.

## Knowledge hierarchy
- `wiki/_index.md`: central directory; `wiki/mocs/`: topical maps (**navigation, not duplicated prose**).
- `wiki/concepts/`: reusable causal/measurement knowledge; `wiki/datasets/`: connector contracts with units, publication cadence and revisions.
- `wiki/sources/`: traceable provenance and external implementation lessons.
- `wiki/decisions/`: immutable ADRs; supersede with a new ADR, do not rewrite history.
- `wiki/tasks.md`: compact roadmap; GitHub Issues are authoritative for task **status** and acceptance criteria.
- `wiki/log.md`: append-only *project-operation* timeline; `data/` and Actions artifacts carry runtime evidence, not the wiki log.
- `wiki/operations/HANDOFF.md`: latest verified working state, blockers and precise next steps.
- `docs/moc/`: legacy entry points; keep references but do not let them become a competing source of truth.

## Ingest → compile → verify → link → log
Read source first, capture URL, publication/observation/available-at timestamps, author and scope. Add/update a topic page if the result changes the project's model. Cite the source page; link it from a MOC and `wiki/_index.md`. If a page contradicts existing material, record both claims and the adjudication in INCIDENTS / an ADR instead of silently overwriting. Run wiki lint and core tests. Log resulting commit, tests, issues and open questions.

Wiki pages use YAML frontmatter: title, kind, status, updated, summary. Use relative Markdown links so GitHub renders them; optional `[[slug|title]]` can be added for Obsidian but **must have a neighboring working Markdown link**. Never create links to nonexistent pages.

## Code and monitoring boundaries
- Do not change risk thresholds solely to make tests pass. Every threshold change needs point-in-time evidence and an out-of-sample counterexample.
- Do not count correlated readings as independent indicator families; no alert on a single routine fluctuation.
- A source URL is not primary-source verification by itself. Candidate issues are not end-user crisis notifications.
- **No material change → no alert.** Distinguish data missing, market calm, system failed and schedule silent.
- Do not place secrets, personal portfolios or private case notes in this **public** repository.
- Never claim automatic future work beyond code actually running in a verified workflow.

## Completion contract
A change is COMPLETE only if code/docs are committed, relevant checks pass, GitHub Issue updated, wiki/log.md appended, wiki/operations/HANDOFF.md refreshed, and the user gets the commit/Issue link and any deployment blocker. If run is unverified say exactly that. Keep explanations concise and factual.

## Monitoring cadence and data lineage (2026-10-29)
Always check [docs/operations/CADENCE.md](docs/operations/CADENCE.md) before editing workflow cron. Cross-check [data/health.json](data/health.json) and [wiki/datasets/registry.md](wiki/datasets/registry.md) before claiming a source works; a source fetched live is not the same as a verified first-publication vintage. Data-health issues are NOT financial-crisis notifications. Code or model changes require a falsifying regression, CI proof, change log, Issue update and source-dated handoff.

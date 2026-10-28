"""Deterministic structural lint for the FCEWS LLM-Wiki knowledge base.

Detects broken local links, missing frontmatter, duplicated titles, orphan pages,
and MOCs missing from the master index. Run from any working directory.
No network or external packages required.
"""
from __future__ import annotations

import re
import sys
from collections import deque
from pathlib import Path
from urllib.parse import unquote

LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
REQUIRED = ("title", "kind", "status", "updated", "summary")
VALID_KINDS = {
    "index", "overview", "moc", "concept", "dataset",
    "source", "decision", "taskboard", "operations", "log", "protocol",
}
VALID_STATUSES = {"active", "planned", "under-review", "superseded", "archived"}
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def frontmatter(page: Path) -> dict[str, str]:
    raw = page.read_text(encoding="utf-8")
    if not raw.startswith("---\n"):
        return {}
    parts = raw.split("\n---\n", 1)
    if len(parts) != 2:
        return {}
    header = parts[0][4:]
    result = {}
    for line in header.splitlines():
        if ":" in line and not line.lstrip().startswith("#"):
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip().strip("'\"")
    return result


def local_links(page: Path, root: Path):
    """Return (target relative path, broken detail) for all relative links.

    Scope is limited to the current repository. External web URLs do not need
    to be online for a successful structural lint.
    """
    contents = page.read_text(encoding="utf-8")
    for raw in LINK.findall(contents):
        link = raw.split("#", 1)[0].split("?", 1)[0].strip().strip("<>")
        if not link or "://" in link or link.startswith(("mailto:", "tel:", "data:", "//")):
            continue
        link = unquote(link)
        target = (page.parent / link).resolve()
        try:
            target.relative_to(root.resolve())
        except ValueError:
            yield (None, f"{page.relative_to(root)}: link outside repository: {raw}")
            continue
        if not target.exists():
            yield (None, f"{page.relative_to(root)}: broken link: {raw}")
        else:
            yield (target, None)


def lint_wiki(root: Path) -> list[str]:
    root = root.resolve()
    wiki = root / "wiki"
    start = wiki / "_index.md"
    errors: list[str] = []
    if not start.exists():
        return ["missing wiki/_index.md"]
    pages = sorted(wiki.rglob("*.md"))
    titles: dict[str, Path] = {}
    edges: dict[Path, set[Path]] = {}
    for page in pages:
        m = frontmatter(page)
        for key in REQUIRED:
            if not m.get(key):
                errors.append(f"{page.relative_to(root)}: missing {key} frontmatter")
        if m.get("kind") and m["kind"] not in VALID_KINDS:
            errors.append(f"{page.relative_to(root)}: invalid kind {m['kind']}")
        if m.get("status") and m["status"] not in VALID_STATUSES:
            errors.append(f"{page.relative_to(root)}: invalid status {m['status']}")
        if m.get("updated") and not DATE.fullmatch(m["updated"]):
            errors.append(f"{page.relative_to(root)}: updated must be YYYY-MM-DD")
        title = m.get("title", "")
        if title in titles:
            errors.append(f"{page.relative_to(root)}: duplicate title with {titles[title].relative_to(root)}")
        elif title:
            titles[title] = page
        edges[page] = set()
        for target, problem in local_links(page, root):
            if problem:
                errors.append(problem)
            elif target.is_file() and wiki in target.parents and target.suffix == ".md":
                edges[page].add(target)
        if m.get("kind") in {"source", "dataset"}:
            body = page.read_text(encoding="utf-8")
            # A source/dataset should point at at least one real external source
            # or a checked-in implementation file. Pure self-referential notes drift.
            if "https://" not in body and "http://" not in body:
                errors.append(f"{page.relative_to(root)}: source/dataset has no external provenance")

    reached = set()
    queue = deque([start])
    while queue:
        page = queue.popleft()
        if page in reached:
            continue
        reached.add(page)
        queue.extend(edges.get(page, set()) - reached)
    for page in pages:
        if page not in reached:
            errors.append(f"{page.relative_to(root)}: orphan wiki page (unreachable from master index)")
    for page in wiki.glob("mocs/*.md"):
        if page not in edges.get(start, set()):
            errors.append(f"{page.relative_to(root)}: MOC absent from master index")
    return sorted(set(errors))


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    errors = lint_wiki(repo)
    if errors:
        print(f"Wiki lint FAIL ({len(errors)} issue(s))")
        for error in errors:
            print("- " + error)
        return 1
    total = len(list((repo / "wiki").rglob("*.md")))
    print(f"Wiki lint PASS: {total} pages, links/frontmatter/MOC coverage verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())

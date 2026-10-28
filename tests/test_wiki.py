"""Adversarial structural checks for persistent second-brain knowledge."""
import tempfile
import unittest
from pathlib import Path

from scripts.wiki_lint import lint_wiki


META = """---
title: {title}
kind: {kind}
status: active
updated: 2026-10-28
summary: A useful permanent project record.
---

{body}
"""


def make(root, name, title, kind="concept", body="Content."):
    path = root / "wiki" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(META.format(title=title, kind=kind, body=body), encoding="utf-8")
    return path


class WikiAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_valid_linked_knowledge_graph(self):
        make(self.root, "_index.md", "Index", "index", "[Concepts](concepts/_index.md)")
        make(self.root, "concepts/_index.md", "Concept Index", "index", "[Concept](a.md)")
        make(self.root, "concepts/a.md", "Unique Concept")
        self.assertEqual(lint_wiki(self.root), [])

    def test_orphan_page_is_detected(self):
        make(self.root, "_index.md", "Index", "index", "[Concepts](concepts/_index.md)")
        make(self.root, "concepts/_index.md", "Concept Index", "index", "No pages listed.")
        make(self.root, "concepts/forgotten.md", "Orphan")
        self.assertTrue(any("orphan" in x for x in lint_wiki(self.root)))

    def test_broken_local_link_is_detected(self):
        make(self.root, "_index.md", "Index", "index", "[lost](missing.md)")
        self.assertTrue(any("broken link" in x for x in lint_wiki(self.root)))

    def test_missing_source_frontmatter_is_detected(self):
        make(self.root, "_index.md", "Index", "index", "[Sources](sources/_index.md)")
        make(self.root, "sources/_index.md", "Source Index", "index", "[Note](n.md)")
        note = self.root / "wiki" / "sources" / "n.md"
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text("# No frontmatter\nhttps://official.example/source\n", encoding="utf-8")
        self.assertTrue(any("missing title" in x for x in lint_wiki(self.root)))

    def test_duplicate_title_is_detected(self):
        make(self.root, "_index.md", "Index", "index", "[A](a.md) [B](b.md)")
        make(self.root, "a.md", "Duplicated")
        make(self.root, "b.md", "Duplicated")
        self.assertTrue(any("duplicate title" in x for x in lint_wiki(self.root)))

    def test_moc_must_appear_in_main_index(self):
        make(self.root, "_index.md", "Index", "index", "[A](a.md) [MOC dir](mocs/_index.md)")
        make(self.root, "a.md", "A", body="[MOC](mocs/r.md)")
        make(self.root, "mocs/_index.md", "MOC Index", "index", "[Risk](r.md)")
        make(self.root, "mocs/r.md", "Risk Map", kind="moc", body="[A](../a.md)")
        self.assertTrue(any("MOC absent" in x for x in lint_wiki(self.root)))

    def test_missing_topic_index_detected(self):
        make(self.root, "_index.md", "Index", "index", "[Concept](concepts/a.md)")
        make(self.root, "concepts/a.md", "Nested")
        self.assertTrue(any("missing _index.md" in x for x in lint_wiki(self.root)))

    def test_topic_index_must_be_reachable(self):
        make(self.root, "_index.md", "Index", "index", "[Concept](concepts/a.md)")
        make(self.root, "concepts/_index.md", "Concept Index", "index", "Not indexed.")
        make(self.root, "concepts/a.md", "Nested")
        self.assertTrue(any("orphan wiki page" in x for x in lint_wiki(self.root)))

    def test_external_urls_not_treated_as_broken_local_links(self):
        make(self.root, "_index.md", "Index", "index", "[Official](https://example.org/doc)")
        self.assertEqual(lint_wiki(self.root), [])


if __name__ == "__main__":
    unittest.main()

"""Tests for drs.py. Standard library only: python3 -m unittest discover decisions/tests"""

from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import drs  # noqa: E402

BODY = """# DR: A Decision

## Context

Some context.

## Decision

The decision.

## Consequences

Costs.

## Alternatives Considered

### Do Nothing

Nothing happens.

## References

None.
"""

DRAFT_BODY = BODY.replace(
    "## References", "## Promotion\n\nCriteria.\n\n## References"
)


def front_matter(
    id="DR-0001",
    title="A Decision",
    summary="Do the thing.",
    date="2026-11-23",
    authors='["A Human"]',
    reviewers='["A Reviewer"]',
    state="Accepted",
    by=None,
    supersedes="[]",
    legacy_bodies=None,
    status_date=None,
):
    lines = [
        "---",
        f'id: "{id}"',
        f'title: "{title}"',
        f'summary: "{summary}"',
        f'date: "{date}"',
        f"authors: {authors}",
        f"reviewers: {reviewers}",
        "status:",
        f'  state: "{state}"',
    ]
    if by:
        lines.append(f'  by: "{by}"')
    if status_date:
        lines.append(f'  date: "{status_date}"')
    lines.append(f"supersedes: {supersedes}")
    if legacy_bodies is not None:
        lines.append(f"legacy_bodies: {legacy_bodies}")
    lines.append("---")
    return "\n".join(lines) + "\n"


class CorpusCase(unittest.TestCase):
    """Writes records into a temp directory and runs the checks over them."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name) / "docs" / "decisions"
        self.dir.mkdir(parents=True)

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, name: str, text: str) -> Path:
        path = self.dir / name
        path.write_text(text, encoding="utf-8")
        return path

    def record(self, number: int, text: str, slug: str = "a-decision") -> Path:
        return self.write(f"{number:04d}-{slug}.md", text)

    def findings(self, strict: bool = False) -> list[drs.Finding]:
        args = type("Args", (), {"dir": str(self.dir), "strict": strict})()
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            drs.cmd_check(args)
        corpus = drs.load(self.dir)
        findings = list(corpus.findings)
        for record in corpus.records:
            findings.extend(drs.check_record(record, corpus))
        findings.extend(drs.check_graph(corpus))
        findings.extend(drs.check_index(corpus))
        if strict:
            for finding in findings:
                if finding.level == "warning" and "unmanaged" in finding.message:
                    finding.level = "error"
        return findings

    def errors(self, **kwargs) -> list[str]:
        return [f.message for f in self.findings(**kwargs) if f.level == "error"]

    def warnings(self, **kwargs) -> list[str]:
        return [f.message for f in self.findings(**kwargs) if f.level == "warning"]

    def index(self) -> str:
        args = type("Args", (), {"dir": str(self.dir)})()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            drs.cmd_index(args)
        return (self.dir / "README.md").read_text(encoding="utf-8")


class FrontMatterDialect(CorpusCase):
    def parse(self, lines: list[str]) -> dict:
        return drs.parse_front_matter(lines, Path("x.md"))

    def test_scalars_and_nesting(self):
        parsed = self.parse(
            [
                'id: "DR-0001"',
                "title: A Decision",
                "authors: [\"A Human\", 'Another']",
                "status:",
                '  state: "Accepted"',
                "supersedes: []",
            ]
        )
        self.assertEqual(parsed["id"], "DR-0001")
        self.assertEqual(parsed["title"], "A Decision")
        self.assertEqual(parsed["authors"], ["A Human", "Another"])
        self.assertEqual(parsed["status"], {"state": "Accepted"})
        self.assertEqual(parsed["supersedes"], [])

    def test_comments_and_blank_lines_are_ignored(self):
        parsed = self.parse(["# a comment", "", 'id: "DR-0001"'])
        self.assertEqual(parsed, {"id": "DR-0001"})

    def test_inline_mapping_rejected_with_line_number(self):
        with self.assertRaises(drs.FrontMatterError) as caught:
            self.parse(["status: {state: Accepted}"])
        self.assertIn("x.md:2", str(caught.exception))

    def test_block_scalar_rejected(self):
        with self.assertRaises(drs.FrontMatterError):
            self.parse(['summary: "ok"', "title: |", "  two lines"])

    def test_anchor_rejected(self):
        with self.assertRaises(drs.FrontMatterError):
            self.parse(["authors: &people", '  - "A"'])

    def test_only_status_may_be_a_mapping(self):
        with self.assertRaises(drs.FrontMatterError) as caught:
            self.parse(["title:", '  inner: "x"'])
        self.assertIn("only `status`", str(caught.exception))

    def test_duplicate_key_rejected(self):
        with self.assertRaises(drs.FrontMatterError):
            self.parse(['id: "DR-0001"', 'id: "DR-0002"'])

    def test_indented_line_outside_mapping_rejected(self):
        with self.assertRaises(drs.FrontMatterError):
            self.parse(['  id: "DR-0001"'])

    def test_unterminated_string_rejected(self):
        with self.assertRaises(drs.FrontMatterError):
            self.parse(['title: "unterminated'])

    def test_missing_value_rejected(self):
        with self.assertRaises(drs.FrontMatterError):
            self.parse(["title:"])

    def test_unclosed_front_matter_rejected(self):
        with self.assertRaises(drs.FrontMatterError):
            drs.split_document('---\nid: "DR-0001"\nbody\n', Path("x.md"))


class RecordShape(CorpusCase):
    def test_a_conformant_record_has_no_findings(self):
        self.record(1, front_matter() + BODY)
        self.index()
        self.assertEqual(self.findings(), [])

    def test_missing_field(self):
        text = front_matter().replace('summary: "Do the thing."\n', "")
        self.record(1, text + BODY)
        self.assertIn("missing required field 'summary'", self.errors())

    def test_empty_summary_and_length(self):
        self.record(1, front_matter(summary="") + BODY)
        self.assertIn("summary is empty; it is the index line", self.errors())
        self.write("0001-a-decision.md", front_matter(summary="x" * 141) + BODY)
        self.assertIn("summary is 141 characters; limit 140", self.errors())

    def test_id_must_be_zero_padded(self):
        self.record(1, front_matter(id="DR-0001") + BODY)
        self.write("0002-b.md", front_matter(id="DR-002") + BODY)
        self.assertIn("id 'DR-002' is not DR-<4+ digits>", self.errors())
        self.write("0003-c.md", front_matter(id="DR-00030") + BODY)
        self.assertIn(
            "id 'DR-00030' is not zero-padded to its width; expected 'DR-0030'", self.errors()
        )
        self.write("0004-d.md", front_matter(id="DR-10000") + BODY)
        self.assertNotIn(
            "id 'DR-10000' is not zero-padded to its width; expected 'DR-10000'", self.errors()
        )

    def test_two_spellings_of_one_number_collide(self):
        self.record(1, front_matter(id="DR-0001") + BODY, slug="one")
        self.write("0030-a.md", front_matter(id="DR-0030", title="Thirty") + BODY)
        self.write("0030-b.md", front_matter(id="DR-00030", title="Also Thirty") + BODY)
        self.assertTrue(any("same record number" in e for e in self.errors()))

    def test_date_must_be_iso(self):
        self.record(1, front_matter(date="23/11/2026") + BODY)
        self.assertIn("date '23/11/2026' is not YYYY-MM-DD", self.errors())

    def test_empty_authors(self):
        self.record(1, front_matter(authors="[]") + BODY)
        self.assertIn("authors is empty; name who reasoned it out", self.errors())

    def test_unratified_accepted_record_is_an_error(self):
        self.record(1, front_matter(reviewers="[]") + BODY)
        self.assertIn("Accepted record has no reviewers; a record nobody ratified is a Draft", self.errors())

    def test_unratified_draft_is_fine(self):
        self.record(1, front_matter(reviewers="[]", state="Draft") + DRAFT_BODY)
        self.index()
        self.assertEqual(self.errors(), [])

    def test_unknown_state(self):
        self.record(1, front_matter(state="Proposed") + BODY)
        self.assertTrue(any("status.state 'Proposed'" in e for e in self.errors()))

    def test_filename_must_match_id(self):
        self.write("0002-a-decision.md", front_matter(id="DR-0001") + BODY)
        self.assertIn("filename numbers 0002 but id is DR-0001", self.errors())

    def test_filename_slug_must_be_lowercase(self):
        self.write("0001-A Decision.md", front_matter() + BODY)
        self.assertTrue(any("filename is not" in e for e in self.errors()))

    def test_relative_links_resolve(self):
        self.write("notes.md", "not a record\n")
        self.record(1, front_matter() + BODY.replace("None.", "[notes](./notes.md) — notes"))
        self.index()
        self.assertEqual(self.errors(), [])

    def test_broken_relative_link(self):
        self.record(1, front_matter() + BODY.replace("None.", "[notes](./missing.md)"))
        self.assertIn("relative link does not resolve: ./missing.md", self.errors())

    def test_external_links_are_not_checked(self):
        self.record(
            1, front_matter() + BODY.replace("None.", "[spec](https://example.com/x) [t](#ctx)")
        )
        self.index()
        self.assertEqual(self.errors(), [])


class Headings(CorpusCase):
    def test_missing_do_nothing(self):
        self.record(1, front_matter() + BODY.replace("### Do Nothing", "### Nothing"))
        self.assertIn("missing heading '### Do Nothing'", self.errors())

    def test_draft_needs_promotion(self):
        self.record(1, front_matter(state="Draft") + BODY)
        self.assertIn("Draft record needs '## Promotion'", self.errors())

    def test_promoted_draft_keeps_its_promotion_heading(self):
        # A promoted draft keeps ## Promotion as the evidence. That must not
        # be an error now the record is Accepted.
        self.record(1, front_matter(state="Accepted") + DRAFT_BODY, slug="b")
        self.index()
        self.assertEqual(self.errors(), [])

    def test_heading_must_be_canonical(self):
        self.record(1, front_matter(state="Draft") + DRAFT_BODY.replace("## Promotion", "## Promotion:"))
        self.assertIn("Draft record needs '## Promotion'", self.errors())


class Graph(CorpusCase):
    def test_supersession_needs_both_edges(self):
        self.record(
            1,
            front_matter(state="Superseded", by="DR-0002") + BODY,
            slug="old",
        )
        self.record(
            2,
            front_matter(id="DR-0002", supersedes='["DR-0001"]') + BODY,
            slug="new",
        )
        self.index()
        self.assertEqual(self.findings(), [])

    def test_missing_reverse_edge(self):
        self.record(1, front_matter(state="Superseded", by="DR-0002") + BODY, slug="old")
        self.record(2, front_matter(id="DR-0002") + BODY, slug="new")
        self.assertIn(
            "Superseded by DR-0002, which does not list DR-0001 in supersedes", self.errors()
        )

    def test_supersedes_must_point_at_a_superseded_record(self):
        self.record(1, front_matter() + BODY, slug="old")
        self.record(2, front_matter(id="DR-0002", supersedes='["DR-0001"]') + BODY, slug="new")
        self.assertIn(
            "supersedes DR-0001 but that record is Accepted, not Superseded", self.errors()
        )

    def test_supersedes_must_resolve(self):
        self.record(1, front_matter(supersedes='["DR-0009"]') + BODY)
        self.assertIn("supersedes DR-0009 does not resolve", self.errors())

    def test_amendment_needs_no_supersedes_mirror(self):
        # Round-one review finding: status.by is required for Amended, so a
        # reverse-edge rule that insists on supersedes would reject it.
        self.record(1, front_matter(state="Amended", by="DR-0002") + BODY, slug="a")
        self.record(2, front_matter(id="DR-0002") + BODY, slug="b")
        self.index()
        self.assertEqual(self.errors(), [])

    def test_amended_can_be_deprecated(self):
        self.record(1, front_matter(state="Deprecated", by="DR-0002") + BODY, slug="a")
        self.record(2, front_matter(id="DR-0002") + BODY, slug="b")
        self.index()
        self.assertEqual(self.errors(), [])

    def test_by_must_resolve(self):
        self.record(1, front_matter(state="Amended", by="DR-0009") + BODY)
        self.assertIn("status.by DR-0009 does not resolve", self.errors())

    def test_by_on_accepted_is_a_warning(self):
        self.record(1, front_matter(by="DR-0002") + BODY, slug="a")
        self.record(2, front_matter(id="DR-0002") + BODY, slug="b")
        self.assertTrue(any("status.by set on a Accepted record" in w for w in self.warnings()))

    def test_duplicate_ids(self):
        self.record(1, front_matter() + BODY, slug="a")
        self.record(2, front_matter() + BODY, slug="b")
        self.assertTrue(any("is also used by" in e for e in self.errors()))

    def test_duplicate_titles_are_flagged(self):
        self.record(1, front_matter(title="Workstation management boundary") + BODY, slug="a")
        self.record(2, front_matter(id="DR-0002", title="Workstation boundary management") + BODY, slug="b")
        self.assertTrue(any("has this already been decided" in w for w in self.warnings()))


class LegacyBodies(CorpusCase):
    LEGACY = front_matter(
        legacy_bodies='["DR-0001"]',
        title="Adoption",
    ) + BODY.replace("## References", "## Refs")

    def test_headings_are_demoted_not_exempt(self):
        self.record(1, front_matter() + BODY.replace("### Do Nothing", ""), slug="a")
        self.record(2, front_matter(id="DR-0002", title="Adoption") + "## Context\n", slug="adoption")
        self.warnings()
        self.record(
            2,
            front_matter(id="DR-0002", title="Adoption", legacy_bodies='["DR-0001"]') + BODY,
            slug="adoption",
        )
        self.assertIn("missing heading '### Do Nothing' (legacy_bodies)", self.warnings())
        self.assertNotIn("missing heading '### Do Nothing'", self.errors())

    def test_filename_mismatch_demoted_for_listed_records(self):
        self.write("2026-09-14-some-decision.md", front_matter() + BODY)
        self.record(
            2,
            front_matter(id="DR-0002", title="Adoption", legacy_bodies='["DR-0001"]') + BODY,
            slug="adoption",
        )
        self.assertTrue(any("(legacy_bodies)" in w and "filename" in w for w in self.warnings()))

    def test_unresolvable_listed_id_is_an_error(self):
        self.record(1, front_matter(legacy_bodies='["DR-0009"]') + BODY)
        self.assertIn("legacy_bodies lists DR-0009, which is not a managed record", self.errors())

    def test_a_record_cannot_exempt_itself(self):
        self.record(1, front_matter(legacy_bodies='["DR-0001"]') + "## Context\n")
        self.assertIn(
            "legacy_bodies lists this record itself; only an adopting record may exempt others",
            self.errors(),
        )

    def test_listing_a_conforming_record_warns(self):
        self.record(1, front_matter() + BODY, slug="a")
        self.record(
            2,
            front_matter(id="DR-0002", title="Adoption", legacy_bodies='["DR-0001"]') + BODY,
            slug="adoption",
        )
        self.assertTrue(any("already conforms; prune it" in w for w in self.warnings()))

    def test_strict_does_not_promote_legacy_warnings(self):
        self.write("2026-09-14-some-decision.md", front_matter() + BODY)
        self.record(
            2,
            front_matter(id="DR-0002", title="Adoption", legacy_bodies='["DR-0001"]') + BODY,
            slug="adoption",
        )
        self.index()
        self.assertEqual(self.errors(strict=True), [])

    def test_unlisted_legacy_filename_is_an_error_in_both_modes(self):
        self.write("2026-09-14-some-decision.md", front_matter() + BODY)
        self.index()
        self.assertIn("filename numbers 2026 but id is DR-0001", self.errors())
        self.assertIn("filename numbers 2026 but id is DR-0001", self.errors(strict=True))


class UnmanagedFiles(CorpusCase):
    def test_file_without_front_matter_warns_by_default(self):
        self.write("notes.md", "Some notes.\n")
        self.record(1, front_matter() + BODY)
        self.index()
        self.assertEqual(self.errors(), [])
        self.assertTrue(any("unmanaged file" in w for w in self.warnings()))

    def test_strict_makes_it_an_error(self):
        self.write("notes.md", "Some notes.\n")
        self.record(1, front_matter() + BODY)
        self.index()
        self.assertTrue(any("unmanaged file" in e for e in self.errors(strict=True)))

    def test_the_index_is_not_a_record(self):
        self.record(1, front_matter() + BODY)
        self.index()
        self.assertEqual(self.errors(strict=True), [])

    def test_hidden_directories_are_skipped(self):
        hidden = self.dir / ".draft"
        hidden.mkdir()
        (hidden / "note.md").write_text("scratch\n", encoding="utf-8")
        self.record(1, front_matter() + BODY)
        self.index()
        self.assertEqual(self.errors(strict=True), [])


class Index(CorpusCase):
    def test_lists_live_and_historical_separately(self):
        self.record(1, front_matter() + BODY, slug="live")
        self.record(2, front_matter(id="DR-0002", state="Superseded", by="DR-0003") + BODY, slug="old")
        self.record(3, front_matter(id="DR-0003", supersedes='["DR-0002"]') + BODY, slug="new")
        text = self.index()
        self.assertIn("## Live", text)
        self.assertIn("## Historical", text)
        self.assertLess(text.index("## Live"), text.index("## Historical"))
        self.assertIn("[DR-0003](0003-new.md)", text)
        self.assertEqual(self.errors(), [])

    def test_preamble_survives_regeneration(self):
        self.record(1, front_matter() + BODY)
        self.index()
        path = self.dir / "README.md"
        path.write_text(
            "# Our decisions\n\nHand written preamble.\n\n" + drs.INDEX_MARKER + "\n\nstale\n",
            encoding="utf-8",
        )
        text = self.index()
        self.assertIn("Hand written preamble.", text)
        self.assertNotIn("stale", text)
        self.assertEqual(self.errors(), [])

    def test_stale_index_is_an_error(self):
        self.record(1, front_matter() + BODY)
        self.index()
        self.record(2, front_matter(id="DR-0002", title="Second") + BODY, slug="second")
        self.assertIn("index is stale; run `drs.py index`", self.errors())

    def test_missing_index_is_an_error(self):
        self.record(1, front_matter() + BODY)
        self.assertIn("index is missing; run `drs.py index`", self.errors())

    def test_pipe_in_a_summary_is_escaped(self):
        self.record(1, front_matter(summary="A | B") + BODY)
        self.assertIn("A \\| B", self.index())


class NewRecord(CorpusCase):
    def new(self, title: str, **kwargs) -> int:
        args = type("Args", (), {"dir": str(self.dir), "title": title, **kwargs})()
        with contextlib.redirect_stdout(io.StringIO()):
            return drs.cmd_new(args)

    def test_scaffolds_the_next_number(self):
        self.record(7, front_matter(id="DR-0007") + BODY, slug="seven")
        self.assertEqual(self.new("A New Thing", author="A Human", reviewer=None), 0)
        path = self.dir / "0008-a-new-thing.md"
        self.assertTrue(path.exists())
        text = path.read_text(encoding="utf-8")
        self.assertIn('id: "DR-0008"', text)
        self.assertIn('date: "', text)
        self.assertIn('authors: ["A Human"]', text)
        self.assertIn('state: "Draft"', text)
        self.assertIn("## Promotion", text)

    def test_the_scaffold_loads_and_only_lacks_its_summary(self):
        self.new("Another Thing", author="A Human", reviewer=None)
        self.index()
        errors = self.errors()
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("summary is empty", errors[0])

    def test_reviewers_are_repeatable(self):
        self.new("Reviewed", author="A Human", reviewer=["One", "Two"])
        text = (self.dir / "0001-reviewed.md").read_text(encoding="utf-8")
        self.assertIn('reviewers: ["One", "Two"]', text)

    def test_title_is_escaped(self):
        self.new('A "quoted" thing', author="A Human", reviewer=None)
        text = (self.dir / "0001-a-quoted-thing.md").read_text(encoding="utf-8")
        self.assertIn('title: "A \\"quoted\\" thing"', text)


class Commands(CorpusCase):
    def test_check_exit_code_and_reporting(self):
        self.record(1, front_matter() + BODY)
        self.index()
        args = type("Args", (), {"dir": str(self.dir), "strict": False})()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(drs.cmd_check(args), 0)
        self.write("0002-broken.md", front_matter(id="DR-0002", title="Broken") + "## Context\n" * 1)
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            self.assertEqual(drs.cmd_check(args), 1)
        self.assertIn("error:", err.getvalue())

    def test_missing_directory_is_reported_not_traced(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(drs.main(["check", "--dir", str(self.dir / "nope")]), 1)
        self.assertIn("is not a directory", err.getvalue())


if __name__ == "__main__":
    unittest.main()

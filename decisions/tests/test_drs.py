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
                if finding.level == "warning" and finding.kind in drs.STRICT_PROMOTES:
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

    def test_a_wrapped_flow_sequence_parses(self):
        # This is dprint's output for a long list, including the trailing comma.
        parsed = self.parse(
            [
                "legacy_bodies: [",
                '  "DR-0001",',
                '  "DR-0002",',
                '  "DR-0003",',
                "]",
            ]
        )
        self.assertEqual(parsed["legacy_bodies"], ["DR-0001", "DR-0002", "DR-0003"])

    def test_a_block_sequence_parses(self):
        parsed = self.parse(["legacy_bodies:", '  - "DR-0001"', '  - "DR-0002"'])
        self.assertEqual(parsed["legacy_bodies"], ["DR-0001", "DR-0002"])

    def test_a_bracket_inside_a_wrapped_item_is_data(self):
        parsed = self.parse(
            [
                "legacy_bodies: [",
                '  "a ] b",',
                '  "c",',
                "]",
            ]
        )
        self.assertEqual(parsed["legacy_bodies"], ["a ] b", "c"])

    def test_an_unterminated_wrapped_sequence_names_its_first_line(self):
        with self.assertRaises(drs.FrontMatterError) as caught:
            self.parse(["legacy_bodies: [", '  "DR-0001",'])
        self.assertIn("x.md:2", str(caught.exception))
        self.assertIn("unterminated flow sequence", str(caught.exception))

    def test_a_block_sequence_item_that_is_a_mapping_is_rejected(self):
        with self.assertRaises(drs.FrontMatterError) as caught:
            self.parse(["legacy_bodies:", '  - id: "DR-0001"'])
        self.assertIn("sequence items must be scalars", str(caught.exception))

    def test_an_empty_sequence_item_is_rejected(self):
        with self.assertRaises(drs.FrontMatterError) as caught:
            self.parse(["legacy_bodies:", "  -"])
        self.assertIn("empty sequence item", str(caught.exception))

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

    def test_empty_id_is_reported(self):
        self.record(1, front_matter(id="") + BODY)
        self.assertIn("id is empty; a record needs its handle", self.errors())

    def test_a_sequence_where_a_scalar_belongs_is_a_finding(self):
        # Inject the raw line: front_matter() quotes its arguments, and quoting
        # is exactly what this case must not do.
        text = front_matter().replace('id: "DR-0001"', 'id: ["DR-0001"]')
        self.record(1, text + BODY)
        self.assertIn("'id' must be a scalar, not list", self.errors())

    def test_a_sequence_title_does_not_reach_the_index(self):
        text = front_matter().replace('title: "A Decision"', 'title: ["A", "B"]')
        self.record(1, text + BODY, slug="a")
        text2 = front_matter(id="DR-0002").replace('title: "A Decision"', 'title: ["A", "B"]')
        self.record(2, text2 + BODY, slug="b")
        self.assertIn("'title' must be a scalar, not list", self.errors())
        written = self.index()
        self.assertNotIn("['A', 'B']", written)

    def test_status_values_must_be_scalars(self):
        text = front_matter().replace('  state: "Accepted"', '  state: ["Accepted"]')
        self.record(1, text + BODY)
        self.assertIn("status values must be scalars", self.errors())

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

    def test_an_indented_heading_is_not_canonical(self):
        self.record(1, front_matter() + BODY.replace("## Decision", "  ## Decision"))
        self.assertIn("missing heading '## Decision'", self.errors())

    def test_headings_inside_a_fence_do_not_count(self):
        fenced = "\n".join("```markdown" if line == "## Decision" else line for line in BODY.splitlines())
        fenced = fenced.replace("```markdown", "```markdown\n## Decision", 1)
        self.record(1, front_matter() + fenced)
        self.assertIn("missing heading '## Decision'", self.errors())

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

    def test_by_on_off_state_warns_then_fails_strict(self):
        self.record(1, front_matter(by="DR-0002") + BODY, slug="a")
        self.record(2, front_matter(id="DR-0002") + BODY, slug="b")
        self.index()
        message = "status.by is set on a record in state Accepted, where it means nothing"
        self.assertIn(message, self.warnings())
        self.assertNotIn(message, self.errors())
        self.assertIn(message, self.errors(strict=True))

    def test_status_by_cannot_name_itself(self):
        self.record(1, front_matter(state="Amended", by="DR-0001") + BODY)
        self.assertIn(
            "status.by names this record; it cannot be its own cause", self.errors()
        )

    def test_a_record_cannot_supersede_itself(self):
        self.record(
            1,
            front_matter(state="Superseded", by="DR-0001", supersedes='["DR-0001"]') + BODY,
        )
        errors = self.errors()
        self.assertIn("supersedes lists this record; it cannot replace itself", errors)
        # One finding, not two: the self-edge is not also reported as a cycle.
        self.assertFalse(any("cycle" in error for error in errors), errors)

    def test_two_record_supersession_cycle(self):
        self.record(
            1,
            front_matter(id="DR-0001", state="Superseded", by="DR-0002", supersedes='["DR-0002"]')
            + BODY,
            slug="a",
        )
        self.record(
            2,
            front_matter(id="DR-0002", state="Superseded", by="DR-0001", supersedes='["DR-0001"]')
            + BODY,
            slug="b",
        )
        self.assertTrue(any("supersedes cycle" in e for e in self.errors()), self.errors())

    def test_status_by_cycle(self):
        self.record(1, front_matter(id="DR-0001", state="Amended", by="DR-0002") + BODY, slug="a")
        self.record(2, front_matter(id="DR-0002", state="Amended", by="DR-0001") + BODY, slug="b")
        self.assertTrue(any("status.by cycle" in e for e in self.errors()), self.errors())

    def test_a_valid_chain_is_not_a_cycle(self):
        self.record(1, front_matter(id="DR-0001", state="Superseded", by="DR-0003") + BODY, slug="a")
        self.record(2, front_matter(id="DR-0002", state="Superseded", by="DR-0003") + BODY, slug="b")
        self.record(
            3, front_matter(id="DR-0003", supersedes='["DR-0001", "DR-0002"]') + BODY, slug="c"
        )
        self.index()
        self.assertEqual(self.errors(), [])

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

    def test_a_listed_number_mismatch_is_not_called_conforming(self):
        self.write("0003-a.md", front_matter(id="DR-0001") + BODY)
        self.record(
            2,
            front_matter(id="DR-0002", title="Adoption", legacy_bodies='["DR-0001"]') + BODY,
            slug="adoption",
        )
        self.assertFalse(any("already conforms; prune it" in w for w in self.warnings()))
        self.assertIn("filename numbers 0003 but id is DR-0001 (legacy_bodies)", self.warnings())

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

    def test_a_dated_legacy_filename_is_described_as_dated(self):
        # The old message read the year as a record number: "filename numbers
        # 2026 but id is DR-0001" was true and useless.
        self.write("2026-09-14-some-decision.md", front_matter() + BODY)
        self.index()
        self.assertIn("dated filename; expected NNNN-slug.md", self.errors())
        self.assertIn("dated filename; expected NNNN-slug.md", self.errors(strict=True))


class StrictPolicy(CorpusCase):
    """--strict promotes unmanaged files and junk metadata, and nothing else."""

    def test_judgement_warnings_survive_strict(self):
        self.record(1, front_matter(title="Workstation management boundary") + BODY, slug="a")
        self.record(
            2, front_matter(id="DR-0002", title="Workstation boundary management") + BODY, slug="b"
        )
        self.index()
        self.assertTrue(any("has this already been decided" in w for w in self.warnings(strict=True)))
        self.assertEqual(self.errors(strict=True), [])

    def test_a_prune_warning_fails_strict(self):
        self.record(1, front_matter() + BODY, slug="a")
        self.record(
            2,
            front_matter(id="DR-0002", title="Adoption", legacy_bodies='["DR-0001"]') + BODY,
            slug="adoption",
        )
        self.index()
        self.assertEqual(self.errors(), [])
        self.assertTrue(any("prune it" in e for e in self.errors(strict=True)))


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
        self.assertIn("index is missing DR-0002; run `drs.py index`", self.errors())

    def test_a_formatter_padded_index_passes(self):
        # The index is a document. A formatter may pad its cells and align its
        # separators; the audit compares content, so that is not staleness.
        self.record(1, front_matter() + BODY)
        text = self.index()
        padded = []
        for line in text.splitlines():
            if line.startswith("|"):
                cells = [cell.strip() for cell in line.strip("|").split("|")]
                if set(cells[0]) <= {"-"}:
                    line = "| " + " | ".join("---" for _ in cells) + " |"
                else:
                    line = "| " + " | ".join(cell.ljust(40) for cell in cells) + " |"
            padded.append(line)
        (self.dir / "README.md").write_text("\n".join(padded) + "\n", encoding="utf-8")
        self.assertEqual(self.errors(), [])

    def test_rows_may_be_reordered(self):
        self.record(1, front_matter() + BODY, slug="a")
        self.record(2, front_matter(id="DR-0002", title="Second") + BODY, slug="b")
        text = self.index()
        head, _, tail = text.partition("## Live")
        rows = [line for line in tail.splitlines() if line.startswith("|")]
        body = [
            line
            for line in tail.splitlines()
            if not line.startswith("|") and line.strip()
        ]
        rebuilt = [rows[0], rows[1], rows[3], rows[2]] + body
        (self.dir / "README.md").write_text(
            head + "## Live\n\n" + "\n".join(rebuilt) + "\n", encoding="utf-8"
        )
        self.assertEqual(self.errors(), [])

    def test_a_row_in_the_wrong_section_is_reported(self):
        # The section tells a reader whether a decision is live. Moving an
        # Accepted row under Historical is a lie about content, not layout.
        self.record(1, front_matter() + BODY)
        text = self.index()
        moved = text.replace("## Live", "## Historical")
        (self.dir / "README.md").write_text(moved, encoding="utf-8")
        self.assertEqual(
            [
                "index places DR-0001 under Historical, but it is Accepted, "
                "which belongs under Live"
            ],
            [f for f in self.errors() if "places DR-0001" in f],
        )

    def test_a_row_outside_any_section_is_reported(self):
        self.record(1, front_matter() + BODY)
        text = self.index()
        (self.dir / "README.md").write_text(text.replace("## Live\n\n", ""), encoding="utf-8")
        self.assertTrue(
            any("under no heading" in error for error in self.errors()), self.errors()
        )

    def test_a_duplicated_row_is_reported(self):
        self.record(1, front_matter() + BODY)
        text = self.index()
        row = [line for line in text.splitlines() if line.startswith("| [DR-0001]")][0]
        stale = row.replace("| Accepted |", "| Draft |")
        (self.dir / "README.md").write_text(text + stale + "\n", encoding="utf-8")
        self.assertTrue(
            any("index lists DR-0001 more than once" in error for error in self.errors()),
            self.errors(),
        )

    def test_a_missing_marker_is_an_error(self):
        self.record(1, front_matter() + BODY)
        text = self.index()
        (self.dir / "README.md").write_text(text.replace(drs.INDEX_MARKER, ""), encoding="utf-8")
        self.assertTrue(any("no generated-section marker" in error for error in self.errors()))

    def test_index_refuses_to_regenerate_without_a_marker(self):
        # The old fallback treated the whole file as preamble and appended a
        # second generated section. Refusing is the only honest answer.
        self.record(1, front_matter() + BODY)
        text = self.index()
        (self.dir / "README.md").write_text(text.replace(drs.INDEX_MARKER, ""), encoding="utf-8")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = drs.main(["--dir", str(self.dir), "index"])
        self.assertEqual(code, 1)
        self.assertIn("has no generated-section marker", err.getvalue())

    def test_check_index_check_does_not_duplicate_the_index(self):
        # The regression that let two reviews disagree: a markerless index
        # passed `check`, then regenerating duplicated the whole table.
        self.record(1, front_matter() + BODY)
        self.index()
        path = self.dir / "README.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(drs.INDEX_MARKER, ""), encoding="utf-8"
        )
        self.assertTrue(self.errors())
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(drs.main(["--dir", str(self.dir), "index"]), 1)
        self.assertEqual(path.read_text(encoding="utf-8").count("| [DR-0001]"), 1)

    def test_a_legacy_filename_with_parentheses_round_trips(self):
        self.write("0001-a_(old).md", front_matter() + BODY)
        self.record(
            2,
            front_matter(id="DR-0002", title="Adoption", legacy_bodies='["DR-0001"]') + BODY,
            slug="adoption",
        )
        self.index()
        self.assertFalse(
            any("link differs" in error for error in self.errors()), self.errors()
        )

    def test_a_pipe_in_a_legacy_filename_round_trips(self):
        # Legal on disk, illegal in a table cell unless escaped. The legacy
        # exemption exists so such a record stays readable, not so it breaks
        # the index.
        self.write("0001-a|old.md", front_matter() + BODY)
        self.record(
            2,
            front_matter(id="DR-0002", title="Adoption", legacy_bodies='["DR-0001"]') + BODY,
            slug="adoption",
        )
        self.index()
        errors = self.errors()
        self.assertFalse(
            any("could not be read" in error or "missing DR-0001" in error for error in errors),
            errors,
        )

    def test_surrounding_whitespace_in_a_title_is_rejected(self):
        # The index is a table: a cell cannot carry leading whitespace, and
        # trimming it silently would make the index say something the record
        # does not.
        text = front_matter().replace('title: "A Decision"', 'title: " A Decision"')
        self.record(1, text + BODY)
        self.assertIn(
            "'title' has leading or trailing whitespace; the index is a table and "
            "cannot carry it — trim the value",
            self.errors(),
        )

    def test_surrounding_whitespace_in_a_summary_is_rejected(self):
        text = front_matter().replace('summary: "Do the thing."', 'summary: "Do the thing. "')
        self.record(1, text + BODY)
        self.assertTrue(
            any("'summary' has leading or trailing whitespace" in e for e in self.errors()),
            self.errors(),
        )

    def test_an_old_index_header_is_one_finding_not_a_cascade(self):
        # An adopter upgrading the tool meets this first; saying "missing" for
        # all nineteen records on top of it would bury the one thing to do.
        self.record(1, front_matter() + BODY)
        text = self.index()
        old = text.replace("| Record | Date | Title | Decision | State |", "| Record | Title | Decision | State |")
        old = old.replace("| --- | --- | --- | --- | --- |", "| --- | --- | --- | --- |")
        (self.dir / "README.md").write_text(old, encoding="utf-8")
        errors = self.errors()
        self.assertEqual(
            [
                "index header has 4 columns; this version writes 5 "
                "(Record, Date, Title, Decision, State) — run `drs.py index`"
            ],
            errors,
        )

    def test_line_numbers_are_file_line_numbers(self):
        self.record(1, front_matter() + BODY)
        text = self.index()
        junk = "| DR-0001 | 2026-11-24 | no link | Nothing. | Accepted |"
        (self.dir / "README.md").write_text(text + junk + "\n", encoding="utf-8")
        # Find the line the junk row actually sits on, 1-based.
        written = (self.dir / "README.md").read_text(encoding="utf-8").splitlines()
        expected = written.index(junk) + 1
        findings = [e for e in self.errors() if "could not be read" in e]
        self.assertEqual(1, len(findings), findings)
        self.assertIn(f"(line {expected})", findings[0])

    def test_an_unreadable_row_names_the_line(self):
        self.record(1, front_matter() + BODY)
        text = self.index()
        (self.dir / "README.md").write_text(
            text + "| DR-0001 | 2026-11-24 | no link | Nothing. | Accepted |\n",
            encoding="utf-8",
        )
        self.assertTrue(
            any("index row could not be read" in error for error in self.errors()),
            self.errors(),
        )

    def test_prose_below_the_marker_warns_and_fails_strict(self):
        self.record(1, front_matter() + BODY)
        text = self.index()
        (self.dir / "README.md").write_text(
            text + "\nA note a human added, which the next run would delete.\n",
            encoding="utf-8",
        )
        self.assertTrue(
            any("will be replaced" in warning for warning in self.warnings()),
            self.warnings(),
        )
        self.assertTrue(any("will be replaced" in error for error in self.errors(strict=True)))

    def test_title_and_link_mismatches_name_their_field(self):
        self.record(1, front_matter() + BODY)
        text = self.index()
        (self.dir / "README.md").write_text(
            text.replace("| A Decision |", "| A Different Decision |"), encoding="utf-8"
        )
        self.assertIn(
            "index is out of date for DR-0001: title differs; run `drs.py index`", self.errors()
        )
        (self.dir / "README.md").write_text(
            text.replace("(0001-a-decision.md)", "(0001-something-else.md)"), encoding="utf-8"
        )
        self.assertIn(
            "index is out of date for DR-0001: link differs; run `drs.py index`", self.errors()
        )

    def test_a_wrong_state_in_the_index_is_reported(self):
        self.record(1, front_matter() + BODY)
        text = self.index()
        (self.dir / "README.md").write_text(
            text.replace("| Accepted |", "| Draft |"), encoding="utf-8"
        )
        self.assertIn(
            "index is out of date for DR-0001: state differs; run `drs.py index`", self.errors()
        )

    def test_a_foreign_row_is_reported(self):
        self.record(1, front_matter() + BODY)
        text = self.index()
        extra = "| [DR-0009](0009-ghost.md) | 2026-11-24 | Ghost | Nothing. | Accepted |\n"
        (self.dir / "README.md").write_text(text + extra, encoding="utf-8")
        self.assertIn("index lists DR-0009, which is not a record", self.errors())

    def test_the_preamble_is_the_reader_s_to_edit(self):
        self.record(1, front_matter() + BODY)
        text = self.index()
        head, sep, tail = text.partition(drs.INDEX_MARKER)
        (self.dir / "README.md").write_text(
            "# Our records\n\nRead DR-0003 first.\n\n" + sep + tail, encoding="utf-8"
        )
        self.assertEqual(self.errors(), [])

    def test_a_pipe_in_a_summary_survives_the_round_trip(self):
        self.record(1, front_matter(summary="A | B") + BODY)
        self.index()
        self.assertEqual(self.errors(), [])

    def test_missing_index_is_an_error(self):
        self.record(1, front_matter() + BODY)
        self.assertIn("index is missing; run `drs.py index`", self.errors())

    def test_live_rows_show_their_state(self):
        self.record(1, front_matter(state="Draft") + DRAFT_BODY, slug="draft")
        self.record(2, front_matter(id="DR-0002", title="Second") + BODY, slug="second")
        text = self.index()
        live = text.split("## Live", 1)[1]
        self.assertIn(" State |", live)
        self.assertIn("| Draft |", live)
        self.assertIn("| Accepted |", live)

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

    def test_new_refuses_when_legacy_files_have_no_front_matter(self):
        # Blast radius: allocating over an all-legacy corpus is renumbering for
        # everyone who retrofits afterwards, so it takes a deliberate override.
        self.write("2026-09-09-legacy.md", "# A legacy record\n\nNo front matter.\n")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = drs.main(
                ["--dir", str(self.dir), "new", "After the retrofit", "--author", "A Human"]
            )
        self.assertEqual(code, 1)
        self.assertIn("1 file(s) here have no front matter", err.getvalue())
        self.assertIn("--force", err.getvalue())
        self.assertFalse((self.dir / "0001-after-the-retrofit.md").exists())

    def test_force_allocates_over_an_unmanaged_corpus(self):
        self.write("2026-09-09-legacy.md", "# A legacy record\n\nNo front matter.\n")
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            self.new("Forward only", author="A Human", reviewer=None, force=True)
        self.assertIn("no front matter", err.getvalue())
        self.assertTrue((self.dir / "0001-forward-only.md").exists())

    def test_new_is_quiet_on_a_fully_managed_corpus(self):
        self.record(1, front_matter() + BODY, slug="a")
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            self.new("Second", author="A Human", reviewer=None)
        self.assertEqual("", err.getvalue())

    def test_reviewers_are_repeatable(self):
        self.new("Reviewed", author="A Human", reviewer=["One", "Two"])
        text = (self.dir / "0001-reviewed.md").read_text(encoding="utf-8")
        self.assertIn('reviewers: ["One", "Two"]', text)

    def test_authors_with_quotes_commas_and_backslashes_round_trip(self):
        awkward = 'A "quoted, person" \\ backslash'
        self.new("Awkward authors", author=awkward, reviewer=['R "one, two"'])
        self.index()
        # The scaffold's own empty summary is the only finding it may have.
        self.assertEqual(self.errors(), ["summary is empty; it is the index line"])
        path = self.dir / "0001-awkward-authors.md"
        parsed = drs.parse_front_matter(
            drs.split_document(path.read_text(encoding="utf-8"), path)[0], path
        )
        self.assertEqual(parsed["authors"], [awkward])
        self.assertEqual(parsed["reviewers"], ['R "one, two"'])

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

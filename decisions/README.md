# decisions

**A protocol for decision records: what deserves one, how a record changes
after it is accepted, and how to keep a corpus of them honest.**

Decision records (also called ADRs) fail in a specific way. Not by being
missing — by being *wrong later*: an accepted record quietly rewritten to
describe what the code does now, a superseded record still claiming to be
current, a decision re-made because nobody found the record from two years
ago. Each of those costs a reader the one thing a record is for, which is
knowing what was decided and why.

This skill encodes a lifecycle and a format that are checkable, plus the
tooling to check them. It is opinionated on purpose: records are for decisions
somebody ratifies, in repositories that have reviews.

## What is here

| Path                                             | What it is                                                                                                                                                    |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`SKILL.md`](SKILL.md)                           | The runtime protocol: artifact taxonomy, when a record is earned, anatomy, lifecycle, amend/supersede procedures, reading order, agent obligations, adoption. |
| [`references/writing.md`](references/writing.md) | Depth for drafting: worked good/bad examples per section, how to write a summary line and a rubric record, how to write an amendment justification.           |
| [`assets/template.md`](assets/template.md)       | What `drs.py new` copies.                                                                                                                                     |
| [`scripts/drs.py`](scripts/drs.py)               | `new`, `index`, `check`. Python 3.11+, standard library only.                                                                                                 |
| [`tests/test_drs.py`](tests/test_drs.py)         | 78 tests, stdlib `unittest`.                                                                                                                                  |

## Setup

Nothing to install. Run the commands **inside the repository whose records you
are touching**, pointing at the script where the skill lives — the records
directory is discovered from the working directory, not from the script:

```bash
cd /path/to/your/repo
python3 /path/to/decisions/scripts/drs.py new "Publish writes durably"
python3 /path/to/decisions/scripts/drs.py index
python3 /path/to/decisions/scripts/drs.py check
```

The default records directory is `<repo root>/docs/decisions`, found by walking
up from the current directory to the nearest `.git`; `--dir` overrides it and
may go before or after the subcommand.

`new` reads the author from `git config user.name` unless you pass `--author`;
reviewers are passed with repeated `--reviewer` flags, because a scaffold
cannot know who will ratify it.

Run the tests with:

```bash
python3 -m unittest discover -s decisions/tests
```

## The shape it enforces

Front matter in a deliberately small YAML subset — flat scalars, one nested
`status` mapping, flow sequences of scalars — with states `Draft`, `Accepted`,
`Amended`, `Deprecated`, `Superseded`, and a body of five sections plus
`### Do Nothing` and (on drafts) `## Promotion`.

Two rules do most of the work:

- **Bodies are not rewritten to change what was decided.** A compatible change
  is amended in place, anchored to a record that says which clause moved;
  a reversal is superseded. The test is semantic: *would someone applying the
  record now make a different choice?*
- **The index is generated, committed, and checked.** It is the answer to
  "have we already decided this?", and a stale one is an error.

## Why these choices, with the evidence

The protocol was mined from three repositories that had each invented a
decision-record practice, and each of which exposed a different defect.

**Front matter instead of a status line in the body.** One of the three wrote
`**Status:** Accepted` in the prose. A record declared superseded by a later
record still said `Accepted` three weeks later, because nothing forced the
older file to be revisited. Prose pointers in one direction rot; a field is
checkable in both directions.

**Sequential ids instead of date prefixes.** A third practice named records
`YYYY-MM-DD-slug.md`. That made the date the only handle — too long to cite
inline, so nobody cited it — and it could not order two records written the
same day, which is exactly the shape of a quick correction. It also produced
two same-titled records five days apart with nothing in the filenames to say
which replaced which.

**`Draft` with named promotion criteria.** A practice that only had
`Accepted` forced every decision made before reality tested it to overclaim.
`Draft` plus observable criteria (and, where a tracker exists, a tracked item
for the promotion work) makes provisional decisions honest and keeps them from
becoming permanent by inattention.

**The bidirectional edge, scoped to supersession.** Requiring every
`status.by` to mirror into a `supersedes` rejects correctly amended and
deprecated records — those are not replacements. Only supersession has two
ends.

**No amendment log in the file.** Two of the three practices appended dated
amendment sections, which makes the current decision a fold over sections with
no merge discipline. Git already holds that history; the `status.by` pointer
names the record that justifies the current state.

**Standard library only, and no YAML parser.** A skill is adopted by copying a
directory into an agent's skill tree, so a dependency the host must install
makes the tool unusable in exactly the environments the skill exists to serve —
that is the same "zero configuration" argument the record format's own
predecessors made for repo-local tools. The cost is a hand-written parser for a
small dialect, which turns out to be a benefit: the format is small *because* it
is checkable, and anything outside it is rejected by line number rather than
silently misread.

**Adoption by retrofit, never by copying.** "Create a new record per still-live
decision and supersede the old one" is the tempting migration, and it is wrong
twice: the decision did not change, so the supersession edge is a lie in the
one place the corpus keeps its memory of *why* things changed; and it dates
every record to the migration. Retrofit front matter into the existing files
and leave the bodies alone.

**Legacy exemptions by id, not filename.** Adoption mints ids for every record
— which is what finally gives a `2026-09-09-python-environment.md` a citable
handle — so the exemption list has a uniform key even where the filenames
never did. A filename-keyed list would silently un-exempt records the day
someone renames them.

## What `check` cannot do

It verifies structure: ids, states, edges, headings, links, index freshness,
duplicate-looking titles. It cannot tell you whether the reasoning is honest,
whether an amendment was really compatible, or whether the alternatives were
considered rather than reconstructed afterwards. A clean `check` means the
corpus is internally consistent, not that it is good. `SKILL.md` says so in as
many words, and it should stay that way.

## Adoption

Forward-only by default: new records follow the format, and existing ones are
left alone until someone touches them. Unmanaged files — `.md` files in the
records directory with no front matter — are warnings, and errors under
`--strict`, which promotes tolerated findings to errors (unmanaged files, junk
metadata) and leaves adoption exemptions and duplicate-title warnings alone,
because those cannot be fixed mechanically and in the first case must not be
fixed at all.

For a full migration, retrofit in place: add front matter, keep the bodies,
keep the original decision dates, mint ids in chronological order, and record
the adoption in one record carrying `legacy_bodies` — the enumerated ids whose
bodies predate the section format. That list demotes their heading and
filename findings to warnings, so a migrated corpus can pass `check` without
rewriting the bodies the protocol forbids rewriting.

Do not copy decisions forward, and do not move old records into an archive
directory: `Deprecated` and `Superseded` already say a record is historical,
and moving it breaks every inbound reference from specs, code comments, and
instructions that are often immutable by convention.

## Composition

- [`orient`](../orient/) discovers decision records during its pass; when this
  skill is installed it should defer to it for the reading protocol.
- [`pebble`](../pebble/) carries the work that produces decisions, and the
  promotion work for drafts.
- [`worktrees`](../worktrees/) decides where the record is written. A record
  and the change that implements it belong in the same branch, so the
  citation and the code land together.

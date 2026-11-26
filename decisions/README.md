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
somebody ratifies, and one signature is enough — a one-maintainer repository
ratifies with its own.

## What is here

| Path                                             | What it is                                                                                                                                                    |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`SKILL.md`](SKILL.md)                           | The runtime protocol: artifact taxonomy, when a record is earned, anatomy, lifecycle, amend/supersede procedures, reading order, agent obligations, adoption. |
| [`references/writing.md`](references/writing.md) | Depth for drafting: worked good/bad examples per section, how to write a summary line and a rubric record, how to write an amendment justification.           |
| [`assets/template.md`](assets/template.md)       | What `drs.py new` copies.                                                                                                                                     |
| [`scripts/drs.py`](scripts/drs.py)               | `new`, `index`, `check`. Python 3.11+, standard library only.                                                                                                 |
| [`tests/test_drs.py`](tests/test_drs.py)         | Test suite, stdlib `unittest`.                                                                                                                                |

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

A fresh scaffold reports exactly two errors — an empty `summary` and an empty
`reviewers` — and that is the design, not a broken scaffold. Both are things
the scaffold cannot know: the summary is the author's judgement, and the
ratifier's name belongs to the ratifier, who adds it in the pull request.

Run the tests with:

```bash
python3 -m unittest discover -s decisions/tests
```

## The shape it enforces

Front matter in a deliberately small YAML subset — flat scalars, one nested
`status` mapping, sequences of scalars in any shape a formatter emits (flow,
wrapped flow with a trailing comma, or block) — with states `Draft`, `Accepted`,
`Amended`, `Deprecated`, `Superseded`, and a body of five sections plus
`### Do Nothing`.

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

This section is a dated narrative, kept as written: entries are appended with
the date the decision was made, and an entry that turns out wrong gets an
editor's note rather than a rewrite. Entries written before 2026-11-26 carry
no date — they were recorded as lessons rather than as events, and their dates
are not recoverable from the text.

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

*Editor's note (2026-11-26): the criteria half did not survive. `Draft` alone
fixed the overclaiming it was written for; the required section made the audit
certify criteria it had never read, and in use it meant "the pull request is
reviewed". See the end of this section.*

**The bidirectional edge, scoped to supersession.** Requiring every
`status.by` to mirror into a `supersedes` rejects correctly amended and
deprecated records — those are not replacements. Only supersession has two
ends.

**No amendment log in the file.** Two of the three practices appended dated
amendment sections, which makes the current decision a fold over sections with
no merge discipline. Git already holds that history; the `status.by` pointer
names the record that justifies the current state.

**The index is checked by content, not by bytes.** The first real corpus found
this before it had a record in it. A byte-identical comparison looks like the
strictest possible staleness check and is actually unworkable: `drs.py index`
writes plain tables, the repository's formatter aligns them, and the two then
fail each other in a loop — regenerate and the formatter complains, format and
the audit reports a stale index. Whichever runs last is "wrong". The contract
was the bug: a generated file that must also be pleasant for a human to read
cannot be byte-identical to its generator's output. `check` now reads the
tables back and compares what each row *says* — the record exists, the decision
matches, the state is current, the link resolves — so a formatted index is
still a valid one, and a genuinely stale row still fails with the field named.

That fix had a second lesson in it, found by review of the fix rather than by
use. The content comparison folded the page into a dictionary of cells, and a
dictionary cannot hold what a reader sees *outside* a cell: which section a row
sits under, whether the record appears twice, or whether the file is even the
generator's. All three are content, all three became invisible, and the shape of
the bug was the same each time — a parse that describes the cells instead of the
document. The check now returns rows in file order with their section, refuses
to guess at a markerless file, and reports any text below the marker that the
next regeneration would delete. A later round closed the same gap twice more,
both cheaply: pipes in a legacy filename are escaped in the link target, and a
title or summary with surrounding whitespace is rejected at the record
boundary, because a table cell can carry neither.

**The index carries dates, because ids are allocation order.** The second
adoption found this: a reconstructed record took the next free id while keeping
its original decision date, so it sorted between two later decisions with
nothing on the page to explain why. Sorting by date instead of id was the
alternative, and worse — ids are the handle people search for. One column keeps
both readable.

**The dialect accepts formatter output, not just hand-written input.** The
first full adoption found this the hard way: a record with seventeen
`legacy_bodies` ids gets its list wrapped by any YAML formatter, and a dialect
that accepted only a single-line flow sequence turned one formatting pass into
seventy errors — with the tempting "fix" being a `dprint-ignore-file` marker on
the most important record in the repository. Sequences are now accepted in every
shape a formatter emits: flow, wrapped flow with a trailing comma, and block.
The rule that came with it is in `SKILL.md`: never suppress the formatter to make
a record pass.

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

**No decision records in this repository (2026-11-26).** Two protocol
questions — whether `Draft` means unratified or unproven, and whether an
adopter can run the audit in CI when the tool is never vendored — had reached
the point where their reasoning needed a home, and both were written up asking
for a decision record, which this repository has nowhere to put. So we
considered adopting the format this skill defines, and declined.

Two arguments decided it. `SKILL.md` is the artifact an adopter actually
loads, so a records directory here is invisible to the reader the rationale
was for; and this repository has no review tradition, so a record's
`reviewers` field could only ever be satisfied by a maintainer ratifying their
own decision — which would have meant committing the corpus to one reading of
`Draft` *before* the `Draft` question was settled. The second is the sharper
of the two: adopting would have answered one of the open questions by
accident.

What was rejected is worth naming, because it is a legitimate use of the
format: a small corpus scoped to protocol decisions that bind adopters — three
or four records, not a habit — which would have given adopters a citable
handle for the reasoning instead of a URL pointing into this repository. What
replaced it is the arrangement `AGENTS.md` now states: rules in `SKILL.md`
that name their rejected option in a line, the argument here, and the work in
the tracker.

**`Draft` means ratified-but-unproven, and nobody signs it for you
(2026-11-26).** The state was defined twice — the lifecycle table read it as a
decision reality had not tested yet, the front-matter table as one nobody had
ratified — so every draft had to satisfy both at once, which is
unsatisfiable: a record awaiting review cannot name observable criteria about
how reality will behave. Three adopters resolved it three ways locally, and
the only Drafts that ever existed were bootstrap artifacts that should not
have landed. One reading now stands: `Draft` is ratified and unproven;
`reviewers` is required on every committed record; an unratified record lives
in the pull request, so merging it is the ratification.

What was rejected: a second state, `Provisional`, for the
ratified-but-unproven case, which would have kept both readings true. It loses
on evidence — no adopter has ever used the state it would add — and on its one
advantage: the only thing it buys is that the corpus may hold a record nobody
ratified, which is the thing the protocol is trying to keep out.

The second half of the decision is that `reviewers` records **who signed, not
that review happened**. A maintainer may ratify their own record. The earlier
position here was that a repository where nothing gets ratified does not need
records; the correction is that a solo repository ratifies with one signature,
which is a weaker claim but a true one, and worth having on the record.

**No promotion section (2026-11-26).** `## Promotion` was required on every
`Draft`, and the requirement could only ever be checked as far as a heading:
`check` can see `## Promotion` and cannot see whether the criteria beneath it
are observable, so the audit was certifying precisely the thing its own
doctrine says a check must never guess at. The reading that made it mean "the
pull request is reviewed" came from reasoning *about* the requirement —
gwl-systems' losing alternative, flint's two-kinds reconciliation — never from
content.

Not one was ever written: across three adoptions and 29 records there is no
`## Promotion` section anywhere. That is evidence of **non-use, not of
failure** — neither adopting corpus holds a `Draft` record at all, so there was
no draft to write one for — and the case for removal does not lean on it. What
the count shows is that a required section bought nothing; what the reasoning
shows is what it degenerated into once anyone thought about it.

The risk it was meant to prevent — a provisional decision becoming permanent by
inattention — is real, and its answer is the one the protocol already uses
elsewhere: say what would settle the decision where the decision is stated, and
put the follow-up in the tracker if there is one.

What was rejected: the two repairs that would have kept the section — making it
optional on `Draft`, or keeping it required and having `check` verify only that
the heading exists. Both keep the audit asserting what it cannot know, and the
second is what was actually shipping. A record written while the section existed
keeps it; an extra heading is not a finding.

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
- [`pebble`](../pebble/) carries the work that produces decisions, and whatever
  follow-up a draft's uncertainty needs.
- [`worktrees`](../worktrees/) decides where the record is written. A record
  and the change that implements it belong in the same branch, so the
  citation and the code land together.

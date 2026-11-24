---
name: decisions
description: Write, amend, supersede, audit, and read decision records (ADRs). Use when a choice is expensive to reverse and deserves a record, when a plan contradicts an already-recorded decision, or when decision records need an index, an audit, or adoption in an existing repo.
---

## When to use this skill

Load this skill before making a decision that will outlive the work that
produced it, and before proposing work in an area the repository has
already decided about.

- **Writing**: a choice just got made — or is about to be — that someone
  will need to understand later without re-deriving it.
- **Reading**: you are about to design, propose, or implement something in
  an area with existing records. Consult them first; the most common way
  records fail is that nobody reads them before re-deciding.
- **Changing one**: an accepted record no longer describes what the
  project does or wants.
- **Auditing**: the record set needs an index, its cross-references
  checked, or an existing repository brought onto the format.

## What a record is for

A decision record exists so a choice made once can be recovered later:
what the situation was, what was decided, what it cost, what was rejected
and why, in the words of whoever decided it. It is not documentation of
the system — that is the spec — and it is not the story of the work —
that is the change history.

Two properties follow, and everything below elaborates them:

1. **A record is evidence of what was decided.** Its body is not revised
   to say what someone later preferred, or the evidence is gone.
2. **A record is only useful if read.** Discovery is part of the
   discipline, not an afterthought: an index, a stable citable handle, and
   a habit of consulting both.

## Three kinds of artifact

Decision records are one of three artifacts that are easy to confuse:

| Artifact                 | Answers                                               | Lives                                            |
| ------------------------ | ----------------------------------------------------- | ------------------------------------------------ |
| **Decision record**      | Why is it this way, and what did we reject?           | `docs/decisions/`                                |
| **Spec / change design** | What does the system do, or what will this change do? | wherever the repo keeps specs (e.g. `openspec/`) |
| **Dated narrative**      | What happened, and what did we say at the time?       | wherever the repo keeps docs                     |

**The boundary test**: a change's design document explains *this change*;
a decision record covers something that **still binds after the change is
archived**. If the reasoning will still be true and binding in a year, it
is a decision record. If it stops mattering when the change lands, it is
design.

The corollary is the part people get wrong: **a change that implements a
recorded decision cites it; a change that makes a new decision either
lands the record first or in the same change.** Do not land the
implementation and promise the record later — by then the reasoning is
gone and the record will document the code instead of the decision.

**Dated narratives are kept as written.** When a narrative turns out to
be wrong, do not revise it to match the new understanding. Add an
editor's note at the top that says what changed and points at the record
that superseded it. The value of the narrative is that it is dated
evidence of what someone believed at a moment; rewriting it destroys
exactly that.

## When a decision earns a record

Write one when any of these is true:

- **Reversal is expensive** — code, data, or a public contract would have
  to be redone to change course.
- **Reconstruction is confusing** — the choice will look arbitrary out of
  context, and the rejected option will be proposed again by someone who
  cannot see why it lost.
- **It binds others** — a convention, invariant, boundary, or rubric that
  future contributors and agents are expected to follow.

Do not write one when:

- The choice is cheap and reversible. Git history already holds it.
- It is implementation detail. That belongs in the spec.
- The spec already states it. Cite the spec; do not duplicate it.
- "Do nothing" is the only alternative. Then ask whether it is actually a
  decision, or just what everyone was going to do anyway.

Reconstructing a decision that was made and never recorded is also in scope,
when the rationale still exists somewhere — an archived change, a review, a
tracked discussion — and something now depends on it being stated. The record is
the evidence's home, not a new argument.

**No record is a legitimate outcome.** A repository with a handful of
records covering the choices that really did bind is healthier than one
with a record per week that nobody reads, and a thin record set is not a
gap to be filled.

One record, one decision. If three choices are tangled together, write
three records and cross-reference them. A record that decides several
things can only be amended or superseded as a unit, which is how records
end up carrying stale clauses.

A **rubric** — a rule for deciding rather than a decision about one case
— is in scope and deserves a record of its own. A default with a bounded
exception is one of the most useful records a repository can have, because
it replaces a judgement call per case with an answer.

## Record anatomy

A record is YAML front matter, then a body whose headings are exact
strings:

```
## Context
## Decision
## Consequences
## Alternatives Considered
### Do Nothing
## References
## Promotion
```

Five top-level sections, `### Do Nothing` as a required subsection of the
fourth, and `## Promotion` on drafts. They are `##` because the record is
the document; they appear below as `###` only because this file is
discussing them.

`## Promotion` is required on a `Draft` and permitted on any later state: a
promoted draft keeps the section, because the criteria it names are the
evidence of what the draft was betting on. `check` compares these lines literally, so a variant —
`## Promotion:`, a different case, a setext underline — is a finding, and
the fix is the canonical heading rather than a looser matcher.

### Front matter

The front matter is a deliberately small dialect, so that it can be
checked mechanically: a block mapping of scalar fields, at most one nested
mapping (`status`), and sequences of scalars. A sequence may be written as a
flow list (`["a", "b"]`) or a block list (`- "a"` lines), and a flow list may
be **wrapped across lines with a trailing comma** — those are the shapes YAML
formatters emit, and rejecting any of them would make "formatted" and "valid"
incompatible. Multiline strings, anchors, tags, and nested mappings beyond
`status` stay outside the dialect; `scripts/drs.py check` rejects them and
names the line. Keep titles and summaries on one line.

**Never suppress the formatter to make a record pass.** No `dprint-ignore-file`
marker, no exclusion in the formatter's config, no "turn it off for this file".
A record that a repository's formatter would rewrite is a record the tool must
accept, and a suppression directive exempts the most important record in an
adoption while hiding the incompatibility instead of reporting it. If
formatting and validity disagree, the tool is wrong — report it rather than
routing around it, exactly as with a record body.

```yaml
---
id: "DR-0007"
title: "Decision Record Lifecycle"
summary: "Bodies are write-once; compatible changes amend in place, reversals supersede."
date: "2026-10-23"
authors: ["<the person or model that wrote it>"]
reviewers: ["<the person or model that ratified it>"]
status:
  state: "Accepted"
supersedes: []
---
```

| Field           | Required                                               | Meaning                                                                                                                                             |
| --------------- | ------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`            | always                                                 | `DR-` plus a zero-padded integer. The citable handle.                                                                                               |
| `title`         | always                                                 | The decision's name, not the question it answers.                                                                                                   |
| `summary`       | always                                                 | The decision in one sentence, 140 characters or fewer. This is what the index shows.                                                                |
| `date`          | always                                                 | The date the decision was made — not the date the file was written, copied, or reformatted.                                                         |
| `authors`       | always                                                 | Who reasoned it out. Name a model by model id when a model drafted it.                                                                              |
| `reviewers`     | always                                                 | Who ratified it. An agent may author a record; a human ratifies it. Empty only while the record is a `Draft` — a record nobody ratified is a draft. |
| `status.state`  | always                                                 | `Draft`, `Accepted`, `Amended`, `Deprecated`, or `Superseded`.                                                                                      |
| `status.by`     | when state is `Amended`, `Deprecated`, or `Superseded` | The id of the record that caused the **current** state.                                                                                             |
| `status.date`   | optional                                               | When the state changed. Omitted means "same as `date`, or recoverable from git".                                                                    |
| `supersedes`    | when this record supersedes anything                   | The ids it replaces.                                                                                                                                |
| `legacy_bodies` | on an adoption record                                  | Ids whose bodies predate this section format. Demotes their heading and filename checks to warnings; changes nothing else.                          |

Titles and summaries carry no leading or trailing whitespace: the index is a
table, and a cell cannot hold it. The audit reports it rather than trimming it,
because a trimmed cell would show something the record does not say.

`status.by` names the record that caused the current state, not one entry
per state the record has ever been in. A record can change state more than
once — amended, then deprecated — and the field holds the latest cause.
Earlier transitions are not lost: they are in git, and in the References of
the records that caused them. Do not grow a history list here; it would
duplicate git and then drift from it.

`authors` and `reviewers` are claims, like a commit author. They are worth
recording because provenance of *reasoning* is different from provenance
of code: a record drafted by a model and ratified by a human is a
different object from one a human wrote, and a later reader deserves to
know which they are reading. Requiring a reviewer is opinionated on
purpose: a repository where nothing gets ratified does not need decision
records, or at least not these.

**File naming**: `NNNN-slug.md`, where `NNNN` matches `id` and `slug` is a
short lowercase hyphenated version of the title. Numbers are never reused
and never reordered, and they record **allocation order, not chronology**: a
reconstructed decision keeps its original `date` and takes the next free id, so
the index carries the date for exactly this reason. A mismatch between filename and id is an error, except
for records listed in an adoption record's `legacy_bodies`, where it is a
warning: adoption keeps legacy filenames because renaming them breaks
inbound links from specs and instructions that are often immutable by
convention. The id in front matter, and the index, are authoritative; see
*Adopting this in an existing repository*.

### Context

The situation going into the decision: what needs deciding, what exists
today, what constrains it. Enough that a reader who was not there
understands the pressure.

**Do not argue the decision here, and do not describe the alternatives.**
A reader who knows only this section should not be able to guess the
answer. If Context gives away the Decision, the reasoning has been
rationalized backwards.

### Decision

What was decided, stated precisely and in the present tense: "X is Y",
not "we discussed making X into Y".

Detailed, but not implementation detail — module and boundary level, not
file level. Name the mechanism, the invariant, the default, and the
exception. Where the decision has several separable parts, use
subheadings, one per part, each stating a commitment a reader could hold
you to.

Where the record decides *how to decide*, state the test itself. A rubric
whose test is not stated is a preference.

### Consequences

What follows, at the level of logical modules and obligations rather than
files: what gets easier, what gets harder, what now has to be true, what
future work is now constrained, what is deliberately left unsolved.

Consequences are not a changelog. Do not enumerate the files to touch.
Do include the costs — a Consequences section with only benefits is a
sign the alternatives were not really considered.

### Alternatives Considered

One subheading per alternative, each stating why it lost. The alternative
that was actually argued for deserves its strongest form, not a strawman:
a reader should be able to see why a reasonable person preferred it.

**`### Do Nothing` is always present.** Why must a decision be made at
all? What happens if nothing changes? It may be short, but it must
describe real consideration. Undefined policy is not neutral — it
delegates the decision to whoever happens to hold the pen, and someone
will hold it.

### References

Links with a one-line description each: the spec that implements this,
tracker issues that carry the investigation, other records this one
builds on or replaces, external documentation. Keep it tight; a link and
five words beats a paragraph.

**An amendment or a supersession always has a reverse edge** —
`status.by` on the record it changes — and that edge is required. A
build-on citation is forward-only: a record does not accumulate a list of
everything that later cited it. Never open an accepted record to add a
backlink; it records a relation about a different record's decision, not a
change to this one.

### Promotion

A Draft record names, in this section, the **observable** criteria that
would promote it to Accepted: what has to be exercised, measured, or
demonstrated. "Wait and see" is not a criterion; "no unscheduled channel
joins occur over a month of real use" is.

If the repository has a tracker, file the promotion work so it cannot be
forgotten. A provisional decision with no path to promotion is an
unrecorded decision wearing a draft's clothes.

## Lifecycle

Five states, and a closed list of what a record may change once it is
accepted:

- a **state transition** changes the `status` block, and nothing else;
- an **amendment** changes the clauses its justifying record names, plus
  the `status` block;
- a **typographic or formatting fix** changes the body and leaves the
  status alone;
- **superseding an old record** changes that record's `status` block, and
  nothing else.

There is no fifth case. In particular, an accepted record's Decision is
never revised to describe what the project later did.

| State        | Meaning                                                       | Leaves via                                       |
| ------------ | ------------------------------------------------------------- | ------------------------------------------------ |
| `Draft`      | Decided in principle; reality has not tested it yet.          | Promotion to `Accepted`, or supersession.        |
| `Accepted`   | Decided and binding.                                          | Amendment, deprecation, or supersession.         |
| `Amended`    | Accepted and binding, with a compatible change made in place. | Further amendment, deprecation, or supersession. |
| `Deprecated` | No longer applicable, with no replacement.                    | Nothing; it is historical.                       |
| `Superseded` | Over-ridden by a later record.                                | Nothing; read the record `status.by` names.      |

`Amended` is still accepted and binding, so it can be deprecated like any
other live record: correcting one clause does not make the rest of a record
harder to retire.

Promotion is a state transition: `Draft` → `Accepted`, with the
`## Promotion` section left as written — it is the evidence, and deleting
it deletes the record of what the draft was betting on.

### The amend-or-supersede test

This is the decision that matters, and it is **semantic, not clerical**:

> If someone applying the record would now make a different choice, the
> change reverses a decision and must be **superseded**. If they would
> make the same choice, the change is an **amendment**.

"Is this change small enough to edit?" has no stable answer and will be
answered differently by every person and agent who touches it. "Does this
change what a reader would do?" has an answer, and it can be answered
before the edit.

## Amending a record

An amendment is for additions, clarifications, vocabulary extensions, and
corrections that do not change what a reader would do.

1. Edit the affected part of the body, and only that part.
2. Set `status.state` to `Amended`; set `status.by` to the id of the
   record that justifies the amendment; set `status.date`.
3. Write the justifying record — a short one, written for this amendment,
   stating **which clause changed and what replaced it**. It has to be
   written now because no earlier record can have described a change that
   had not happened yet; if several clauses move at once, one record can
   justify all of them. An amendment whose justification cannot be read is
   an unexplained body edit.
4. Point the two records at each other: the amended record's
   `status.by`, the justifying record's References.
5. Run `scripts/drs.py index` and commit both records and the index
   together.

Amendments are not free: an amended record cannot be read honestly
without following `status.by`, so each one costs the reader a hop. Amend
when the alternative is a whole new record for one clause; supersede when
the reasoning would otherwise mislead.

Typographic and formatting changes — reflowed text, fixed links, a
formatter's markdown normalization — are not amendments. Make them, and
leave the status alone. If a formatting pass would rewrite what a clause
*means*, it is not a formatting pass.

## Superseding a record

1. **Write the new record.** It states, in Context, what it replaces and
   why; in Alternatives, the position the old record took and why it lost;
   in `supersedes`, the old record's id. Its Alternatives MUST carry the
   old position, because that is the reasoning a reader will otherwise
   lose.
2. **Set the old record's status** to `Superseded` with `status.by` the
   new id and `status.date` the supersession date.
3. **Change nothing else in the old record.** Not its Decision, not its
   Consequences, not its title. It records what was decided then, and it
   stays that way.
4. **Both edges, one commit.** A supersession applied in half is the
   defect this rule exists to prevent — the orphaned record still claims
   to be live, and the only person who could fix it has moved on.
5. Run `scripts/drs.py index` and commit both records and the index.

Reissuing a record to change one clause is expensive: it forces restating
unchanged reasoning, several pages of it, to alter a sentence. That cost
is why the amendment path exists. It is still the right move when the
decision itself moved.

## Reading records before you decide

1. **Start at the index** (`docs/decisions/README.md`). It lists every
   record with its one-sentence decision and current state. This is how
   you find out the thing was decided two years ago.
2. **Open the records that govern your area**, and check
   `status.state` in the front matter — never infer state from the
   directory position, the filename, or the order of sections. A
   `Superseded` record can sort first.
3. **Follow `status.by` whenever it is present.** The amendment or
   supersession is part of the decision, not a footnote to it — an
   amended record cannot be read honestly without the hop, and a
   superseded one should not be read at all until you know what replaced
   it. A `Draft` has no `status.by`; there is nothing to follow.
4. **Read `Do Nothing`.** It usually holds the real argument.

If a record contradicts what you are about to build, you have found
either a constraint or a decision that needs revisiting. Both are useful;
neither is a reason to proceed quietly.

## Tooling

The skill bundles one script, `scripts/drs.py` (Python 3.11+, standard
library only), which operates on `<repo>/docs/decisions/` by default.

The canonical tool is the one in the installed skill — invoke it by path from
inside the repository being edited, and do not vendor a copy: a repo-local fork
is a second implementation that has to be maintained deliberately, and an
unversioned one is worse than no tool. If provenance matters, record the tool's
identity in the adopting record's References; `drs.py --version` prints a hash
of the script, which is the closest thing a skill has to a release number.
Pass `--dir` for a different location. It reads every `.md` file under
that directory, recursively, and always skips the generated index —
`README.md` in that directory is a view of the records, never one of them.

```bash
python3 scripts/drs.py new "<title>"   # scaffold the next record from assets/template.md
python3 scripts/drs.py index           # regenerate docs/decisions/README.md
python3 scripts/drs.py check           # audit the set; exit 1 on errors
python3 scripts/drs.py check --strict  # fail on tolerated findings too
```

`check` verifies what can be verified mechanically:

- front matter parses; ids are unique and well-formed; states are in the
  vocabulary;
- every `status.by` resolves to an existing record, and is present exactly
  when the state requires it — one set on an `Accepted` or `Draft` record is
  reported as junk metadata, which `--strict` turns into an error;
- each id in a record's `supersedes` resolves to a record in `Superseded`
  state whose `status.by` names that record — and every `Superseded`
  record is listed in the `supersedes` of the record naming it. The
  supersession edge is checked in both directions, and **only** that edge
  is: amendments and deprecations name a justifying record in
  `status.by`, but nothing replaces them, so their edges have no mirror;
- every required heading is present, `## Promotion` is present on every
  `Draft`, and its presence is accepted in any other state;
- the relative links written *inside* each record's body resolve;
- the index is current and complete;
- near-duplicate titles among live records are flagged for a human.

`--strict` promotes tolerated findings to errors — unmanaged files and junk
metadata — and deliberately leaves two alone. A `legacy` finding (a heading or
filename demoted by `legacy_bodies`) stays a warning forever, because the only
way to silence it would be to rewrite a body the protocol forbids rewriting. A
`judgement` finding (the duplicate-title heuristic) stays a warning too: a guess
about whether two decisions are the same is not something a build should fail
on. So `--strict` means "this corpus is clean", except where clean is either
impossible or not mechanical.

The heading checks compare whole lines as exact strings. That is
deliberate: they can report a missing section and cannot report a content
defect they did not see. The cost is that a valid variant heading will not
match, so the corpus must use the canonical headings given in *Record
anatomy* — a variant is a finding, not a false positive. Anything subtler
— is this section substantive? does this Draft name criteria reality could
test? — is out of scope, because a check that guesses is a check that
lies.

It also cannot see references *into* a record. The link check reads each
record's outbound links and nothing else, so a spec, an instruction file, a
code comment, or an inventory can be pointing at a path that no longer exists
while the audit stays green. That asymmetry is why renaming a record is a
repository-wide change and not a tidy-up: nothing here will tell you what you
broke.

It cannot verify the things that matter most: whether the reasoning is
honest, whether an amendment was really compatible, whether the
alternatives were considered or invented afterwards, whether a Draft
names promotion criteria reality could ever test. Those stay with you,
and a clean `check` is not evidence of a good record set.

**The index is generated, committed, and checked.** Commit it with the
records it describes: the new one-liner then appears in the pull request
diff, where a reviewer can see the decision in the same place they review
the reasoning. A stale index is an error, because a stale index is how a
repository ends up re-deciding something it settled last year.

**The check compares content, not bytes.** The index is a document people
read, so a formatter may pad its cells, align its separators, and reflow the
preamble above the generated section — none of that is staleness. What `check`
verifies is what a reader would take from the page:

- every record has a row, and no record has two. A stale row beside the current
  one is a contradiction the reader cannot resolve;
- each row carries the record's decision date. Ids are allocation order, not
  chronology — a reconstructed record can hold an early date and a late id — and
  without the date a reader cannot see where that happened;
- each row's link, title, decision and state still match the record it names;
- each row sits under the section its state implies — `Live` for a live state,
  `Historical` otherwise. A binding decision filed under "what we replaced" is
  wrong even when every cell is right;
- every row can be read at all. A row the audit cannot parse is a finding, not
  a line silently skipped.

Regenerate when the *content* drifts, and format however you like — but
regenerate before formatting, because `index` rewrites the file and formatting
first loses the formatting.

**The marker is regeneration metadata, not decoration.** `drs.py index` writes
`<!-- generated by drs; do not edit below -->`: everything below it is
regenerated, everything above it is yours. Keep your prose above the marker —
text below it is reported as a warning, because the next run will delete it. A
file with no marker at all is an error, and `index` refuses to regenerate one:
without the marker the generator cannot tell your prose from its own previous
output, and the fallback it used to make duplicated the entire index on the
next run.

## Agent obligations

The parts of this discipline that only bind an agent:

- **Consult before proposing.** Before drafting a proposal, a design, or
  a plan in an area with records, read the ones that govern it and say
  which you are honoring. If none apply, say that too.
- **Name the record you are following, by id**, in the proposal, the pull
  request body, and the commit subject (`DR-0007: ...`). An agent that
  cites a decision makes the citation checkable; one that paraphrases it
  makes it unverifiable.
- **Never rewrite a body to match what you built.** If the implementation
  diverged, either the implementation is wrong or the record needs an
  amendment or a supersession — propose that as its own tracked item, with
  the record named. Quietly correcting the record to describe the code is
  the failure this entire skill exists to prevent.
- **Never treat a record as advisory because it is inconvenient.** A
  binding record is a constraint on your work, not a suggestion from a
  previous session. If you believe it is wrong, say so and propose the
  change; do not route around it.
- **Do not invent alternatives.** If you did not consider them, write
  what you actually considered, however thin. A fabricated Alternatives
  section is worse than a short honest one, because it makes the record
  look like reasoning.
- **Write the record yourself when the decision is yours**, with `authors`
  naming you (by model id) and `reviewers` naming who ratified it. Do not
  leave a decision of yours unrecorded because a human did not write it.

## Adopting this in an existing repository

Adoption is forward-only by default: new records follow the format, and
existing ones are left alone until someone touches them. `check` reports
unmanaged files as warnings rather than errors for this reason.

When a repository does need its whole set migrated, retrofit **in place**.
Do it **before** scaffolding any new record: `drs.py new` allocates the next id
from *managed* records only, so on an all-legacy corpus it will hand out
`DR-0001` to a record written today, and the retrofit then has to renumber
around it. `new` **refuses** when it sees unmanaged files for this reason, naming the
count and telling you to retrofit first. `--force` allocates anyway, which is
what forward-only adoption wants; the blast radius of getting the order wrong is
corpus-wide renumbering, so it takes a deliberate word rather than a warning
line.

1. **Add front matter to the existing files; change no body.** Mint ids in
   chronological order, write the `summary` line, set `state` from what
   the record actually is — not from what its old status line claims,
   which may have gone stale when a superseding record was written and
   nobody returned to correct it.
2. **A body that carries a dated pre-protocol amendment stays `Accepted`.** A
   record whose body says "Amendment (2026-09-12)" and gives no justifying
   record cannot enter `Amended` — that state is defined by a named record, and
   inventing one to satisfy the field fabricates history. Set the state to the
   record's *current standing* and leave the amendment where it is: the body as
   published is the decision, and the note inside it is evidence of how it got
   there.
3. **Keep `date:` as the original decision date**, not the retrofit date.
   `date` means when the decision was made; a retrofit does not make it
   again.
4. **Allow filename/id mismatches for legacy files.** Renaming them
   breaks inbound links from specs, code comments, and instructions that
   are often immutable by convention — and `check` will not tell you, because
   it follows links out of records rather than into them. Keep the paths; the
   index is what bridges id to path. If a rename is genuinely wanted, grep the
   repository for the old path first, then treat it as a separate change with
   its own review.
5. **Record the adoption in one record**, carrying `legacy_bodies`: the
   ids of the records whose bodies predate this section format, with a
   reason per entry in its prose. Enumerated, not a blanket exemption — a
   blanket exemption becomes where future sloppiness hides, while adding a
   name to a list of names is a visible diff against a record.

`legacy_bodies` demotes the heading checks and the filename/id check to
warnings for exactly the ids it lists, and changes nothing else. Every
listed id must resolve to a managed record: an unresolvable id is an error,
because the list is the one place the exemption is supposed to be
trustworthy.
Listing a record whose body conforms anyway is a warning worth pruning. If
several records carry the field, their lists union.

Files with no front matter cannot be listed at all. They are *unmanaged*,
which is its own finding: a warning by default, since forward-only
adoption leaves them alone, and an error under `--strict`, which promotes
tolerated findings generally — with one exclusion, the generated index, which
is never a record and is always skipped. Adoption exemptions are the other
exception; see *Tooling*. Neither mode asks
anyone to rewrite a legacy body, because a check that can only pass by
falsifying history is a check people switch off.

### When the successor was never a record

A legacy record may name its replacement in prose — a change, a pull request, a
commit — because the decision was made and implemented without a record. Then
`status.by` has no record to name, and the three easy answers are all wrong:
naming the adoption record claims adoption caused the reversal, leaving the old
state claims the reversal never happened, and inventing no successor leaves a
reader with a dangling pointer.

**Write the missing record.** It states what was decided, keeps the original
decision date (the date the decision was made, not the date it was written
down), carries the old position in its Alternatives, and cites the evidence —
the archived change, its design, the review that approved it, the tracked work.

This is **not** the copy-forward this section forbids. Copy-forward fabricates a
supersession for a decision that did not change; reconstruction documents a
decision that did change and was never written down. The distinction is
evidence: an archived change plus the review that accepted it, not an inference
from the code. If that evidence does not exist, the decision belongs to
whichever record *does* explain it, or to none.

Claim only what the evidence supports. `authors` names whoever is accountable
for the reconstruction and anyone the evidence names as having decided; where
the drafting model is unrecorded — a change from before agents signed their work
— say so in References rather than inventing a name. A record that admits what
it cannot verify is worth more than one with a plausible blank filled in.

It is also the one legitimate exception to *do not write a record for a decision
you have already implemented*: the implementation is not the reason for the
record, the missing rationale is.

Do not copy decisions forward into new files and supersede the originals.
The decision did not change, so the supersession would be false, and the
supersession graph is the one part of the corpus that cannot be
reconstructed from anything else. Do not move legacy records into an
archive directory either: `Deprecated` and `Superseded` already say a
record is historical, and moving it breaks every inbound reference.

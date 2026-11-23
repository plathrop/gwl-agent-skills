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

| Artifact | Answers | Lives |
| --- | --- | --- |
| **Decision record** | Why is it this way, and what did we reject? | `docs/decisions/` |
| **Spec / change design** | What does the system do, or what will this change do? | wherever the repo keeps specs (e.g. `openspec/`) |
| **Dated narrative** | What happened, and what did we say at the time? | wherever the repo keeps docs |

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

A record is YAML front matter, then a body in six sections.

### Front matter

The front matter is a deliberately small dialect, so that it can be
checked mechanically: a block mapping of scalar fields, at most one nested
mapping (`status`), and flow sequences of quoted scalars
(`["a", "b"]`). Multiline strings, anchors, and nested structures beyond
`status` are outside the dialect; `scripts/drs.py check` rejects them and
names the line. Keep titles and summaries on one line.

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

| Field | Required | Meaning |
| --- | --- | --- |
| `id` | always | `DR-` plus a zero-padded integer. The citable handle. |
| `title` | always | The decision's name, not the question it answers. |
| `summary` | always | The decision in one sentence, 140 characters or fewer. This is what the index shows. |
| `date` | always | The date the decision was made — not the date the file was written, copied, or reformatted. |
| `authors` | always | Who reasoned it out. Name a model by model id when a model drafted it. |
| `reviewers` | always | Who ratified it. An agent may author a record; a human ratifies it. |
| `status.state` | always | `Draft`, `Accepted`, `Amended`, `Deprecated`, or `Superseded`. |
| `status.by` | when state is `Amended`, `Deprecated`, or `Superseded` | The id of the record that caused the state change. |
| `status.date` | optional | When the state changed. Omitted means "same as `date`, or recoverable from git". |
| `supersedes` | when this record supersedes anything | The ids it replaces. |

`authors` and `reviewers` are claims, like a commit author. They are worth
recording because provenance of *reasoning* is different from provenance
of code: a record drafted by a model and ratified by a human is a
different object from one a human wrote, and a later reader deserves to
know which they are reading.

**File naming**: `NNNN-slug.md`, where `NNNN` matches `id` and `slug` is a
short lowercase hyphenated version of the title. Numbers are never reused
and never reordered. If a repository has legacy records whose filenames do
not match their ids, the id in front matter and the index are
authoritative; see *Adopting this in an existing repository*.

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

Bidirectional links are not optional between records. If this record
builds on another, or reverses one, say so here — and see *Superseding*
for the matching edge on the other record.

### Promotion (Draft records only)

A Draft record names, in this section, the **observable** criteria that
would promote it to Accepted: what has to be exercised, measured, or
demonstrated. "Wait and see" is not a criterion; "no unscheduled channel
joins occur over a month of real use" is.

If the repository has a tracker, file the promotion work so it cannot be
forgotten. A provisional decision with no path to promotion is an
unrecorded decision wearing a draft's clothes.

## Lifecycle

Five states, and only the `status` block mutates once a record is
accepted.

| State | Meaning | Leaves via |
| --- | --- | --- |
| `Draft` | Decided in principle; reality has not tested it yet. | Promotion to `Accepted`, or supersession. |
| `Accepted` | Decided and binding. | Amendment, deprecation, or supersession. |
| `Amended` | Accepted and binding, with a compatible change made in place. | Further amendment, or supersession. |
| `Deprecated` | No longer applicable, with no replacement. | Nothing; it is historical. |
| `Superseded` | Over-ridden by a later record. | Nothing; read the record `status.by` names. |

Transitions mutate the `status` block only. Promotion is
`Draft` → `Accepted` with the `## Promotion` section left as written —
it is the evidence, and deleting it deletes the record of what the draft
was betting on.

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
3. Write or extend the justifying record so it states **which clause
   changed and what replaced it**. An amendment whose justification
   cannot be read is an unexplained body edit.
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
3. **Follow `status.by`** for anything not `Accepted` or `Amended`. The
   amendment or supersession is part of the decision, not a footnote to
   it.
4. **Read `Do Nothing`.** It usually holds the real argument.

If a record contradicts what you are about to build, you have found
either a constraint or a decision that needs revisiting. Both are useful;
neither is a reason to proceed quietly.

## Tooling

The skill bundles one script, `scripts/drs.py` (Python 3.11+, standard
library only), which operates on `<repo>/docs/decisions/` by default.
Pass `--dir` for a different location.

```bash
python3 scripts/drs.py new "<title>"   # scaffold the next record from assets/template.md
python3 scripts/drs.py index           # regenerate docs/decisions/README.md
python3 scripts/drs.py check           # audit the set; exit 1 on errors
python3 scripts/drs.py check --strict  # treat adoption-era warnings as errors
```

`check` verifies what can be verified: ids unique and well-formed; states
in the vocabulary; `status.by` present when required and resolving; every
`supersedes` edge matched by a `status.by` edge and vice versa; required
sections present, including `### Do Nothing`; a `## Promotion` section on
every Draft; relative links resolving; the index current and complete;
near-duplicate titles among live records flagged for a human.

It cannot verify the things that matter most: whether the reasoning is
honest, whether an amendment was really compatible, whether the
alternatives were considered or invented afterwards. Those stay with you,
and a clean `check` is not evidence of a good record set.

**The index is generated, committed, and checked.** Commit it with the
records it describes: the new one-liner then appears in the pull request
diff, where a reviewer can see the decision in the same place they review
the reasoning. A stale index is an error, because a stale index is how a
repository ends up re-deciding something it settled last year.

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

When a repository does need its whole set migrated, retrofit **in place**:

1. **Add front matter to the existing files; change no body.** Mint ids in
   chronological order, write the `summary` line, set `state` from what
   the record actually is — not from what its old status line claims,
   which may have gone stale when a superseding record was written and
   nobody returned to correct it.
2. **Keep `date:` as the original decision date**, not the retrofit date.
   `date` means when the decision was made; a retrofit does not make it
   again.
3. **Allow filename/id mismatches for legacy files.** Renaming them
   breaks inbound links from specs, code comments, and instructions that
   are often immutable by convention. The index bridges id to path.
4. **Record the adoption in one record**, with an **enumerated** list of
   records grandfathered under an older section format and a reason per
   entry. Enumerated, not a blanket exemption: a blanket exemption becomes
   where future sloppiness hides, while adding a name to a list of names
   is a visible diff against a record.

Do not copy decisions forward into new files and supersede the originals.
The decision did not change, so the supersession would be false, and the
supersession graph is the one part of the corpus that cannot be
reconstructed from anything else. Do not move legacy records into an
archive directory either: `Deprecated` and `Superseded` already say a
record is historical, and moving it breaks every inbound reference.

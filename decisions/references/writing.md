# Writing a decision record

Depth for when you are actually drafting. The mandatory rules are in
[`SKILL.md`](../SKILL.md); this file is about writing a record someone will
still want to read in two years.

## Start from the decision, not the discussion

A record is not a transcript with the conclusion at the bottom. If you find
yourself narrating the conversation — who said what, in what order, which
option seemed promising at lunchtime — you are writing a meeting minute. The
reader needs the shape of the problem, the choice, and what the choice costs.

The test for a finished record: someone who was not in the room can apply it
to a new case without asking you.

## The sections, and the failure mode of each

| Section      | Failure mode                                                                |
| ------------ | --------------------------------------------------------------------------- |
| Context      | Reads like an argument for the decision.                                    |
| Decision     | Reads like a plan; a reader cannot tell what they are now obliged to honor. |
| Consequences | Lists benefits only, or lists files.                                        |
| Alternatives | Strawmen, or a `Do Nothing` that says "nothing".                            |
| References   | A link dump with no statement of why the link matters.                      |

### Context that does not give away the answer

Bad:

> We need a queue, because the worker fleet cannot keep up with writes, and
> the right fix is to put a queue in front of the writers.

The first clause is context; the second is the decision and its justification,
front-run. A reader who reads only Context should be able to think of three
plausible directions, one of which happens to be the one taken.

Good:

> Writers currently do synchronous work that can take seconds. Their callers
> time out at one second, so an increase in write volume shows up as client
> errors rather than as latency. Two questions follow: where the asynchronous
> work belongs, and whether callers can be made to wait.

Nothing in that paragraph is the answer, and it names the shape of the
decision without naming it.

### Decision that states an obligation

Bad:

> We discussed whether to add a queue and decided it seemed reasonable.

Good:

> Every write that can succeed without its side effects complete publishes to
> `writes.in` and returns once the message is durable. Consumers must be
> idempotent: the queue guarantees at-least-once delivery, never
> exactly-once.

The second version is checkable. Someone reading it later can tell whether the
code honors it, and can tell when a proposed change would violate it. Aim for
sentences that can be *violated*, because those are the sentences that do work.

Where the decision has parts, split them into subheadings with a one-line
statement each. If a subheading needs three paragraphs, it may be a separate
record.

### Consequences that include the bill

Every real decision costs something. If yours does not, you have not found it
yet, and the reader will discover it at the worst moment. Name the cost in the
same voice as the benefit:

> Consumers must be idempotent, which most of them are not today: three of the
> five need a dedupe key added. Read paths must be able to tolerate a write
> that has been acknowledged but not yet applied — the UI will need a
> pending state it does not have.

Consequences are also where you record what you deliberately did **not**
solve, so the next person does not mistake an omission for an oversight.

### Alternatives that give the rejected position its best case

The point of the section is not to prove you were right. It is to save the next
person from re-proposing something that already lost, and to let them notice
when the reason it lost has stopped being true.

So state the strongest version of the alternative, then the specific reason it
lost — not a general worry. "Too complex" is not a reason; "requires a second
deployment unit per tenant, and we have no per-tenant deployment" is.

**`Do Nothing` is never filler.** The useful version answers: what breaks,
when, and how would we notice? If the answer is "nothing, ever", the record may
not be a decision at all.

### References that say why

> - `docs/specs/queue.md` — the delivery guarantee this record relies on
> - DR-0004 — the sync path this record deliberately leaves in place
> - the load test from 2026-08-02 — the numbers behind "callers time out at one
>   second"

A bare list of links is a reading assignment with no syllabus.

## Writing the summary line

The summary is the only part of the record most readers will see, because it is
what the index shows.

- State the decision, not the topic: "every write publishes durably before it
  returns", not "queue architecture".
- One sentence, no "we", no "this record discusses".
- Keep it under the 140-character limit with room to spare; a truncated
  summary in a table is worse than a terse one.

Test: read six summaries in a row. You should be able to tell what the system
now does, in what order it was decided, and where it reversed course.

## Rubric records

A record can decide *how to decide* — a default with a bounded exception. That
is often the most valuable kind, because it converts a judgement call per case
into an answer.

The requirement is that the test itself is stated and can be applied by someone
who disagrees with you:

> **Default:** a config secret is encrypted with sops+age to the fleet key.
> **Exception:** it may live in the control node's tool config when its blast
> radius is the account rather than the fleet. The test is blast radius, not
> where the value is used: a key that can destroy the fleet belongs elsewhere
> even if it never leaves one host.

Note what makes that usable: a default, an exception, a named test, and one
worked example of the test applied to a case where intuition points the other
way. Without the test, the exception becomes a hole.

## Justifying an amendment

An amendment is justified by a record that says which clause moved and what
replaced it. Keep it short and mechanical:

> DR-0012 § Decision, second paragraph, replaces "four-digit ids" with ids that
> widen past 9999. Counts above four digits are now reachable; the clause as
> written would make them invalid. No behavior changes below 9999, so nothing
> that applies the record makes a different choice.

That last sentence is the one that does the work: it states why this is an
amendment and not a supersession, in the terms the protocol uses.

## Superseding

The new record has to carry the old position in its Alternatives, because the
old record's reasoning is the thing a reader loses when they follow the
pointer. One paragraph, strongest form, and the specific reason it stopped
being right:

> **Event-sourced storage (DR-0001).** Append events and fold them; history is
> free and rebuilds are cheap. It lost on query: five of the six questions the
> team asks daily required a full fold, and the fold had grown to eleven
> seconds. The events are still the source of truth for the audit log, so this
> record reverts the storage decision without discarding the history.

### Splitting a record

When the old record decided several things and the decision moved on two of
them, the successors each carry one clause, and together they have to
reconstruct the reasoning the old record held. The old body stays where it is;
what each successor carries in its Alternatives is the old record's position on
*that* clause.

> **DR-0020 — Event storage.** Append events and fold them. It replaces the
> storage clause of DR-0001, which chose synchronous writes because the fold
> was cheap at the time; the fold is now eleven seconds, and that is the
> specific reason the clause stopped being right.
>
> **DR-0021 — Query path.** Reads are served from a projection, rebuilt from
> the event log. It carries DR-0001's read-path clause, which assumed the
> same table served reads and writes; the projection is what makes DR-0020's
> folds cheap enough to keep.

The test that a split is complete: a reader holding only the successors should
be unable to re-propose anything the old record had already rejected. A clause
that landed in no successor takes its reasoning with it, and the next person
argues for it again. A clause that landed in two successors leaves the pair
free to drift apart, which is the multi-decision record rebuilt one level up.

## What not to write

- **A decision you have already implemented and cannot reasonably revisit.**
  That is a changelog entry with a template around it. Say so in the change
  instead.
- **A record whose only alternative is `Do Nothing`.** If nothing plausible
  competed, the choice was not contested, and a record will not help anyone.
- **A record that restates the spec.** The spec says what the system does;
  the record says why it does that and not something else. If the "why" is not
  interesting, there is no record.
- **Anything you would not want cited back at you.** Records are read when
  someone wants to argue with a decision. Write the version you can defend.

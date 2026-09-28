# discovery

A skill that encodes the repository-orientation pass: what an agent
does in the first minutes of a session in one of Grey's repos (or any
repo with similar conventions), and what it should produce.

## Why this exists

Discovery kept being improvised. Each session re-derived the same
sequence — read the instructions, check the tracker, look at specs,
skim decision records, check git state — with varying thoroughness and
no cross-checking habit. Two failure modes recurred:

1. **Missing the instruction chain's requirements** (load these
   skills; this repo uses pebble/worktrees/openspec), leading to
   protocol violations later in the session.
2. **Taking documents at face value.** A proposal referencing a
   decision record that isn't on the branch, an issue describing
   finished work, a blocker rated below the work it blocks — none of
   these show up in any single command's output. They only surface
   when outputs are cross-checked against each other, and that step
   was never explicitly anyone's job.

The second failure mode is the reason this skill exists: the pass
itself is cheap, but the cross-checks and synthesis are where it pays
off. The canonical catch: a proposal in a worktree cited a
`secret-placement-rubric` decision record that didn't exist on either
`main` or the worktree's branch — because it lived on a *different
unmerged branch* the work was stacked on. Reading commands
individually would never have found that; comparing them did.

## What it does

`SKILL.md` is the runtime protocol. The summary:

1. **Instruction chain** — global then project instructions; load the
   skills they mandate.
2. **Skeleton and tooling** — root layout, README, toolchain configs.
3. **Issue tracker** — ready queue, blockers, epics, recent history;
   priority-discrepancy flags.
4. **Specs and changes** — openspec active changes read fully,
   archive skimmed for conventions.
5. **Decision records** — governing records read fully, supersession
   chains noted.
6. **Git/worktrees/PRs** — mapped to each other; stacking detected.
7. **Cross-checks** — references resolve, tracker matches reality,
   priorities agree with the graph, stale things named.
8. **Synthesis** — a compact report: where work is, what's anomalous,
   and (if asked) a ranked recommendation.

## Design notes

- **Order is deliberate.** Instructions first (they gate which steps
  apply), tracker before code (the queue tells you which code matters),
  cross-checks last (they need every earlier output to compare
  against).
- **Discovery is read-only by construction.** No claims, no edits, no
  PRs. This keeps it safe to run reflexively at session start without
  it turning into an unplanned state change.
- **Depth is a budget.** Full pass when the session will do real work;
  a scan suffices for a single-question session. The skill says where
  the depth goes when spent: instructions, active changes, governing
  decision records.
- **It composes with the other skills rather than replacing them.**
  Priority-discrepancy handling and work-ranking defer to the
  `pebble` skill; worktree discipline defers to the `worktrees` skill.
  Discovery's job is the orientation pass and the synthesis, nothing
  else.

## Configuration

None. The pass adapts by detection: `.pebble/` enables the tracker
step, `openspec/` enables the spec step, `docs/decisions` (or an ADR
directory) enables the record step. Repos with none of these just get a
shorter pass.
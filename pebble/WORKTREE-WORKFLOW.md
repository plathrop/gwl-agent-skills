# Pebble + git branches: the worktree workflow

*Design note, 2026-08-15. Decided by Grey and Remi after two incidents:
stranded pebble events riding an unmerged feature branch (2026-08-14)
and a textual-merge fight over `.pebble/issues.jsonl` during a rebase
(2026-08-15). Applies to every repo that uses pebble.*

## The problem

Pebble's ledger (`.pebble/issues.jsonl`) is an append-only event log
checked into the working tree. Git branches diverge working trees. So:

- Pebble commands run while the checkout sits on a feature branch
  append events to the *branch's* copy — events strand there until the
  branch merges (or forever, if it doesn't).
- A feature-branch checkout's ledger is a frozen snapshot: `pb list`
  lies by omission.
- When two branches both carry ledger changes, git's textual merge of
  the JSONL produces duplicate and out-of-order events.

## What the tool already does (measured, not assumed)

- **pb is worktree-aware.** Run from a *linked* worktree, `pb` resolves
  reads AND writes to the **primary checkout's** `.pebble` — not the
  worktree's own copy. (`--local` overrides.) Verified 2026-08-15 by
  creating an issue from a linked worktree and watching the primary
  checkout's file grow.
- **`pb merge` dedupes.** Merging two event files sharing history
  yields the union, not the concatenation. It is a reconciliation tool,
  not just a file combiner.
- **Nested worktrees technically work** (git allows `.worktrees/`
  inside the project root once gitignored, and `git clean -fdx` skips
  embedded repositories unless forced twice) — but every recursive tool
  (test runners, formatters, linters) must then be taught to ignore the
  directory, forever. Rejected in favor of a separate location.

## The discipline

1. **The primary checkout rests on main.** It is the ledger's home.
2. **Feature work happens in linked worktrees**, at
   `~/Source/worktrees/<project>/<feature>`.
3. **`.pebble` changes are committed only from the primary checkout**
   (which is always on main) — commit and push immediately, as today.
4. **pb commands from inside a feature worktree are fine and
   encouraged** — they transparently read and write main's live ledger.
   This is the mechanism that makes the discipline nearly free: the
   tool's default IS the desired behavior. Never pass `--local` in a
   feature worktree.

Consequences: feature branches never touch `.pebble`, so rebases and
merges stop conflicting on it; stray pebble commands from any worktree
land in the right place; there is one live view of the ledger, and
everyone sees it.

## Construction backstops (planned — not yet built)

- **Pre-commit hook** (versioned via `core.hooksPath=.githooks`):
  reject commits touching `.pebble/issues.jsonl` on any branch but
  main, with an error pointing at this document. Turns discipline slips
  into immediate, educational errors.
- **Merge driver**: `.gitattributes` entry
  `.pebble/issues.jsonl merge=pebble` with driver
  `pb merge %A %B -o %A`. When an accident slips through (or a clone
  lacks hooks), merges reconcile by event-union-with-dedupe instead of
  line-soup. (Validate event-order assumptions when building it.)

## Worktree ergonomics

- Each feature worktree needs its own `npm install` (JS repos). Remove
  worktrees promptly after merge; `git worktree list` is the survey
  command.
- Parallel work gets *easier*: two agents in two worktrees, no branch
  dance, no stash adventures.

## Transition

Adopt per-repo when its primary checkout next rests on main. (For
hearth: when PR #12 merges.) The first ledger write under the new rules
should be the pebble tracking the two backstops above.

## Upstream

pb's author has clearly circled this problem (the worktree-aware
default proves it). A kind feature request: a first-class
"ledger lives in the primary checkout" mode for pebble commands run in
the primary checkout while it sits on a feature branch — or a built-in
`pb merge-driver` subcommand suitable for `.gitconfig`.

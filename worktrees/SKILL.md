---
name: worktrees
description: Git worktree workflow discipline — the primary checkout rests on main, feature work happens in linked worktrees (~/Source/worktrees/<project>/<feature>), and shared working-tree state (Pebble ledgers) is committed only from main. Use when starting feature work, creating or switching worktrees, touching cross-branch shared files, or cleaning up after merges.
---

## When to use this skill

Load this skill when starting feature work in a repo, creating or
managing git worktrees, or committing files that are shared working-tree
state across branches (e.g. a `.pebble/` issue ledger). It exists because
agents conflated "how do I use pebble" with "where does my work
physically happen" — this skill is the latter, and it is
pebble-agnostic.

## Core discipline

1. **The primary checkout rests on main.** Don't do feature work in it.
2. **Feature work happens in linked worktrees**, at
   `~/Source/worktrees/<project>/<feature>`.
3. **Shared working-tree state commits only from the primary checkout.**
   If a file is append-only cross-branch state (a Pebble ledger,
   a changelog-by-convention), its changes belong on main immediately,
   never riding a feature branch.
4. **Remove worktrees promptly after merge** — `git worktree list` is
   the survey command.

## Working in a worktree

```bash
# Create (from the primary checkout, which is on main):
git worktree add ~/Source/worktrees/<project>/<feature> -b <feature-branch>

# Work there normally: edit, test, commit the FEATURE's files there.
# The feature branch carries the feature — nothing else.

# Clean up after merge:
git worktree remove ~/Source/worktrees/<project>/<feature>
```

- Each worktree needs its own dependency install (`npm install`,
  `uv sync`, whatever the repo uses) — worktrees do not share
  `node_modules` or venvs.
- The branch is cheap; the worktree is the workspace. Rebasing and
  force-pushing the feature branch is fine — it owns nothing outside
  itself.

## Interplay with Pebble (`.pebble/` repos)

In repos tracked with Pebble, the ledger (`.pebble/issues.jsonl`) is
shared working-tree state and follows rule 3:

- Run `pb` commands from anywhere, worktrees included — `pb` resolves
  to the **primary checkout's** ledger by default, so every view is the
  live view. Never pass `pb --local` in a feature worktree.
- Commit `.pebble` changes only from the primary checkout, on main,
  and push immediately.
- For the `pb`-side mechanics (ledger merge reconciliation, `--local`
  semantics), see the **pebble** skill.

## Backstops (belt and suspenders)

Discipline slips happen. Pebble repos can install construction
backstops via the pebble skill's `scripts/setup-worktree-backstops.sh`:
a pre-commit hook that rejects `.pebble` changes on non-main branches,
and a git merge driver that reconciles ledger files by event-union
instead of line-soup. If a pre-commit hook rejects your commit with a
pointer to this discipline, that's the backstop working — move the
change to the primary checkout.

## Why this exists

See [WORKTREE-WORKFLOW.md](WORKTREE-WORKFLOW.md) for the incident
history (stranded ledger events, textual JSONL merge fights), the
measured tool behaviors this relies on, and the rejected alternatives
(nested worktrees, per-worktree ledgers).

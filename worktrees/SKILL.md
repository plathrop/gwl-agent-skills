---
name: worktrees
description: Git worktree workflow discipline — the primary checkout rests on main, feature work happens in linked worktrees outside the checkout under a fixed worktree root, and shared working-tree state (append-only ledgers etc.) is committed only from main. Use when starting feature work, creating or switching worktrees, touching cross-branch shared files, or cleaning up after merges.
---

## When to use this skill

Load this skill when starting feature work in a repo, creating or
managing git worktrees, or committing files that are shared working-tree
state across branches (e.g. an append-only issue ledger checked into the
tree). It's about where work physically happens, and it is
tool-agnostic.

## Core discipline

1. **The primary checkout rests on main.** Don't do feature work in it.
2. **Feature work happens in linked worktrees**, outside the checkout,
   under a fixed worktree root. The default convention is
   `~/worktrees/<project>/<feature>` — set `WORKTREES_ROOT` (honored by
   this skill's setup script) or adjust the paths to your layout. The
   load-bearing rule is that worktrees live *outside the primary
   checkout*, not any particular path.
3. **Shared working-tree state commits only from the primary checkout.**
   If a file is append-only cross-branch state (an issue ledger, a
   changelog-by-convention), its changes belong on main immediately,
   never riding a feature branch.
4. **Remove worktrees promptly after merge** — `git worktree list` is
   the survey command.

## Working in a worktree

```bash
# Create (from the primary checkout, which is on main):
git worktree add <worktrees-root>/<project>/<feature> -b <feature-branch>

# Work there normally: edit, test, commit the FEATURE's files there.
# The feature branch carries the feature — nothing else.

# Clean up after merge:
git worktree remove <worktrees-root>/<project>/<feature>
```

- Each worktree needs its own dependency install (`npm install`,
  `uv sync`, whatever the repo uses) — worktrees do not share
  `node_modules` or venvs.
- The branch is cheap; the worktree is the workspace. Rebasing and
  force-pushing the feature branch is fine — it owns nothing outside
  itself.

## Ledger merge backstop

Discipline slips happen, so a repo can install a construction
backstop with `scripts/setup-ledger-merge.sh` from this skill: a git
merge driver (`.gitattributes` entry plus `pb merge`) that reconciles
an append-only ledger (e.g. `.pebble/issues.jsonl`) by event-union
instead of line-soup when a merge does collide. The script is
idempotent and also removes the pre-commit guard hook an older version
installed, if one is present — the discipline doesn't rely on hooks.
If a ledger merge conflicts, don't hand-pick lines: see
[WORKTREE-WORKFLOW.md](WORKTREE-WORKFLOW.md) for the reconciliation
recipe.

## Why this exists

See [WORKTREE-WORKFLOW.md](WORKTREE-WORKFLOW.md) for the incident
history, the measured tool behaviors this relies on, and the rejected
alternatives (nested worktrees, per-worktree ledgers).

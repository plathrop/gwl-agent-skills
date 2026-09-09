# Worktrees Skill

Agent skill for the household's git worktree discipline: the primary
checkout rests on `main`, feature work happens in linked worktrees at
`~/Source/worktrees/<project>/<feature>`, and shared working-tree state
(a Pebble ledger, for instance) is committed only from the primary
checkout.

## What the skill does

Teaches the agent where work physically happens, so that:

- the primary checkout stays clean and on main (always pull-able,
  always the live view of shared state),
- feature branches own nothing outside themselves (safe to rebase,
  force-push, abandon),
- cross-branch shared files never strand on unmerged branches.

## Why a separate skill

This discipline generalizes beyond any one tool — it applies to any
feature work in any repo. The sharpest teeth are the `.pebble/` ledger
rules, but feature-work placement and main-line hygiene stand on their
own.

## Rationale and incident history

See [WORKTREE-WORKFLOW.md](WORKTREE-WORKFLOW.md): the two incidents that
motivated the discipline, the measured tool behaviors it relies on, and
the rejected alternatives.

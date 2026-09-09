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

This discipline lived inside the **pebble** skill, because its sharpest
teeth are the `.pebble/` ledger rules. But agents only encountered it
when the task named pebble — then conflated "how do I track work" with
"where does my worktree go". The discipline is general (it applies to
any feature work in any repo), so it earned its own skill (2026-09-09).
The pebble skill still covers the `pb`-specific mechanics
(primary-tree resolution, `--local`, ledger merge reconciliation) and
cross-references this skill for the discipline.

## Rationale and incident history

See [WORKTREE-WORKFLOW.md](WORKTREE-WORKFLOW.md): the two incidents that
motivated the discipline, the measured tool behaviors it relies on, the
construction backstops (pre-commit hook + merge driver, shipped with the
pebble skill's scripts), and the rejected alternatives.

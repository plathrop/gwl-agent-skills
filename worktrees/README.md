# Worktrees Skill

Agent skill for the household's git worktree discipline: the primary
checkout rests on `main`, feature work happens in linked worktrees at
`~/Source/worktrees/<project>/<feature>`, and shared working-tree state
(append-only ledgers and the like) is committed only from the primary
checkout.

## What the skill does

Teaches the agent where work physically happens, so that:

- the primary checkout stays clean and on main (always pull-able,
  always the live view of shared state),
- feature branches own nothing outside themselves (safe to rebase,
  force-push, abandon),
- cross-branch shared files never strand on unmerged branches.

## Why a skill

This discipline is general — it applies to any feature work in any
repo, regardless of what tools the repo uses. It exists because agents
used to meet it only as a section of another skill's protocol and
conflated the two; work placement is its own concern and gets its own
skill (2026-09-09).

## Installing the backstops

For a repo with shared working-tree state, install the guard hook and
merge driver with:

```bash
~/Source/gwl-agent-skills/worktrees/scripts/setup-worktree-backstops.sh /path/to/repo
```

The script is idempotent and will:

- copy `scripts/pre-commit` to `<repo>/.githooks/pre-commit` (rejects
  ledger commits on non-main branches) and make it executable
- ensure `.gitattributes` contains `.pebble/issues.jsonl merge=pebble`
- set repo-local git config: `core.hooksPath=.githooks`,
  `merge.pebble.name`, and `merge.pebble.driver="pb merge %A %B -o %A"`
- create `~/Source/worktrees/<repo-name>` for the worktree convention

Re-run it for each clone and after updating the canonical hook. It
refuses to overwrite existing different hooks/config; integrate those
manually first.

## Rationale and incident history

See [WORKTREE-WORKFLOW.md](WORKTREE-WORKFLOW.md): the two incidents that
motivated the discipline, the measured tool behaviors it relies on, the
rejected alternatives, and the ledger merge-conflict recovery recipe
(appendix).

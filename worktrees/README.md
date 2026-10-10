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

## Installing the ledger merge backstop

For a repo with shared working-tree state (e.g. a pebble ledger),
install the event-union merge driver and the worktree-convention
directory with:

```bash
<path-to-this-repo>/worktrees/scripts/setup-ledger-merge.sh /path/to/repo
```

The script is idempotent and will:

- ensure `.gitattributes` contains `.pebble/issues.jsonl merge=pebble`
- set repo-local git config: `merge.pebble.name`, and
  `merge.pebble.driver="pb merge %A %B -o %A"`
- remove the pre-commit guard hook an older version of this skill
  installed, if one is present (pre-commit hooks are no longer part of
  the discipline)
- create the worktree-convention directory for this repo

Re-run it for each clone and after updating the script. It refuses to
overwrite existing different config; integrate those manually first.

## Rationale and incident history

See [WORKTREE-WORKFLOW.md](WORKTREE-WORKFLOW.md): the two incidents that
motivated the discipline, the measured tool behaviors it relies on, the
rejected alternatives, and the ledger merge-conflict recovery recipe
(appendix).

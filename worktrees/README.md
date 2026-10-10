# Worktrees Skill

Agent skill for a git worktree discipline: the primary checkout rests on
`main`, feature work happens in linked worktrees outside the checkout
under a fixed worktree root (default convention
`~/worktrees/<project>/<feature>`; set `WORKTREES_ROOT` or adjust to
your layout), and shared working-tree state (append-only ledgers and
the like) is committed only from the primary checkout.

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
  (`$WORKTREES_ROOT` or `~/worktrees` by default)

Re-run it for each clone and after updating the script. It refuses to
overwrite existing different config; integrate those manually first.

### One-time global alternative

The install splits in two: the `.gitattributes` entry is *committed*, so
it travels with every clone — but the git config is machine state and
does not, which is why a fresh clone of a pebble repo silently falls
back to textual merge until the script runs. If you work in
pebble-tracked repos regularly, you can set the merge driver in your
global git config once per machine instead of per clone:

```bash
git config --global merge.pebble.driver 'pb merge %A %B -o %A'
git config --global merge.pebble.name 'Pebble ledger event-union merge'
```

The driver is namespaced (`merge.pebble.*`) and inert in any repo
without a `merge=pebble` attribute, so this is safe on machines that
have `pb` installed. Only set it there: if the driver fires and `pb`
is missing, the merge errors out (loud, and arguably right for an
append-only ledger — but a surprise on a machine that never touches
pebble). The per-repo config the script writes uses the same values,
so the two coexist without conflict.

## Rationale and incident history

See [WORKTREE-WORKFLOW.md](WORKTREE-WORKFLOW.md): the two incidents that
motivated the discipline, the measured tool behaviors it relies on, the
rejected alternatives, and the ledger merge-conflict recovery recipe
(appendix).

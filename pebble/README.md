# Pebble Skill

Agent skill for working with [Pebble](https://www.npmjs.com/package/@markmdev/pebble),
a lightweight local-first issue tracker. Pebble stores issues as
append-only JSONL in `.pebble/issues.jsonl`, requires no service or
database, and is driven entirely by the `pb` CLI.

## What the skill does

The skill teaches the agent a simple issue-tracking protocol while it
codes:

1. **Orient** — check `pb ready` / `pb list` / `pb blocked` to find work
2. **Claim** — `pb claim <id>` before starting on an issue
3. **Record** — leave `pb comments` when making decisions or discoveries
4. **Close** — `pb close <id> --reason "<what changed>"` when done
5. **File** — create new issues for work discovered along the way

It also covers work breakdown (epics → tasks → dependencies), the
business rules an agent is likely to trip over (can't close via
`update`, can't claim blocked issues, epic close cascades), and
multi-worktree behavior.

## Design decisions

- **JSON-first.** `pb` outputs JSON by default; the skill instructs the
  agent to consume that and reserve `--pretty` for human-facing moments.
  This keeps agent consumption scriptable and unambiguous.
- **Protocol, not reference.** `SKILL.md` leads with the workflow loop
  (orient → claim → record → close → file) because that's what changes
  agent behavior. The full command table is included as a quick
  reference, but `pb <cmd> --help` and the upstream
  [CLI reference](https://github.com/markmdev/pebble/blob/main/docs/cli-reference.md)
  remain the source of truth.
- **Never touch the log.** The skill explicitly forbids editing
  `.pebble/issues.jsonl` directly — all mutations go through the CLI so
  events stay well-formed and sourced.
- **Harness-agnostic runtime.** No subagents or harness-specific
  tooling in the loaded protocol — just the `pb` CLI, so the skill
  works anywhere. Optional repo-setup scripts live under `scripts/`
  for the worktree backstops below.
- **Branch discipline is a house rule, not a tool feature.** Because the
  ledger lives in the working tree, feature branches diverge it. The
  skill prescribes the worktree workflow (primary checkout on main,
  feature work in linked worktrees) — see
  [WORKTREE-WORKFLOW.md](WORKTREE-WORKFLOW.md) for the design note.

## Requirements

- Node 18+ and Pebble installed: `npm install -g @markmdev/pebble`
- A repo initialized with `pb init` (the skill covers this if missing)

## Installing the worktree backstops

For a repo that uses Pebble with feature branches, install the ledger
guard hook and merge driver with:

```bash
~/Source/gwl-agent-skills/pebble/scripts/setup-worktree-backstops.sh /path/to/repo
```

Run it from a checkout of this skill repo. The script is idempotent and
will:

- copy `scripts/pre-commit` to `<repo>/.githooks/pre-commit` and make it
  executable
- ensure `.gitattributes` contains `.pebble/issues.jsonl merge=pebble`
- set repo-local git config: `core.hooksPath=.githooks`,
  `merge.pebble.name`, and `merge.pebble.driver="pb merge %A %B -o %A"`
- create `~/Source/worktrees/<repo-name>` for the house worktree
  convention

Re-run it for each clone and after updating the canonical hook in this
skill. It refuses to overwrite an existing different
`.githooks/pre-commit`, `core.hooksPath`, merge driver, or
`.gitattributes` merge setting; integrate those manually first.

Manual equivalent:

```bash
cd /path/to/repo
mkdir -p .githooks
cp ~/Source/gwl-agent-skills/pebble/scripts/pre-commit .githooks/pre-commit
chmod +x .githooks/pre-commit
printf '.pebble/issues.jsonl merge=pebble\n' >> .gitattributes
git config core.hooksPath .githooks
git config merge.pebble.name "Pebble ledger event-union merge"
git config merge.pebble.driver "pb merge %A %B -o %A"
```

## Usage

Install the skill using your harness's skill mechanism (see the repo
root README). It loads when the agent is working in a Pebble-tracked
repo or the user asks it to file/find/close issues via `pb`.

No configuration is needed for the skill itself. Pebble itself can be
configured via `.pebble/config.json` (issue ID prefix, worktree sharing
behavior). Repo backstop setup is optional but recommended for repos
that use feature branches — see "Installing the worktree backstops"
above.

## Reference

Upstream Pebble docs (full source at `~/Source/pebble/`):

- `docs/cli-reference.md` — complete command/flag reference
- `CLI_EXAMPLES.md` — example commands with sample output

Note: the docs occasionally drift from the shipped CLI (e.g. shorthand
flags that don't exist). Flag usage in this skill was verified against
the installed `pb --help` output; when in doubt, trust `pb <cmd> --help`.

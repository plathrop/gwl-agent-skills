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
4. **Close** — `pb close <id> -c "<what changed>"` when done
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
- **Harness-agnostic.** No subagents, scripts, or harness-specific
  tooling — just the `pb` CLI, so the skill works anywhere.

## Requirements

- Node 18+ and Pebble installed: `npm install -g @markmdev/pebble`
- A repo initialized with `pb init` (the skill covers this if missing)

## Usage

Install the skill using your harness's skill mechanism (see the repo
root README). It loads when the agent is working in a Pebble-tracked
repo or the user asks it to file/find/close issues via `pb`.

No configuration is needed. Pebble itself can be configured via
`.pebble/config.json` (issue ID prefix, worktree sharing behavior).

## Reference

Upstream Pebble docs (full source at `~/Source/pebble/`):

- `docs/cli-reference.md` — complete command/flag reference
- `CLI_EXAMPLES.md` — example commands with sample output

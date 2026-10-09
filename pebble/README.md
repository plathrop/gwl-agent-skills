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
   (search first to dedupe)
6. **Place** — pebbles have parents by default: bugs under the bugs
   bucket, future work under the backlog bucket, everything else under
   its workstream epic; if there's no home, ask rather than orphan
7. **Watch** — flag priority discrepancies (e.g. a P3 bug blocking a
   P1 task) with a recommendation, never silently adjusting
8. **Recommend** — rank ready work when asked for next steps
9. **Buckets** — recognize `[bucket]`-tagged standing epics (bugs inbox,
   future-work backlog) and exempt them from drift/staleness flags
10. **Claim honestly** — claiming flags work in progress, it doesn't
    lock it; surface contention instead of silently re-claiming

It also covers work breakdown (epics → tasks → dependencies), a P0–P4
priority rubric for consistent assignment, and the business rules an
agent is likely to trip over (can't close via `update`, can't claim
blocked issues, epic close cascades).

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
  works anywhere.
- **One fact about worktrees, stated once.** `pb` resolves to the
  primary checkout's ledger by default; the skill says so and says
  nothing more, because the discipline around worktrees is a separate
  concern (and a separate skill in this family, not a dependency).
- **Priorities are the user's call.** The skill gives the agent a
  rubric for consistent assignment and a protocol for flagging
  discrepancies, but priority changes are recommended, never made
  silently — the tracker is a shared record of the user's judgment.
- **Pebbles have parents by default.** Orphaned issues lose context and
  clutter the tree views, so every new issue gets a home: bugs under
  the bugs bucket, future work under the backlog bucket, everything
  else under its workstream epic. When no home exists, the agent asks
  rather than orphaning — and epic creation stays with the user
  (recommend, don't create unprompted), because epic scope is the same
  kind of judgment as priorities.
- **Claiming flags, it doesn't lock.** `pb claim` sets `in_progress` and
  nothing more — no assignee exists in the data model, and re-claiming
  an issue someone else is on succeeds silently (`claimedIds: []` means
  nothing was flipped). The skill tells the agent to read the claim
  response and surface contention instead of assuming the claim made
  the issue theirs. Verified against the CLI source ([`claimWithCascade`
  in state.ts](https://github.com/markmdev/pebble/blob/main/src/cli/lib/state.ts#L572),
  v0.2.0).
- **Bucket epics are first-class.** An epic tagged `[bucket]` in its
  title is a standing container (a bugs inbox or a future-work backlog),
  not a workstream. Its fixed priority is a positioning label, not a
  reflection of its children, so the parent/child-drift heuristic exempts
  it — and orientation exempts it from staleness flags too. The title
  tag is the authoritative signal: names vary by project and P4 does not
  identify a bucket, so the tag is what an agent keys off.

## Requirements

- Node 18+ and Pebble installed: `npm install -g @markmdev/pebble`
- A repo initialized with `pb init` (the skill covers this if missing)

## Usage

Install the skill using your harness's skill mechanism (see the repo
root README). It loads when the agent is working in a Pebble-tracked
repo or the user asks it to file/find/close issues via `pb`.

No configuration is needed for the skill itself. Pebble itself can be
configured via `.pebble/config.json` (issue ID prefix, worktree sharing
behavior).

## Reference

Upstream Pebble docs ([source repo](https://github.com/markmdev/pebble/);
local checkout at `~/Source/external/pebble/`):

- [docs/cli-reference.md](https://github.com/markmdev/pebble/blob/main/docs/cli-reference.md) — complete command/flag reference
- [CLI_EXAMPLES.md](https://github.com/markmdev/pebble/blob/main/CLI_EXAMPLES.md) — example commands with sample output

Note: the docs occasionally drift from the shipped CLI (e.g. shorthand
flags that don't exist). Flag usage in this skill was verified against
the installed `pb --help` output; when in doubt, trust `pb <cmd> --help`.

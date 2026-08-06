---
name: pebble
description: Track work with the Pebble local issue tracker (pb CLI) — create, claim, block, and close issues, work from ready queues, and record progress as you code
---

## When to use this skill

Load this skill when working in a repository that uses Pebble for issue
tracking (a `.pebble/` directory exists at the repo root, or the user
mentions `pb` / Pebble issues). Use it to find work, record progress, and
keep the issue tracker in sync with what you are actually doing.

Pebble is a local-first tracker: all state lives in `.pebble/issues.jsonl`
(append-only JSONL). Never edit this file directly — always use the `pb`
CLI.

## Output conventions

`pb` is JSON-first: every command returns JSON by default, which is what
you should consume. Only add `--pretty` when the user is watching the
terminal and wants human-readable output.

```bash
pb ready              # JSON — use this
pb ready --pretty     # human-readable — only for the user's benefit
```

Partial IDs work everywhere — you rarely need to type a full issue ID.

## Core protocol

### 1. Orient

At the start of a task, find out what there is to work on:

```bash
pb ready                 # issues with no open blockers (the work queue)
pb list --status in_progress   # work already claimed (possibly by you earlier)
pb blocked -v            # what is stuck and why
pb summary               # epic-level view with child completion counts
```

If the user named a specific issue, go straight to it:

```bash
pb show <id>             # full details: status, parent, deps, comments
pb comments list <id>
```

### 2. Claim before you work

Before making code changes for an issue, claim it:

```bash
pb claim <id>
```

If the claim fails because of open blockers, run `pb blocked -v` or
`pb dep tree <id>` to see the blocker chain, and either work the blocker
first or report back to the user.

### 3. Record progress

Leave a trail as you work — comments are cheap and the log is the memory
of the project:

```bash
pb comments add <id> "Found root cause: race in session refresh"
```

Add a comment when you: discover something non-obvious, make a design
decision, hit a blocker, or hand off partial work.

### 4. Close with context

When the work is done and verified, close with a `--reason` explaining
what was done — the reason becomes part of the permanent event log:

```bash
pb close <id> --reason "Fixed in src/auth/login.tsx; added regression test"
```

Always pass `--reason`. If there is more to say (decisions, caveats,
follow-ups), also add `--comment` — but never close "bare" when you can
state why in one line.

Close multiple issues at once with `pb close <id1> <id2> ...`.

### 5. File new work you discover

If you find bugs, follow-up work, or scope creep while coding, file it
rather than silently expanding your current task:

```bash
pb create "Fix flaky logout redirect" -t bug -p 1
pb create "Refactor auth module" -t task --parent <epic-id>
```

## Structuring work

When the user asks you to plan or break down a larger piece of work:

1. Create an epic: `pb create "<goal>" -t epic -p <0-4>`
2. Create child tasks: `pb create "<step>" --parent <epic-id>`
3. Wire dependencies so `pb ready` produces a sensible queue:
   - `pb dep add <task> <blocker>` — task is blocked by blocker
   - or at creation: `pb create "..." --blocked-by <id1,id2>`
4. Show the result: `pb summary` and `pb dep tree <epic-id>`

Notes:

- **Blocking** deps are directional and control the ready queue.
- **Related** links (`pb dep relate <a> <b>`) are bidirectional and do
  not affect readiness — use for "see also" relationships.
- Priorities: 0 critical, 1 high, 2 medium (default), 3 low, 4 backlog.
- Types: `task`, `bug`, `epic`.

## Business rules that will bite you

- Statuses: `open`, `in_progress`, `blocked`, `closed`.
- You **cannot** set status to `closed` via `pb update` — use `pb close`.
- You **cannot** claim or start an issue with open blockers.
- Closing an epic is refused while any child is still open — close or
  reparent the children first.
- Dependency cycles are rejected.
- `pb delete` soft-deletes (hidden, restorable with `pb restore`);
  deleting an epic cascades to its children.

## Multi-worktree repos

In a git worktree, `pb` uses the **main tree's** `.pebble/` by default so
issues are shared across worktrees. If the user wants worktree-local
issues, pass `--local` (global flag, works on any command):

```bash
pb --local create "Experiment-specific task"
```

Every event records which worktree it came from (`lastSource` field), so
you can tell where work happened.

## Command quick reference

| Command | Purpose |
|---------|---------|
| `pb init` | Initialize `.pebble/` in the current directory |
| `pb create <title> [-t type] [-p 0-4] [-d desc] [--parent id] [--blocked-by ids]` | New issue |
| `pb update <id> [--title|--description|--priority|--status|--parent]` | Edit fields (not close) |
| `pb claim <id...>` | Set status `in_progress` (cascades to open parents) |
| `pb close <id...> [--reason text] [--comment text]` | Close with a recorded reason |
| `pb reopen <id> [--reason text]` | Reopen closed issue |
| `pb delete <id...>` / `pb restore <id...>` | Soft delete / restore (`-r` for reason) |
| `pb list [--status|-t|--priority|--parent] [-v] [--flat] [--limit n]` | Filtered listing (tree by default) |
| `pb show <id>` | Issue details |
| `pb ready [-v]` | Work queue — no open blockers |
| `pb blocked [-v]` | Blocked issues, with reasons |
| `pb dep add\|remove <id> <blocker>` | Manage blockers |
| `pb dep relate\|unrelate <a> <b>` | Manage related links |
| `pb dep list <id>` / `pb dep tree <id>` | Inspect dependencies |
| `pb comments add\|list <id> [text]` | Comments |
| `pb summary [--status s] [--limit n]` | Epic progress overview |
| `pb history [--limit n] [--since 7d]` | Recent activity |
| `pb search <query>` | Full-text search |
| `pb graph [--root id]` | ASCII dependency graph |
| `pb ui [--port n]` | Web UI (default port 3333) |

Global flags: `-P/--pretty` (human output), `--local` (worktree-local
`.pebble/`), `-h/--help`. Shorthand flags vary per command — check
`pb <cmd> --help` when unsure.

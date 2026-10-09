---
name: pebble
description: Track work with the Pebble local issue tracker (pb CLI) — create, claim, block, and close issues, work from ready queues, and record progress as you code
---

## When to use this skill

Load this skill when working in a repository that uses Pebble for issue
tracking (a `.pebble/` directory exists at the repo root, or the user
mentions `pb` / Pebble issues). Use it to find work, record progress, and
keep the issue tracker in sync with what you are actually doing.

Pebble is a local-first tracker: all state lives in `.pebble/issues.jsonl`,
an append-only JSONL event log. Never edit this file directly — every
change goes through the `pb` CLI.

## Output conventions

`pb` outputs JSON by default; consume that. Add `--pretty` only when
the user is watching the terminal and wants human-readable output.

```bash
pb ready              # JSON — use this
pb ready --pretty     # human-readable — only for the user's benefit
```

Partial IDs work everywhere — you rarely need a full issue ID.

## Core protocol

### 1. Orient

At the start of a task, find out what there is to work on:

```bash
pb ready                      # issues with no open blockers (the work queue)
pb list --status in_progress  # work already claimed (possibly by you earlier)
pb blocked -v                 # what is stuck and why
pb summary                    # epic-level view with child completion counts
pb history --since 7d         # recent activity — what moved, what closed
```

If the user named a specific issue, go straight to it:

```bash
pb show <id>                  # full details: status, parent, deps, comments
```

There is no `pb comments list` — comments are included in `pb show <id>`.

### 2. Claim before you work

Before making code changes for an issue, claim it:

```bash
pb claim <id>
```

If the claim fails because of open blockers, run `pb blocked -v` or
`pb dep tree <id>` to see the blocker chain, then either work the
blocker first or report back to the user.

### 3. Record progress

Leave a trail as you work — comments are cheap, and the log is the
memory of the project:

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
follow-ups), also add `--comment` — but never close bare when you can
state why in one line. Close multiple issues at once with
`pb close <id1> <id2> ...`.

### 5. File new work you discover

If you find bugs, follow-up work, or scope creep while coding, file it
rather than silently expanding your current task — but `pb search` first
to check it doesn't already exist; if it does, extend it with a comment
instead of filing a duplicate:

```bash
pb search "logout redirect"   # dedupe before creating
pb create "Fix flaky logout redirect" -t bug -p 1
pb create "Refactor auth module" -t task --parent <epic-id>
```

See *Structuring larger work* below for epics and dependencies.

## Shaping the tracker

### Structuring larger work

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
  not affect readiness — use them for "see also" relationships.
- Types: `task`, `bug`, `epic`.
- Priorities: 0–4 — see *Assigning priorities* for how to choose.

### Assigning priorities

Priorities are coarse bands, 0–4: **P0** critical, **P1** high, **P2**
medium (the default for new work), **P3** low, **P4** backlog.
"Backlog" is just the pretty-print label for P4 (`pb show --pretty`
renders `Priority: P4 (backlog)`); there is no separate backlog value,
and `--priority` accepts 0–4 only.

Consistent assignment keeps the queue meaningful. The convention:

- **P0 — dangerous or blocking**: dangerous bugs (data loss, security,
  active outage), and any issue — bug or task — that blocks current
  P1 work.
- **P1 — active work**: active workstreams and immediate next goals;
  bugs that associate closely with one of those; and bugs that don't
  meet the "dangerous" bar but are likely to become footguns during
  P1 work, block P1 work, or describe risks that are currently
  prevented by convention rather than construction.
- **P2 — default**: the default priority for new work.
- **P3 — should-do, deferrable**: the default for things that should be
  done but can reasonably wait — cleanups, and bugs that don't fall
  into a higher level.
- **P4 — future**: future features, explicitly deferred work, and
  one-off thoughts discovered during other work.

Note the consequence for blockers: a blocker of current P1 work is P0
by definition. That inversion is the most common discrepancy you'll
find — see *Keeping the tracker consistent*.

### Bucket epics

Most Pebble projects keep one or two **bucket epics**: permanent
containers for a category of work rather than bounded deliverables.
They never "finish"; their priority is a *fixed label* that positions
them in the list, not a reflection of their children. The common two:

- **A bugs inbox** (P0) — sits at the top so bugs surface above feature
  work. Children carry *independent* priorities; a P3 bug in a P0
  bucket is by design, not drift.
- **A future/backlog grab-bag** (P4) — "someday" ideas. Every child is
  P4. Active work leaves the bucket by *promoting the child's priority
  and/or reparenting it under a workstream epic* — never by adjusting
  the bucket's priority.

A bucket epic is tagged `[bucket]` in its **title** (e.g.
`Bugs [bucket]`, `Backlog [bucket]`), so the tag is visible in
`pb list`, `pb summary`, and `pb ready` without `pb show`. The tag is
the authoritative signal: an epic is a bucket iff its title carries
`[bucket]` (or the project's AGENTS.md names it one). Untagged epics
are workstreams for the *Parent/child drift* heuristic in *Keeping the
tracker consistent*. In repos that predate the convention, an
evergreen description ("evergreen", "parking lot", "holding pen",
"standing epic") is a hint that an untagged epic may be a bucket.
When you create a bucket epic, tag its title.

When you initialize a repo (`pb init`), create the two buckets as
scaffolding rather than retrofitting them later:

```bash
pb create "Bugs [bucket]" -t epic -p 0 -d "Evergreen bucket epic for filing bugs."
pb create "Backlog [bucket]" -t epic -p 4 -d "Evergreen bucket epic for filing future work."
```

Default to both — an empty bucket is cheap, and a missing one means
retrofitting later. Skip one only if the repo clearly won't collect
that kind of work.

### Keeping the tracker consistent

Priorities and the dependency graph tell two stories about urgency, and
they must agree. When they contradict, that's usually a stale
priority — but it's not your call to fix silently. Flag it, recommend,
and let the user decide.

Watch for:

- **Blocker inversion** — a blocker rated lower priority than the issue
  it blocks. Nothing downstream of it can start until it's done, so it
  is at least as urgent as what it blocks (a blocker of P1 work is P0
  by the convention above). Either the blocker should be raised or the
  blocked issue should be lowered — one of the two ratings is wrong.
- **Parent/child drift** — a *workstream* epic's priority should
  roughly reflect its children: a P1 epic whose children are all P4 is
  probably a stale epic; a P4 epic with a P1 child probably has a
  child with a mistyped priority. Bucket epics are exempt (see
  *Bucket epics*): their priority is a fixed label, not a child
  average. Before flagging drift, check the epic's title for the
  `[bucket]` tag. The one bucket case still worth flagging is a
  *non-P4 child filed in a P4 backlog* — that child is active work in
  the wrong place; promote and/or reparent the child, don't touch the
  bucket.

These surface in any view that shows the graph or hierarchy:
`pb dep tree <id>`, `pb blocked -v`, `pb summary`, and `pb list --parent`.

When you spot a discrepancy:

1. **Don't silently `pb update --priority`.** Priorities encode the
   user's judgment, and the tracker is the shared record — the user
   may know a reason the numbers disagree that the graph doesn't show.
2. **Raise it with a concrete recommendation**: which issue's priority
   looks wrong, which direction to move it, and why (e.g. "P3 bug #47
   blocks the P1 login epic #12 — suggest raising #47 to P0, or
   lowering #12 if it's no longer urgent").
3. **If the user agrees**, make the change and add a `pb comments add`
   noting why, so the history explains the jump.

Also sanity-check at creation time: before wiring `pb dep add` /
`--blocked-by` or parenting a child under a *workstream* epic, look at
the priorities you're about to connect. (The bucket-epic exemption
applies here too — a P3 bug under a P0 bugs bucket is fine.)

## Recommending next work

When the user asks "what are the best next steps?", rank the work
rather than dumping `pb ready`. The user is asking for judgment, not a
mechanical sort. Weight the dimensions like this:

1. **Priority as coarse bands, not a strict sort.** P0/P1 is "do now";
   P2/P3 is scheduled work; P4 is ideas. Within a band, don't let a
   one-level priority difference decide — priorities are coarse and
   go stale.
2. **Level of definition** — the strongest within-band tiebreaker. A
   well-specified issue can be started correctly without a design
   conversation first; the top of this dimension is an issue with an
   associated openspec spec. Vague issues need the user's input before
   they're truly ready.
3. **Age** — an old issue has been passed over repeatedly, which
   deserves an explanation in your ranking (fix it, finish it, or
   deprioritize it) even if it stays ranked low.
4. **Complexity** — a nudge, not a rule: lower-complexity issues are
   quicker, lower-risk wins, so prefer them when a band is otherwise
   tied.
5. **Your judgment — an override, not a weight.** If you believe
   something deserves a higher or lower position than the mechanical
   ranking produces, move it and say why. The user values agent
   judgment that catches nuance, but only when it's argued, never
   silently.

Present the result as a short ordered list — issue, one-line rationale
each — and flag anything you promoted or deferred against the
mechanical ordering.

## Reference

### Business rules that will bite you

- Statuses: `open`, `in_progress`, `blocked`, `closed`.
- You **cannot** set status to `closed` via `pb update` — use `pb close`.
- You **cannot** change an issue's `type` via `pb update` (no `--type`
  flag). To promote a task → epic (or demote), use the HTTP API that
  `pb ui` serves: `pb ui --no-open --port <n>` then
  `curl -X PUT localhost:<n>/api/issues/<id> -H 'Content-Type: application/json' -d '{"type":"epic"}'`.
  The data model supports type changes; only the CLI omits the flag.
- You **cannot** claim or start an issue with open blockers.
- Closing an epic is refused while any child is still open — close or
  reparent the children first.
- Dependency cycles are rejected.
- `pb delete` soft-deletes (hidden, restorable with `pb restore`);
  deleting an epic cascades to its children.

### Working from a git worktree

If you are working in a git worktree, `pb` reads and writes the
**primary checkout's** `.pebble/` ledger, not the worktree's — that is
the default behavior and the correct one. Nothing extra to do.

### Command quick reference

| Command | Purpose |
|---------|---------|
| `pb init` | Initialize `.pebble/` in the current directory |
| `pb create <title> [-t type] [-p 0-4] [-d desc] [--parent id] [--blocked-by ids]` | New issue |
| `pb update <id...> [--title\|--description\|--priority\|--status\|--parent]` | Edit fields (not close); accepts multiple IDs |
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
| `pb comments add <id> <text>` | Add a comment (read comments via `pb show <id>`) |
| `pb summary [--status s] [--limit n]` | Epic progress overview |
| `pb history [--limit n] [--since 7d]` | Recent activity |
| `pb search <query>` | Full-text search |
| `pb graph [--root id]` | ASCII dependency graph |
| `pb ui [--port n]` | Web UI (default port 3333) |

Global flags: `-P/--pretty` (human output), `-h/--help`. Shorthand
flags vary per command — check `pb <cmd> --help` when unsure.
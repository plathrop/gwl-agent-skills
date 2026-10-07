---
name: orient
description: Systematically orient in a repository at the start of a session — read the instruction chain, mine the issue tracker, specs, decision records, and git/worktree/PR state, cross-check references, and synthesize where the work is.
---

## When to use this skill

Load this skill when entering a repository for the first time in a
session, when asked to "familiarize yourself", "get up to speed", "see
where things stand", or when resuming work in a repo after a gap.
It is also the right preamble before recommending what to work on
next — you cannot rank work you haven't seen.

**Orient is read-only.** It claims no issues, edits no files, opens
no PRs. Its output is a synthesis for the user and orientation for the
agent. Acting on a finding — filing a bug, claiming work, recording a
finding in the tracker — is a *follow-up* after you report, never part of
the pass itself.

## Principles

- **Instructions before code.** The instruction chain (global →
  project AGENTS.md, or their equivalents) gates everything else; read
  them before touching the repo, and load any skills they name as
  required.
- **Mine, don't list.** The value of orientation is synthesis — blocking
  chains, stale work, contradictions — not a dump of command output.
- **Cross-check references.** The highest-value finds are broken ones: a
  decision record cited by a proposal but missing from the branch, an
  open issue describing finished work, a branch with no worktree.
- **Depth follows stakes.** Read governing documents (instructions,
  active change artifacts, current decision records) fully. Skim
  everything else. Budget a full pass when the session will do real
  work; a quick scan suffices to answer a single question.

## The pass, in order

Order matters: instructions tell you which of the later steps apply,
and the tracker tells you which code matters before you read any.

### 1. Instruction chain

- Read the global agent instructions, then the project's AGENTS.md.
  Instruction chains compound; if they conflict, surface the conflict
  rather than silently picking a winner.
- Load skills the project instructions name as required (pebble,
  worktrees, openspec, a review wrapper, etc.).

### 2. Skeleton and tooling

- `ls` the repo root; read the README.
- Identify the toolchain from its config files (mise.toml, package.json,
  dprint.json, requirements.yml, ...) and any layout docs the project
  itself points at (e.g. an `ansible/README.md`).

### 3. Issue tracker (if the repo uses one, e.g. `.pebble/`)

```
pb ready              # the work queue
pb list --status in_progress   # work already claimed / in flight
pb blocked -v         # stuck work and why
pb summary            # epics in flight
pb history --since 14d
pb dep tree <epic>    # for each active epic
```

- Build the picture: in-flight epics, the ready queue, blocking chains.
- Flag priority discrepancies per the pebble skill — blockers rated
  below the work they block, parents drifting from their children.
  Recommend a fix; don't apply it silently.

### 4. Specs and changes (if the repo uses openspec)

```
openspec list --json
openspec status --change <name> --json
```

- Active changes are the live work: read each change's `proposal.md`,
  `design.md`, `tasks.md`, and delta specs. Note which tasks are done.
- Archived changes are the history: skim titles for cadence and the
  project's conventions, read one if its subject is relevant.
- Read `openspec/config.yaml` if present for stated project context.

### 5. Decision records

- Locate the decision-record directory (commonly `docs/decisions`).
- Read the records that govern current conventions fully, and note the
  supersession chains — which record is authoritative for each concern
  is exactly the fact later sessions will need.
- Recent records matter most; older ones are background.

### 6. Git, worktrees, and pull requests

```
git log --oneline -20
git worktree list
git branch -a
gh pr list --state open --json number,title,baseRefName,headRefName,reviewDecision
gh pr view <n> --json title,baseRefName,headRefName,headRefOid,reviewDecision,reviews,comments
```

- Map the three to each other: a worktree without a branch, a branch
  without a PR, an open PR whose branch has moved on — each is a
  question to resolve, not necessarily a problem.
- Note each PR's review state (approved / changes requested / pending)
  and whether the local merge protocol applies.
- Check what each open branch is based on: **stacked branches** (a
  change branched off another unmerged change) change both the review
  diff and the merge order.

### 7. Cross-checks (where orientation earns its keep)

- **References resolve.** Distinguish the two kinds: *local artifacts*
  (decision records, specs, in-repo runbooks) should exist on the branch
  you're reading; *service-backed references* (tracker issues, external
  URLs) resolve against their service, not the filesystem — don't flag a
  valid issue or URL as broken. For a missing local artifact, suspect a
  sibling or stacked branch first: search by path across refs
  (`git log --all --oneline -- <path>`), then the PR list, before
  declaring the reference dead. (`--grep` matches commit *subjects*,
  which need not contain the filename.)
- **Tracker matches reality.** An open issue describing work that
  appears done in history (or closed work that regressed) is worth
  flagging; don't silently reconcile. (In a worktree, `pb` reads the
  *primary checkout's* ledger, so "reality" is main's, not the
  worktree's.)
- **Priorities agree with the dependency graph** (per the pebble
  skill).
- **Stale things** get named: untouched in-progress issues, lingering
  worktrees, branches whose PRs are gone.

### 8. Synthesize

Report compactly — the user wants the shape, not the raw data:

- **Where the work is**: in-flight epics and their blocking chains.
- **What just happened**: recent history, one line per theme.
- **Open PRs**: title, base, review state, and any stacking.
- **Anomalies**: every cross-check failure and what it implies.
- If asked what to do next, rank the work per the pebble skill's
  ranking guidance, rather than reciting the ready queue.

## What not to do

- Don't write, claim, or start anything during the orientation pass.
- Don't ask the user for facts the repo can answer — verify first, ask
  only for genuine judgment calls.
- Don't read everything fully; depth is a budget, spend it on
  instructions, active changes, and governing records.
- Don't restate the project's instructions back to the user verbatim —
  they wrote them. Synthesize what's *live* now.
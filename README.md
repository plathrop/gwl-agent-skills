# gwl-agent-skills

Agent skills for coding agents: harness-agnostic protocols for repo
orientation, local issue tracking, git worktree discipline, GitHub
attribution, and driving other agents headlessly.

The skills are opinionated by design — each encodes a way of working
that has earned its keep in real sessions — but they are written to be
**usable as-is**: no personal names, layouts, or identities baked in,
and any setup values are configuration, not facts. Adopt one as
written, or adapt it to your own conventions.

## Skills

| Skill | Description |
|-------|-------------|
| [orient](orient/) | Orient in a repo at session start — instruction chain, tracker, specs, decision records, git/PR state, cross-checks, synthesis |
| [pebble](pebble/) | Work protocol for the Pebble (`pb`) local issue tracker — claim, track, and close issues while coding |
| [worktrees](worktrees/) | Git worktree discipline — primary checkout on main, feature work in linked worktrees, shared-tree state (ledgers etc.) committed only from main |
| [gh-app](gh-app/) | Post GitHub reviews, comments, and statuses as your GitHub App instead of the user's personal account |
| [drive-pi](drive-pi/) | Drive the pi coding agent CLI headlessly — print/JSON/RPC modes, commissioning not-me code reviews and scoped subagents |

The skills are independent but compose well: orient discovers which of
the others apply (pebble, worktrees), pebble records the work, and
worktrees decides where the work physically happens.

## Installation

Install a skill using whatever mechanism your agent harness provides.
The common pattern is a symlink from the harness's skills directory —
adjust both paths to your setup:

```bash
ln -s /path/to/gwl-agent-skills/<skill> <your-harness-skills-dir>/
```

Examples of skill directories:

- [opencode](https://opencode.ai): `~/.config/opencode/skills/`
- [pi](https://github.com/earendil-works/pi): `~/.pi/agent/skills/`

Some skills also ship scripts (wrappers, setup helpers) that expect to
be on `PATH` — see each skill's README for its setup notes.

## Structure

```
<skill>/
  SKILL.md          # Runtime protocol (loaded by the agent at runtime)
  README.md         # Design rationale, usage, and configuration
  scripts/          # Supporting scripts (if any)
```

`SKILL.md` is the protocol the agent executes; `README.md` is for
humans — why the skill exists, how to configure it, and what it
assumes. Authoring conventions (portability, harness-agnosticism) are
in [AGENTS.md](AGENTS.md).

## License

[MIT](LICENSE)

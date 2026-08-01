---
name: grite
description: Create, query, comment on, and close issues in grite, the canonical task tracker for the palimpsest and hearth repos. Use when filing bugs or design issues, checking work priorities, recording decisions on existing issues, or managing task state and dependencies.
---

# Grite

Grite is the canonical task system. Both the palimpsest and hearth repos have their **own** grite databases — `cd` to the correct repo before creating or querying issues.

## Common commands

```bash
# List issues (human-readable table — usually what you want)
grite issue list                      # all issues
grite issue list --state open
grite issue list --state closed

# Find an issue ID by keyword (IDs are short hashes like 871348d3)
grite issue list | grep -i "keyword"

# Create an issue
grite issue create --title "Short title" --body "Longer description" --label agent:todo --json

# Comment (records decisions, checkpoints, amendments)
grite issue comment <ID> --body "..." --json

# Close
grite issue close <ID> --json

# Sync
grite sync --pull --json
grite sync --push --json
```

## Dependencies

```bash
grite issue dep add <A> --target <B> --type depends_on   # B must finish before A
grite issue dep add <A> --target <B> --type blocks       # A must finish before B
grite issue dep list <ID>
grite issue dep topo --state open      # execution order for open tasks
```

## Gotchas (learned the hard way)

- **`--json` output is noisy.** It wraps results in an object that includes a `wal_head` blob and other metadata — piping it to `python -c "json.load(sys.stdin)"` and expecting a bare list will fail or return nothing. If you need to find an ID, use the plain table output and `grep`.
- **Long `--body` strings work fine.** Don't truncate decisions to keep the command short; the issue is the durable record.
- **Comment early, comment often.** Decisions made in conversation belong on the issue the same session — conversation context evaporates, the grite record persists. Amendments go in as new comments, not edits; the trail is the point.
- **Session-start routine** (in repos with grite): `grite sync --pull --json`, `grite issue list --state open`, `grite issue dep topo --state open`.

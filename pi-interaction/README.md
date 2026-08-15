# pi-interaction

**Skill for driving the [pi](https://github.com/earendil-works/pi) coding
agent CLI headlessly** — as a review colleague, a scoped-question
subagent, or a one-shot generator with full process observability.

## Why this exists

A fresh pi instance on a cheap strong model is a *not-me reviewer* — a
colleague with no stake in the work, no memory of writing it, and no
politeness about it. Commissioning one is the fastest known way to get
real findings on your own code for ~$0.50.

The skill encodes what we learned the hard way:

- `--mode json` (JSONL event stream) beats print mode for anything whose
  *process* matters — the stream survives a timeout kill, so even a dead
  review leaves its hunt readable.
- Reviewers die chasing dependency semantics. Fence the scope, hand them
  the answers you already paid for, and give them a delegation budget.
- Findings are claims to verify, and regression tests must be watched to
  fail before they're trusted.

## Install

Symlink into pi's skills directory:

```bash
ln -s /path/to/gwl-agent-skills/pi-interaction ~/.pi/agent/skills/
```

## Contents

- `SKILL.md` — the full protocol: mode selection, the review command
  shape, prompt invariants, the SDK-reading fence, result processing.

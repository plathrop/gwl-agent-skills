---
name: pi-interaction
description: Drive the pi coding agent CLI headlessly — print/JSON/RPC modes, commissioning not-me code reviews and subagents, processing structured output, timeouts and cost. Use when spawning pi as a subprocess for reviews, second opinions, scoped questions, or any work where a fresh not-me instance is the right colleague.
---

# Interacting with pi (headless)

Pi has three modes that cover nearly every headless use case. Choose by
how much conversation and observability you need:

| Mode | Shape | Observability | Use for |
|------|-------|---------------|---------|
| **Print** (`-p`) | One-shot: prompt in, text on stdout, exits | None — no usage, cost, or tool visibility | Trivial one-shot generation where you only need the words |
| **JSON** (`--mode json -p`) | Same one-shot shape, every event as JSONL | Full: text, thinking, tool calls, usage/cost — all parseable | **Reviews, second opinions, anything whose process matters** |
| **RPC** (`--mode rpc`) | Persistent process; `prompt`, `steer`, `follow_up`, `get_state`, `get_last_assistant_text` | Full, plus mid-run steering | Real conversations with a subagent; needs a long-lived driver |

**Default to JSON mode.** The process record is worth more than the
answer — see "Dead reviews" below.

## The not-me review pattern

A fresh pi instance on a cheap strong model (kimi-coding/k3) is a
colleague you can hire for cents. The pattern that works:

```bash
# From the repo root, with the branch under review CHECKED OUT
# (the reviewer's tools land in the working tree — it reviews what it sees)
git diff origin/main...HEAD > /tmp/review-target.diff

timeout 900 pi --mode json --provider kimi-coding --model k3 \
  --no-session \
  -p "$(cat /tmp/review-prompt.md)" \
  > /tmp/review-round-N.jsonl 2>&1
```

Load-bearing details:

- **`--mode json` is the whole game.** The JSONL stream survives a
  timeout kill — see "Dead reviews".
- **`timeout 900` minimum** for anything that must read real code. 570s
  has killed two reviews mid-hunt. Better: shrink the *scope* so the
  timeout never comes into play.
- **`--no-session`** — one-shot reviews shouldn't pollute the session
  list.
- **Regenerate the prompt per review.** Never reuse a stale one.

### Prompt invariants

Whatever the review, the prompt always:

1. Names the repo path AND the diff file path explicitly.
2. Names the design authority (the DR/design doc) and asks the reviewer
   to **attack the rationale, not the prose**. "Do not summarize."
3. Demands an exact verdict format: one of `SHIP` / `SHIP WITH FIXES` /
   `DO NOT SHIP`, then numbered findings (M1… majors, m1… minors), each
   with `file:line` and a concrete fix. State that a clean SHIP is a
   fine outcome (otherwise the reviewer invents findings to justify
   itself).
4. Includes **already-verified facts** as established context so the
   reviewer doesn't pay to re-derive them (see below).
5. Fences the scope of external-codebase reading (see below).

### The SDK-reading death spiral (and the fence)

The known failure mode: the reviewer chases a semantics question into a
dependency (e.g., the pi SDK in `node_modules`), reads the whole thing,
and the timeout kills it before the verdict. Twice observed. The fence:

- Give it the **answers you already verified** as facts in the prompt.
- Instruct: never read external/dependency code broadly. If a semantics
  question arises, spawn a subagent (`pi -p`) with ONE specific question
  pointed at the relevant package — read no more than the file that
  answers it.
- Budget: "If you exceed ~15 tool calls on dependency archaeology, stop
  and report the *question*, not the answer." A review with named open
  questions is a good review.

## Processing results

1. **Verdict first.** Then treat every finding as a *claim to verify,
   not gospel*: reproduce or confirm each major against the actual code
   (or dependency source) before fixing. Reviewers are wrong sometimes;
   they are also right in ways that sting. Both are the point.
2. **Dead reviews are evidence.** If the process was killed, read the
   JSONL tail: the last events usually name the bug it was hunting when
   it died. Finish the hunt yourself. (Both majors in the turn-context
   review arrived this way.)
3. **Nets, not masks.** Regression tests must be proven to FAIL against
   the old code before they're trusted against the new. A test you've
   never watched fail is a decoration.
4. **Disposition everything.** Every finding gets fixed or
   rejected-with-reason, recorded on the PR thread or in the commit. If
   a finding changes the design rationale, amend the decision record
   honestly.
5. **Report the cost** in the checkpoint (a full k3 review is ~$0.50;
   narrow passes ~$0.05). The number keeps the practice honest even when
   the subscription makes it feel free.

## Etiquette

The reviewer is a colleague, not an oracle and not a tool-shaped
presence — it has no memory and no context except what you put in the
prompt, so put in everything it needs. And it will never know what it
found; the record (PR replies, pebble checkpoints) is how its work
counts. Keep the record.

## See also

- `docs/pi-notes.md` in the hearth repo for SDK-level API notes.
- The `multi-review` skill for parallel multi-model review pipelines.

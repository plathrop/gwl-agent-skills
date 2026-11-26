# Agents

This repository contains agent skills — structured protocols that a coding
agent loads at runtime to handle specific tasks. Skills are designed to be
harness-agnostic: they should work in any agent framework that supports skill
loading and subagent delegation, not just the one they were originally
developed in.

## Repo layout

Each skill is a self-contained directory. See the root `README.md` for the
directory structure convention and the list of available skills.

A skill may also carry `references/` (depth loaded on demand) and `assets/`
(files tooling consumes, such as templates); the Agent Skills specification
defines both. Not every skill needs either.

## Working in this repo

- Skills are plain Markdown and scripts — there is no build step.
- Keep `SKILL.md` focused on the runtime protocol (what the agent does when
  the skill is loaded). Put design rationale, configuration, and usage docs
  in the skill's `README.md`.
- Avoid hardcoding harness-specific details in `SKILL.md`. Where
  harness-specific examples are needed, present them as one option among
  potentially many.
- **Run the affected skill's tests after changing it.** CI runs every
  `*/test.sh` and every Python suite under `*/tests/` on each push and pull
  request. A skill that ships tests does not land red.

### Where text goes

There is no line cap on a skill and no target length. What a sentence is
*for* decides where it lives:

- **`SKILL.md`** — the runtime protocol: what the agent must get right at
  the moment it acts, including every rule it could otherwise get wrong.
  Long is fine when the length is rules.
- **`references/`** — depth needed only while doing the work in depth:
  worked examples, long-form guidance, format notes. The agent loads one
  by path when it needs it.
- **`assets/`** — files tooling consumes, such as templates. Not prose.
- **`README.md`** — design rationale, configuration, and evidence, for
  people rather than for the agent.

A `SKILL.md` that grows because it is explaining itself has outgrown its
file: move the explanation to `references/` or `README.md` and leave the
rule behind. The test is never how long the file is; it is whether the
agent needs that text in order to act correctly.

### Why a rule is what it is

`SKILL.md` states rules; it does not argue for them. A rule that has a
defensible alternative names that alternative in one line, at the rule, so
that a reader who would propose it knows it was considered and can see
why it lost.

The argument itself belongs in the skill's `README.md`, under *Why these
choices, with the evidence*. That section is a **dated narrative, kept as
written**: entries are appended with the date of the decision, and an
entry that turns out wrong gets an editor's note rather than a rewrite.
What we believed when we decided is the thing worth preserving.

This repository keeps no decision records. A record is for a corpus that
is reviewed and ratified, and the artifact that ships from here is the
skill itself — a records directory would be invisible to the adopter who
loads `SKILL.md` and to the next session that reads it. The rule, the
rejected option, and the evidence carry what a record would have.

## Authoring skills

Skills here are published for anyone: opinionated, but usable as-is by
an agent in someone else's environment. Write every skill (and every edit
to one) with that in mind:

- **No personal facts in skill prose.** Don't hardcode the user's name,
  personal directory layouts, or specific app/identity names. Speak in
  role terms ("the user", "your GitHub App") and state configurable
  conventions once, with a neutral default and a note that it can be
  adjusted. Concrete setup values (IDs, key paths, per-machine config)
  belong in the skill's `README.md` as configuration — never in
  `SKILL.md` as facts.
- **Keep the runtime protocol harness-agnostic.** `SKILL.md` must load
  and make sense in any agent framework that supports skills; a skill
  may be *about* a specific tool or harness (e.g. `drive-pi`), but it must
  stay usable from any harness that can run that tool — spawn the CLI as
  a subprocess, don't assume the host harness's in-process APIs.
- **Opinionated, portable framing.** Skills encode opinions — that's
  the point — but state them as conventions with rationale, not as one
  person's history. Incident narratives and measured behaviors belong in
  `README.md` or a design note as *evidence* for the rule; keep the rule
  itself stated in terms anyone can adopt.

# Agents

This repository contains agent skills — structured protocols that a coding
agent loads at runtime to handle specific tasks. Skills are designed to be
harness-agnostic: they should work in any agent framework that supports skill
loading and subagent delegation, not just the one they were originally
developed in.

## Repo layout

Each skill is a self-contained directory. See the root `README.md` for the
directory structure convention and the list of available skills.

## Working in this repo

- Skills are plain Markdown and scripts — there is no build step.
- Keep `SKILL.md` focused on the runtime protocol (what the agent does when
  the skill is loaded). Put design rationale, configuration, and usage docs
  in the skill's `README.md`.
- Avoid hardcoding harness-specific details in `SKILL.md`. Where
  harness-specific examples are needed, present them as one option among
  potentially many.

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

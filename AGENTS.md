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

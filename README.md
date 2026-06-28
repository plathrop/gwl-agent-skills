# gwl-agent-skills

Custom agent skills for coding agents. Each skill lives in its own directory
with a `SKILL.md` (the orchestration protocol) and a `README.md` (design
rationale and usage docs).

## Skills

| Skill | Description |
|-------|-------------|
| [multi-review](multi-review/) | Parallel multi-model code review pipeline with conflict resolution and feedback triage |

## Installation

Install skills using whatever mechanism your agent harness provides. In
[opencode](https://opencode.ai), you can symlink them into your config
directory:

```bash
# Link a skill
ln -s /path/to/gwl-agent-skills/<skill> ~/.config/opencode/skills/

# If the skill includes subagents, link those too
for agent in /path/to/gwl-agent-skills/<skill>/agents/*; do
  ln -s "$agent" ~/.config/opencode/agents/"$(basename "$agent")"
done
```

See each skill's README for skill-specific setup instructions.

## Structure

```
<skill>/
  SKILL.md          # Orchestration protocol (loaded by the agent at runtime)
  README.md         # Design docs, usage, and configuration
  agents/           # Subagent definitions (if any)
  scripts/          # Supporting scripts (if any)
```

## License

[MIT](LICENSE)

# Multi-Review Skill

Multi-model code review pipeline designed for opencode. Three review
subagents run in parallel each backed by a different model with a
different review lens.

The skill should work in any harness which supports skills and
sub-agents. However it was written for opencode and hasn't been tested
with any other harness.

## Design

### Architecture

```
build agent (primary)
  │
  ├─ loads skill: multi-review
  │
  ├─ Task (parallel) ──┬── review-arch   (architecture lens)
  │                     ├── review-logic  (logic/edge-case lens)
  │                     └── review-sec    (security/prod-readiness lens)
  │
  ├─ collect & deduplicate findings
  ├─ triage: integrate / reject / flag conflict
  ├─ apply fixes
  ├─ report to user
  ├─ track reviewer performance ──▶ ~/Source/reviewer-performance/
  └─ push PR
```

### Components

| File                     | Role                                                        |
|--------------------------|-------------------------------------------------------------|
| `agents/review-arch.md`  | Subagent — architecture and design coherence lens           |
| `agents/review-logic.md` | Subagent — logic correctness and edge-case lens             |
| `agents/review-sec.md`   | Subagent — security and production-readiness lens           |
| `SKILL.md`               | Orchestration protocol — modes, triage rules, output format |

### Installation

Put the skill directory wherever your harness expects to find skills.
Copy or symlink the agent definitions from `agents/` into wherever your
harness defines subagents.

#### opencode

For easy setup:

```bash
mkdir -p ~/.config/opencode/skills
mkdir -p ~/.config/opencode/agents
ln -s /path/to/multi-review ~/.config/opencode/skills/
for agent in /path/to/multi-review/agents/*; do
  ln -s "$agent" ~/.config/opencode/agents/"$(basename "$agent")"
done
```

### Review lenses

Each reviewer shares much of the same review criteria (logic,
security, architecture, production readiness, etc.). The
differentiation is a one-paragraph "lens" preamble that nudges the
model toward a specific area. Agent names are tied to the lens, not
the model — models can be swapped without renaming anything.

| Agent          | Lens                                                                | Current model     |
|----------------|---------------------------------------------------------------------|-------------------|
| `review-arch`  | Structural reasoning, abstraction boundaries, design coherence      | DeepSeek V4 Flash |
| `review-logic` | Precise logic, edge cases, boundary conditions, boolean correctness | Qwen 3.6 Plus     |
| `review-sec`   | Security posture, operational readiness, failure modes              | GLM 5.2           |

### Modes

- **Full review** (default): all three reviewers in parallel. Use for
  any meaningful code change.
- **Quick review**: `review-logic` only. Use for low-risk changes
  (docs, config, minor refactors) or when explicitly requested.

### Own PR vs. external PR

The skill handles two contexts:

|                      | Own PR                                     | External PR                                                  |
|----------------------|--------------------------------------------|--------------------------------------------------------------|
| Detected by          | `gh pr view` author matches `gh api user`  | Author does not match                                        |
| Make code changes    | Yes — integrate fixes                      | No — read-only                                               |
| Triage findings      | Full triage — accept/reject/flag conflicts | Relevance triage — filter trivial/obvious/stylistic findings |
| Output               | Review summary, then push                  | Review summary for user to interpret into PR comments        |
| Performance tracking | Yes                                        | Yes (with `external: true`)                                  |

For external PRs the build agent checks out the branch, runs the
multi-review, performs a lightweight relevance triage (filtering
findings not worth posting), and presents a summary. The user reads
the report and writes their own PR comments based on the findings.

### Conflict resolution

| Conflict type            | Resolution                                              |
|--------------------------|---------------------------------------------------------|
| Reviewer vs. reviewer    | Flagged for user decision — no autonomous resolution    |
| Reviewer vs. build agent | Build agent decides, documents reasoning for user audit |

The reviewer-vs-reviewer policy is intentionally conservative. Once
there is enough data on reviewer accuracy, this may shift to
majority-vote or weighted-confidence resolution.

## Future work

### Tailored vs. identical prompts

The current lens differentiation is deliberately light (one paragraph
per reviewer). Future options based on data:
- **Increase specialization** if a model clearly excels in its lens
  area — give it more detailed criteria for that area and reduce
  coverage of areas other reviewers handle better.
- **Remove lenses entirely** if the differentiation doesn't produce
  measurably different findings — just run three identical reviews for
  redundancy.
- **Asymmetric review criteria** — e.g., only review-arch covers
  architecture, only review-sec covers security, all three review logic.
  This reduces token spend but risks blind spots.

### Conflict resolution policy

Currently reviewer-vs-reviewer conflicts are always escalated to the
user. Once there is confidence in reviewer reliability:
- **Majority vote**: if 2 of 3 agree, auto-resolve in their favor
- **Severity-weighted**: auto-resolve suggestions by majority, always
  escalate critical/warning conflicts
- **Confidence scoring**: if a model provides a confidence signal,
  weight its vote accordingly

### Cost optimization

- Skip reviewers whose lens isn't relevant to the change (e.g., skip
  the security reviewer for a pure docs change)
- Adaptive mode selection: auto-choose quick vs. full based on diff
  size, file types, and risk heuristics
- Cache-friendly prompt design to maximize cached-read token rates

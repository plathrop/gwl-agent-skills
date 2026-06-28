---
name: multi-review
description: Orchestrate parallel code reviews from multiple models before pushing a PR, with conflict resolution and feedback triage
---

## When to use this skill

Load this skill when you are about to push a pull request, or when the
user asks you to review an existing PR. It provides a multi-model
review pipeline that catches more issues before code reaches (or stays
on) GitHub.

## Review modes

### Full review (default)

Invoke **all three** review subagents in parallel:

- `review-arch` — architecture and design lens (currently DeepSeek V4 Flash)
- `review-logic` — logic correctness and edge-case lens (currently Qwen 3.6 Plus)
- `review-sec` — security and production-readiness lens (currently GLM 5.2)

### Quick review

Invoke only `review-logic` for a single-model review. Use this for
low-risk changes (docs, config, minor refactors) or when the user
explicitly asks for a quick review.

The user will tell you which mode to use. If they say "review" without
qualification before a PR, default to **full review**.

## Workflow

### 1. Prepare the diff

Before invoking reviewers, ensure:

- You are on the correct feature branch
- All intended changes are committed (reviewers are read-only)
- You have a clear summary of what changed and why

### 2. Invoke reviewers

Launch the review subagents via the Task tool. For full review, launch
all three in a **single message** so they run in parallel:

```
Task(review-arch):  "Review the changes on this branch. <diff summary>"
Task(review-logic): "Review the changes on this branch. <diff summary>"
Task(review-sec):   "Review the changes on this branch. <diff summary>"
```

Provide each reviewer with:
- A concise description of the change (what and why)
- The list of changed files or a diff reference
- Any context that would help them understand the intent

### 3. Collect and deduplicate findings

Once all reviews return, merge findings:

1. **Exact duplicates**: If two or more reviewers flag the same issue
   at the same location, keep one and note which reviewers agreed.
2. **Overlapping findings**: If reviewers flag the same area but with
   different angles (e.g., one says "race condition", another says
   "missing lock"), combine into a single finding that captures both
   perspectives.
3. **Unique findings**: Keep as-is, attributed to the originating
   reviewer.

### 4. Triage and resolve

For each finding, determine its disposition:

#### Agree — integrate the fix

If the finding is valid and actionable, fix it. No discussion needed.
This is the common case for clear bugs, missing error handling, and
security issues.

#### Context-tier findings

review-sec may flag findings with severity **context** — these are
genuine concerns in pre-existing or unchanged code that this PR did not
introduce. Do not integrate or reject these. Instead, collect them in a
separate "Context Notes" section of the report. They are informational:
the user may choose to file a follow-up ticket, note them for later, or
ignore them. They do not count as accepted or rejected for performance
tracking — track them separately if the field is available, otherwise
omit them from accepted/rejected counts.

#### Reviewer-vs-reviewer conflict

If reviewers **contradict each other** (e.g., one says "add a retry"
and another says "retries will mask the real issue"), do NOT resolve
this yourself. Flag it for the user:

```
CONFLICT — reviewers disagree:
  - review-arch: <position>
  - review-logic: <position>
  Your input needed.
```

Wait for user direction before proceeding.

#### Reviewer-vs-build-agent disagreement

If a reviewer flags something but you (the build agent) believe the
current code is correct, you may override the finding. You MUST:

1. Explain your reasoning clearly
2. Reference the specific code or design decision that justifies it
3. Include this in the final report so the user can audit your
   judgment

This applies to cases like: a reviewer suggests an alternative
approach that trades off differently than what was intentionally
chosen, or a reviewer flags something that is handled elsewhere in
the codebase.

### 5. Integrate fixes

Apply all accepted fixes. After making changes:

- Re-run any relevant tests or checks
- Commit the review-driven fixes as a separate commit or amend,
  per the user's preference

### 6. Report

Present a structured summary to the user before pushing:

```
## Multi-Review Summary

### Mode: full | quick

### Fixes Applied
- <file:line> — <what was fixed> (flagged by: review-arch, review-logic)
- <file:line> — <what was fixed> (flagged by: review-sec)

### Findings Rejected (build agent override)
- <file:line> — <finding summary>
  Reason: <why this was not integrated>
  Flagged by: <reviewer(s)>

### Conflicts (awaiting user input)
- <description of disagreement>
  - review-arch: <position>
  - review-logic: <position>

### Context Notes (pre-existing concerns, not introduced by this PR)
- <file:line> — <concern> (flagged by: review-sec)
  Suggested follow-up: <file a ticket / note for later / ignore>

### Reviewer Agreement
- All reviewers agreed: no significant issues  [if applicable]
- N findings from M reviewers, K integrated, J rejected, C context, L conflicts

### Overall Assessment
<one-sentence summary of code health>
```

If there are **no conflicts** and **no rejections**, the report can be
abbreviated — just list fixes applied and the overall assessment.

### 7. Push

Only push the PR after:
- All fixes are applied and committed
- The report has been shown to the user
- Any conflicts have been resolved by the user
- The user has acknowledged the report (explicit or implicit)

If there are existing review threads that the fixes address, note
which threads are resolved in the report so the user can respond to
them on GitHub.

## External PR workflow

When the user asks you to review a PR you did not author, follow this
workflow instead of the standard one above.

### Detecting external PRs

When given a PR to review, check authorship first:

```sh
gh pr view <number-or-url> --json author --jq '.author.login'
```

Compare this against the current user:

```sh
gh api user --jq '.login'
```

If the author matches, this is **our PR** — use the standard workflow
above. If the author does not match, this is an **external PR** — use
the workflow below.

### External PR steps

#### 1. Checkout the branch (read-only intent)

```sh
gh pr checkout <number-or-url>
```

Do **not** make any code changes to this branch. You are reviewing
someone else's work.

#### 2. Gather context

- Read the PR description: `gh pr view <number-or-url>`
- Get the diff: `gh pr diff <number-or-url>`
- Note the base branch so reviewers understand what changed

#### 3. Invoke reviewers

Same as the standard workflow — launch review subagents (full or
quick, per user's request or default to full) with the diff and PR
description as context.

#### 4. Collect and deduplicate findings

Same as the standard workflow — merge, deduplicate, and attribute
findings.

#### 5. Participatory triage

For external PRs, you are not just a filter — you are a **participant**
in the review. You have already read the diff and the PR description
in step 2, and you understand the code well enough to triage the
subagent findings. Use that understanding to also contribute your own
findings where the subagents missed something.

##### 5a. Relevance triage

Perform a **lightweight relevance triage** of the subagent findings.
The goal is to filter out findings that are not worth the PR author's
time — you are acting as a quality gate on the review itself.

For each finding, ask: **"Would I actually post this comment on the
PR?"** Drop a finding if it meets ANY of these criteria:

- **Purely stylistic** — formatting, naming preferences, or
  conventions that are subjective and not established in the repo
- **States the obvious** — restates what the diff already makes clear,
  or points out something any reader would notice
- **Trivially low-value** — e.g., "consider adding a comment here",
  "you could use a more descriptive variable name" — advice that
  wouldn't change the author's behavior or improve the code
  meaningfully
- **Out of scope** — suggests broader refactoring or improvements
  unrelated to the PR's intent

Do **not** drop findings that are:
- Bugs, logic errors, or edge cases (regardless of severity)
- Security or correctness issues
- Missing error handling that could cause real failures
- Substantive design concerns about the approach

Mark dropped findings as `filtered` (not `rejected` — this is a
relevance filter, not a correctness judgment). Findings that pass
the filter are `accepted`.

This triage should be fast — a single pass, not a deep deliberation.
When in doubt, keep the finding; the user can always decide not to
post it.

##### 5b. Build-agent findings

During triage, you will have formed your own understanding of the
code. If you identify issues the subagents missed, **add them as
build-agent findings.** These are your unique contribution — leverage
the context you have that the subagents don't:

- Cross-referencing the PR against design docs, tickets, or related
  PRs in the same work stream
- Broader codebase context (how this change interacts with callers,
  consumers, or data flows the subagents didn't explore)
- Contract or API mismatches between the PR description and the
  implementation
- Patterns you recognize from similar code elsewhere in the project

Do **not** re-flag issues the subagents already caught — your value
here is additive coverage, not redundancy. Attribute build-agent
findings as `(flagged by: build-agent)` in the report.

#### 6. Present the review summary

Show the user a review report. The build agent does **not** post
reviews — the user reads the report and writes their own PR comments
based on the findings.

```
## Multi-Review Summary (External PR)

### PR: <url>
### Author: <login>
### Mode: full | quick

### Findings for Review
- **critical** | <file:line> — <issue> (flagged by: review-arch, review-logic)
  Recommendation: <what to do>
- **warning** | <file:line> — <issue> (flagged by: review-sec)
  Recommendation: <what to do>
- **suggestion** | <file:line> — <issue> (flagged by: build-agent)
  Recommendation: <what to do>

### Findings Filtered (not worth posting)
- <file:line> — <finding summary> (flagged by: review-arch)
  Reason: purely stylistic / states the obvious / trivially low-value / out of scope
- <file:line> — <finding summary> (flagged by: review-sec)
  Reason: ...

### Context Notes (pre-existing concerns, not introduced by this PR)
- <file:line> — <concern> (flagged by: review-sec)
  Suggested follow-up: <file a ticket / note for later / ignore>

### Reviewer Agreement
- N findings from M reviewers + build-agent, K passed relevance triage, J filtered, C context
- Findings where multiple reviewers agreed: L
- Build-agent contributed: B additional findings

### Overall Assessment
<one-sentence summary>
```

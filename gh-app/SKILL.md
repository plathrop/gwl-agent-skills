---
name: gh-app
description: Post GitHub reviews, comments, and statuses as the gwl-agents GitHub App instead of the user's personal account. Use whenever an agent needs to write to GitHub — post a PR review (including a real "changes requested" verdict), comment on a PR or issue, or set a status — so the action is attributed to the app, not the user.
---

# Posting to GitHub as the gwl-agents app

Agents act on GitHub through the **`gwl-agents` GitHub App**, not the
user's personal account. The app has its own identity (`gwl-agents[bot]`),
so anything you post is unambiguously attributed to the agent, and you can
post real reviews with a verdict (approve / request changes / comment).

## The one rule

**Use `gh-app` for every write to GitHub — except creating the PR itself.**

- **Creating the PR**: use plain `gh` (Grey's personal credentials). Grey
  is the author of record for the work; the PR opens as @plathrop. Push
  the branch and `gh pr create` exactly as you normally would.
- **Everything after the PR exists** — reviews, PR/issue comments,
  statuses, labels — use `gh-app` so it's attributed to `gwl-agents[bot]`.
- **Editing or merging the PR itself** (title, body, ready-for-review,
  merge when Grey asks): also plain `gh` — the PR is Grey's.
- Reads are always fine with plain `gh` (see below).

`gh-app` *can* technically create PRs (it's the same `gh`), but don't —
GitHub won't let an identity review its own PR, so a bot-authored PR can
never receive a real review verdict from the agents that act on it.

`gh-app` is the same `gh` CLI, but authenticated as the app. Every
command you already know works unchanged.

## Posting a review

A review carries a verdict. Use the verdict that matches your findings:

```bash
# Request changes (the "real review" that was previously impossible)
gh-app pr review <pr> --request-changes --body "..."

# Approve
gh-app pr review <pr> --approve --body "..."

# Comment (no verdict)
gh-app pr review <pr> --comment --body "..."
```

`<pr>` is a PR number or URL. `gh-app` resolves the repo from the current
directory, exactly like `gh`.

The same thing via the API, when you need more control:

```bash
gh-app api repos/OWNER/REPO/pulls/<pr>/reviews \
  -f event=REQUEST_CHANGES -f body="..."
```

## Posting a comment

```bash
gh-app pr comment <pr> --body "..."
gh-app issue comment <n> --body "..."
```

## Marking the review as an agent review

Start every review body with the literal text `agent-review`, optionally
followed by ` by <model_id>` if you know your model ID (omit it if you
don't). The app identity already separates you from the user; this header
records *which* agent/model wrote it.

```
agent-review by gpt-5.2

<findings...>
```

## Reading (no attribution concern)

Reads don't create attribution confusion, so plain `gh` is fine:

```bash
gh pr view <pr>
gh pr diff <pr>
gh api repos/OWNER/REPO/pulls/<pr>
```

## Minting a raw token (rarely needed)

`gh-app` handles authentication for you. If you ever need the raw
installation token (e.g. for a tool that isn't `gh`):

```bash
GH_TOKEN="$(gh-app-token)" some-other-tool ...
```

`gh-app-token` prints a fresh installation access token, cached locally
for its ~1-hour lifetime.

## Scope

The app is installed on a fixed set of repositories. If `gh-app` reports
a 404/403 on a repo, the app is not installed there — ask the user before
trying anything else.

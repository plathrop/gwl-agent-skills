# gh-app

Post to GitHub as the `gwl-agents` GitHub App instead of the user's
personal account.

## Why

Coding agents used to post reviews and comments through the user's
personal `gh` credentials. That caused two problems:

1. **Attribution confusion** — an agent's review looked like the user
   wrote it, so readers couldn't tell who was speaking.
2. **No real reviews** — agents could only leave comments, never a proper
   "changes requested" verdict.

A GitHub App fixes both: it has its own identity (`gwl-agents[bot]`), and
with `pull_requests: write` it can post real reviews with a verdict.

## How it works

GitHub Apps authenticate in two steps:

1. Sign a short-lived JWT with the app's private key (RS256).
2. Exchange the JWT for an **installation access token** scoped to the
   repos the app is installed on.

`gh-app-token` does both and caches the token for its ~1-hour lifetime.
`gh-app` is a thin wrapper that sets `GH_TOKEN` to that token and runs
`gh` unchanged. `gh-app-token` requires Node.js 18+ (it uses the global
`fetch`).

```
gh-app pr review 123 --request-changes --body "..."   # as gwl-agents[bot]
```

## Setup

One-time, per machine:

1. Create the GitHub App (done — `gwl-agents`, app ID `4608186`).
2. Generate a private key in the app's settings and save it locally.
3. Install the app on the repos it should act on.
4. Write the local config:

```bash
mkdir -p ~/.config/gh-app
install -m 600 /path/to/downloaded-key.pem ~/.config/gh-app/private-key.pem
cat > ~/.config/gh-app/config.json <<EOF
{
  "app_id": 4608186,
  "installation_id": 154042224,
  "private_key": "$HOME/.config/gh-app/private-key.pem"
}
EOF
```

5. Put the scripts on `PATH`:

```bash
ln -s "$(pwd)/scripts/gh-app" ~/.local/bin/gh-app
ln -s "$(pwd)/scripts/gh-app-token" ~/.local/bin/gh-app-token
```

6. Verify:

```bash
# should list the repos the app is installed on
gh-app api /installation/repositories --jq '.repositories[].full_name'
```

(Note: `gh-app api user` does *not* work — installation tokens can't
access the `/user` endpoint, which requires a user token.)

## Configuration

`gh-app-token` reads, in order of precedence:

| Env var | Config key | Meaning |
|---------|-----------|---------|
| `GH_APP_ID` | `app_id` | The app's numeric ID |
| `GH_APP_INSTALLATION_ID` | `installation_id` | The installation to act as |
| `GH_APP_PRIVATE_KEY` | `private_key` | Path to the PEM, or the PEM text itself |
| `GH_APP_CONFIG_DIR` | — | Override config dir (default `~/.config/gh-app`) |
| `GH_APP_CACHE_DIR` | — | Override token cache dir (default `~/.cache/gh-app`) |
| `GH_APP_API_URL` | — | Override API base (default `https://api.github.com`) |

The private key and token cache are written with `0600` permissions and
must never be committed to a repository.

## Security notes

- The private key is the crown jewel: anyone with it can mint tokens for
  every repo the app is installed on. Keep it out of git and backups that
  aren't encrypted.
- Installation tokens expire after ~1 hour and are scoped to the app's
  installed repos and granted permissions — far less dangerous than a
  long-lived personal token.
- The app holds broad permissions (`contents`, `secrets`, `workflows`,
  `security_events`, ...) by design — future agent tasks will use them,
  not just reviews. Treat the private key accordingly.

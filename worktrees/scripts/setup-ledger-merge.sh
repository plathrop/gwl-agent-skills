#!/bin/sh
set -eu

# Install the pebble-ledger event-union merge driver for a repo, plus the
# worktree-convention directory. Idempotent; re-run per clone and after
# updating this script.
#
# An older version of this script also installed a pre-commit hook that
# rejected ledger commits off main. Pre-commit hooks are no longer part
# of the discipline; if one of ours is present, this script removes it.

if [ "$#" -gt 1 ]; then
  echo "usage: $0 [repo-path]" >&2
  exit 2
fi

repo=${1:-$PWD}

repo_root=$(git -C "$repo" rev-parse --show-toplevel 2>/dev/null) || {
  echo "error: $repo is not inside a git repository" >&2
  exit 1
}

command -v pb >/dev/null 2>&1 || {
  echo "error: pb not found in PATH; install Pebble first" >&2
  exit 1
}

desired_driver='pb merge %A %B -o %A'
desired_name='Pebble ledger event-union merge'
attribute_line='.pebble/issues.jsonl merge=pebble'
gitattributes="$repo_root/.gitattributes"

# Remove a ledger-guard pre-commit hook installed by an older version.
hooks_dir="$repo_root/.githooks"
old_hook="$hooks_dir/pre-commit"
if [ -f "$old_hook" ] && grep -q 'refusing to commit .pebble/issues.jsonl outside main' "$old_hook"; then
  rm -f "$old_hook"
  rmdir "$hooks_dir" 2>/dev/null || true
  if [ ! -e "$hooks_dir" ] && [ "$(git -C "$repo_root" config --get core.hooksPath || true)" = ".githooks" ]; then
    git -C "$repo_root" config --unset core.hooksPath
  fi
  echo "Removed obsolete .githooks/pre-commit ledger guard (pre-commit hooks are no longer part of this discipline)."
elif [ -f "$old_hook" ]; then
  echo "note: $old_hook exists and is not the old ledger guard; leaving it alone." >&2
fi

current_driver=$(git -C "$repo_root" config --get merge.pebble.driver || true)
if [ -n "$current_driver" ] && [ "$current_driver" != "$desired_driver" ]; then
  echo "error: merge.pebble.driver is already '$current_driver'; refusing to overwrite" >&2
  exit 1
fi

if [ -f "$gitattributes" ] && grep -Eq '^\.pebble/issues\.jsonl[[:space:]]+merge=' "$gitattributes"; then
  if ! grep -qxF "$attribute_line" "$gitattributes"; then
    echo "error: $gitattributes already sets a different merge driver for .pebble/issues.jsonl" >&2
    exit 1
  fi
fi

if [ ! -f "$gitattributes" ]; then
  cat > "$gitattributes" <<'EOF'
# Reconcile the pebble ledger by event union, not textual line merge.
# Requires: git config merge.pebble.driver "pb merge %A %B -o %A"
EOF
elif [ -s "$gitattributes" ] && [ -n "$(tail -c 1 "$gitattributes")" ]; then
  printf '\n' >> "$gitattributes"
fi

if ! grep -qxF "$attribute_line" "$gitattributes"; then
  printf '%s\n' "$attribute_line" >> "$gitattributes"
fi

git -C "$repo_root" config merge.pebble.name "$desired_name"
git -C "$repo_root" config merge.pebble.driver "$desired_driver"

common_dir=$(git -C "$repo_root" rev-parse --git-common-dir)
case "$common_dir" in
  /*) ;;
  *) common_dir="$repo_root/$common_dir" ;;
esac
primary_root=$(CDPATH= cd -- "$(dirname -- "$common_dir")" && pwd)
project=$(basename "$primary_root")
worktree_parent="${WORKTREES_ROOT:-$HOME/worktrees}/$project"
mkdir -p "$worktree_parent"

cat <<EOF
Installed pebble ledger merge backstop in $repo_root
- merge attribute: .gitattributes ($attribute_line)
- git config: merge.pebble.driver='$desired_driver'
- worktree convention dir: $worktree_parent
EOF

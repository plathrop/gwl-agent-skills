#!/bin/sh
set -eu

if [ "$#" -gt 1 ]; then
  echo "usage: $0 [repo-path]" >&2
  exit 2
fi

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo=${1:-$PWD}

repo_root=$(git -C "$repo" rev-parse --show-toplevel 2>/dev/null) || {
  echo "error: $repo is not inside a git repository" >&2
  exit 1
}

command -v pb >/dev/null 2>&1 || {
  echo "error: pb not found in PATH; install Pebble first" >&2
  exit 1
}

hook_source="$script_dir/pre-commit"
hook_target_dir="$repo_root/.githooks"
hook_target="$hook_target_dir/pre-commit"
desired_driver='pb merge %A %B -o %A'
desired_name='Pebble ledger event-union merge'
attribute_line='.pebble/issues.jsonl merge=pebble'
gitattributes="$repo_root/.gitattributes"

current_hooks_path=$(git -C "$repo_root" config --get core.hooksPath || true)
if [ -n "$current_hooks_path" ] && [ "$current_hooks_path" != ".githooks" ]; then
  echo "error: core.hooksPath is already '$current_hooks_path'; integrate .githooks/pre-commit manually" >&2
  exit 1
fi

current_driver=$(git -C "$repo_root" config --get merge.pebble.driver || true)
if [ -n "$current_driver" ] && [ "$current_driver" != "$desired_driver" ]; then
  echo "error: merge.pebble.driver is already '$current_driver'; refusing to overwrite" >&2
  exit 1
fi

if [ -f "$hook_target" ] && ! cmp -s "$hook_source" "$hook_target"; then
  echo "error: $hook_target already exists and differs; integrate the pebble guard manually" >&2
  exit 1
fi

if [ -f "$gitattributes" ] && grep -Eq '^\.pebble/issues\.jsonl[[:space:]]+merge=' "$gitattributes"; then
  if ! grep -qxF "$attribute_line" "$gitattributes"; then
    echo "error: $gitattributes already sets a different merge driver for .pebble/issues.jsonl" >&2
    exit 1
  fi
fi

mkdir -p "$hook_target_dir"
cp -f "$hook_source" "$hook_target"
chmod +x "$hook_target"

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

git -C "$repo_root" config core.hooksPath .githooks
git -C "$repo_root" config merge.pebble.name "$desired_name"
git -C "$repo_root" config merge.pebble.driver "$desired_driver"

common_dir=$(git -C "$repo_root" rev-parse --git-common-dir)
case "$common_dir" in
  /*) ;;
  *) common_dir="$repo_root/$common_dir" ;;
esac
primary_root=$(CDPATH= cd -- "$(dirname -- "$common_dir")" && pwd)
project=$(basename "$primary_root")
worktree_parent="$HOME/Source/worktrees/$project"
mkdir -p "$worktree_parent"

cat <<EOF
Installed pebble worktree backstops in $repo_root
- hook: .githooks/pre-commit
- merge attribute: .gitattributes ($attribute_line)
- git config: core.hooksPath=.githooks, merge.pebble.driver='$desired_driver'
- worktree convention dir: $worktree_parent
EOF

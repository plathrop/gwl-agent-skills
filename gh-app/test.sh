#!/usr/bin/env bash
# Regression tests for gh-app/scripts/gh-app: a failed token mint must be a
# hard stop, never a silent fallback to the caller's personal gh auth.
#
# Reproduces a real incident (2026-11-21): `export GH_TOKEN="$(gh-app-token)"`
# under `set -e` does NOT propagate the mint's failure (observed on bash 5.3),
# so the script continued with an empty GH_TOKEN and `gh` authenticated from
# the keyring as the user.
#
# Run: bash gh-app/test.sh
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
wrapper="$here/scripts/gh-app"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# fake gh-app-token + fake gh, both on PATH via $work/bin: the fake gh records
# that it was reached (with the token it was handed).
mkdir -p "$work/bin"
cat > "$work/bin/gh" <<'EOF'
#!/usr/bin/env bash
echo "gh ran with GH_TOKEN='${GH_TOKEN-<unset>}'" > "$SANDBOX/gh-called"
EOF
chmod +x "$work/bin/gh"

# a mint that fails the way gh-app-token does: error to stderr, exit 1, no token
cat > "$work/bin/gh-app-token" <<'EOF'
#!/usr/bin/env bash
echo "gh-app-token: missing configuration." >&2
exit 1
EOF
chmod +x "$work/bin/gh-app-token"

run_case() { # $1 = description
    rm -f "$work/gh-called"
    SANDBOX="$work" PATH="$work/bin:$PATH" GH_TOKEN= bash -c "unset GH_TOKEN; '$wrapper' pr view 1" >/dev/null 2>"$work/err"
}

# --- mint fails: wrapper must exit nonzero and must not run gh ---

status=0
run_case "mint fails" || status=$?
[ "$status" -ne 0 ] || { echo "FAIL: wrapper exited 0 after a failed token mint"; exit 1; }
[ ! -e "$work/gh-called" ] || { echo "FAIL: gh ran after a failed mint: $(cat "$work/gh-called")"; exit 1; }
[ "$(wc -l < "$work/err")" -gt 0 ] || echo "note: no diagnostics on stderr after failed mint"
echo "ok: failed mint -> nonzero exit, gh not invoked"

# --- mint succeeds but emits nothing: same hard stop ---

cat > "$work/bin/gh-app-token" <<'EOF'
#!/usr/bin/env bash
exit 0
EOF
chmod +x "$work/bin/gh-app-token"

status=0
SANDBOX="$work" PATH="$work/bin:$PATH" bash -c "unset GH_TOKEN; '$wrapper' pr view 1" >/dev/null 2>"$work/err" || status=$?
[ "$status" -ne 0 ] || { echo "FAIL: wrapper exited 0 on an empty token"; exit 1; }
[ ! -e "$work/gh-called" ] || { echo "FAIL: gh ran on an empty token"; exit 1; }
grep -q "produced no token" "$work/err" || { echo "FAIL: no 'produced no token' diagnostic in: $(cat "$work/err")"; exit 1; }
echo "ok: empty token -> nonzero exit with diagnostic, gh not invoked"

# --- mint succeeds: gh runs with the minted token exported ---

cat > "$work/bin/gh-app-token" <<'EOF'
#!/usr/bin/env bash
echo "gho_faketoken123"
EOF
chmod +x "$work/bin/gh-app-token"

SANDBOX="$work" PATH="$work/bin:$PATH" bash -c "unset GH_TOKEN; '$wrapper' pr view 1" >/dev/null 2>&1
[ -e "$work/gh-called" ] || { echo "FAIL: gh did not run on the happy path"; exit 1; }
grep -q "GH_TOKEN='gho_faketoken123'" "$work/gh-called" || { echo "FAIL: gh saw the wrong token: $(cat "$work/gh-called")"; exit 1; }
echo "ok: happy path -> gh invoked with GH_TOKEN exported"

echo "all gh-app tests passed"

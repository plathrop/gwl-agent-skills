#!/usr/bin/env bash
# The round trip through a real formatter: generate a corpus, format it with
# the repository's dprint config, and require drs.py check to pass.
#
# The unit tests can only assert the shapes a formatter produces; this is the
# only place the formatter and the tool are exercised against each other. It
# exists because an adoption record with seventeen legacy ids wraps its
# legacy_bodies list, and a dialect that only accepted one-line flow sequences
# turned that wrapping into seventy errors.
#
# Usage: bash decisions/tests/roundtrip.sh   (needs dprint, python3)
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill="$(dirname "$here")"
repo="$(dirname "$skill")"
drs="$skill/scripts/drs.py"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
records="$tmp/docs/decisions"
mkdir -p "$records"

# Seventeen legacy records: body predates the section format, dated filename,
# so each needs a legacy_bodies entry. Enough of them to wrap the list.
for n in $(seq -w 1 17); do
    cat >"$records/2026-09-$(printf '%02d' "$((10#$n))")-legacy-$n.md" <<EOF
---
id: "DR-00$n"
title: "Legacy decision $n"
summary: "A legacy decision kept for the round trip."
date: "2026-09-$(printf '%02d' "$((10#$n))")"
authors: ["A Human"]
reviewers: ["A Reviewer"]
status:
  state: "Accepted"
supersedes: []
---
# Legacy decision $n

## Context

## Decision

## Consequences

## Options considered

## References
EOF
done

ids=""
for n in $(seq -w 1 17); do
    ids="$ids\"DR-00$n\", "
done
ids="${ids%, }"

cat >"$records/0019-adoption.md" <<EOF
---
id: "DR-0019"
title: "Adoption"
summary: "This repository adopts the decision record format."
date: "2026-11-24"
authors: ["A Human"]
reviewers: ["A Reviewer"]
status:
  state: "Accepted"
supersedes: []
legacy_bodies: [$ids]
---
# DR-0019: Adoption

## Context

## Decision

## Consequences

## Alternatives Considered

### Do Nothing

## References
EOF

# A split supersession: DR-0005 is replaced by DR-0020 and DR-0021, so its
# `status.by` is a sequence inside the nested `status` mapping -- a shape only
# this fixture exercises, and one a YAML formatter is entitled to wrap.
python3 - "$records/2026-09-05-legacy-05.md" <<'REWRITE'
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
split = '  state: "Superseded"\n  by: ["DR-0020", "DR-0021"]\n  date: "2026-11-27"'
text = text.replace('  state: "Accepted"', split, 1)
path.write_text(text, encoding="utf-8")
REWRITE

for n in 20 21; do
    cat >"$records/00$n-split-part-$n.md" <<EOF
---
id: "DR-00$n"
title: "Split part $n"
summary: "One clause of the legacy decision, carried forward."
date: "2026-11-27"
authors: ["A Human"]
reviewers: ["A Reviewer"]
status:
  state: "Accepted"
supersedes: ["DR-0005"]
---
# Split part $n

## Context

## Decision

## Consequences

## Alternatives Considered

### Do Nothing

## References
EOF
done

python3 "$drs" --dir "$records" index >/dev/null
echo "roundtrip: baseline check"
python3 "$drs" --dir "$records" check

echo "roundtrip: formatting with the repository config"
dprint fmt --config "$repo/dprint.jsonc" "$records" >/dev/null

# The point of the exercise: the formatter really did wrap the list.
if ! grep -A2 '^legacy_bodies: \[$' "$records/0019-adoption.md" >/dev/null; then
    echo "roundtrip: FAIL: the formatter did not wrap legacy_bodies; the test proves nothing" >&2
    exit 1
fi

echo "roundtrip: check after formatting"
python3 "$drs" --dir "$records" check

# The split survives the formatter in whatever shape it chose: the check above
# proves the tool accepted it, and this proves the fixture still holds a split
# rather than a pair of unrelated decisions.
if ! grep -q 'DR-0020' "$records/2026-09-05-legacy-05.md"; then
    echo "roundtrip: FAIL: the split supersession did not survive formatting" >&2
    exit 1
fi

echo "roundtrip: ok"

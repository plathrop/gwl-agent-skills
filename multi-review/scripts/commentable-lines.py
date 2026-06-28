#!/usr/bin/env python3
"""Parse GitHub PR file patches and emit commentable line ranges.

Usage:
    gh api repos/{owner}/{repo}/pulls/{number}/files --paginate | \
        python3 commentable-lines.py [--json]

Reads the JSON array from gh api on stdin. For each changed file, parses
the unified diff patch headers to determine which right-side (addition)
lines are valid targets for GitHub PR review inline comments.

Default output (human-readable):
    src/app/handler.py  1-139
    src/app/client.py  1-138
    Dockerfile  1-4,6-10

JSON output (--json):
    {
      "src/app/handler.py": [[1, 139]],
      "src/app/client.py": [[1, 138]],
      "Dockerfile": [[1, 4], [6, 10]]
    }

Each range is inclusive: [start, end]. A comment on any line within a
range is valid for the `line` field of a GitHub PR review comment
(right side / additions).

For new files (@@ -0,0 +1,N @@), the range is simply [1, N], which
means diff line = source line.

For modified files with multiple hunks, each hunk produces a separate
range covering the right-side lines in that hunk.

Files without a patch (binary files, renames with no content change)
are omitted from the output.
"""

import json
import re
import sys

HUNK_RE = re.compile(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def parse_ranges(patch: str) -> list[list[int]]:
    """Extract commentable right-side line ranges from a unified diff patch."""
    ranges = []
    for m in HUNK_RE.finditer(patch):
        start = int(m.group(1))
        count = int(m.group(2)) if m.group(2) is not None else 1
        if count == 0:
            # Deletion-only hunk (file truncated to empty); no right-side lines.
            continue
        ranges.append([start, start + count - 1])
    return ranges


def format_ranges(ranges: list[list[int]]) -> str:
    """Format ranges as '1-139,145-200' for human-readable output."""
    parts = []
    for start, end in ranges:
        if start == end:
            parts.append(str(start))
        else:
            parts.append(f"{start}-{end}")
    return ",".join(parts)


def main():
    use_json = "--json" in sys.argv

    data = json.load(sys.stdin)
    result = {}

    for f in data:
        patch = f.get("patch")
        if not patch:
            continue
        filename = f["filename"]
        ranges = parse_ranges(patch)
        if ranges:
            result[filename] = ranges

    if use_json:
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        for filename, ranges in result.items():
            print(f"{filename}  {format_ranges(ranges)}")


if __name__ == "__main__":
    main()

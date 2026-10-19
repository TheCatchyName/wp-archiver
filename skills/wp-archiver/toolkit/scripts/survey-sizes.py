#!/usr/bin/env python
"""List the largest folders under a directory, so hundreds of MB hiding in "media" are seen before you copy or zip them.

    python scripts/survey-sizes.py archive/<host>/public_html/wp-content/uploads [depth=1] [top=25]

Python rather than `du`: on big trees on a bind-mounted drive `du` takes minutes (ENV-12). Read-only.
"""
import os
import sys
from pathlib import Path


def tree_size(p: Path) -> int:
    total = 0
    for root, _dirs, files in os.walk(p):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    base = Path(sys.argv[1])
    depth = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    top = int(sys.argv[3]) if len(sys.argv) > 3 else 25
    rows = []
    level = [base]
    for _ in range(depth):
        nxt = []
        for d in level:
            for e in sorted(d.iterdir()):
                if e.is_dir():
                    rows.append((tree_size(e), e))
                    nxt.append(e)
                else:
                    rows.append((e.stat().st_size, e))
        level = nxt
    print(f"{base}: {tree_size(base)/1048576:.1f} MB total")
    for size, p in sorted(rows, key=lambda r: -r[0])[:top]:
        print(f"{size/1048576:9.1f} MB  {p.relative_to(base)}")


if __name__ == "__main__":
    main()

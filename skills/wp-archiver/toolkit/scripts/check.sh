#!/usr/bin/env bash
# One-shot prune check: HTML snapshot + screenshots for the current state, diffed against a base.
#   bash scripts/check.sh <label> [base=baseline]
# Pass = visual diff 0.000% on every page (a page that flips between two layouts is a known-flaky page: re-shoot it warm, VIS-2), and the
# HTML diff is only the removed plugin's own assets. Warm the server first; visual.py warns on cut-off captures.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv/bin/python; [ -x "$PY" ] || PY=.venv/Scripts/python   # POSIX / Windows venv layout
LABEL="${1:?usage: check.sh <label> [base]}"; BASE="${2:-baseline}"
bash scripts/snapshot.sh "$LABEL" | tail -1
$PY scripts/visual.py shot "$LABEL" | grep -v '^ok' || true
echo "=== visual diff vs $BASE"
$PY scripts/visual.py diff "$BASE" "$LABEL" | grep -vE '^\s+0\.000%' || true
echo "=== HTML tag-line differences vs $BASE (all pages, unique, CSS bodies/tokens filtered)"
norm() { sed -E 's/></>\n</g; s/(data-token-time|data-token|nonce|data-nonce)="[^"]*"/\1=""/g; s/\?ver=[0-9a-zA-Z._-]+//g' "$1"; }
for f in ".data/snapshots/$BASE"/*.html; do
  n=$(basename "$f")
  diff <(norm "$f") <(norm ".data/snapshots/$LABEL/$n") | grep -E '^[<>] *<' || true
done | grep -vE 'field-hp|time_token' | cut -c1-200 | sort | uniq -c | sort -rn | head -40

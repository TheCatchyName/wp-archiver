#!/usr/bin/env bash
# Compare two snapshots page by page. Prints changed-line counts per page, then the diff of the
# first changed page so the nature of the change is visible at a glance.
#   bash scripts/diff-snapshots.sh baseline no-visitors
set -euo pipefail
cd "$(dirname "$0")/.."
A=".data/snapshots/${1:?usage: diff-snapshots.sh <a> <b>}"; B=".data/snapshots/${2:?}"
# Split minified HTML onto lines at tag boundaries so a diff is readable, drop volatile tokens.
norm() { sed -E 's/></>\n</g; s/(data-token-time|data-token|nonce|data-nonce)="[^"]*"/\1=""/g; s/\?ver=[0-9a-zA-Z._-]+//g' "$1"; }
changed=0; first=""
for f in "$A"/*.html; do
  n=$(basename "$f"); [ -f "$B/$n" ] || { echo "MISSING in $2: $n"; continue; }
  c=$(diff <(norm "$f") <(norm "$B/$n") | grep -cE '^[<>]' || true)
  printf "%5s changed lines  %s\n" "$c" "$n"
  if [ "$c" -gt 0 ]; then changed=$((changed+1)); [ -z "$first" ] && first="$n"; fi
done
echo "pages with differences: $changed"
[ -n "$first" ] && { echo "--- first diff ($first):"; diff <(norm "$A/$first") <(norm "$B/$first") | head -60; }
exit 0

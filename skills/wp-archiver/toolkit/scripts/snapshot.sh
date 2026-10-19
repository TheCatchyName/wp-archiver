#!/usr/bin/env bash
# Capture the rendered HTML of every published URL into .data/snapshots/<label>/ (gitignored).
#   bash scripts/snapshot.sh baseline        # before changing anything
#   bash scripts/snapshot.sh no-visitors     # after removing a plugin
#   bash scripts/diff-snapshots.sh baseline no-visitors
# This is the proof step for pruning: a plugin/asset is "unused" only if the diff is empty (or
# only noise: nonces, timestamps, the plugin's own markup).
set -euo pipefail
cd "$(dirname "$0")/.."
LABEL="${1:?usage: snapshot.sh <label>}"
OUT=".data/snapshots/$LABEL"
mkdir -p "$OUT"

docker compose --profile tools run --rm wpcli sh -c \
  'wp post list --post_type=page,post --post_status=publish --field=url' 2>/dev/null \
  | grep -E '^http' | sort -u > ".data/snapshots/$LABEL.urls"

fetch() {
  u="$1"; out="$2"
  n=$(echo "$u" | sed -E 's#^http://localhost(:[0-9]+)?/?##; s#/#_#g; s#_$##')
  [ -z "$n" ] && n=home
  curl -s -o "$out/$n.html" -w "%{http_code} %{time_total}s $n\n" "$u"
}
export -f fetch
xargs -P 4 -I{} bash -c 'fetch "{}" "'"$OUT"'"' < ".data/snapshots/$LABEL.urls"
echo "snapshot '$LABEL': $(ls "$OUT" | wc -l) pages in $OUT"

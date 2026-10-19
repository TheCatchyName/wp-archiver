#!/usr/bin/env bash
# Install a builder adapter's asset files into a site repo (idempotent). Run once BUILDER is known (phase 00/03):
#
#   bash <skill>/builders/apply.sh <builder> [site-repo=.]      e.g.  bash .../builders/apply.sh divi .
#
# Copies, from builders/<builder>/ into <site-repo>/scripts/:
#   export-extra-urls.txt      -> its lines are appended to scripts/export-extra-urls.txt (only lines not already there)
#   check-site-dir-only.txt    -> scripts/check-site-dir-only.txt (merged the same way)
#   *.php.example              -> scripts/ (example form/notice scripts; copy without .example and fill in)
# Everything else in the adapter folder is documentation (README.md) and stays in the skill. Without an adapter (plain
# theme, block editor) there is nothing to apply.
set -euo pipefail
BUILDER="${1:?usage: apply.sh <builder> [site-repo]}"
SITE="${2:-.}"
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$HERE/$BUILDER"
[ -d "$SRC" ] || { echo "no adapter '$BUILDER' in $HERE (see builders/README.md to write one)"; exit 1; }
[ -d "$SITE/scripts" ] || { echo "$SITE/scripts not found: run this from the site repo (or pass its path)"; exit 1; }

merge() {  # append the lines of $1 missing from $2
  touch "$2"
  added=0
  while IFS= read -r line || [ -n "$line" ]; do
    [ -z "$line" ] && continue
    grep -qxF -- "$line" "$2" || { printf '%s\n' "$line" >> "$2"; added=$((added + 1)); }
  done < "$1"
  echo "  $(basename "$1"): $added line(s) added to $2"
}

echo "applying builder adapter '$BUILDER' to $SITE"
[ -f "$SRC/export-extra-urls.txt" ] && merge "$SRC/export-extra-urls.txt" "$SITE/scripts/export-extra-urls.txt"
[ -f "$SRC/check-site-dir-only.txt" ] && merge "$SRC/check-site-dir-only.txt" "$SITE/scripts/check-site-dir-only.txt"
for f in "$SRC"/*.php.example; do
  [ -e "$f" ] || continue
  if [ -e "$SITE/scripts/$(basename "$f")" ]; then echo "  $(basename "$f"): already in scripts/"; else cp "$f" "$SITE/scripts/" && echo "  $(basename "$f"): copied to scripts/ (copy without .example, fill in the constants)"; fi
done
echo "done. Read $SRC/README.md: it lists what is automatic and what still needs a decision."

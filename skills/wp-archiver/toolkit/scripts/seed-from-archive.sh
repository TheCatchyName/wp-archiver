#!/usr/bin/env bash
# One-time (re-runnable) baseline seed from the raw hosting download. Run from the repo root in a POSIX shell
# (Git Bash on Windows) BEFORE the first `docker compose up`:
#
#   bash scripts/seed-from-archive.sh
#
# Expects archive/<host>/public_html/ (the files) and archive/<host>/<dump>.sql (the database). It reproduces the
# live site as closely as possible so the first render is a trustworthy baseline: ALL plugins and the active theme
# come along. Pruning happens afterwards, one proven step at a time (phase 05). Nothing is deleted from the archive.
# NOTE: needs the FULL download -- run it before trim-archive.py (ARC-4).
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; . ./.env; set +a
: "${ACTIVE_THEME:?set ACTIVE_THEME in .env}"

SRC="${ARCHIVE_SRC:-}"
if [ -z "$SRC" ]; then
  n=0
  for c in archive/*/; do [ -d "${c}public_html" ] && { SRC="${c%/}"; n=$((n + 1)); }; done
  [ "$n" -eq 1 ] || { echo "found $n archive/*/public_html folders; put the download in archive/<host>/ or set ARCHIVE_SRC"; exit 1; }
fi
WPC="$SRC/public_html/wp-content"
DEST=".data/html/wp-content"
SKIP=" ${UPLOADS_SKIP:-simply-static wp_encryption wpforms ai1wm-backups updraft backwpup siteground-optimizer-assets et_temp} "

DUMP="${DUMP_FILE:+$SRC/$DUMP_FILE}"
if [ -z "$DUMP" ]; then
  set -- "$SRC"/*.sql
  [ "$#" -eq 1 ] && [ -f "$1" ] || { echo "expected exactly one .sql in $SRC; set DUMP_FILE in .env"; exit 1; }
  DUMP="$1"
fi
echo "source: $SRC   dump: $(basename "$DUMP")"
mkdir -p "$DEST/plugins" "$DEST/themes" wp/uploads db

# 1. Database seed (gitignored until scrubbed: it holds user hashes and visitor data).
cp -n "$DUMP" db/seed.sql 2>/dev/null || true
[ -f db/seed.sql ] && echo "db/seed.sql ready"

# 2. Plugins: all of them, so the first render matches the live site. Host-specific and drop-in code
#    (object-cache.php, mu-plugins/, db-error.php) is deliberately NOT copied: it needs the old host's
#    Redis/services and would error locally (RST-4).
cp -a "$WPC"/plugins/. "$DEST/plugins/"

# 3. Theme: the active one (+ EXTRA_THEMES, e.g. a child theme's parent). The others are unused cruft.
[ -d "$WPC/themes/$ACTIVE_THEME" ] || { echo "theme '$ACTIVE_THEME' not found in $WPC/themes"; exit 1; }
cp -a "$WPC/themes/$ACTIVE_THEME" "$DEST/themes/"
for t in ${EXTRA_THEMES:-}; do cp -a "$WPC/themes/$t" "$DEST/themes/"; done   # a child theme's parent

# 4. Media library, minus regenerable caches / backup plugins' temp files (UPLOADS_SKIP). Survey folder sizes first
#    with `python scripts/survey-sizes.py $WPC/uploads` -- hundreds of MB hide in plugin folders (ARC-1).
for d in "$WPC"/uploads/*/; do
  n=$(basename "$d")
  case "$SKIP" in *" $n "*) echo "skip uploads/$n"; continue ;; esac
  cp -a "$d" wp/uploads/
done
# Loose files directly in uploads/ (rare) come too.
find "$WPC/uploads" -maxdepth 1 -type f -exec cp -a {} wp/uploads/ \;

echo "done. Next: docker compose up -d --build, then docker compose --profile tools run --rm wpcli sh setup.sh"

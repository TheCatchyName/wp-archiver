#!/usr/bin/env bash
# Rebuild site/ from the running local WordPress, end to end:
#   bash scripts/build-site.sh
#
#   1. export.py          crawl http://localhost -> site/ (root-relative URLs, WP cruft stripped)
#   2. pack-raw-images.py zip the untouched media library -> raw/ (BEFORE anything is optimised)
#   3. optimize_images.py WebP, max 1080px wide, <=200KB each (CSS backgrounds recompressed, never resized)
#   4. check-site.py      every local reference must resolve to a file
#
# Then prove it visually (serial capture; see phases/07-export.md):
#   python scripts/serve-site.py &            (python = the venv's: .venv/bin/python or .venv/Scripts/python)
#   SHOT_WORKERS=1 SITE_ORIGIN=http://localhost:9090 python scripts/visual.py shot static
#   python scripts/visual.py diff <wordpress-shot> static     # expect 0.000% (a flaky band can flicker)
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv/bin/python; [ -x "$PY" ] || PY=.venv/Scripts/python   # POSIX / Windows venv layout
$PY scripts/export.py
$PY scripts/pack-raw-images.py
$PY scripts/optimize_images.py
$PY scripts/check-site.py site

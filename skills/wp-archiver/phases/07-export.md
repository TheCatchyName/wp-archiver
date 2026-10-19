# Phase 07 — Static export (crawler) and proof

**Goal** `site/`: plain files, root-relative, no WordPress machinery, visually identical to the dynamic site. **Needs** phase 06 state running at `http://localhost`. **Produces** `site/`, `overlay/`, a filled `scripts/export-extra-urls.txt`. **Gotchas** EXP-1..10, VIS-4, ENV-1.

## Steps
1. **Fix content bugs in the DB, not in `site/`** (EXP-8): broken `href`s found in the crawl log → `wp search-replace` in `post_content` *and* builder data (`--dry-run` first), then flush the builder's CSS cache.
2. **Favicon** (EXP-9): `python scripts/make-favicon.py <logo-file>` → `overlay/` (colour-to-alpha on a white-background logo; `.ico` 16/32/48, 192 px, apple-touch). The logo is the header's `<img class="custom-logo">` under `wp/uploads/`.
3. `python scripts/export.py` — crawls `/`, the WP-CLI page list and `export-extra-urls.txt`; drops query strings; rewrites the origin to root-relative in all text files; strips generator/RSD/REST/oEmbed/shortlink/pingback/feed/XFN/emoji tags; makes canonical/OG absolute on `FINAL_URL`; writes `404.html`, `robots.txt` (`Allow: /`, EXP-7) and `_headers` (`X-Robots-Tag: noindex, nofollow`); copies `overlay/`. Add head cruft your theme/builder emits to `HEAD_STRIP`; add real dynamic URLs to `SKIP`.
4. **Find runtime-only assets:** `python scripts/serve-site.py` (background, port 9090) → browse or shoot → `sort -u .data/export/404.log` → add every missing path to `scripts/export-extra-urls.txt` → re-export → repeat until the log is empty (EXP-1). For Elementor start from `builders/elementor/export-extra-urls.txt`; other builders: [`../builders/README.md`](../builders/README.md).
5. **Prove parity serially:** `SHOT_WORKERS=1 SITE_ORIGIN=http://localhost:9090 python scripts/visual.py shot static`, then `python scripts/visual.py diff <wordpress-shot> static` → 0.000% (a known flaky band may flip; re-shoot). **Never parallel** (VIS-4). If one page looks wrong, check it in a real browser (several reloads) before changing anything.
6. **Integrity + hygiene:** `python scripts/check-site.py` (0 missing) and grep `site/` for `localhost`, `wp-json`, `xmlrpc`, `wp-login` and every old host (0 each). Review the third-party hosts it lists (EXP-10).

## Exit criteria
0.000% (or explained) on every page, 0 missing references, empty 404 log, no leftover local/old hosts.

## Decisions
Self-host third-party fonts/avatars or accept them (reference run: accepted). Keep or drop each remaining visible plugin feature.

## Reference run
232 files, 15.4 MB before image optimisation. Rejected: a one-click static-export plugin (4,026 files, 192.5 MB, `localhost` left in 29 files: EXP-6) and `wget` (query strings as filenames: EXP-2).

# Page-builder adapters

The toolkit is builder-neutral on purpose; everything that depends on how a page is built lives behind a **builder adapter** — a folder here plus the `BUILDER` value in `.env`. Plain themes and the block editor need no adapter beyond what the toolkit already does.

| Builder | Status | Adapter |
|---|---|---|
| Elementor 4.3 | proven on one site | [`elementor/`](elementor/README.md) |
| Divi 4 (4.20.2) | proven end to end and deployed on one small site; Divi 5 untested; slider/video interaction untested | [`divi/`](divi/README.md) |
| Beaver Builder, WPBakery, Bricks, Oxygen, … | not yet attempted | write one with [`_template.md`](_template.md) when you meet it, and contribute it back |

## What an adapter has to answer

Ask these in recon (phase 01), then settle them during phases 03–08. Each row names the toolkit seam it feeds.

| Question | Seam | Why it bites |
|---|---|---|
| Which assets does the page's JavaScript request at runtime that no HTML/CSS parser can see (lazy chunks, JS-built URLs)? | `scripts/export-extra-urls.txt`, found via the static server's 404 log | missing chunks leave sliders, tabs or stretched sections broken on the static copy (EXP-1) |
| Where are old hosts stored outside the database — generated CSS, font files, cached JSON? | `scripts/setup.sh` | `wp search-replace` only touches the DB (RST-6) |
| Does it store URLs JSON-escaped (`http:\/\/host`)? | `setup.sh`, `export.py`, `optimize_images.py` already handle both forms | a plain-only replace misses most of its data (RST-5) |
| What flushes its generated CSS/caches after a DB change? | `setup.sh`, `prune.sh`, phase 07 | stale generated CSS makes the baseline lie |
| Which options/meta are caches or logs (delete) and which are registries (keep)? | `scripts/scrub.sql` | deleting a registry silently changes the render (DB-2) |
| What head tags or inline scripts does it add that should not ship? | `HEAD_STRIP` in `scripts/export.py` | dead endpoints and trackers in the static HTML |
| Which widgets/shortcodes are dynamic (forms, search, maps with API keys, live feeds)? | phase 05 notice step, `archive-form-notice.php` | they render empty or print raw shortcodes once the plugin is gone (PRN-1) |
| How does it paint images — `<img>`, CSS backgrounds at natural size, data attributes? | `scripts/optimize_images.py` | downscaling a natural-size background changes the composition (IMG-1) |
| Is the builder or theme premium (licence-bound code)? | phase 10 `trim-archive.py` | the vendor zip cannot be re-downloaded without a licence (ARC-3): keep it or record that it is gone |

`bash builders/apply.sh <builder> <site-repo>` installs an adapter's asset files (`export-extra-urls.txt`, `check-site-dir-only.txt`, `*.php.example`) into a site repo, idempotently; the generic `scrub.sql` and `export.py` already carry the builder-specific entries marked `builder:`.

Write the answers down as an adapter (`builders/<name>/README.md`, plus any asset files), add its traps to `reference/gotchas.md` under the stable ID scheme, and set `BUILDER=<name>` in `.env`.

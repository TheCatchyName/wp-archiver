# Builder adapter: <name> (<status: untested | proven on N sites>)

Copy this file to `builders/<name>/README.md`. Fill in each section from what you actually observed — leave a section out rather than guessing. Mark anything unverified as such.

## Detect
How to recognise it in recon: `generator` meta, plugin/theme folder names, CSS class prefixes, shortcode or block names.

## Runtime assets (feeds `scripts/export-extra-urls.txt`)
Lazy-loaded chunks or JS-built URLs the crawler cannot see, and how you found them (the 404 log). Ship a reusable list as `builders/<name>/export-extra-urls.txt` if it is stable across versions (state the versions).

## Absolute URLs outside the database (feeds `scripts/setup.sh`)
Generated CSS, font files, cached JSON that embed the old host, and the exact rewrite.

## Caches and regeneration
The command (WP-CLI or admin) that rebuilds its generated CSS/JS after a DB change; where the generated files live.

## Scrub notes (feeds `scripts/scrub.sql`)
Options/meta/tables: which are caches or logs (safe to delete), which are registries (keep), with the evidence.

## Head cruft (feeds `HEAD_STRIP`)
Tags or inline scripts to strip from the exported HTML.

## Dynamic widgets
Forms, search, maps, feeds: what they render once the plugin is gone, and the replacement used.

## Images
How it draws images; anything the optimiser must treat specially.

## Licensing
Premium builder/theme/add-on code in the download that cannot be re-downloaded.

## Traps
New gotchas, added to `reference/gotchas.md` with the next free ID in the right area, and cited here.

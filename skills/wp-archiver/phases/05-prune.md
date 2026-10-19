# Phase 05 — Prune (prove it, never guess)

**Goal** remove every plugin/theme/asset the rendered site doesn't need, with evidence. **Needs** phase 04 baseline. **Produces** `docker/wordpress/plugins.lock`, a filled-in `scripts/prune.sh`, `scripts/archive-form-notice.php` (if a dead form exists). **Gotchas** PRN-1..6, VIS-2, VIS-4, DB-3.

## Steps
1. **Inventory** with `wp plugin list --fields=name,status,version --format=table`; grep the dump for block/shortcode usage (`wp:<namespace>`, `[shortcode`); note which plugins print markup on the page (view-source) and which are host/tracker/SEO/security/caching helpers.
2. **Dead dynamic features first** (PRN-1): if a form plugin must go, inspect the builder data of the pages that embed it (dump the widget tree with `wp eval-file`), then replace the form with a deliberate notice using `scripts/archive-form-notice.php.example` (copy, fill in IDs/wording, run), re-check, and only then remove the plugin. The notice wording is the owner's call.
3. **Batches** (PRN-6), each: `wp plugin deactivate a b c` → warm → `bash scripts/check.sh <label> <previous>`: (a) trackers / host helpers / SEO toggles / template importers → (b) block libraries with zero uses in content → (c) inactive plugins last. Read the HTML diff (should list only the removed plugins' own assets) and the pixel diff (0.000%). On a visible diff: reactivate one at a time, re-shoot only that page (`visual.py shot <label> <slug>`), **warm first** (PRN-4).
4. Then `wp plugin delete …`, `wp theme delete` (unused defaults), flush the builder's CSS cache; write survivors + versions to `plugins.lock`.
5. **Prove the restore** (once): wipe `.data/`, run phases 03–04 again from the raw download, diff HTML against the first baseline (only nonces/tokens differ), then run `bash scripts/prune.sh` and diff full-height screenshots against the restored baseline. ≈12 min; it also turns the prune into a script — write `prune.sh` from your batches before this step.

## Exit criteria
Every page 0.000% vs baseline except explained ones (the notice pages, jitter pages matching a known layout); `prune.sh` reproduces the result from a fresh restore.

## Notes
- Don't delete anything that changes content (data tables, a visible scroll-to-top button, a widget the owner likes) without the owner's say.
- Reference run: 19 plugins → 4 plus the theme; 14 of 17 pages 0.000%, one jitter page, two notice pages.

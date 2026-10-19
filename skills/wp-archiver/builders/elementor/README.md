# Builder adapter: Elementor (proven on one site: Elementor 4.3 + Header Footer Elementor)

Set `BUILDER=elementor` in `.env`. Elementor renders ordinary HTML + static CSS/JS, so it exports cleanly; it is only painful to *edit* as raw HTML.

## Detect
`<meta name="generator" content="Elementor x.y.z">`; `wp-content/plugins/elementor/` in asset URLs; `elementor-widget-*` classes; `_elementor_data` post meta.

## Runtime assets
Elementor lazy-loads webpack chunks at runtime: `wp-content/plugins/elementor/assets/js/chunks/*.min.js` (EXP-1). The reference run listed all 23 chunk files of Elementor 4.3 in [`export-extra-urls.txt`](export-extra-urls.txt) — append its lines to the site's `scripts/export-extra-urls.txt`. For another Elementor version regenerate the list from the plugin directory (`ls .data/html/wp-content/plugins/elementor/assets/js/chunks`) and confirm with the static server's 404 log.

## Absolute URLs outside the database
- Page data stores URLs JSON-escaped (`http:\/\/host`) in `_elementor_data`: `setup.sh` replaces both forms (RST-5).
- Self-hosted Google-font CSS (`uploads/elementor/google-fonts/css/*.css`) hard-codes absolute URLs to the old host *inside the files*; `setup.sh` `sed`s them. If skipped, a web font silently fails (RST-6).

## Caches and regeneration
`wp elementor flush-css` (setup.sh and prune.sh call it when Elementor is active). Cold renders shift layouts by a pixel or two, so warm every page before judging a diff (VIS-2).

## Scrub notes
- Delete: `_elementor_css`, `_elementor_element_cache`, `_elementor_controls_usage` post meta; `elementor_log`, `elementor_remote_info_library`, `elementor_controls_usage`, `_elementor_assets_data`, `_elementor_global_css`, `_elementor_element_cache_unique_id` options (all in the generic sections of `scrub.sql`).
- **Keep `_elementor_local_google_fonts`**: it is the registry of self-hosted fonts, not a cache (DB-2).
- The `e_events` table is plugin telemetry: `TRUNCATE` it only when you have confirmed it exists.

## Head cruft
Nothing Elementor-specific needed in `HEAD_STRIP`. `elementorFrontendConfig` carries a per-render token, so it shows up as noise in HTML diffs (EXP-4).

## Dynamic widgets
Form widgets (plugin widgets such as a form plugin's widget type, or a shortcode pasted into a text widget): see `scripts/archive-form-notice.php.example` (PRN-1). Inspect the Elementor tree before editing.

## Images
Sections often draw photos with `background-size: auto` (natural pixels). The optimiser recompresses CSS-background images but never resizes them (IMG-1); `<img>` elements are safe to downscale.

## Traps
EXP-1, EXP-4, RST-5, RST-6, DB-2, IMG-1 (tagged *Elementor* in `reference/gotchas.md`).

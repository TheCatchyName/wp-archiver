# Builder adapter: Divi 4 (proven end to end and deployed once: Divi **4.20.2**, WordPress 7.1.3, a 4-URL site). Divi 5 untested.

Set `BUILDER=divi` in `.env`. Written *during* the first Divi site; each line is tagged **observed** (seen and verified there) or **open** (not yet confirmed). Divi 5 and larger Divi sites are untested.

**Automatic now:** `builders/apply.sh divi <site-repo>` installs the files below; `export.py` rewrites protocol-relative URLs and crawls the 404 page's assets; `check-site.py` flags leaks and honours the directory list; `scrub.sql` deletes Divi's cache option and the Elegant Themes licence credentials (no-ops on other sites); `visual.py` captures at a visitor viewport. **Still a decision per site:** the contact-form wording, which `_et_*` meta to drop, anything the **open** items below cover.

Files here: [`check-site-dir-only.txt`](check-site-dir-only.txt) (copy to `scripts/`), [`divi-form-notice.php.example`](divi-form-notice.php.example) (copy to `scripts/`).

## Detect
- **Observed:** `wp-content/themes/Divi/` in asset URLs. Divi is a *theme*, not a plugin: `plugins/` can be empty and `active_plugins` empty. `et_pb_*` and `et-boc` classes; Theme Builder regions as `et_pb_section_N_tb_header` / `_tb_footer`; content stored as `[et_pb_*]` shortcodes. The generator meta names WordPress only: read the Divi version from `themes/Divi/style.css`.
- **Observed:** the theme directory name is capitalised (`Divi`): use it verbatim in `ACTIVE_THEME` (Linux is case-sensitive).

## Capture and layout
- **Observed (VIS-8):** hero and feature sections use viewport-unit heights, so a tall-window screenshot stretched a hero to ~9,000 px. The default `SHOT_MODE=cdp` is required.
- **Observed (VIS-9):** the footer social icons exist only at phone width; compare at 390 px too.

## Licensing and secrets
- **Observed (ARC-3):** the theme is premium (Elegant Themes), ~54 MB, not re-downloadable without a licence: it stays in the archive zip (the active theme is always on `trim-archive.py`'s keep-list). `mu-plugins/et-safe-mode` is Divi's support helper; it is not copied locally.
- **Observed (DB-4):** option `et_automatic_updates_options` holds the owner's **Elegant Themes username and API key**; `et_support_site_id` is a support-site token. Both are deleted by the scrub, and the raw dump/archive zip that still contains them is a secret. Consider rotating the API key if the raw dump ever left your control.

## Dynamic widgets
- **Observed:** the contact page uses Divi's contact-form module (`[et_pb_contact_form …]…[/et_pb_contact_form]`) that posts back to the page: dead on a static host. `divi-form-notice.php.example` replaces it with an owner-worded notice and clears Divi's per-post caches. Saved library layouts (`et_pb_layout`) may also contain a form: they are not rendered on pages and were left alone.

## Runtime assets (feeds `scripts/export-extra-urls.txt`)
- **Observed:** nothing extra was needed on a site with no sliders in use: the crawler followed the generated `wp-content/et-cache/<post-id>/*.css` links, and the static server's 404 log stayed empty. Divi's generated CSS/JS lives under `et-cache/` and is served as ordinary static files.
- **Observed (EXP-12):** the 404 page references its own `et-cache/notfound/*.css`; `export.py` now crawls what the 404 page references.
- **Observed:** the home page uses Divi sliders (`et_pb_slider`) and video-background sections (`et_pb_section_video_bg`); the static copy matched WordPress pixel-for-pixel at load, at desktop and phone width, with a clean 404 log. **Open:** slider autoplay/transitions and video playback were not exercised by interaction; confirm in a real browser.

## Absolute URLs outside the database
- **Observed (EXP-11):** Divi's inline CSS uses **protocol-relative** URLs (`url(//host/wp-content/themes/Divi/core/admin/fonts/modules/social/modules.woff)`): the exporter now rewrites them, and `check-site.py` flags leftovers as `LEAK`.
- **Observed:** Theme Builder header/footer are posts of type `et_header_layout` / `et_body_layout` / `et_footer_layout`; their hand-typed links (`/home`, `/contact`) were redirected by WordPress on the live site and 404 on a static host (EXP-13). Fix in the DB.
- **Observed:** the normal plain `search-replace` rewrote the old host in shortcodes (183 replacements in the first run); no JSON-escaped form was needed.

## Caches and regeneration
- **Observed:** replacing content via `wp_update_post` required deleting the page's cached Divi meta (`_et_builder_module_features_cache`, `_et_dynamic_cached_shortcodes`, `_et_dynamic_cached_attributes`, `et_enqueued_post_fonts`); the form-notice script does this and the page then rendered the new content. Divi regenerates `et-cache/` on render.
- **Open:** whether `et_enqueued_post_fonts` can be deleted site-wide in the scrub (it was kept: DB-2).

## Scrub notes (feeds `scripts/scrub.sql`)
- **Observed:** `bash scripts/inventory.sh` (run on the raw DB) surfaced all of the following, including the credential options, with values masked. Leftovers of plugins that were no longer installed (an SEO plugin, a visitor-analytics plugin, a hosting helper, ActionScheduler) remained as options, tables, user meta and taxonomy rows even with `active_plugins` empty: inventory by prefix and drop them (PRN-2). Hosting-helper options include service keys and a data token.
- **Observed:** `_et_builder_da_feature_cache` (option) is a Divi cache and safe to delete. **Kept**, because they may be settings or registries the render depends on (DB-2): options `et_divi`, `et_pb_*` (incl. per-form `et_pb_contact_form_*`), `et_google_api_settings`; post meta `_et_pb_*`, `_et_builder_*`, `_global_colors_info`. Parity held at 0.000% with them kept.
- **Open:** which `_et_*` post meta can be dropped without a visual change.

## Head cruft (feeds `HEAD_STRIP`)
- **Observed:** nothing Divi-specific needed stripping.

## Images
- **Observed (IMG-1, IMG-6):** hero sections draw large photos as CSS backgrounds; the optimiser kept them at natural size and recompressed (one needed q40 to approach the budget): look at the crop.

## Traps
VIS-8, VIS-9, EXP-11, EXP-12, EXP-13, IMG-6, ENV-14 (all found on this site).

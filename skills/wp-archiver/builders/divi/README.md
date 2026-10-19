# Builder adapter: Divi (IN PROGRESS: first trial, Divi 4.20.2 on WordPress 7.1.3)

Set `BUILDER=divi` in `.env`. Written *during* the first Divi site, so each line is tagged **observed** (seen on that site) or **open** (still to confirm). Update it as the run goes; promote **open** items when proven.

## Detect
- **Observed:** `wp-content/themes/Divi/` in asset URLs (Divi is a *theme*, not a plugin: `plugins/` can be empty); `et_pb_*` and `et-boc` classes; Theme Builder regions as `et_pb_section_N_tb_header` / `_tb_footer`; post content stored as `[et_pb_*]` shortcodes; the theme directory name is capitalised (`Divi`): use it verbatim in `ACTIVE_THEME` on case-sensitive filesystems.
- **Observed:** the generator meta names WordPress only; Divi does not announce its version there (read it from `style.css`).

## Capture and layout
- **Observed (VIS-8):** hero and feature sections are sized in viewport units, so the legacy tall-window screenshot stretched a hero to ~9,000 px. Use the default `SHOT_MODE=cdp`. Measured real heights at 1280×800 were a few hundred to ~7,000 px.
- **Observed:** `#page-container` carries `overflow: auto hidden` and `body` `overflow: hidden auto`, but the document still scrolls normally (`documentElement.scrollHeight` is the page height).

## Licensing
- **Observed:** the theme is premium (Elegant Themes) and ~54 MB. It cannot be re-downloaded without a licence (ARC-3), so it stays in the archive zip (the active theme is always on `trim-archive.py`'s keep-list). `mu-plugins/et-safe-mode` is Divi's support helper and is not needed locally.

## Dynamic widgets
- **Observed:** the contact page uses Divi's contact-form module (`et_pb_contact_form`, a maths captcha question) that posts to the page itself. It is dead on a static host: replace it with a deliberate notice or a `mailto:` (owner's decision). `archive-form-notice.php.example` is Elementor-shaped; for Divi edit the `[et_pb_contact_form …]` shortcode in `post_content` (and Theme Builder templates) instead of a widget tree.

## Runtime assets (feeds `scripts/export-extra-urls.txt`)
- **Open:** Divi writes generated CSS/JS under `wp-content/et-cache/<post-id>/…` and references it from the HTML; confirm the crawler follows those links and whether any chunk is requested only at runtime (check the static server's 404 log, phase 07).
- **Open:** video backgrounds (`et_pb_section_video_bg` appeared in the markup but no `.mp4` URL was found in the rendered home page): confirm whether any video asset is needed.

## Absolute URLs outside the database
- **Open:** check `et-cache` and any generated CSS for the old host after `setup.sh`; Divi's Theme Builder and layout data live in `post_content` / `postmeta` and were rewritten by the normal `search-replace` (183 replacements in the first run: plain; no JSON-escaped hits needed).

## Caches and regeneration
- **Open:** how to flush Divi's generated CSS (`et-cache`) after a DB change: deleting the folder, or Divi > Theme Options > Builder > Advanced > Static CSS File Generation. Until confirmed, warm every page before judging a diff (VIS-2).

## Scrub notes (feeds `scripts/scrub.sql`)
- **Observed:** a former SEO plugin (AIOSEO), a visitor-analytics plugin (MonsterInsights) and a hosting AI helper left tables and options behind even though no plugin was installed or active (`active_plugins` was empty): `*_aioseo_*`, `*_monsterinsights_cache`, `*_sg_ai_log_events`, `*_actionscheduler_*`. These go on the scrub's drop list.
- **Open:** Divi's own options (`et_divi`, `et_*`) and postmeta (`_et_pb_*`): which are caches and which are settings the render depends on (DB-2). Inventory by prefix before deleting any.

## Head cruft (feeds `HEAD_STRIP`)
- **Open:** nothing identified yet.

## Images
- **Open:** whether Divi draws images as CSS backgrounds at natural size (IMG-1): the optimiser keeps backgrounds at full size and only recompresses them.

## Traps
VIS-8 (found here). Add new ones to `reference/gotchas.md` and cite them.

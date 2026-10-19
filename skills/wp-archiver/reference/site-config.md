# Per-site configuration — what to fill in for each site

Almost every per-site value lives in one file, `.env` (see `.env.example`), read by `docker-compose.yml` and every script. Phases 01–03 give you the facts; this page says where to find each and which files still need hand edits.

## Collect these facts first (phases 01 recon + 02 capture give you all of them)

| Fact → `.env` key | How to find it |
|---|---|
| Hosts baked into content → `OLD_HOSTS` | recon HTML + `grep -oE 'https?://[^/"]+'` on the dump: temp domains, `www.` variants, the dead original domain (scheme-less, space-separated) |
| Final host → `FINAL_URL` | the owner |
| WordPress / PHP / MySQL versions → `WP_VERSION` `PHP_VERSION` `MYSQL_VERSION` | live `generator` meta or `wp-includes/version.php`; the dump header (`-- Server version`, `-- PHP Version`) |
| Table prefix → `TABLE_PREFIX` | `CREATE TABLE` in the dump, or `$table_prefix` in `wp-config.php` |
| Dump filename → `DUMP_FILE` (only if the archive has several `.sql`) | the capture folder |
| Active theme → `ACTIVE_THEME` | `wp option get stylesheet` (child theme: put the parent in `EXTRA_THEMES`) |
| Page builder → `BUILDER` | `generator` meta; `grep -o 'wp-content/(plugins|themes)/[^/"]+'` on the home page |
| Custom CSS post ID | `theme_mods_<theme>` → `custom_css_post_id` (feeds the scrub's custom-CSS cleanup) |
| Dynamic features | recon: forms, embeds, counters, comments, search |
| Logo for the favicon | header `<img class="custom-logo">` |
| Indexing stance | the owner (`noindex` is the default for an archive of a dead site) |

## Files that may still need a hand edit

| File | Edit |
|---|---|
| `.env` | everything above, plus generated local-only passwords |
| `scripts/export-extra-urls.txt` | runtime-only assets found in phase 07's 404 log (Elementor: start from the shipped chunk list) |
| `scripts/export.py` | `HEAD_STRIP` if the theme/builder adds head cruft; `SKIP` if the site has real dynamic URLs |
| `scripts/prune.sh` | write it from your proof batches (ships as a commented template) |
| `scripts/archive-form-notice.php` | copy from `.example`; **fully site-specific** (post IDs, widget types, wording) — only when a dead form needs a notice |
| `scripts/scrub.sql` | the PER-SITE sections (ship as commented examples): removed plugins' option families and tables, stray post types, stale custom-CSS posts |
| `scripts/trim-archive.py` | `HISTORICAL` and `EXTRA_KEEP` lists at the top |
| `scripts/visual.py` | nothing normally; `SHOT_HEIGHT`, `BROWSER` are env vars |
| `scripts/check-site.py` | `DIR_ONLY` (JS config base URLs that are directories, not files) if the builder needs more |
| `wrangler.jsonc` | `name`, `routes[0].pattern`, `compatibility_date` (today), `workers_dev` |
| `docker/wordpress/plugins.lock` | the real survivors (phase 05) |
| `CLAUDE.md`, `docs/STATUS.md` | the placeholders |

Reuse as-is: `docker/wordpress/*` (versions come from `.env`), `scripts/setup.sh`, `snapshot.sh`, `check.sh`, `diff-snapshots.sh`, `serve-site.py`, `pack-raw-images.py`, `optimize_images.py` (CLI flags for width/size), `make-favicon.py` (pass the logo path), `build-site.sh`, `.gitignore`, `.gitattributes`, `.editorconfig`.

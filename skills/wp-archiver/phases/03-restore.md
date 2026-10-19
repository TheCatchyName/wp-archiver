# Phase 03 — Restore locally (Docker, state next to the repo)

**Goal** the original site running at `http://localhost`, reachable by WP-CLI, with a local admin. **Needs** phase 02 download, phase 00 repo. **Produces** `.data/` (MySQL + WP tree), `wp/uploads/`, `db/seed.sql` (raw, still gitignored). **Gotchas** ENV-1, ENV-2, ENV-6, ENV-7, ENV-8, RST-3..7, RST-9.

## Steps
0. If not done in phase 00: `bash <skill>/builders/apply.sh <BUILDER> .` (see [`../builders/README.md`](../builders/README.md)).
1. **Fill `.env`** from what you learned in phases 01–02: `WP_VERSION`, `PHP_VERSION`, `MYSQL_VERSION`, `TABLE_PREFIX`, `OLD_HOSTS` (every host baked into content: temp domains, `www.` variants, the dead original), `ACTIVE_THEME`, `BUILDER`. Check old hosts with `grep -oE 'https?://[^/"\\ ]+' <dump> | sort | uniq -c | sort -rn | head -30`.
2. `bash scripts/seed-from-archive.sh` — copies the dump to `db/seed.sql`, **all** plugins + the active theme + dated media into `.data/html/wp-content` and `wp/uploads` (skipping caches, backup-plugin folders and old-host drop-ins). Survey `uploads/` first with `python scripts/survey-sizes.py archive/<host>/public_html/wp-content/uploads` and extend `UPLOADS_SKIP` in `.env` for anything big and regenerable (ARC-1). The baseline must reproduce the live site, so *all* plugins come along; pruning is phase 05.
3. `docker compose up -d --build` — MySQL (same major as the host) imports `db/seed.sql` on first start of an empty `.data/mysql` (≈40 s for a 29 MB dump); WordPress is pinned to the live WP/PHP versions on `127.0.0.1:80`; outbound HTTP blocked; revisions off.
4. `docker compose --profile tools run --rm wpcli sh setup.sh` — rewrites every old origin (plain and JSON-escaped), `home`/`siteurl`, `blog_public=0`, flushes the builder's CSS cache, fixes the old host inside Elementor's self-hosted font CSS (when present), creates the local admin from `.env`.
5. **Verify:** every published URL returns 200 (`curl -s -o /dev/null -w "%{http_code}" …`); the home page looks right (screenshot in a browser if you have one); no old-host strings in rendered HTML (`curl -s http://localhost/ | grep -c <old-host>` = 0); the admin login works (POST `wp-login.php` → 302 + cookie; `/wp-admin/` 200).

## Exit criteria
URLs 200, local admin logs in, no old host in output, `wp plugin list` shows the original plugin set.

## Notes
- The first request is slow (≈12 s cold, 4 s warm: ENV-8). A reboot can leave containers up without a published port (ENV-1).
- The raw seed contains PII and hashes: it stays gitignored until phase 06 replaces it.
- Reference run: 35 tables imported; ≈16,200 URL replacements in the first `setup.sh`; 17 published URLs.

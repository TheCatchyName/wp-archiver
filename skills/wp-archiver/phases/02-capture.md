# Phase 02 — Capture (the one phase that needs the owner)

**Goal** a complete download of the site while the hosting plan is alive. **Needs** hosting-panel access (the owner's). **Produces** `archive/<host>/` containing `public_html/` and one `.sql` dump. **Gotchas** RST-1, RST-2, RST-8, ENV-11. Everything in `archive/` is gitignored and secret.

## Steps (owner does the downloading; the agent writes down exactly what to click)
1. **Files:** download all of `public_html` (SFTP, or the host's file manager "download/zip") into `archive/<host>/public_html/`.
2. **Database:** phpMyAdmin → Export → SQL, all tables → `archive/<host>/<dbname>.sql`. This works even when the plan blocks "manual backups". Keep the file as the host produced it.
3. Note for `.env` (see [`../reference/site-config.md`](../reference/site-config.md)): WordPress version (`wp-includes/version.php`), PHP and MySQL versions (dump header), table prefix, active theme, dump collation (`utf8mb4_0900_ai_ci` ⇒ you need **MySQL**, not MariaDB: RST-3).
4. **Do not** run an export plugin on the old host and trust it (RST-2); do not delete anything from the download yet (ARC-4).
5. Extract any zip the host produced into its own new folder; if a move fails with "permission denied", something holds the folder open: close it (ENV-11).

## Optional: trim before you capture
Pruning unused plugins on the live site first makes the download smaller and cleaner. Rules: full backup first; take the **baseline before** removing anything; prune with the proof loop (phase 05) against the live URL. **Caveat:** `snapshot.sh` lists URLs with WP-CLI, so remote pruning needs it adapted to a sitemap/REST URL list (`visual.py` already targets any origin via `SITE_ORIGIN`). Until that exists, capture first and prune locally.

## Exit criteria
`archive/<host>/public_html/` and exactly one `.sql` exist (or `DUMP_FILE` is set in `.env`); the owner confirms nothing else was meant to be captured (other databases, cron-built files, mail).

## Human decisions
Who downloads; where a temp/clone host lives if the real one is gone; whether to try trim-before-capture.

# Phase 10 — Retire (trim the archive, store it, stop the old hosting)

**Goal** keep only what can't be regenerated, in one zip stored privately; shut the old host down. **Needs** the site built, scrubbed and **deployed** (the trim removes what `seed-from-archive.sh` needs: ARC-4). **Produces** `archive/<name>-<date>.zip`, `archive/historical/`. **Gotchas** ARC-1..5, DB-7.

## Steps
1. **Survey** the download: `python scripts/survey-sizes.py archive/<host>/public_html/wp-content 2` — hundreds of MB hide in plugin folders (ARC-1). Set `ARCHIVE_NAME` in `.env`; fill `HISTORICAL` (older snapshots: backup zips, earlier dumps, backup-plugin folders) and `EXTRA_KEEP` at the top of `scripts/trim-archive.py`.
2. **Dry run:** `python scripts/trim-archive.py` prints KEEP / MOVE / DELETE with sizes. **Show the DELETE list to the owner** — premium plugin code cannot be re-downloaded (ARC-3).
3. `--apply`: writes `MANIFEST.md` (WordPress version, every plugin/theme with version, items that look premium, what was deleted and why), moves old snapshots to `archive/historical/` (never deletes them, ARC-2), deletes the rest, zips with maximum deflate and tests the zip. Compare the zip's entry count with the tree, then delete the unzipped tree.
4. **Owner:** store the zip (and `historical/` if wanted) somewhere private — it contains `wp-config.php` (ARC-5) — then delete the local copies and `.data/backup/*.sql` (DB-7).
5. Stop the old hosting (owner). Update `docs/STATUS.md` and `docs/DECISIONS.md` with where the zip lives.

## Exit criteria
Zip verified and stored off the machine; local unscrubbed material deleted; hosting cancelled or scheduled.

## Reference run
1,170 MB → 87 MB → **44 MB zip** (1,325 files); 909 MB deleted (core, plugins, 19 themes, a 374 MB failed export, a 62 MB GeoIP database, an object-cache plugin, logs, host keys); 174 MB of history moved aside.

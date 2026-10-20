# Phase 06 — Scrub the database and make a committable seed

**Goal** a small, PII-free `db/seed.sql` that rebuilds the site. **Needs** phase 05 done (plugins gone). **Produces** a filled-in `scripts/scrub.sql`, a tracked `db/seed.sql`. **Gotchas** DB-1..7, ENV-5, ENV-10, RST-8.

## Steps
1. **Inventory:** `bash scripts/inventory.sh` (read-only; values of credential-looking options are masked, so the output is safe to read). Run it on the *unscrubbed* DB: it lists table sizes (stats expiry 0), `posts` by type/status, top `postmeta` keys, options **grouped by prefix**, credential-looking options, users, comments, `usermeta` keys, taxonomies. Decide per family: caches / logs / keys → delete; registries / settings → keep (DB-2).
2. **Fill in `scripts/scrub.sql`'s PER-SITE sections** (they ship as commented examples): removed plugins' option families and tables, stray post types, stale custom-CSS posts, default draft pages. Sections 1–5 and 6a (revisions, auto-drafts/trash, orphans, regenerable caches, comment PII, users with unusable hashes and placeholder emails, **local admin deleted**, transients) are generic and run as-is.
3. `bash scripts/scrub.sh --seed` — backup → scrub → `OPTIMIZE` → dump seed (flags in tool-index) → *then* boot WP and recreate the local admin (DB-1).
4. **Audit the seed** before committing ([`../reference/tool-index.md`](../reference/tool-index.md) §3 "Seed audit"): emails, IPv4s, password hashes, key/secret/token markers, `session_tokens`, removed plugins' names (DB-4). Real addresses become placeholders.
5. **Prove it:** warm + `visual.py` diff vs the baseline (attribute every difference: the owner's own edits, fixes, intended changes — DB-3); then wipe `.data/mysql`, `docker compose up -d`, `setup.sh`, re-shoot (DB-5).
6. Un-ignore and commit `db/seed.sql` (delete its line in `.gitignore`; `.gitattributes` marks it `-diff`); keep `WP_POST_REVISIONS=false`, `EMPTY_TRASH_DAYS=0` in compose (DB-6).

## Exit criteria
Seed audited clean; a DB rebuilt from the seed alone renders identically; unscrubbed backups in `.data/backup/` noted for deletion once the archive zip is stored (DB-7).

## Human decisions
Is the seed tracked? What happens to remaining approved comments (spam)? Real email addresses → placeholders.

## Reference run
44 → 2.6 MB DB; 29 MB dump → 1.1 MB seed; 35 → 13 tables; `posts` 760 → 202 rows (almost all revisions); options 531 → 203; comments 14 → 2.

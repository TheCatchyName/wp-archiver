# Phase 01 — Recon (read-only, from outside)

**Goal** decide whether the site is a candidate and collect the per-site facts. **Needs** the live (or temp) URL only. **Produces** a findings note (put it in `docs/STATUS.md` or `docs/RECON.md`). **Gotchas** RST-1, RST-2.

**Run the `wp-archiver-recon` skill** — it is the single source for these steps (checks, classification, exit criteria) and also works without Docker or a repo. Use its output to fill the "collect first" table in [`../reference/site-config.md`](../reference/site-config.md).

## Exit criteria
Candidate or not, decided with the owner; page/post/media counts, theme + builder, visible plugins, dynamic features, third-party hosts and old domains listed.

## Human decisions
Candidate or not · what to do with each dynamic feature · indexing stance (`noindex` is the default for an archive of a dead site).

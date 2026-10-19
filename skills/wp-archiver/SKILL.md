---
name: wp-archiver
description: Archive a WordPress site as a static site on Cloudflare — capture the old host's files + database, restore locally in Docker, prune and scrub with pixel-diff proof, crawl to static files, optimise images, hand the deploy to the owner. Use to archive, freeze, retire or migrate a WordPress site to static hosting, to export WordPress to static HTML, or to continue a run in a repo that has docker-compose.yml and scripts/export.py.
---

# wp-archiver

Turns a mostly-static WordPress site (no logins, shop or member areas) into plain files on Cloudflare Workers, with every step proven against a frozen baseline rather than assumed. The agent does the reversible local work; **the owner decides, deploys and pushes**.

Proven on one Elementor site (Windows + Docker Desktop + Git Bash). Other page builders and operating systems are untested: expect to extend [`builders/`](builders/README.md) and report what you learn.

## Hard rules

- **Owner-only actions:** `git push`, `wrangler deploy`, DNS changes, deleting anything from the raw download, cancelling the old host. Prepare, dry-run, report, then stop.
- **Secrets stay out of git and out of the transcript:** `.env`, everything under `archive/`, unscrubbed dumps. Never print `wp-config.php` or `docker compose config` output (ENV-5).
- **Proof over guesses:** "unused" means a pixel/HTML diff against the baseline says so. State what each check did **not** cover (VIS-1); report a mistake as a correction, not a quiet fix.
- **Falsify first:** when a diff blames a plugin, try to disprove it (toggle, re-shoot warm, look in a real browser) before editing (SES-7).
- **Only archive sites the user owns or is authorised to archive.**

## Start here

1. **New site or continuing?** If the working directory has `docs/STATUS.md`, read it and resume at its phase. Otherwise this is a new run: do phase 00.
2. **Skill directory** = the folder holding this file. The copyable stack is `toolkit/` beside it; in a site repo the same files sit at the repo root (`scripts/`, `docker-compose.yml`, …). `python` below means the site repo's venv interpreter (`.venv/bin/python` or `.venv/Scripts/python`).
3. **Load one phase file at a time**, run it to its exit criteria, record decisions in `docs/DECISIONS.md`, update `docs/STATUS.md`, then open the next. Reach gotchas by area prefix (`grep -n "^- \*\*VIS-" reference/gotchas.md`), not by reading the file.

## The phases

| # | Phase | Produces | Done when |
|---|---|---|---|
| 00 | [setup](phases/00-setup.md) — site repo + toolkit | bootstrapped repo, venv, `.env` | `docker compose config -q` passes |
| 01 | [recon](phases/01-recon.md) — read-only survey (also the standalone `wp-archiver-recon` skill) | candidate verdict + facts | verdict and fact sheet written |
| 02 | [capture](phases/02-capture.md) — owner downloads files + DB dump | `archive/<host>/` | both parts present |
| 03 | [restore](phases/03-restore.md) — Docker stack at `http://localhost` | running original site | all URLs 200, no old host in output |
| 04 | [baseline](phases/04-baseline.md) — freeze "correct", measure noise | HTML + full-height PNG sets | noise floor 0.000% |
| 05 | [prune](phases/05-prune.md) — remove unused plugins with proof | `plugins.lock`, `prune.sh` | all pages 0.000% vs baseline (or explained) |
| 06 | [scrub](phases/06-scrub.md) — small PII-free seed | tracked `db/seed.sql` | audited clean; rebuild from seed matches |
| 07 | [export](phases/07-export.md) — crawl to `site/` and prove parity | `site/`, `overlay/` | parity, 0 missing refs, empty 404 log |
| 08 | [images](phases/08-images.md) — raw mirror + WebP | `raw/`, lean `site/` | every raster within budget, parity holds |
| 09 | [publish](phases/09-publish.md) — Workers config; **owner deploys** | `wrangler.jsonc`, live site | owner confirms the live site |
| 10 | [retire](phases/10-retire.md) — trim + store the archive, stop the old host | `archive/*.zip` | zip verified and stored off-machine |

**Order.** As proven: 00 → 10 in sequence; 04–08 are one loop in practice (after any content or plugin change, re-run the cheapest check that covers it). Recommended next time: trim unused plugins on the live site *before* the final capture so the download is smaller — baseline first, full backup first; the toolkit's harness assumes a local site, so that needs `snapshot.sh` adapted to a sitemap/REST URL list (see phase 02).

## Reference (open on demand)

| When | Open |
|---|---|
| A symptom or a risky step — before it, or when it breaks | [`reference/gotchas.md`](reference/gotchas.md), grep by area prefix (ENV, RST, VIS, PRN, DB, EXP, IMG, PUB, ARC, SES) |
| Running a script, copying a recipe | [`reference/tool-index.md`](reference/tool-index.md) |
| Filling `.env` and per-site edits | [`reference/site-config.md`](reference/site-config.md) |
| Principles; when to stop and ask | [`reference/best-practices.md`](reference/best-practices.md) |
| The page builder is not plain content (Elementor, Divi, blocks…) | [`builders/README.md`](builders/README.md) |
| Whole-run evidence: what it took, mistakes made and how each was caught | [`reference/case-study.md`](reference/case-study.md) |

## Human decision points (stop and ask, never default)

Which dynamic features to drop or replace · what a dead form should say · indexing stance of the copy · whether third-party fonts/avatars stay · what to delete from the raw archive and whether history snapshots go · whether a scrubbed seed is tracked · where the raw media zip lives (LFS vs release asset) · `git push` · `wrangler deploy` and the DNS cutover · where the archive zip is stored.

# Best practices — WordPress → static archive

The principles that made the reference run work, each with the reason and where it lives. One line each; read this once, then use the
phase files. IDs in brackets point into [`gotchas.md`](gotchas.md).

## Process

1. **Capture first, while the host is alive.** Files + DB dump (phpMyAdmin works when manual backups are blocked). The raw download is the
   only copy once the plan ends. Keep it out of git. [RST-1, RST-8]
2. **Freeze "correct" before touching anything.** Baseline = rendered HTML + full-height screenshots of every published URL. Measure the
   noise floor (identical state twice → 0.000%) so a later difference means something. [VIS-1, VIS-2, VIS-7]
3. **Prove, never guess.** A plugin/asset is unused when removing it leaves the pixel diff at 0.000% and the HTML diff showing only its own
   assets. Change one batch, re-render **warm**, read the diff, bisect only on a real diff. [PRN-4, PRN-6]
4. **Attribute every difference.** Owner's own edits, a real fix, an intended change, or a defect of mine: say which, with a dated backup
   to show it. A baseline can itself be broken. [DB-3, VIS-6]
5. **Say what a check did not cover.** "0.000% on all pages" was true for the top 6000 px only. Cap/limit guards in tools (warn when a
   capture may be cut off) beat vigilance. [VIS-1, SES-1]
6. **Script everything that you did by hand twice** — and make each script idempotent and dry-run-first: `prune.sh`, `scrub.sh --seed`,
   `build-site.sh`, `trim-archive.py` (dry run by default). The scripts are the runbook. [SES-4]
7. **Prove restores, not just backups.** From-scratch restore (raw → local) then re-apply the prune; rebuild the DB from the tracked seed.
   A backup you have not restored is a hope. [DB-5, phase 05]

## Data and secrets

8. **Scrub in SQL, from an inventory.** List table sizes, posts by type, options grouped by prefix, users, comments *before* writing the
   delete list. Keep registries, delete caches/logs/keys. Dump the seed **before** WordPress boots again; audit it (emails, IPs, hashes, key
   markers) before committing. [DB-1, DB-2, DB-4]
9. **Git ships the artefact, not the source.** `site/` (byte-exact), a scrubbed seed, scripts, config, docs. Big raw media = one reproducible zip
   in LFS (or a Release asset). Hosting archives, `.env`, unscrubbed dumps never enter git. [PUB-5, IMG-2, IMG-5, RST-8]
10. **Trim an archive last, with a keep-list and a manifest.** Delete what is regenerable (core, plugins, themes by version) or junk; move
    history aside; record exact versions; zip; integrity-test. [ARC-1..5]

## Build and verify

11. **A crawler you control beats a plugin you don't.** 232 files vs 4,026 for a one-click export plugin. It drops query strings, rewrites hosts everywhere, strips cruft,
    and the static server's 404 log tells you what it missed. [EXP-1, EXP-2, EXP-6]
12. **Verify the static site the way production serves it** (clean URLs, 404 page, headers) and compare it pixel-for-pixel with the dynamic
    site, serially. Add an integrity check (every reference resolves). [VIS-4, EXP-5]
13. **Optimise last, and never blindly.** Raw mirror first; downscale `<img>`, only recompress CSS backgrounds; leave files alone when WebP is
    bigger; re-run parity. [IMG-1..4]
14. **Don't pay for what you can avoid:** block outbound HTTP from the local WP, disable revisions/trash, drop plugins before export. [DB-6, PRN-3]

## Working with Windows + Docker

15. **LF everywhere, ports outside Windows' reserved ranges, relative paths into containers, secrets out of the transcript.**
    [ENV-1, ENV-2, ENV-3, ENV-5]
16. **Falsify before fixing.** When a diff "looks like" plugin X or an emoji change, toggle it, re-shoot warm, and check in a real browser
    before editing (twice the cause was test-harness timing, not the site). [VIS-4, PRN-4, SES-7]

## Human decision points (stop and ask — never default)

Which dynamic features to drop or replace · what a dead form should say · indexing/SEO stance of the copy · whether third-party fonts and
avatars stay · what to delete from the raw archive (and whether history snapshots go) · whether a scrubbed seed is tracked · `git push` ·
`wrangler deploy` and the DNS/custom-domain cutover · where the archive zip is stored.

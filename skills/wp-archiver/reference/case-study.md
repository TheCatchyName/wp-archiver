# Reference run — evidence, not instructions

One complete run of this workflow, written up so you can judge what it costs and where it goes wrong. Site: a 17-URL Elementor content site (11 pages, 5 posts, ~570 media files) on shared hosting that was being cancelled; moved to Cloudflare Workers static assets. Agent-driven with the owner deciding. Environment: Windows 10, Docker Desktop, Git Bash. **One site, one builder, one OS** — treat the numbers as an example, not a promise.

## Numbers

| Measure | Value |
|---|---|
| Elapsed | 3 days, 26 commits, nothing pushed or deployed by the agent |
| Site shipped | 17 URLs, 232 files, 11.6 MB, 0 runtime plugins |
| Verification | pixel parity with the dynamic site re-checked after every phase on all 17 pages (differences only where intended or explained); 1,349 references resolve; 0 404s |
| Database | 44 MB → 2.6 MB; seed 29 MB → 1.1 MB; tables 35 → 13; `posts` rows 760 → 202 |
| Hosting download | 1,170 MB, 35,536 files → 44 MB trimmed zip |
| Images | 7.03 → 3.25 MB (−54%); originals preserved in one 34 MB reproducible zip |
| Toolkit at the end | ~20 scripts, 11 phase documents, 76 indexed gotchas |

## Mistakes the agent made, and how each was caught

| # | Mistake | Caught by | Now prevented by |
|---|---|---|---|
| 1 | Capture window 6000 px; claimed "0.000% on all pages" | a form region absent from a diff that must show it | VIS-1: 10000 px + cut-off guard; measure heights first |
| 2 | Deleted Elementor's font **registry** as if it were a cache | the pixel diff on one page | DB-2: group options by prefix, decide per family |
| 3 | Dumped the seed after booting WordPress | the seed audit (an account record, a fresh key) | DB-1: scrub → dump → boot, baked into `scrub.sh` |
| 4 | Python wrote CRLF into a shell script | container error | ENV-3: `.gitattributes`, `newline='\n'` |
| 5 | Chased "plugin X leaks CSS into tables" for a cold-render jitter | toggling + warm re-shoot + a real browser | VIS-2, PRN-4, SES-7 |
| 6 | Optimiser resized a CSS background | pixel diff on one page | IMG-1 |
| 7 | Blamed an emoji-regex change for parallel-Chrome flakiness | stable in a real browser; serial run 0.000% | VIS-4 |
| 8 | Python patches in shell heredocs mangled escapes (twice) | `ast.parse` / syntax error | ENV-4: edit tool or a script file |
| 9 | Printed secrets (host keys, compose-resolved passwords) | noticed immediately | ENV-5, SES-1 |
| 10 | Trusted stale `information_schema` stats | row counts that "didn't change" | ENV-10 |

Nearly all were caught by a **comparison against a measured reference** (pixel diff, seed audit, row counts): the harness paid for itself. The two that hurt most (1, 7) were *test-method* errors, not site defects.

## What worked
- Baseline + noise floor + pixel diff from day one; one command to judge any change.
- Idempotent, dry-run-first scripts (`prune.sh`, `scrub.sh --seed`, `trim-archive.py`, `optimize_images.py --dry-run`): the scripts became the runbook.
- Proving restores (from-scratch restore; rebuild from the seed) rather than assuming backups work.
- The owner staying in charge of every outward-facing and destructive decision; the agent proposing with a recommendation and doing the reversible work.
- Recording decisions and gotchas as they happened, then restructuring for retrieval at the end.

## What was left undone
1. Measure page heights *before* writing the harness (cheap; would have avoided the main correction) — now step 1 of phase 04.
2. Parametrise the remaining hard-coded values from `.env` — done in this repo's toolkit.
3. Adapt the harness to a **remote** baseline so unused plugins can be trimmed on the live host before capture — still open (phase 02).
4. Try the playbook on a second site with a different theme/builder — the Elementor-specific parts (chunk list, font CSS, scrub entries) are where it will need work; `builders/README.md` lists the seams.

## Standing instructions that helped
*"Slow me down if I'm missing anything"* (surfaced PII, secrets, LFS quotas, DNS pre-conditions) · *"leave the unsure ones and call me for a significant snag"* · a visible task plan per request, long jobs in the background with polling, small logical commits.

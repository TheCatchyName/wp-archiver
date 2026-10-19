# Phase 08 — Raw mirror and image optimisation

**Goal** a lean `site/` with every original byte preserved elsewhere. **Needs** phase 07 export. **Produces** `raw/images-raw.zip` (+ manifest; Git LFS or a release asset), optimised `site/`. **Gotchas** IMG-1..5, EXP-10.

## Steps
1. **Decide where the raw zip lives** (owner, IMG-5): Git LFS (`git lfs install --local`; `.gitattributes` already routes `raw/*.zip`) or a release asset (delete that line, add `raw/` to `.gitignore`).
2. **Pack the originals first:** `python scripts/pack-raw-images.py`, then `--verify`. It zips `wp/uploads/<year>/…` reproducibly — run twice and compare hashes; unchanged inputs must give the same zip (no new LFS object).
3. **Dry run** the optimiser: `python scripts/optimize_images.py --dry-run` — per-image before/after, kept files, over-budget files. Defaults: WebP, ≤1080 px wide (downscale, never crop), ≤200 KB; PNGs try lossless first; q82→q40, then 10% shrinks.
4. Run it for real, or simply `bash scripts/build-site.sh` (export → pack → optimise → check). It **recompresses but never resizes** images used as CSS backgrounds (IMG-1), leaves an image alone if WebP is bigger (IMG-3), and rewrites every reference (plain and JSON-escaped).
5. `python scripts/check-site.py` → 0 missing. Re-run the **serial** static parity check (phase 07 step 5) against the original-image WordPress shots; an unexpected diff on an image page usually means a natural-size background was resized (IMG-1). For hero photos eyeball the crop too (IMG-4).

## Exit criteria
Every raster ≤ budget (or reported), 0 missing references, parity 0.000% (flaky bands aside), raw zip verified.

## Decisions
Max width/size (defaults 1080 px / 200 KB); LFS vs release asset for the raw zip.

## Reference run
539 files, 35.4 MB raw → 34.3 MB zip; 99 images 7.03 → 3.25 MB (−54%), 18 CSS backgrounds kept at full size, largest result 188 KB; `site/` 232 files, 11.6 MB.

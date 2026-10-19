# Phase 04 — Baseline (freeze "correct" before touching anything)

**Goal** reference renders every later change is judged against, with a measured noise floor. **Needs** phase 03 running. **Produces** `.data/snapshots/baseline/` (HTML), `baseline-png/` (screenshots), `baseline.urls`. **Gotchas** VIS-1..8, ENV-13.

## Steps
1. **Check the capture is trustworthy before trusting a diff** (VIS-1, VIS-8). `visual.py` captures at a 1280×800 viewport and prints each page's real height (default `SHOT_MODE=cdp`; no window size to guess). Spot-check one tall page against `document.documentElement.scrollHeight` at 1280×800 in a real browser (not in an iframe: viewport units resolve against the iframe). Pages over 16,000 px are truncated with a warning. Only if CDP capture fails on your machine fall back to `SHOT_MODE=window` (legacy tall window: set `SHOT_HEIGHT` above the tallest page, and it is invalid on sites with viewport-unit sections).
2. **Warm** every page: `for u in $(cat .data/snapshots/<label>.urls); do curl -s -o /dev/null "$u"; done` (twice after any restart/flush). Cold renders jitter (VIS-2).
3. `bash scripts/snapshot.sh baseline` (rendered HTML; URL list from `wp post list`) and `python scripts/visual.py shot baseline` (full-page PNGs; ~3 s per page).
4. **Noise floor:** `python scripts/visual.py shot noise` then `python scripts/visual.py diff baseline noise` — must print 0.000% everywhere. If a page flips between layouts (a table or slider script racing the capture), keep a **second baseline** (`baseline_b`) and treat that page as passing if it matches either.
5. **Prove the harness can fail:** compare against a state with a known visible change (VIS-7) before trusting a green result.

## Exit criteria
Baseline HTML + PNG sets exist for every URL at full height (no truncation warnings); noise floor 0.000% (flaky pages identified and named); one capture's height cross-checked in a real browser.

## Notes
- Keep only `baseline`, the full-height PNG sets and the current reference; delete scratch renders (they reached 450 MB).
- The baseline can itself be wrong (a font that fails because the old host's certificate expired: RST-6/VIS-6) — later differences need explanations, not just verdicts.
- Reference run: 17 URLs; one page flipped between two layouts; the first window (6000 px) hid the bottom of three pages.

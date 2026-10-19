# Phase 04 — Baseline (freeze "correct" before touching anything)

**Goal** reference renders every later change is judged against, with a measured noise floor. **Needs** phase 03 running. **Produces** `.data/snapshots/baseline/` (HTML), `baseline-png/` (screenshots), `baseline.urls`. **Gotchas** VIS-1..7, ENV-13.

## Steps
1. **Measure the tallest page** so the capture window can't cut it off (VIS-1). With a browser tool: create hidden same-origin `<iframe>`s (width 1280) for each URL and read `contentDocument.documentElement.scrollHeight` ([`../reference/tool-index.md`](../reference/tool-index.md) §3). Without one: take a first shot and read `visual.py`'s "bottom rows not uniform" warning. Set `SHOT_HEIGHT` above the maximum (default 10000; Chrome caps at 16384).
2. **Warm** every page: `for u in $(cat .data/snapshots/<label>.urls); do curl -s -o /dev/null "$u"; done` (twice after any restart/flush). Cold renders jitter (VIS-2).
3. `bash scripts/snapshot.sh baseline` (rendered HTML; URL list from `wp post list`) and `python scripts/visual.py shot baseline` (full-page PNGs; ~2 min for 17 pages).
4. **Noise floor:** `python scripts/visual.py shot noise` then `python scripts/visual.py diff baseline noise` — must print 0.000% everywhere. If a page flips between layouts (a table or slider script racing the capture), keep a **second baseline** (`baseline_b`) and treat that page as passing if it matches either.
5. **Prove the harness can fail:** compare against a state with a known visible change (VIS-7) before trusting a green result.

## Exit criteria
Baseline HTML + PNG sets exist for every URL at full height; noise floor 0.000% (flaky pages identified and named); tallest page < window height.

## Notes
- Keep only `baseline`, the full-height PNG sets and the current reference; delete scratch renders (they reached 450 MB).
- The baseline can itself be wrong (a font that fails because the old host's certificate expired: RST-6/VIS-6) — later differences need explanations, not just verdicts.
- Reference run: 17 URLs; one page flipped between two layouts; the first window (6000 px) hid the bottom of three pages.

# Phase 09 — Publish (Cloudflare Workers static assets)

**Goal** `site/` live at the final host, noindex, with a real 404 page. **Needs** phase 08 `site/`. **Produces** `wrangler.jsonc`, committed `site/`. **Gotchas** PUB-1..7. **The owner runs `git push` and `wrangler deploy` — never do either unasked.**

## Steps (agent prepares, owner deploys)
1. **Verify option names against the current docs** (PUB-1) — fetch the pages listed in [`../reference/tool-index.md`](../reference/tool-index.md) §3 "Cloudflare" — then fill in `wrangler.jsonc`: assets-only Worker `name`, `compatibility_date` = today, `routes: [{pattern: "<host>", custom_domain: true}]`, `workers_dev: true|false`, `assets: {directory: "./site", html_handling: "auto-trailing-slash", not_found_handling: "404-page"}`. Limits: 20,000 files (free), 25 MiB each.
2. **Dry run** with any installed wrangler: `node <project>/node_modules/wrangler/bin/wrangler.js deploy --dry-run --outdir .data/export/wrangler-out` (PUB-3; a parse check only). Delete the `.wrangler/` scratch dir it creates (gitignored).
3. **Commit** in logical pieces: tooling → data (seed) → `raw/` (LFS pointer) → `site/` (byte-exact, PUB-5) → `wrangler.jsonc` → docs. `git lfs ls-files` shows the zip.
4. **Owner:** (a) delete any existing A/CNAME record for the hostname (PUB-2); (b) `git push` (uploads the LFS object); (c) `npx wrangler deploy` (dry run first).
5. **After deploy:** `curl -I https://<host>/` → `200` + `x-robots-tag: noindex, nofollow`; a bad URL returns the 404 page; click through the pages; the `*.workers.dev` URL works unless disabled (PUB-4). A favicon change takes a while to appear (PUB-6).

## Exit criteria
The live site looks like the local one; headers correct; the owner confirms.

## Human decisions
Indexing stance · `workers_dev` on or off · the custom domain and DNS cutover · who pushes and deploys (the owner).

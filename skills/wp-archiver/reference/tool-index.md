# Tool and invocation index

Everything you can run, by phase. Run from the site repo's root in a POSIX shell (Git Bash on Windows). `python` = the
repo venv's interpreter (`.venv/bin/python`, or `.venv/Scripts/python` on Windows). "Per-site" = configured in `.env` or edited
before reuse; the full list is [`site-config.md`](site-config.md). Gotcha IDs point into [`gotchas.md`](gotchas.md).

## 1. Scripts (all in `scripts/`)

| Phase | Script | Run | Reads → writes | Per-site? | Gotchas |
|---|---|---|---|---|---|
| setup | `requirements.txt` | `python -m venv .venv`, then `<venv python> -m pip install -r requirements.txt` | → `.venv/` (Pillow only) | no | ENV-3 |
| baseline | `_cdp.py` | (imported by `visual.py`) | minimal DevTools-protocol client: full-page screenshot at a normal viewport | no | VIS-8 |
| all | `_env.py` | (imported by the Python scripts) | `.env` → `ROOT`, `env()`, `require()` | no | — |
| capture/retire | `survey-sizes.py` | `python scripts/survey-sizes.py <dir> [depth] [top]` | largest folders under a directory | no | ARC-1, ENV-12 |
| restore | `seed-from-archive.sh` | `bash scripts/seed-from-archive.sh` | `archive/<host>/` → `db/seed.sql`, `.data/html/wp-content` (all plugins + active theme), `wp/uploads` | `.env`: `ACTIVE_THEME`, `UPLOADS_SKIP`, `DUMP_FILE` | RST-4, ARC-4 |
| restore | `setup.sh` | `docker compose --profile tools run --rm wpcli sh setup.sh` | rewrites old origins (plain + JSON-escaped), `home`/`siteurl`, `blog_public=0`, builder CSS flush, Elementor font-CSS hosts, local admin from `.env` | `.env`: `OLD_HOSTS` | RST-5, RST-6, ENV-2 |
| baseline | `snapshot.sh` | `bash scripts/snapshot.sh <label>` | live pages (URL list from `wp post list`) → `.data/snapshots/<label>/*.html`, `<label>.urls` | no | VIS-2 |
| baseline | `visual.py shot` | `python scripts/visual.py shot <label> [slug…]` | URL list → `.data/snapshots/<label>-png/*.png` (1280 wide, full real height; headless Chrome/Edge via `_cdp.py`) | env `SHOT_MODE` (`cdp` default / `window`), `SHOT_VIEWPORT_HEIGHT`, `SHOT_SETTLE`, `BROWSER`, `SHOT_WORKERS`, `SITE_ORIGIN`; window mode: `SHOT_HEIGHT`, `CAPTURE` | VIS-1,3,5, ENV-13 |
| baseline | `visual.py diff` | `python scripts/visual.py diff <a> <b>` | two PNG sets → per-page % + bbox, masks in `<b>-vs-<a>-diff/` | no | VIS-2, IMG-4 |
| baseline | `diff-snapshots.sh` | `bash scripts/diff-snapshots.sh <a> <b>` | two HTML snapshots → changed-line counts + first diff | no | EXP-4 |
| prune | `check.sh` | `bash scripts/check.sh <label> [base=baseline]` | snapshot + shots + both diffs + tag-line summary of removed assets | no | VIS-2, PRN-4 |
| prune | `archive-form-notice.php.example` | copy to `archive-form-notice.php`, then `docker compose --profile tools run --rm wpcli wp eval-file archive-form-notice.php` | builder data of the form pages → notice widget (idempotent) | **yes** (post IDs, wording, widget types) | PRN-1 |
| prune | `prune.sh` | `bash scripts/prune.sh` | applies the proven prune to a fresh restore | **yes** (ships as a template: write it from your batches) | PRN-2 |
| scrub | `scrub.sh` / `scrub.sql` | `bash scripts/scrub.sh [--seed]` | backup → `scrub.sql` → OPTIMIZE → (seed dump) → WP boot → local admin | **yes** (`scrub.sql` PER-SITE sections ship as commented examples) | DB-1..7, ENV-10 |
| export | `export.py` | `python scripts/export.py [--out DIR] [--origin URL]` | local WP → `site/` (+ `overlay/`) | `.env`: `FINAL_URL`; `HEAD_STRIP`, `SKIP` in the file | EXP-1..3,7,9 |
| export | `export-extra-urls.txt` | (read by `export.py`) | runtime-only asset paths | **yes** (Elementor: start from `builders/elementor/export-extra-urls.txt`) | EXP-1 |
| export | `serve-site.py` | `python scripts/serve-site.py [port=9090] [dir=site]` | serves `site/` like Cloudflare; 404s → `.data/export/404.log` | no | EXP-5, ENV-1 |
| export | `make-favicon.py` | `python scripts/make-favicon.py <logo>` | logo → `overlay/{favicon.ico,icon-192.png,apple-touch-icon.png}` | logo path | EXP-9 |
| images | `pack-raw-images.py` | `python scripts/pack-raw-images.py [--verify]` | `wp/uploads/<year>/…` → `raw/images-raw.zip` + manifest | no | IMG-2, IMG-5 |
| images | `optimize_images.py` | `… optimize_images.py [--dry-run] [--max-width 1080] [--max-kb 200]` | `site/` images → WebP, refs rewritten | defaults | IMG-1,3,4 |
| images | `check-site.py` | `… check-site.py [site]` | every local reference must resolve; lists third-party hosts | `DIR_ONLY` | EXP-10 |
| export+images | `build-site.sh` | `bash scripts/build-site.sh` | export → pack-raw → optimise → check | no | all above |
| retire | `trim-archive.py` | `python scripts/trim-archive.py` (dry run) then `--apply` | raw download → manifest, history aside, trimmed zip | `.env`: `ACTIVE_THEME`, `ARCHIVE_NAME`; `HISTORICAL`, `EXTRA_KEEP` in the file | ARC-1..5 |

Typical sequences:
- **Prune loop:** `docker … wp plugin deactivate X` → warm (`for u in $(cat .data/snapshots/baseline.urls); do curl -s -o /dev/null $u; done`)
  → `bash scripts/check.sh try-X <prev>` → read the diff.
- **Static proof:** `build-site.sh` → `serve-site.py` (background) → `SHOT_WORKERS=1 SITE_ORIGIN=http://localhost:9090 … visual.py shot static`
  → `visual.py diff <wordpress-shot> static` → `sort -u .data/export/404.log`.

## 2. Stack and config files

| File | Role |
|---|---|
| `docker-compose.yml` | `db` (MySQL `MYSQL_VERSION`, bind `.data/mysql`, seed from `db/`), `wordpress` (built from `docker/wordpress/`, `127.0.0.1:80`, config via `WORDPRESS_CONFIG_EXTRA`), `wpcli` (profile `tools`) |
| `docker/wordpress/Dockerfile`, `zz-local.ini` | WordPress image pinned to the live versions; opcache/realpath tuning |
| `docker/wordpress/plugins.lock` | the survivors + theme with versions (documentation; no installer yet) |
| `.env` / `.env.example` | **the one per-site config file**: source-site facts (versions, prefix, `OLD_HOSTS`, theme, `BUILDER`, `FINAL_URL`) + local-only DB passwords + `WP_ADMIN_*`; read by compose and every script |
| `.gitattributes`, `.editorconfig` | LF everywhere, `site/**` byte-exact, `raw/*.zip` → LFS, `db/seed.sql` `-diff` |
| `overlay/` | files that exist only in the static build (favicon set) |
| `wrangler.jsonc` | Cloudflare Workers static-assets deploy config |

## 3. Recipes (copy-paste)

**WP-CLI** (any command): `docker compose --profile tools run --rm wpcli wp <args>` — e.g. `plugin list --fields=name,status,version --format=table`,
`plugin deactivate a b`, `plugin delete a b`, `theme delete x`, `post list --post_type=page,post --post_status=publish --field=url`,
`search-replace OLD NEW --all-tables-with-prefix --skip-columns=guid --dry-run --report-changed-only`, `elementor flush-css`,
`eval-file x.php`, `option get <name>`, `user list --fields=ID,user_login,roles`.

**SQL** (read-only inventory): write a `.sql` file, then
`docker compose exec -T db sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" <db>' < file.sql`. Start with an inventory query file:
table sizes (`SET SESSION information_schema_stats_expiry=0`), `posts` by `post_type, post_status`, `postmeta` by key size, options grouped by
prefix (`SUBSTRING_INDEX(TRIM(LEADING '_' FROM option_name),'_',1)`), users, comments.

**Seed dump flags:** `mysqldump --single-transaction --no-tablespaces --skip-comments --skip-dump-date --skip-extended-insert
--default-character-set=utf8mb4` (one INSERT per row = reviewable, stable).

**Seed audit:** `grep -oE '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}' db/seed.sql | sort -u`; IPv4 regex; `grep -cE '\$P\$|\$wp\$|\$2y\$'`;
key markers (`BEGIN (EC|RSA|PUBLIC|PRIVATE)|api[_-]?key|secret|token|license`); `session_tokens`.

**Rebuild DB from the seed (proof):** `docker compose down; mv .data/mysql .data/mysql.old; docker compose up -d` (waits for import), then `setup.sh`.

**Real-browser checks (any browser tool you have):** open the page; run JavaScript in it for (a) computed styles of an element,
(b) page heights — create hidden same-origin `<iframe>`s at width 1280 and read `contentDocument.documentElement.scrollHeight`, (c) Elementor
state (`elementorFrontend`, overlay opacity) across repeated reloads; the network log for 404s; a screenshot for a look; reset any viewport emulation afterwards. Compare crops with Pillow into one side-by-side PNG and look at it.

**Windows diagnostics:** `netsh interface ipv4 show excludedportrange protocol=tcp`; PowerShell
`Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" | Where CommandLine -like '*--headless*'` (orphans); `git ls-files --eol`;
`git lfs ls-files`; `git check-attr -a <path>`.

**Cloudflare:** verify config options in the docs before writing them (fetch `developers.cloudflare.com/workers/static-assets/routing/advanced/html-handling/`,
`…/static-assets/headers/`, `…/workers/wrangler/configuration/`, `…/workers/platform/limits/`). Dry run:
`node <any project>/node_modules/wrangler/bin/wrangler.js deploy --dry-run --outdir .data/export/wrangler-out`; real deploy (owner only): `npx wrangler deploy`.
After deploy: `curl -I https://<host>/` shows `x-robots-tag: noindex`, a bad URL returns the 404 page.

## 4. Agent capabilities this workflow uses

| Capability | Used for |
|---|---|
| Shell (POSIX; Git Bash on Windows) | docker / wp-cli, the scripts, Python one-offs; background mode for jobs over ~2 min |
| Windows shell (PowerShell) | `netsh`, process inspection/kill, moves a POSIX shell can't do (ENV-11) |
| File read / write / edit tools | scripts and docs (preferred over Python patches inside shell heredocs: ENV-4) |
| Image reading | render a side-by-side crop PNG and look at it to judge a diff |
| Web fetch / search | current Cloudflare docs |
| A real-browser tool (optional) | page-height and JS-state checks, network 404s, screenshots (§3) |
| A visible task plan | one plan per request, updated as steps finish |

# Gotchas — indexed by area

Every trap hit on the reference run (and how it was found), keyed by ID so phase files can cite them without repeating.
**Fetch only your area:** `grep -n "^- \*\*VIS-" gotchas.md`. Format: **ID** [phase] symptom → cause → fix.
Phases: setup, recon, capture, restore, baseline, prune, scrub, export, images, publish, retire. Newest additions go at the end
of their area; never renumber (other files cite the IDs). Entries tagged *Elementor* are page-builder specific; the same slot
for another builder lives in [`../builders/README.md`](../builders/README.md). Windows/Docker entries (ENV) apply to that stack only.

| Prefix | Area | Used in phases |
|---|---|---|
| ENV | Windows / Docker / shell / git environment | all |
| RST | capture and local restore | capture, restore |
| VIS | baseline and the visual-diff harness | baseline, prune, export, images |
| PRN | pruning plugins | prune |
| DB | database scrub and seed | scrub |
| EXP | static export | export |
| IMG | images and the raw mirror | images |
| PUB | git, Cloudflare, deploy | publish |
| ARC | archive trim and retirement | retire |
| SES | habits for an AI-agent session driving this | all |

## ENV — environment

- **ENV-1** [restore] *Connection refused after a reboot; container "Up" but `Ports` shows `8080/tcp` with no mapping.* Windows
  reserves dynamic TCP ranges after reboots (here 8036–8535, Hyper-V/WinNAT); Docker then fails to bind ("forbidden by its access
  permissions") but the `restart: unless-stopped` containers still start unpublished. Check `netsh interface ipv4 show
  excludedportrange protocol=tcp`, avoid the 8000–8600 range; this stack uses **port 80** (`http://localhost`). Recreate the
  container to re-publish: `docker compose up -d --force-recreate wordpress`.
- **ENV-2** [all] *`sh: can't open 'C:/Program Files/Git/scripts/setup.sh'`.* Git Bash rewrites arguments starting with `/` before
  passing them to `docker`. Run scripts from the compose `working_dir` with a relative path (`sh setup.sh`, `wp eval-file x.php`);
  or `MSYS_NO_PATHCONV=1`.
- **ENV-3** [all] *`set: illegal option -` inside a `sh` script.* Python's text-mode write on Windows produced CRLF. LF everywhere:
  `.gitattributes` (`* text=auto eol=lf`) + `.editorconfig`, `core.autocrlf=false`, write files with `newline='\n'`. Check `git
  ls-files --eol` (want `i/lf w/lf`). Fix a bad working copy by deleting it and `git checkout`-ing it, not dos2unix/sed.
- **ENV-4** [all] *SyntaxError after a Python patch run from a Bash heredoc.* Escapes like `"\\n"` or `"\/"` in patch code arrive as a
  literal newline / invalid escape (broke `export.py` and `CLAUDE.md` once each). Use the Edit tool for small changes, or write the
  patch script to a file with the Write tool and run it; always `ast.parse` / `sh -n` afterwards.
- **ENV-5** [all] *Secrets in the transcript.* `docker compose config` prints resolved env including DB passwords; `cat`-ing a
  host config file printed vendor licence keys. Never paste either; redact when inspecting config.
- **ENV-6** [restore] *WP-CLI: "YIKES, running as root", or "Error establishing a database connection ... host mysql".* The `wpcli`
  service needs `user: "33:33"` (www-data of the apache image), `HOME=/tmp`, the *same* `WORDPRESS_DB_*` env as the web container
  (shared via a YAML anchor — `wp-config.php` reads them from the environment), and `working_dir: /scripts`. `allow-root` in
  `wp-cli.yml` is ignored; `path: /var/www/html` in it works.
- **ENV-7** [restore] *Edited `WORDPRESS_CONFIG_EXTRA` but nothing changed / grep finds nothing in wp-config.php.* The generated
  `wp-config.php` `eval()`s that env var at runtime; recreate the container, don't regenerate the file.
- **ENV-8** [restore] *3–4 s per uncached page, 12 s cold.* PHP on a Windows bind mount is file-I/O bound (`wp-login.php` alone 3 s).
  Opcache + realpath cache (`docker/wordpress/zz-local.ini`) took 9 s → 4 s; blocking outbound HTTP changed nothing. Remaining lever:
  a named volume for `.data/html` (not done).
- **ENV-9** [setup] *C: at 90%.* Docker Desktop's disk image lives on C:; keep every stateful thing as a bind mount on the big drive.
- **ENV-10** [scrub] *Table sizes unchanged after a big delete.* MySQL 8 caches `information_schema` stats for 24 h: use
  `SET SESSION information_schema_stats_expiry=0`. The `mysql:8.4` image has no `mysqlcheck`; use `OPTIMIZE TABLE`.
- **ENV-11** [capture] *`mv: Permission denied` on a downloaded folder.* Some process (editor, terminal, indexer) holds it; close
  it or move it by hand. Don't fight it.
- **ENV-12** [all] *`du` / recursive `find` take minutes on a big tree on a bind-mounted drive, or a shell wrapper rejects compound
  `find` predicates.* Use Python `os.walk` for sizes (`scripts/survey-sizes.py`) and simple `find` forms.
- **ENV-13** [baseline] *Orphaned headless Chrome after a timeout.* Kill only processes whose command line has `--headless` and a temp
  profile (PowerShell `Get-CimInstance Win32_Process`); never touch the user's own Chrome. `visual.py` now kills its own tree.
- **ENV-14** [scrub/any] *`wp db query` (or `wp db export`) in the `wpcli` container fails with "TLS/SSL error: self-signed certificate in certificate chain".*
  The cli image's MySQL client insists on TLS against MySQL 8.4's self-signed certificate. Run SQL through the db container instead
  (`docker compose exec -T db sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE"' < file.sql`) or add `--skip-ssl`.

## RST — capture and restore

- **RST-1** [recon/capture] *curl/WebFetch "certificate has expired" on the host's temp domain.* Use `curl -k` for read-only recon;
  the temp domain dies with the hosting plan, so capture early. (Also the root cause of RST-6.)
- **RST-2** [capture] *A one-click static-export plugin run on the old host produced 7,576 files and zero HTML.* Never trust it; count
  the `.html` files. Capture files + DB and export locally instead.
- **RST-3** [restore] *MariaDB can't import the dump.* The dump uses `utf8mb4_0900_ai_ci`; run **MySQL** at the host's version.
- **RST-4** [restore] *Errors from `object-cache.php` / Redis.* Old-host drop-ins (`wp-content/object-cache.php`, `mu-plugins/`,
  `db-error.php`) must never be copied locally.
- **RST-5** [restore, Elementor] *Old host still referenced in Elementor pages after `search-replace`.* Elementor stores URLs JSON-escaped
  (`http:\/\/host`); replace both forms (`setup.sh` does) and flush Elementor CSS.
- **RST-6** [restore, Elementor] *A web font silently fails.* Elementor's self-hosted Google-font CSS (`uploads/elementor/google-fonts/css/*.css`)
  hard-codes absolute URLs to the old host *inside the files*; DB search-replace can't reach them. `setup.sh` `sed`s them. Here the
  first baseline had the heading font broken for exactly this reason (the host's cert was expired).
- **RST-7** [restore] *Every request logs failing `ALTER TABLE` for a missing table.* The dump lacked a visitor plugin's tables; harmless
  once the plugin is removed.
- **RST-8** [capture] *Secrets and PII sit in the raw download.* `wp-config.php`, `keys/private.pem`, vendor keys, error logs; user
  hashes, visitor IPs, spam comments in the SQL. Gitignore `archive/`; track only a scrubbed seed.
- **RST-9** [restore] *A plugin that crawls its own URL fails in Docker.* `localhost` inside the container must be the web server:
  keep Apache on 80 and publish 80 (`http://localhost`). Not needed once export is our own crawler on the host.

## VIS — baseline and the visual harness

- **VIS-1** [baseline] *"0.000% on all pages" while three pages were taller than the capture window.* The first harness used a 6000 px
  window; home (7,988 px), formula and a post were taller, so the contact form at the bottom of Home was never compared. Window now 10000 px
  (Chrome caps at 16,384), `visual.py` warns when the bottom rows aren't uniform background. **Measure real page heights**
  (`visual.py` cdp mode prints them; VIS-8) before trusting a result; state what a check did *not* cover.
- **VIS-2** [baseline] *Layout jitters between identical runs.* Warm + identical state = pixel-identical (noise floor 0.000%); right after
  a plugin toggle, CSS flush or restart a TablePress/DataTables page shifts ~1 px per table (5% of the page) and flips between layouts.
  Warm every page (`curl` loop) first; re-shoot before blaming a change; a known-flaky page passes if it matches *any* known layout.
- **VIS-3** [baseline] *Headless Chrome hangs for minutes.* `--virtual-time-budget` hung >180 s against the slow WordPress server; use
  `--timeout=20000`. Virtual time was no better against the static server.
- **VIS-4** [export] *Random 5–60% "differences" on the static site, different pages each run, while a real browser looked fine.* Three
  parallel headless Chromes against an instantly-responding server broke Elementor's JS init in the shots (the slow WP server had masked
  it). Capture serially: `SHOT_WORKERS=1`. Verify a suspicious page in the real browser (6 reloads, same JS state) before touching the site.
- **VIS-5** [baseline] *Screenshot process never exits on very tall pages.* `visual.py` kills the process tree on timeout and accepts the
  PNG if it was written.
- **VIS-6** [prune] *The baseline can itself be wrong* (VIS: broken web font, see RST-6). A difference "vs baseline" needs an explanation,
  not just a verdict; sometimes the new state is the correct one.
- **VIS-7** [baseline] *Prove the harness can fail.* Run it once against a change you know is visible; the Home form region not appearing
  in a diff was what exposed VIS-1.

- **VIS-8** [baseline] *A "full-page" screenshot shows one giant hero section; the page is "9,000 px tall" in the capture but ~7,000 px in a browser.*
  Page builders size sections in viewport units (`min-height: 90vh`). A capture window as tall as the page makes 1 vh = the page height, so every such
  section stretches: the shot is of a layout no visitor sees, the real page is cut off, and "0.000%" proves nothing about the parts below the first
  section. Capture at a normal viewport (1280×800) and take the full height from the surface: `visual.py`'s default `SHOT_MODE=cdp` (`_cdp.py`), which
  also prints each page's real height (replacing the guess in VIS-1). Check any capture against `document.documentElement.scrollHeight` at 1280×800 in a
  real browser. Iframes are not a measurement tool for this: viewport units resolve against the iframe's own height. `SHOT_MODE=window` is the legacy
  tall-window mode, valid only when no section uses viewport units. Found on the first Divi site.
- **VIS-9** [export] *Desktop parity is 0.000% but a phone shows a broken icon.* Responsive breakpoints are separate layouts: elements that exist only
  at narrow widths (a footer social row, the mobile menu) are not in a 1280 px capture. Repeat the WordPress-vs-static comparison at 390 px
  (`SHOT_WIDTH=390 SHOT_VIEWPORT_HEIGHT=844`, new labels) before calling parity proven. Found on the first Divi site, where it exposed EXP-11.
## PRN — pruning plugins

- **PRN-1** [prune] *Removing the form plugin prints the literal `[form id="44"]` on Contact and blanks a widget on Home.* Replace the
  form with a deliberate notice first (`archive-form-notice.php.example`, idempotent, edits Elementor data of the live pages, wording as constants).
  The Contact "form" was a text widget holding a pasted shortcode, Home's a plugin widget — inspect the Elementor tree before editing.
- **PRN-2** [prune] *`wp plugin delete` leaves tables.* It runs uninstall hooks but the plugin's tables (and prefix-less ones) remain: that
  list is the scrub's drop list (DB phase).
- **PRN-3** [prune] *A tracker plugin was also the page's only third-party script* (a CDN chart library) — removing it removed a runtime
  dependency.
- **PRN-4** [prune] *"Plugin X leaks CSS into tables" (5% `about` diff).* It didn't: cold-render jitter (VIS-2). Bisect by toggling one
  plugin and re-shooting warm; the final state without X matched the baseline exactly.
- **PRN-5** [prune] *Revisions still carry the old form/content.* Prune and edit only live pages; the revisions go in the scrub.
- **PRN-6** [prune] *Batch the proof loop.* Group obviously-dead plugins (trackers, host helpers, SEO toggles, template importers), then block
  libraries with zero uses in content, then inactive plugins; `check.sh` after each; bisect only on a real diff.

## DB — scrub and seed

- **DB-1** [scrub] *Nothing may boot WordPress between the scrub and the seed dump.* WP-CLI or a page view makes plugins re-create option
  rows (Freemius `fs_accounts`, an export plugin's key) inside the dump. `scrub.sh` dumps first, boots WP after.
- **DB-2** [scrub, Elementor] *Deleted an option I took for a cache — a font fell back to Google's CDN.* `_elementor_local_google_fonts` is a **registry**
  of self-hosted fonts. Group all options by prefix and decide per family before deleting; keep registries, delete caches/logs/keys.
- **DB-3** [scrub] *Differences vs the first baseline after the scrub.* Attribute each one: the owner's own wp-admin edits (a trashed sample
  comment), a real fix (the font), the intended change (notices). Keep dated DB backups to prove which.
- **DB-4** [scrub] *PII/credentials in the seed.* Audit before committing: emails, IPv4s, `$P$`/`$wp$` hashes, key/secret/token markers,
  `session_tokens`. Users get an unusable password hash and placeholder emails; `admin_email` was the owner's real address; the local
  admin is deleted before the dump and recreated by `setup.sh`; comments keep only approved ones with email/IP/agent blanked.
- **DB-5** [scrub] *Prove the seed.* Wipe `.data/mysql`, `up`, `setup.sh`, re-shoot: all pages identical (flaky ones aside).
- **DB-6** [scrub] *The DB re-bloats.* `WP_POST_REVISIONS=false`, `EMPTY_TRASH_DAYS=0` in the compose config; ~700 of 760 `posts` rows were
  revisions here.
- **DB-7** [scrub] *Unscrubbed copies pile up in `.data/backup/`.* They hold hashes and visitor logs; delete them once the archive zip is stored.

## EXP — static export

- **EXP-1** [export, Elementor] *Pages with slideshows / stretched sections render wrong on the static site.* Elementor lazy-loads JS chunks
  (`assets/js/chunks/*.min.js`) at runtime; no parser sees them. Serve `site/` with `serve-site.py`, read its 404 log, add the paths to
  `scripts/export-extra-urls.txt` (all 23 chunk files are listed — reusable for any Elementor 4.3 site, regenerate from the plugin dir).
- **EXP-2** [export] *Query strings as filenames.* `style.css?ver=1.2` becomes `style.css@ver=1.2` under wget on Windows and loses its MIME
  type. The crawler drops queries; Cloudflare ignores them for asset matching.
- **EXP-3** [export] *`localhost` left in CSS/JS/JSON.* Rewrite the origin in **every** text file, plain and JSON-escaped, to root-relative;
  make canonical/OG URLs absolute on the final host.
- **EXP-4** [export, Elementor] *Noise in HTML diffs.* Elementor's `elementorFrontendConfig` line carries a per-render token; TablePress prints
  `from cache` comments; WPForms honeypot labels are random. Not changes.
- **EXP-5** [export] *`serve-site.py` is a local test server only.* Cloudflare never runs it; it exists to surface 404s. Any JS file in
  `site/` works on Cloudflare.
- **EXP-6** [export] *Simply Static (free) is the wrong tool here:* no WP-CLI command, runs as a background queue in the web container,
  output 192.5 MB / 4,026 files (whole plugin trees, every thumbnail), `localhost` left in 29 files, WP cruft intact. The 232-file crawler
  output is the same site.
- **EXP-7** [export] *`robots.txt` `Disallow: /` hides the `X-Robots-Tag: noindex` header.* Ship `Allow: /` and rely on the header (and
  WordPress's own noindex meta while `blog_public=0`).
- **EXP-8** [export] *Broken links that were always broken.* The crawl surfaces them (a `href` starting with an encoded space); fix in the
  DB (post_content **and** Elementor data), not in `site/`.
- **EXP-9** [export] *WordPress's default favicon ships when no Site Icon is set.* Add a favicon via `overlay/` (+ `<link rel=icon>` tags).
- **EXP-10** [export] *Third-party runtime requests remain* (Google Fonts, Gravatar). A decision, not a bug: here accepted (worst case
  fallback fonts / missing avatars). `check-site.py` lists them.
- **EXP-11** [export] *An icon font (or any `url()` in inline CSS) is missing on the static site, yet the static server's 404 log is empty.*
  Inline CSS can use protocol-relative URLs (`url(//localhost/wp-content/…)`); a rewrite that only handles `http(s)://host` and JSON-escaped `\/` leaves them, and
  the browser resolves them to the *other* server (WordPress on port 80, still running) cross-origin, where fonts are blocked by CORS: a missing glyph, no 404.
  Fixed in `export.py` (`//host/` → `/`) and flagged by `check-site.py` as `LEAK`. Prove a static copy with **WordPress stopped**
  (`docker compose stop wordpress`) so nothing can fall through to it. Found on the first Divi site.
- **EXP-12** [export] *The 404 page loads CSS no normal page does and those files are missing from `site/`.* The 404 response is fetched separately from the
  crawl (Divi: `et-cache/notfound/*.css`, a customizer CSS with its own `?ver`). `export.py` now crawls what the 404 page references.
- **EXP-13** [export] *Nav links to `/home`, `/contact` pass on the live site but 404 on the static one.* WordPress redirects guessed permalinks (301 to
  `/`, `/contact-us/`); a static host does not. They sit in builder layouts (Divi Theme Builder header/footer are posts of type `et_*_layout`), not in the menu.
  Find them from `check-site.py`'s MISSING list and fix in the DB (`wp search-replace 'href="/home"' 'href="/"'`), never in `site/` (EXP-8).

## IMG — images and the raw mirror

- **IMG-1** [images, Elementor] *Resized background looks zoomed out.* Elementor sections often draw a photo with `background-size: auto` (natural
  pixels). Shrinking it to 1080 px changed the composition (found by the pixel diff). Recompress CSS-background images, never resize
  them; `<img>` elements are safe to downscale.
- **IMG-2** [images] *Pack the originals first.* `pack-raw-images.py` before `optimize_images.py`. The zip is reproducible (sorted,
  fixed timestamps) so unchanged inputs never create a new LFS object.
- **IMG-3** [images] *WebP bigger than the original* for tiny JPEGs: leave them. `x.jpg` and `x.png` both → `x.webp`: collision handled
  (`x-png.webp`).
- **IMG-4** [images] *A pixel threshold hides subtle compression.* `visual.py` ignores per-pixel gray diffs ≤ 24; q82 WebP passes with
  0.000%. For hero photos eyeball the crop too.
- **IMG-5** [images] *Git LFS limits.* GitHub free: 1 GiB storage + 1 GiB/month bandwidth. One 34 MB zip is fine; don't commit changed copies
  casually. Alternative: a GitHub Release asset (no quota, not in clones).
- **IMG-6** [images] *A full-bleed hero photo ends at "q40, size kept (over budget)".* The optimiser keeps CSS-background images at their natural
  size (IMG-1), so a 2560 px photo can only meet the 200 KB budget by dropping quality to q40, which can look soft on a large screen. Parity passes (the diff
  threshold ignores small gray differences: IMG-4), so look at the crop by eye and, if it is poor, raise `--max-kb` for that run or accept a larger file.

## PUB — git, Cloudflare, deploy

- **PUB-1** [publish] *Workers or Pages?* Cloudflare's docs steer new static sites to **Workers static assets**; use `wrangler.jsonc` with
  `assets.directory`, `html_handling: auto-trailing-slash`, `not_found_handling: 404-page`. Verify option names against
  `developers.cloudflare.com/workers/static-assets/` and `/workers/wrangler/configuration/` (they change). Limits: 20,000 files (free), 25 MiB each.
- **PUB-2** [publish] *`custom_domain: true` fails* if the hostname already has an A/CNAME record: delete it first; wrangler creates the record.
- **PUB-3** [publish] *Which wrangler?* An older 3.x install may not parse newer config options in `--dry-run`; `npx wrangler` fetches the current
  4.x. Dry runs create a `.wrangler/` scratch dir (gitignored).
- **PUB-4** [publish] *The `*.workers.dev` URL stays public* unless `workers_dev: false`. Fine with noindex; decide.
- **PUB-5** [publish] *Git rewrites static files.* Mark `site/**` `-text -diff` so bytes deploy exactly and diffs aren't noise.
- **PUB-6** [publish] *Browsers cache favicons for weeks;* a redeploy is not instantly visible.
- **PUB-7** [publish] *Never push or deploy unasked.* The owner runs `git push` and `wrangler deploy`.

## ARC — archive trim and retirement

- **ARC-1** [retire] *Hundreds of MB hide in "media".* `uploads/simply-static` (374 MB), a 62 MB GeoIP database: survey sizes by folder before
  zipping.
- **ARC-2** [retire] *Old snapshots are history, not junk:* move them aside (`archive/historical/`), never delete without asking.
- **ARC-3** [retire] *Premium plugin code can't be re-downloaded* (Gravity Forms, Object Cache Pro): note it in the manifest as unrecoverable.
- **ARC-4** [retire] *`seed-from-archive.sh` needs the full download.* Trim last, after the site is built, scrubbed and deployed.
- **ARC-5** [retire] *The zip contains `wp-config.php` (DB credentials, salts).* Treat it as a secret when storing it.

## SES — habits for an AI-agent session

- **SES-1** Every "verified" must say what it covered (VIS-1). Report corrections as corrections, not quiet fixes.
- **SES-2** Take a backup before any destructive script; scripts take their own first (`scrub.sh`).
- **SES-3** Long jobs: `run_in_background`, then poll with an `until`/`for` loop on the output file; keep the machine quiet during timing-sensitive
  captures (VIS-4).
- **SES-4** Dry-run first for deletions (`trim-archive.py`, `optimize_images.py --dry-run`, `wp search-replace --dry-run`); show the list.
- **SES-5** Keep commits small and logical (tooling / data / site / docs); never push or deploy; a mixed working tree + a cleanup request =
  `git stash`, do the cleanup commit, `git stash pop` with `-c merge.renormalize=true`.
- **SES-6** Update the task plan up front; record each decision in the log when it is made, not at the end.
- **SES-7** When something looks like a plugin's fault, try to falsify it (toggle, re-shoot warm, check in a real browser) before editing.

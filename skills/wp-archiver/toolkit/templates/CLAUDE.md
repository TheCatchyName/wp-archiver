# <site name> — static archive

Static archive of `<old host>` (WordPress), built with the **wp-archiver** skill and served from `<final host>` on Cloudflare.
Local WordPress runs in Docker; the deployable output is `site/`. Process: use the `wp-archiver` skill (start at its `SKILL.md`; one phase file at a time).

| Path | What it is |
| --- | --- |
| `docs/STATUS.md` | Where the run stands: current phase, open decisions, next step. Update before ending a session |
| `docs/DECISIONS.md` | Dated, append-only log of choices made (and by whom). New entries above the `END-OF-LOG` marker |
| `docker-compose.yml`, `docker/` | MySQL + WordPress pinned to the old host's versions on `http://localhost`; `wpcli` tool service |
| `scripts/` | The toolkit (index: the skill's `reference/tool-index.md`) |
| `db/seed.sql` | The scrubbed database seed (raw dump until phase 06; gitignored until then) |
| `site/` | The static site Cloudflare serves. Built by `scripts/build-site.sh`; byte-exact in git, never hand-edit |
| `raw/` | The untouched media library as one reproducible zip + sha256 manifest |
| `overlay/` | Files that exist only in the static build (favicon set) |
| `archive/` | The raw hosting download / trimmed zip. **Secrets. Never tracked, never deleted without the owner's go-ahead** |
| `wrangler.jsonc` | Cloudflare Workers config (assets-only) |

## Hard rules

- The owner runs `git push` and `wrangler deploy`, and any DNS change. Prepare, dry-run, report; never do these unasked.
- Never commit `.env`, anything under `archive/`, or an unscrubbed `db/seed.sql`. Audit the seed for hashes/IPs/keys after every re-dump.
- Never print secrets into the transcript (`docker compose config`, `wp-config.php`).
- LF line endings everywhere (`.gitattributes`); check with `git ls-files --eol`.
- Say what a check did **not** cover. Report corrections as corrections.

## Git workflow

<state the owner's preference here: e.g. "commit directly with Conventional Commits, never push" or "stage only, the owner reviews">

# wp-archiver (the skill repo)

Agent skills + a script toolkit that archive a mostly-static WordPress site as a static site on Cloudflare. **This repo is public-facing and contains no real site's data.** Real archive runs live in sibling folders (one git repo per site, ignored here by the allowlist `.gitignore`); this repo is the reusable extraction.

| Path | What |
|---|---|
| `skills/wp-archiver/` | The workflow skill: `SKILL.md` (router), `phases/NN-*.md`, `reference/` (gotchas, tool index, site config, best practices, case study), `builders/` (page-builder adapters), `toolkit/` (the stack copied into each site repo) |
| `skills/wp-archiver-recon/` | Standalone read-only triage skill |
| `tools/check-docs.py` | Link / gotcha-ID / script-name / syntax checker. Run after any doc or script edit |
| `tools/leak-scan.py` | Scans committable files for private terms (from the untracked `.private-terms`) and generic leaks. Run before every commit |
| `docs/ROADMAP.md`, `AI-DISCLOSURE.md`, `CONTRIBUTING.md` | Human-facing project docs |

## Rules for editing this repo

- **No real site data**: use `example.site`-style placeholders (`old.example.site`, `archive.example.site`, `example-site`). Never copy a real domain, prefix, post ID, dump, log or credential in. Run `python tools/leak-scan.py` before committing.
- **Scripts are `.env`-driven**; per-site values do not get hard-coded. Anything destructive is idempotent and dry-run-first.
- **Keep the skill small and layered**: `SKILL.md` routes, one phase file per step ending on a checkable exit criterion, facts live in one place and are pointed to (see the `writing-for-agents` guidance if you have it).
- **Gotcha IDs are stable**: never renumber; append to the end of an area and cite from the phase that uses it.
- **Honesty about verification**: mark untested paths as untested; keep the "verified / not verified" table in `AI-DISCLOSURE.md` current. The generalised toolkit has been regression-tested on the reference site only, not yet on a second site.
- Run `python tools/check-docs.py` after edits; it must print `0 problems`.
- Commit directly with Conventional Commits; never `git push` unless the owner asks. Agent-assisted commits keep the `Co-Authored-By` trailer.

# Phase 00 — Setup (new site repo + toolkit)

**Goal** an empty repo for the site with the toolkit, a venv and a filled-in `.env`. **Needs** Docker (Desktop or Engine) running, a POSIX shell (Git Bash on Windows), Python 3.11+, git, Chrome or Edge (for screenshots). `git lfs` if the raw media mirror will use LFS. **Produces** a bootstrapped repo. **Gotchas** ENV-1, ENV-3, ENV-9.

## Steps
1. **Create the site repo** as its own folder (one repo per site; ask the owner where). `git init`, then `git config --local core.autocrlf false` (ENV-3). Commit identity, signing and push policy are the owner's: ask once and record it in the site `CLAUDE.md` "Git workflow".
2. **Copy the toolkit** (dotfiles included) from this skill's `toolkit/` into the repo root:
   ```
   cp -r <skill>/toolkit/. <site>/
   mkdir -p <site>/docs && mv <site>/templates/STATUS.md <site>/templates/DECISIONS.md <site>/docs/ \
     && mv <site>/templates/CLAUDE.md <site>/CLAUDE.md && rmdir <site>/templates
   ```
   Fill in the `<…>` placeholders in `CLAUDE.md` and `docs/STATUS.md`. Do **not** create `site/ raw/ db/ overlay/ wp/ .data/ archive/` by hand; scripts make them.
3. **Venv:** `python -m venv .venv`, then `.venv/bin/python -m pip install -r requirements.txt` (Windows: `.venv/Scripts/python`). It needs only Pillow. If using LFS: `git lfs install --local`.
4. **`.env`:** `cp .env.example .env`. Generate the three passwords yourself (`python -c "import secrets; print(secrets.token_urlsafe(18))"`); they are local-only. Leave the source-site facts (versions, prefix, old hosts, theme) for phases 01–03; `COMPOSE_PROJECT_NAME` and `FINAL_URL` can be set now. [`../reference/site-config.md`](../reference/site-config.md) lists every value and where to find it.
5. **Builder assets** (once `BUILDER` is known, usually after recon): `bash <skill>/builders/apply.sh <builder> .` installs the adapter's extra-URL list, directory-only reference list and form-notice example into `scripts/` (idempotent). No adapter needed for a plain theme.
6. **Check the machine:** `docker compose version`; on Windows `netsh interface ipv4 show excludedportrange protocol=tcp` (the stack publishes **port 80**; ENV-1); free disk on the drive that will hold `.data/` (ENV-9).

## Exit criteria
`docker compose config -q` passes (never print the resolved config: ENV-5); `git ls-files --eol` shows only `i/lf w/lf` once files are staged; the venv imports Pillow (`python -c "import PIL"`); `docs/STATUS.md` exists.

## Human decisions
Where the repo lives; the git workflow (commit directly vs stage-only; signing); whether this site is a candidate at all (phase 01).

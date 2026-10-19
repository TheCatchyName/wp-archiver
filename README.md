# wp-archiver

![built with Claude Code](https://img.shields.io/badge/built%20with-Claude%20Code-d97757) ![AI-agent workflow](https://img.shields.io/badge/workflow-AI--agent%20driven-555) ![license MIT](https://img.shields.io/badge/license-MIT-blue)

**Agent skills that turn a mostly-static WordPress site into plain files on Cloudflare — with every step proven against a frozen baseline instead of assumed.**

You are leaving a WordPress host (or just want a fast, patch-free copy of a site nobody edits any more). You have the host's files and a database dump. `wp-archiver` tells an AI coding agent how to: restore the site locally in Docker, prove which plugins are dead by pixel-diffing the render, scrub personal data from the database, crawl the result to static files, optimise the images, and hand you a `site/` folder plus a ready Cloudflare Workers config. **You** decide, push and deploy; the agent does the reversible local work.

> **AI-agent workflow.** This was built by, and is meant to be run by, an AI coding agent ([Claude Code](https://claude.com/claude-code)). It runs commands on your machine. Read [`AI-DISCLOSURE.md`](AI-DISCLOSURE.md) before you use it, in particular what has and has not been tested.

```
example.site (old host)                                          archive.example.site (Cloudflare)
  files + SQL dump ─► Docker restore ─► baseline ─► prune ─► scrub ─► crawl ─► images ─► site/ ─► you deploy
     (you download)   (localhost:80)    (HTML+PNG)  (proof)   (seed)   (static)  (WebP)    (byte-exact)
```

## What is in the box

| Path | What |
|---|---|
| [`skills/wp-archiver/`](skills/wp-archiver/SKILL.md) | The workflow skill: 11 phases (setup → recon → capture → restore → baseline → prune → scrub → export → images → publish → retire), one short file each, plus references |
| [`skills/wp-archiver-recon/`](skills/wp-archiver-recon/SKILL.md) | Standalone read-only triage: *is this site a good candidate?* Needs no Docker or repo |
| [`skills/wp-archiver/toolkit/`](skills/wp-archiver/toolkit/) | The copyable stack the skill installs into a site repo: Docker compose (MySQL + pinned WordPress + WP-CLI), the snapshot / pixel-diff harness, scrub, crawler, image optimiser, archive trimmer |
| [`skills/wp-archiver/reference/gotchas.md`](skills/wp-archiver/reference/gotchas.md) | 83 indexed traps with symptom → cause → fix, so the agent fetches only the area it needs |
| [`skills/wp-archiver/builders/`](skills/wp-archiver/builders/README.md) | Page-builder adapters (Elementor proven; the rest welcome) |
| [`skills/wp-archiver/reference/case-study.md`](skills/wp-archiver/reference/case-study.md) | The reference run: numbers, the ten mistakes an agent made and how each was caught |

## Install

As a Claude Code plugin (replace `<owner>` with the GitHub account hosting this repo):

```
/plugin marketplace add TheCatchyName/wp-archiver
/plugin install wp-archiver@wp-archiver
```

Or copy the skill folders into your personal skills directory:

```bash
cp -r skills/wp-archiver skills/wp-archiver-recon ~/.claude/skills/
```

The skills are plain Markdown plus scripts, so other agents that read `SKILL.md`-style instructions can use them too; the phase files and toolkit do not depend on Claude-specific tools.

## Use

In an empty folder for the new site, with the agent started there:

> Archive the WordPress site at https://old.example.site as a static site on Cloudflare, final host archive.example.site. Use the wp-archiver skill.

The agent runs phase 00 (creates the site repo from the toolkit), recon, then asks you to download the host's `public_html` and a database dump (phase 02) — the one step only you can do. After that it works through restore → baseline → prune → scrub → export → images, stopping at the decision points listed in [`SKILL.md`](skills/wp-archiver/SKILL.md). It will not push, deploy or change DNS.

Just curious whether a site qualifies? Ask: *"Use wp-archiver-recon on https://example.site."*

## Requirements

Docker (Desktop or Engine) · a POSIX shell (Git Bash on Windows) · Python 3.11+ (Pillow is the only dependency) · git (+ git-lfs if you keep the raw media mirror in LFS) · Chrome or Edge for screenshots · a Cloudflare account to deploy · an AI coding agent that can run shell commands.

## Status and limits

- **Proven on one site**: a 17-page Elementor site, Windows 10 + Docker Desktop + Git Bash. The generalised toolkit was re-run against that same site and reproduced its output; it has since archived and deployed a second, different site (Divi) end to end, with six gaps found and fixed along the way (what is and isn't verified: [`AI-DISCLOSURE.md`](AI-DISCLOSURE.md)).
- **Not for sites visitors change** — WooCommerce, memberships, LMS, bookings. Recon rejects them.
- Page builders other than Elementor, and macOS/Linux hosts, are untested. The seams are documented; see [`docs/ROADMAP.md`](docs/ROADMAP.md).
- Static output only: forms, search and comments become notices or third-party embeds, by your decision.

## Safety

The raw download contains database credentials, salts, private keys and visitor data. The workflow keeps `archive/`, `.env` and unscrubbed dumps out of git and makes you the only one who can push or deploy — but that is a prompt, not a sandbox. Review what the agent proposes, work from backups, and only archive sites you own or are authorised to archive.

## Contributing

Reports from other builders, hosts and operating systems are the most valuable contribution. See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License and notices

[MIT](LICENSE). WordPress, Elementor, Cloudflare, Docker, Claude and other names are trademarks of their respective owners; this project is independent and is not affiliated with, endorsed by or sponsored by any of them. "WP" in the name abbreviates "WordPress" descriptively.
